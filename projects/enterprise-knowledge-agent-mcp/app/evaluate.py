"""Deterministic synthetic retrieval, refusal, and MCP-tool evaluation.

Measures retrieval hit@k and whether the intended source was returned. Does NOT
purport to measure LLM answer correctness or production security.
"""
from __future__ import annotations
import json
from pathlib import Path
from app.cli import seed
from app.core import search_knowledge
from app.agent import run_agent


def evaluate(path='data/evaluation/gold.json'):
    seed(Path('data/sample_docs'))
    cases=json.loads(Path(path).read_text(encoding='utf-8'))
    details=[]
    for c in cases:
        hits=search_knowledge(c['query'],c.get('top_k',4))
        expected=c.get('source')
        ok=(any(h['source']==expected for h in hits) if expected else not hits)
        details.append({'query':c['query'],'expected_source':expected,
                        'found_sources':[h['source'] for h in hits], 'passed':ok})
    return {'cases':len(cases),'passed':sum(x['passed'] for x in details),
            'hit_rate':round(sum(x['passed'] for x in details)/len(details),4),
            'details':details,'dataset':'synthetic','metric':'source hit@k + empty-result check'}

if __name__=='__main__': print(json.dumps(evaluate(),ensure_ascii=False,indent=2))
