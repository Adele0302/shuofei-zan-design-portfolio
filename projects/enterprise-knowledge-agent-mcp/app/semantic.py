"""Optional *real* dense embeddings + persistent local cosine search.

Select EMBEDDING_BACKEND=sentence-transformers or openai explicitly. Offline
baseline never claims semantic similarity when no trained model is installed.
"""
from __future__ import annotations
import os
import struct
from functools import lru_cache
from typing import Any


def model_config() -> tuple[str,str]:
    provider=os.getenv('EMBEDDING_BACKEND','off').strip().lower()
    if provider=='sentence-transformers':
        return provider,os.getenv('LOCAL_EMBEDDING_MODEL','sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
    if provider=='openai':
        return provider,os.getenv('OPENAI_EMBEDDING_MODEL','text-embedding-3-small')
    return 'off',''


@lru_cache(maxsize=2)
def _local_model(name: str):
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(name)

def _encode(texts: list[str]) -> list[list[float]]:
    backend,model=model_config()
    if backend=='off':
        return []
    if backend=='sentence-transformers':
        # Allow normal hub download only when user selects this backend.
        encoder=_local_model(model)
        return encoder.encode(texts,normalize_embeddings=True).tolist()
    if backend=='openai':
        from openai import OpenAI
        if not os.getenv('OPENAI_API_KEY'):
            raise RuntimeError('OPENAI_API_KEY required for OpenAI embeddings')
        results=OpenAI(timeout=25,max_retries=1).embeddings.create(model=model,input=texts)
        return [r.embedding for r in sorted(results.data,key=lambda x:x.index)]
    raise ValueError('invalid embedding backend')


def _normalised(values: list[float]) -> list[float]:
    length=sum(x*x for x in values)**.5
    return [float(x)/length for x in values] if length>1e-9 else []


def index_document(docid: str, workspace: str) -> str:
    backend,model=model_config()
    if backend=='off':
        return 'disabled (lexical only)'
    from app.core import connect
    with connect() as c:
        rows=c.execute('SELECT c.id,c.text FROM chunks c JOIN documents d ON d.id=c.document_id '
                       'WHERE d.id=? AND d.workspace=? ORDER BY c.ordinal',(docid,workspace)).fetchall()
    try:
        vectors=_encode([r['text'] for r in rows])
        if len(vectors)!=len(rows):
            raise RuntimeError('embedding response length mismatch')
        entries=[]
        for row,v in zip(rows,vectors):
            v=_normalised(v)
            if not v:
                raise RuntimeError('embedding contains zero vector')
            entries.append((row['id'],backend+':'+model,len(v),struct.pack('<'+'f'*len(v),*v)))
        with connect() as c:
            c.executemany('INSERT OR REPLACE INTO chunk_vectors(chunk_id,model_id,dimension,vector) '
                          'VALUES (?,?,?,?)',entries)
        return 'indexed:'+backend+':'+model
    except Exception as e:
        # Explicit non-silent degradation; contents remain searchable lexically.
        return 'unavailable:'+type(e).__name__


def semantic_rank(query: str, rows: list[Any]) -> list[tuple[int,float]]:
    backend,model=model_config()
    if backend=='off' or not rows:
        return []
    try:
        from app.core import connect
        with connect() as c:
            vectors=c.execute('SELECT chunk_id,dimension,vector FROM chunk_vectors WHERE model_id=?',
                              (backend+':'+model,)).fetchall()
        lookup={r['chunk_id']:r for r in vectors}
        vec=_normalised(_encode([query])[0])
        if not vec:
            return []
        result=[]
        for i,r in enumerate(rows):
            record=lookup.get(r['id'])
            if not record or record['dimension']!=len(vec):
                continue
            passage=struct.unpack('<'+'f'*len(vec),record['vector'])
            sim=sum(a*b for a,b in zip(vec,passage))
            # Conservative initial threshold, must be tuned for chosen model.
            if sim>=float(os.getenv('DENSE_MIN_SIMILARITY','0.35')):
                result.append((i,sim))
        return sorted(result,key=lambda x:-x[1])
    except Exception:
        return []
