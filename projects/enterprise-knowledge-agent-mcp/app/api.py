"""Authenticated workspace-scoped FastAPI surface for FDE demo."""
from __future__ import annotations
import uuid
from pathlib import Path
from fastapi import FastAPI, HTTPException, File, UploadFile, Depends
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from app.core import (add_document, delete_document, approve_ticket, review_ticket,
                      get_ticket, list_documents, recent_audit, search_knowledge)
from app.agent import run_agent, DRAFT_PHRASES
from app.security import Identity,get_identity,need

app=FastAPI(title='Enterprise Knowledge Agent + MCP',version='0.2.0',
            description='Synthetic procurement data; approval is local status only; API key required.')

class AskRequest(BaseModel):
    question:str=Field(min_length=2,max_length=1000)
    create_draft:bool=False
    top_k:int=Field(default=4,ge=1,le=10)

class SearchRequest(BaseModel):
    query:str=Field(min_length=1,max_length=1000)
    top_k:int=Field(default=4,ge=1,le=10)

class ApprovalRequest(BaseModel):
    # No user-supplied approver; authenticated reviewer identity is authoritative.
    note:str=Field(default='',max_length=300)

@app.get('/',response_class=HTMLResponse,include_in_schema=False)
def home():
    return (Path(__file__).parent/'ui'/'index.html').read_text(encoding='utf-8')

@app.get('/health')
def health():
    return {'status':'ok','type':'local portfolio demo','purchase_actions':'disabled',
            'api_auth':'configured' if __import__('os').getenv('APP_API_KEYS') else 'not_configured'}

@app.get('/documents')
def documents(actor:Identity=Depends(get_identity)):
    return list_documents(workspace=actor.workspace)

@app.post('/documents/upload')
async def upload(file:UploadFile=File(...),actor:Identity=Depends(get_identity)):
    need(actor,'editor')
    data=await file.read(8*1024*1024+1)
    try:return add_document(file.filename or 'untitled.txt',data,workspace=actor.workspace)
    except (ValueError,UnicodeError) as e:raise HTTPException(status_code=400,detail=str(e))

@app.delete('/documents/{document_id}')
def remove(document_id:str,actor:Identity=Depends(get_identity)):
    need(actor,'editor')
    if not delete_document(document_id,actor.workspace):
        raise HTTPException(status_code=404,detail='document not found')
    return {'deleted':True,'document_id':document_id}

@app.post('/search')
def search(req:SearchRequest,actor:Identity=Depends(get_identity)):
    return search_knowledge(req.query,req.top_k,workspace=actor.workspace)

@app.post('/agent/ask')
def ask(req:AskRequest,actor:Identity=Depends(get_identity)):
    # Check both explicit flag and phrases to prevent reader from creating drafts.
    will_write=req.create_draft or any(x in req.question.lower() for x in DRAFT_PHRASES)
    if will_write:need(actor,'editor')
    return run_agent(req.question,req.create_draft,req.top_k,workspace=actor.workspace)

@app.get('/tickets/{ticket_id}')
def ticket(ticket_id:str,actor:Identity=Depends(get_identity)):
    try:return get_ticket(ticket_id,workspace=actor.workspace)
    except KeyError:raise HTTPException(status_code=404,detail='ticket not found')

@app.post('/tickets/{ticket_id}/approve')
def approve(ticket_id:str,req:ApprovalRequest,actor:Identity=Depends(get_identity)):
    need(actor,'reviewer')
    try:return approve_ticket(ticket_id,actor.name,str(uuid.uuid4()),workspace=actor.workspace)
    except ValueError as e:raise HTTPException(status_code=409,detail=str(e))

@app.post('/tickets/{ticket_id}/reject')
def reject(ticket_id:str,req:ApprovalRequest,actor:Identity=Depends(get_identity)):
    need(actor,'reviewer')
    try:return review_ticket(ticket_id,actor.name,False,str(uuid.uuid4()),workspace=actor.workspace)
    except ValueError as e:raise HTTPException(status_code=409,detail=str(e))

@app.get('/audit')
def audits(actor:Identity=Depends(get_identity)):
    need(actor,'reviewer')
    return recent_audit(workspace=actor.workspace)
