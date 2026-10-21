"""Offline-first end-to-end workflow commands for the demo."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from app.core import (add_document,list_documents,approve_ticket,search_knowledge,
                      connect,workspace_id)
from app.agent import run_agent


def seed(path:Path,workspace:str|None=None):
    if not path.is_dir():
        raise ValueError(f'not a directory: {path}')
    rows=[]
    for filename in sorted(path.iterdir()):
        if filename.is_file() and filename.suffix.lower() in ('.txt','.md','.pdf','.docx'):
            rows.append(add_document(filename.name,filename.read_bytes(),workspace))
    return rows


def reindex(workspace:str|None=None):
    from app.semantic import index_document
    w=workspace_id(workspace)
    with connect() as c:
        rows=c.execute('SELECT id,filename FROM documents WHERE workspace=?',(w,)).fetchall()
    return [{'document':r['filename'],'index_status':index_document(r['id'],w)} for r in rows]


def main():
    parser=argparse.ArgumentParser(description='FDE enterprise knowledge Agent v2')
    parser.add_argument('--workspace',default='demo',help='local workspace (default: demo)')
    sub=parser.add_subparsers(dest='action',required=True)
    sub.add_parser('seed').add_argument('--path',default='data/sample_docs')
    ask=sub.add_parser('ask');ask.add_argument('question');ask.add_argument('--draft',action='store_true')
    ap=sub.add_parser('approve');ap.add_argument('ticket_id');ap.add_argument('--by',required=True)
    sub.add_parser('docs')
    sub.add_parser('reindex')
    search=sub.add_parser('search');search.add_argument('query')
    args=parser.parse_args()
    w=workspace_id(args.workspace)
    if args.action=='seed': result=seed(Path(args.path),w)
    elif args.action=='ask':result=run_agent(args.question,args.draft,workspace=w)
    elif args.action=='approve':result=approve_ticket(args.ticket_id,args.by,'local-cli-review',workspace=w)
    elif args.action=='docs':result=list_documents(w)
    elif args.action=='reindex':result=reindex(w)
    else:result=search_knowledge(args.query,workspace=w)
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
