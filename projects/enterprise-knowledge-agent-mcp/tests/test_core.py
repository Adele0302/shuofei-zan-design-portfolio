import pytest
from app.core import (add_document, search_knowledge, list_documents, draft_ticket,
                      approve_ticket, get_ticket, chunk_text, read_document)


def test_chunking_is_bounded():
    chunks=chunk_text('a'*1500, 650, 90)
    assert all(len(c)<=650 for c in chunks)
    assert len(chunks)>1


def test_ingest_and_deduplicate():
    a=add_document('policy.md','超过5000元需要财务审批'.encode())
    b=add_document('policy.md','超过5000元需要财务审批'.encode())
    assert a['chunks']==1 and b['duplicate'] and len(list_documents())==1


def test_bad_file_type():
    with pytest.raises(ValueError): add_document('malware.exe',b'hi')


def test_empty_document():
    with pytest.raises(ValueError): add_document('x.txt',b'   ')


def test_file_size_limit():
    with pytest.raises(ValueError): read_document('a.txt',b'x'*(8*1024*1024+1))


def test_search_returns_citation(seeded):
    hits=search_knowledge('BOM 工程更改单 ECO')
    assert hits and hits[0]['source']=='03_BOM变更与验收.md'
    assert hits[0]['citation'].startswith('[03_')


def test_search_abstains_without_docs():
    assert search_knowledge('不存在的问题')==[]


def test_invalid_topk(seeded):
    with pytest.raises(ValueError): search_knowledge('采购',99)


def test_ticket_requires_approval():
    add_document('supplier.md','供应商延误超过3个工作日需要处理'.encode())
    t=draft_ticket('供应商延期整改','供应商延误超过3个工作日需要处理','[supplier.md#c1]','trace')
    assert t['status']=='draft' and t['reviewed_at'] is None
    approved=approve_ticket(t['id'],'Demo Reviewer','trace-approve')
    assert approved['status']=='approved' and approved['reviewed_by']=='Demo Reviewer'
    with pytest.raises(ValueError): approve_ticket(t['id'],'Demo Reviewer','trace-again')


def test_ticket_source_required():
    with pytest.raises(ValueError): draft_ticket('更新采购流程','请重新审批采购流程','','trace')
