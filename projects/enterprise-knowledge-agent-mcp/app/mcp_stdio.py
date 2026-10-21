"""Minimal MCP stdio JSON-RPC tool server (protocol 2024-11-05).

This implements core initialize/tools/list/tools/call interoperability without
an extra framework. It is NOT the official MCP SDK; advanced MCP features (e.g.
resources, streaming HTTP, cancellation) are outside this portfolio demo.
"""
from __future__ import annotations
import json
import sys
import traceback
from typing import Any
from app import __version__
from app.core import search_knowledge, draft_ticket, get_ticket, list_documents

TOOLS = [
    {'name':'search_knowledge','description':'Search only ingested procurement documents and return citations.',
     'inputSchema':{'type':'object','properties':{'query':{'type':'string'},'top_k':{'type':'integer','minimum':1,'maximum':10}},'required':['query']}},
    {'name':'list_documents','description':'List ingested document metadata.',
     'inputSchema':{'type':'object','properties':{}}},
    {'name':'create_ticket_draft','description':'Create a LOCAL ticket draft; never submits a purchase or approves a ticket.',
     'inputSchema':{'type':'object','properties':{'title':{'type':'string'},'reason':{'type':'string'},'source':{'type':'string'},'trace_id':{'type':'string'}},'required':['title','reason','source','trace_id']}},
    {'name':'get_ticket','description':'Get local draft or approved ticket status.',
     'inputSchema':{'type':'object','properties':{'ticket_id':{'type':'string'}},'required':['ticket_id']}}
]


def invoke(name: str, args: dict[str,Any]) -> Any:
    if name=='search_knowledge': return search_knowledge(args['query'], int(args.get('top_k', 4)))
    if name=='list_documents': return list_documents()
    if name=='create_ticket_draft': return draft_ticket(args['title'],args['reason'],args['source'],args['trace_id'])
    if name=='get_ticket': return get_ticket(args['ticket_id'])
    raise ValueError('unknown MCP tool')


def handle(req: dict[str, Any]) -> dict[str, Any] | None:
    if 'id' not in req:  # notifications never receive replies
        return None
    ident = req['id']
    method = req.get('method')
    try:
        if method=='initialize':
            result={'protocolVersion':'2024-11-05','capabilities':{'tools':{}},
                    'serverInfo':{'name':'procurement-knowledge-mcp','version':__version__}}
        elif method=='ping': result={}
        elif method=='tools/list': result={'tools':TOOLS}
        elif method=='tools/call':
            params=req.get('params') or {}
            name=params.get('name')
            if name not in {x['name'] for x in TOOLS}:
                raise ValueError('unknown MCP tool')
            output=invoke(name,params.get('arguments') or {})
            result={'content':[{'type':'text','text':json.dumps(output,ensure_ascii=False)}], 'isError':False}
        else:
            return {'jsonrpc':'2.0','id':ident,'error':{'code':-32601,'message':'Method not found'}}
        return {'jsonrpc':'2.0','id':ident,'result':result}
    except (KeyError, TypeError, ValueError) as e:
        if method=='tools/call':
            return {'jsonrpc':'2.0','id':ident,'result':{'content':[{'type':'text','text':str(e)}],'isError':True}}
        return {'jsonrpc':'2.0','id':ident,'error':{'code':-32602,'message':str(e)}}
    except Exception:
        print(traceback.format_exc(),file=sys.stderr)
        return {'jsonrpc':'2.0','id':ident,'error':{'code':-32603,'message':'Internal error'}}


def main() -> None:
    for line in sys.stdin:
        try:
            req=json.loads(line)
            if not isinstance(req,dict):
                continue
            result=handle(req)
            if result is not None:
                print(json.dumps(result,ensure_ascii=False),flush=True)
        except json.JSONDecodeError:
            print(json.dumps({'jsonrpc':'2.0','id':None,'error':{'code':-32700,'message':'Parse error'}}),flush=True)

if __name__=='__main__': main()
