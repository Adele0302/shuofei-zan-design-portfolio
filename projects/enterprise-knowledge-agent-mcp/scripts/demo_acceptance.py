"""Offline end-to-end hiring demo, isolated, auditable, no external side effects.

Run: python scripts/demo_acceptance.py [--output demo_result.json]

It does not claim official SDK/LLM interoperability; reports actual engine/protocol.
"""
from __future__ import annotations
import argparse
import json
import os
import tempfile
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.cli import seed
from app.agent import run_agent
from app.core import approve_ticket, list_documents


def main(output:str|None=None)->dict:
    old={k:os.environ.get(k) for k in ('APP_DB_PATH','EMBEDDING_BACKEND','OPENAI_API_KEY','MCP_PROTOCOL')}
    with tempfile.TemporaryDirectory(prefix='fde_demo_flow_') as directory:
        os.environ['APP_DB_PATH']=str(Path(directory)/'knowledge.sqlite3')
        os.environ['EMBEDDING_BACKEND']='off'
        os.environ['MCP_PROTOCOL']='fallback'  # explicit, truthful deterministic stdio demonstration
        os.environ.pop('OPENAI_API_KEY',None)
        try:
            seeded=seed(Path('data/sample_docs'),workspace='demo')
            question='创建工单：供应商A打样尺寸偏差，处理流程是什么？'
            result=run_agent(question,create_draft=True,workspace='demo')
            ticket=result.get('ticket')
            if not ticket:
                raise RuntimeError('No ticket was created: inspect retrieved evidence / MCP trace')
            reviewed=approve_ticket(ticket['id'],'Independent Demo Reviewer','demo-acceptance',workspace='demo')
            output_data={'demo':'synthetic/offline full journey',
                         'documents':len(list_documents('demo')),
                         'question':question,
                         'answer_mode':result['mode'],
                         'agent_engine':result['agent_engine'],
                         'mcp_protocol':result['mcp_protocol'],
                         'citations':[h['citation'] for h in result['sources']],
                         'source_refs':[h['source_ref'] for h in result['sources']],
                         'tool_trace':result['tool_trace'],
                         'ticket_id':ticket['id'],'ticket_before':ticket['status'],
                         'ticket_after':reviewed['status'],
                         'external_purchase_actions':0,
                         'passed':reviewed['status']=='approved' and ticket['status']=='draft'}
            if output:Path(output).write_text(json.dumps(output_data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            return output_data
        finally:
            for k,v in old.items():
                if v is None:os.environ.pop(k,None)
                else:os.environ[k]=v

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',help='Optional JSON output path')
    args=parser.parse_args()
    r=main(args.output)
    print(json.dumps(r,ensure_ascii=False,indent=2))
    if not r['passed']:raise SystemExit(1)
