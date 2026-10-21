"""Tenant-scoped SQLite document store, lexical retrieval and gated ticket lifecycle.

This is a local portfolio proof of concept. Records and approvals are never
connected to actual purchase ordering systems.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sqlite3
import uuid
from collections import Counter
from io import BytesIO
from pathlib import Path
from typing import Any

DB_DEFAULT = 'local_data/knowledge_v2.sqlite3'
ALLOWED_EXTENSIONS = {'.txt', '.md', '.pdf', '.docx'}
MAX_FILE_BYTES = 8 * 1024 * 1024
MAX_TEXT_CHARS = 1_000_000
STOPWORDS = {'and', 'the', 'is', 'of', 'to', 'a', 'in', 'with', 'for', 'what', 'how', 'we',
             'on', 'my', 'does', 'are', 'do', 'can', 'about', 'i', 'an', 'from', 'that', 'this',
             '请问', '什么', '如何', '请', '一下', '关于'}


def workspace_id(workspace: str | None = None) -> str:
    value = workspace if workspace is not None else os.getenv('FDE_WORKSPACE', 'demo')
    if not re.fullmatch(r'[a-zA-Z0-9_-]{1,48}', value or ''):
        raise ValueError('invalid workspace identifier')
    return value


def db_path() -> Path:
    return Path(os.getenv('APP_DB_PATH') or DB_DEFAULT)


def connect() -> sqlite3.Connection:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(path), timeout=10)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA foreign_keys=ON')
    c.execute('PRAGMA busy_timeout=5000')
    return c


def initialize() -> None:
    with connect() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS documents (
          id TEXT PRIMARY KEY, workspace TEXT NOT NULL, filename TEXT NOT NULL,
          sha256 TEXT NOT NULL, added_at TEXT NOT NULL DEFAULT (datetime('now')),
          UNIQUE(workspace,sha256));
        CREATE TABLE IF NOT EXISTS chunks (
          id INTEGER PRIMARY KEY AUTOINCREMENT, document_id TEXT NOT NULL,
          ordinal INTEGER NOT NULL, text TEXT NOT NULL,
          FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS chunk_vectors (
          chunk_id INTEGER NOT NULL, model_id TEXT NOT NULL, dimension INTEGER NOT NULL,
          vector BLOB NOT NULL, PRIMARY KEY (chunk_id,model_id),
          FOREIGN KEY(chunk_id) REFERENCES chunks(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS tickets (
          id TEXT PRIMARY KEY, workspace TEXT NOT NULL, title TEXT NOT NULL,
          reason TEXT NOT NULL, source TEXT NOT NULL,
          status TEXT NOT NULL CHECK(status IN ('draft','approved','rejected')),
          created_at TEXT NOT NULL DEFAULT (datetime('now')),
          reviewed_by TEXT, reviewed_at TEXT);
        CREATE TABLE IF NOT EXISTS audit (
          id INTEGER PRIMARY KEY AUTOINCREMENT, workspace TEXT NOT NULL,
          trace_id TEXT NOT NULL, action TEXT NOT NULL, detail TEXT NOT NULL,
          created_at TEXT NOT NULL DEFAULT (datetime('now')));
        CREATE INDEX IF NOT EXISTS chunks_document_id ON chunks(document_id);
        CREATE INDEX IF NOT EXISTS documents_workspace ON documents(workspace);
        CREATE INDEX IF NOT EXISTS audit_workspace ON audit(workspace);
        CREATE INDEX IF NOT EXISTS tickets_workspace ON tickets(workspace);
        ''')
        # Fail loudly if an old demo DB is reused, rather than silently mixing schema.
        fields = {r['name'] for r in c.execute('PRAGMA table_info(documents)')}
        if 'workspace' not in fields:
            raise RuntimeError('v1 SQLite schema detected; set APP_DB_PATH to a fresh v2 path')


def audit(trace_id: str, action: str, data: dict[str, Any], workspace: str | None = None) -> None:
    w = workspace_id(workspace)
    initialize()
    with connect() as c:
        c.execute('INSERT INTO audit(workspace,trace_id,action,detail) VALUES (?,?,?,?)',
                  (w, trace_id[:80], action[:80], json.dumps(data, ensure_ascii=False)[:4000]))


def tokens(text: str) -> list[str]:
    parts = re.findall(r'[\u3400-\u9fff]+|[a-zA-Z][a-zA-Z0-9_\-]*|\d+(?:\.\d+)?', text.lower())
    out: list[str] = []
    for part in parts:
        if re.fullmatch(r'[\u3400-\u9fff]+', part):
            out.extend([part] if len(part) == 1 else [part[i:i+2] for i in range(len(part)-1)])
        elif part not in STOPWORDS and len(part) > 1:
            out.append(part)
    return out


def chunk_text(text: str, size: int = 650, overlap: int = 90) -> list[str]:
    if not 0 <= overlap < size:
        raise ValueError('invalid chunk overlap')
    text = re.sub(r'\r\n?', '\n', text).strip()
    result, start = [], 0
    while start < len(text):
        end = min(len(text), start + size)
        if end < len(text):
            pivot = max(text.rfind('\n', start + size//2, end),
                        text.rfind('。', start + size//2, end))
            if pivot > start:
                end = pivot + 1
        result.append(text[start:end])
        if end == len(text):
            break
        start = max(start+1, end-overlap)
    return result


def read_document(filename: str, contents: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError('file type must be txt, md, pdf or docx')
    if len(contents) > MAX_FILE_BYTES:
        raise ValueError('file exceeds 8 MiB limit')
    try:
        if suffix in {'.txt', '.md'}:
            text = contents.decode('utf-8-sig')
        elif suffix == '.pdf':
            from pypdf import PdfReader
            reader = PdfReader(BytesIO(contents))
            if len(reader.pages) > 150:
                raise ValueError('PDF exceeds 150-page limit')
            text = '\n'.join(p.extract_text() or '' for p in reader.pages)
        else:
            from docx import Document
            document = Document(BytesIO(contents))
            text = '\n'.join([*(p.text for p in document.paragraphs),
                              *(cell.text for t in document.tables for row in t.rows for cell in row.cells)])
    except (UnicodeError, ValueError):
        raise
    except Exception as e:
        raise ValueError('unsupported, encrypted or malformed document') from e
    if len(text) > MAX_TEXT_CHARS:
        raise ValueError('parsed text exceeds character limit')
    if not text.strip():
        raise ValueError('document contains no extractable text')
    return text


def _safe_filename(name: str) -> str:
    name = Path(name.replace('\\','/')).name[:120]
    name = re.sub(r'[\[\]#\x00-\x1f]', '_', name)
    if not name or name.startswith('.') or Path(name).suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ValueError('invalid filename or extension')
    return name


def add_document(filename: str, contents: bytes, workspace: str | None = None) -> dict[str,Any]:
    w = workspace_id(workspace)
    safe = _safe_filename(filename)
    text = read_document(safe, contents)
    digest = hashlib.sha256(contents).hexdigest()
    docid = hashlib.sha256((w+':'+digest).encode()).hexdigest()[:20]
    initialize()
    chunks = chunk_text(text)
    with connect() as c:
        if c.execute('SELECT id FROM documents WHERE workspace=? AND sha256=?',(w,digest)).fetchone():
            return {'document_id':docid,'filename':safe,'duplicate':True,'chunks':0,'workspace':w}
        c.execute('INSERT INTO documents(id,workspace,filename,sha256) VALUES(?,?,?,?)',(docid,w,safe,digest))
        c.executemany('INSERT INTO chunks(document_id,ordinal,text) VALUES(?,?,?)',
                      [(docid,i+1,item) for i,item in enumerate(chunks)])
    from app.semantic import index_document
    status = index_document(docid, w)   # explicit status if embedding provider is unavailable
    return {'document_id':docid,'filename':safe,'duplicate':False,'chunks':len(chunks),
            'workspace':w,'vector_index':status}


def list_documents(workspace: str | None = None) -> list[dict[str,Any]]:
    w = workspace_id(workspace)
    initialize()
    with connect() as c:
        return [dict(r) for r in c.execute(
            'SELECT d.id,d.filename,d.added_at,COUNT(c.id) AS chunks '
            'FROM documents d LEFT JOIN chunks c ON c.document_id=d.id '
            'WHERE d.workspace=? GROUP BY d.id ORDER BY d.added_at DESC,d.filename',(w,))]


def delete_document(document_id: str, workspace: str | None = None) -> bool:
    w=workspace_id(workspace)
    initialize()
    with connect() as c:
        row=c.execute('DELETE FROM documents WHERE id=? AND workspace=?',(document_id,w))
        return row.rowcount == 1


def _lexical_rank(rows: list[sqlite3.Row], query: str) -> list[tuple[int,float]]:
    q = Counter(tokens(query))
    if not q:
        return []
    corp = [Counter(tokens(r['text'])) for r in rows]
    avg_len = max(1,sum(sum(x.values()) for x in corp)/max(1,len(corp)))
    df: Counter = Counter()
    for ct in corp:
        df.update(set(ct))
    found: list[tuple[int,float]]=[]
    for i,counts in enumerate(corp):
        score=0.0
        length=sum(counts.values())
        for term in q:
            tf=counts.get(term,0)
            if tf:
                idf=math.log(1+(len(rows)-df[term]+.5)/(df[term]+.5))
                score += idf*(tf*2.2)/(tf+1.2*(.25+.75*length/avg_len))
        if score>0:
            found.append((i,score))
    return sorted(found,key=lambda x:-x[1])


def search_knowledge(query: str, top_k: int=4, workspace: str | None=None) -> list[dict[str,Any]]:
    w=workspace_id(workspace)
    if not isinstance(query,str) or not query.strip() or len(query)>1000:
        raise ValueError('query must be 1-1000 characters')
    if not isinstance(top_k,int) or not 1<=top_k<=10:
        raise ValueError('top_k must be 1..10')
    initialize()
    with connect() as c:
        rows=c.execute('SELECT c.id,c.ordinal,c.text,d.filename,d.id AS document_id '
                       'FROM chunks c JOIN documents d ON d.id=c.document_id '
                       'WHERE d.workspace=? ORDER BY c.id',(w,)).fetchall()
    if not rows:
        return []
    lexical=_lexical_rank(rows,query)
    dense=[]
    from app.semantic import semantic_rank
    dense=semantic_rank(query,rows,w)  # [] when disabled/unavailable; never mislabeled semantic
    # Reciprocal rank fusion. Dense similarity gate prevents unrelated matches.
    fused: dict[int,float]={}
    modes: dict[int,set[str]]={}
    for mode,ranking in [('lexical',lexical),('dense',dense)]:
        for rank,(index,_score) in enumerate(ranking[:50],start=1):
            fused[index]=fused.get(index,0)+1/(60+rank)
            modes.setdefault(index,set()).add(mode)
    ranked=sorted(fused,key=lambda i:(-fused[i],rows[i]['filename'],rows[i]['ordinal']))[:top_k]
    return [{'source':rows[i]['filename'],'document_id':rows[i]['document_id'],
             'chunk_id':rows[i]['ordinal'],'citation':f"[{rows[i]['filename']}#c{rows[i]['ordinal']}]",
             'snippet':rows[i]['text'][:800], 'source_ref':f"[{rows[i]['document_id']}#c{rows[i]['ordinal']}]",
             'score':round(fused[i],6),
             'retrieval_mode':'+'.join(sorted(modes[i]))} for i in ranked]


def _valid_source(source: str, workspace: str) -> bool:
    """Resolve an immutable document ID. Legacy filename refs must be unique.

    A user can upload different documents with the *same filename*. A human
    citation is not therefore an adequate authorization reference: silently
    accepting it could attach evidence from an entirely different document.
    """
    match=re.fullmatch(r'\[([^\[\]#]+)#c(\d+)\]',source)
    if not match:
        return False
    marker,ordinal=match[1],int(match[2])
    with connect() as c:
        if re.fullmatch(r'[0-9a-f]{20}',marker):
            row=c.execute('SELECT COUNT(*) FROM chunks c JOIN documents d ON d.id=c.document_id '
                          'WHERE d.workspace=? AND d.id=? AND c.ordinal=?',
                          (workspace,marker,ordinal)).fetchone()
        else:
            row=c.execute('SELECT COUNT(*) FROM chunks c JOIN documents d ON d.id=c.document_id '
                          'WHERE d.workspace=? AND d.filename=? AND c.ordinal=?',
                          (workspace,marker,ordinal)).fetchone()
    return row[0]==1


def draft_ticket(title: str, reason: str, source: str, trace_id: str,
                 workspace: str | None=None) -> dict[str,Any]:
    w=workspace_id(workspace)
    title,reason,source=(str(x).strip() for x in (title,reason,source))
    if not (5<=len(title)<=160 and 10<=len(reason)<=1200):
        raise ValueError('ticket title or reason length invalid')
    initialize()
    if not _valid_source(source,w):
        raise ValueError('source must reference a document within this workspace')
    tid='T-'+uuid.uuid4().hex[:12].upper()
    with connect() as c:
        c.execute('INSERT INTO tickets(id,workspace,title,reason,source,status) VALUES (?,?,?,?,?,?)',
                  (tid,w,title,reason,source,'draft'))
    audit(trace_id,'ticket_drafted',{'ticket_id':tid,'source':source},w)
    return get_ticket(tid,w)


def get_ticket(ticket_id: str, workspace: str | None=None) -> dict[str,Any]:
    w=workspace_id(workspace)
    initialize()
    with connect() as c:
        row=c.execute('SELECT * FROM tickets WHERE id=? AND workspace=?',(ticket_id,w)).fetchone()
    if row is None:
        raise KeyError('ticket not found')
    return dict(row)


def review_ticket(ticket_id: str, reviewer: str, approve: bool, trace_id: str,
                  workspace: str | None=None) -> dict[str,Any]:
    w=workspace_id(workspace)
    reviewer=reviewer.strip()
    if not 2<=len(reviewer)<=100:
        raise ValueError('reviewer identity must be 2-100 characters')
    with connect() as c:
        cur=c.execute("UPDATE tickets SET status=?, reviewed_by=?, reviewed_at=datetime('now') "
                      "WHERE id=? AND workspace=? AND status='draft'",
                      ('approved' if approve else 'rejected', reviewer,ticket_id,w))
        if cur.rowcount!=1:
            raise ValueError('ticket missing or already reviewed')
    audit(trace_id,'ticket_approved' if approve else 'ticket_rejected',
          {'ticket_id':ticket_id,'reviewer':reviewer},w)
    return get_ticket(ticket_id,w)


def approve_ticket(ticket_id: str, approved_by: str, trace_id: str,
                   workspace: str | None=None) -> dict[str,Any]:
    return review_ticket(ticket_id,approved_by,True,trace_id,workspace)


def recent_audit(limit: int=30, workspace: str | None=None) -> list[dict[str,Any]]:
    w=workspace_id(workspace)
    initialize()
    with connect() as c:
        return [dict(r) for r in c.execute('SELECT trace_id,action,detail,created_at '
                                          'FROM audit WHERE workspace=? ORDER BY id DESC LIMIT ?',
                                          (w,min(100,max(1,limit))))]
