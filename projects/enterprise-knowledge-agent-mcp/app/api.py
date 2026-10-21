"""FastAPI application: upload, grounded Q&A, tickets, audits."""
from __future__ import annotations
import uuid
from fastapi import FastAPI, HTTPException, File, UploadFile
from pydantic import BaseModel, Field
from app.core import add_document, approve_ticket, get_ticket, list_documents, recent_audit
from app.agent import run_agent

app=FastAPI(title='Procurement Knowledge Agent + MCP',version='0.1.0',
            description='Synthetic-data FDE portfolio demo; never places purchases.')

class AskRequest(BaseModel):
    question: str = Field(min_length=2,max_length=1000)
    create_draft: bool = False
    top_k: int = Field(default=4,ge=1,le=10)

class ApprovalRequest(BaseModel):
    approved_by: str = Field(min_length=2,max_length=100)

@app.get('/health')
def health(): return {'status':'ok','llm':'optional','purchase_actions':'disabled'}

@app.get('/documents')
def documents(): return list_documents()

@app.post('/documents/upload')
async def upload(file: UploadFile = File(...)):
    # Size is enforced while reading to protect memory even without content-length.
    data=await file.read(8*1024*1024+1)
    try: return add_document(file.filename or 'untitled.txt',data)
    except (ValueError,UnicodeError) as e: raise HTTPException(status_code=400,detail=str(e))
    except Exception as e: raise HTTPException(status_code=400,detail='failed to parse document') from e

@app.post('/agent/ask')
def ask(body: AskRequest):
    try: return run_agent(body.question,body.create_draft,body.top_k)
    except ValueError as e: raise HTTPException(status_code=400,detail=str(e))

@app.get('/tickets/{ticket_id}')
def ticket(ticket_id: str):
    try: return get_ticket(ticket_id)
    except KeyError: raise HTTPException(status_code=404,detail='ticket not found')

@app.post('/tickets/{ticket_id}/approve')
def approve(ticket_id: str, body: ApprovalRequest):
    try: return approve_ticket(ticket_id,body.approved_by,str(uuid.uuid4()))
    except ValueError as e: raise HTTPException(status_code=409,detail=str(e))

@app.get('/audit')
def audits(): return recent_audit()
