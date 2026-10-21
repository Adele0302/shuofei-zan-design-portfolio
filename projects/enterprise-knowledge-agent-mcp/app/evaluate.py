"""Reproducible, measured synthetic retrieval benchmark.

Does not claim accuracy on real business corpora; neither generative answer
quality nor prompt-injection robustness follows from source-hit metrics.
"""
from __future__ import annotations
import json
import os
import tempfile
import time
from pathlib import Path
from app.cli import seed
from app.core import search_knowledge


def evaluate(path: str='data/evaluation/gold.json',isolated:bool=True)->dict:
    original=os.environ.get('APP_DB_PATH')
    casefile=Path(path)
    cases=json.loads(casefile.read_text(encoding='utf-8'))
    tmp=tempfile.TemporaryDirectory(prefix='fde_eval_') if isolated else None
    if tmp:os.environ['APP_DB_PATH']=str(Path(tmp.name)/'eval.sqlite3')
    try:
        seed(Path('data/sample_docs'),workspace='eval')
        details=[]
        for case in cases:
            begin=time.monotonic()
            hits=search_knowledge(case['query'],case.get('top_k',4),workspace='eval')
            elapsed=(time.monotonic()-begin)*1000
            expected=case.get('source')
            rank=next((i+1 for i,r in enumerate(hits) if r['source']==expected),0) if expected else 0
            abstained=len(hits)==0
            passed_case=bool(rank) if expected else abstained
            details.append({'question':case['query'],'expected_source':expected,
                            'retrieved_sources':[h['source'] for h in hits],
                            'rank':rank,'passed':passed_case,'latency_ms':round(elapsed,2)})
        positives=[r for r in details if r['expected_source']]
        negatives=[r for r in details if not r['expected_source']]
        pcount=len(positives) or 1
        ncount=len(negatives) or 1
        return {'dataset':'synthetic / 4 fictional Markdown policies',
                'cases':len(details),'passed':sum(r['passed'] for r in details),
                'source_hit_at_k':round(sum(bool(r['rank']) for r in positives)/pcount,4),
                'mrr_at_k':round(sum(1/r['rank'] for r in positives if r['rank'])/pcount,4),
                'empty_result_accuracy':round(sum(r['passed'] for r in negatives)/ncount,4),
                'mean_retrieval_latency_ms':round(sum(r['latency_ms'] for r in details)/max(len(details),1),2),
                'details':details,'scope':'retrieval only; no claims about generative accuracy'}
    finally:
        if original is None:os.environ.pop('APP_DB_PATH',None)
        else:os.environ['APP_DB_PATH']=original
        if tmp:tmp.cleanup()

if __name__=='__main__':
    print(json.dumps(evaluate(),ensure_ascii=False,indent=2))
