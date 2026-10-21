"""Run end-to-end demo without an HTTP client or API credentials."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from app.core import add_document, list_documents, approve_ticket, search_knowledge
from app.agent import run_agent


def seed(path: Path):
    rows=[]
    for file in sorted(path.iterdir()):
        if file.suffix.lower() in ('.txt','.md','.pdf','.docx'):
            rows.append(add_document(file.name,file.read_bytes()))
    return rows


def main():
    parser=argparse.ArgumentParser(description='Enterprise procurement knowledge agent')
    sub=parser.add_subparsers(dest='action',required=True)
    s=sub.add_parser('seed'); s.add_argument('--path',default='data/sample_docs')
    q=sub.add_parser('ask'); q.add_argument('question');q.add_argument('--draft',action='store_true')
    a=sub.add_parser('approve');a.add_argument('ticket_id');a.add_argument('--by',required=True)
    sub.add_parser('docs')
    opts=parser.parse_args()
    if opts.action=='seed': result=seed(Path(opts.path))
    elif opts.action=='ask': result=run_agent(opts.question,opts.draft)
    elif opts.action=='approve': result=approve_ticket(opts.ticket_id,opts.by,'cli-approval')
    else: result=list_documents()
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
