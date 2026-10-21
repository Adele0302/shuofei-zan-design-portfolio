import pytest
from fastapi.testclient import TestClient
from app.api import app
from tests.conftest import KEY_ADMIN,KEY_EDITOR,KEY_REVIEWER,KEY_READER,KEY_B

@pytest.fixture
def client():
    return TestClient(app,headers={'X-API-Key':KEY_ADMIN})


def test_health(client):
    assert client.get('/health').json()['purchase_actions']=='disabled'


def test_auth_required(client):
    assert client.get('/documents',headers={'X-API-Key':'bad'}).status_code == 401
    assert client.get('/documents').status_code == 200


def test_upload_rejects_binary(client):
    assert client.post('/documents/upload',files={'file':('evil.exe',b'content')}).status_code==400


def test_upload_query_and_approve(client):
    data='采购预算超出5000元需要部门负责人和财务审批。'
    r=client.post('/documents/upload',files={'file':('policy.md',data.encode('utf8'))})
    assert r.status_code==200
    ask=client.post('/agent/ask',json={'question':'请创建工单：超过5000元的审批？','create_draft':True})
    assert ask.status_code==200
    item=ask.json()['ticket']
    assert item['status']=='draft'
    assert client.get('/tickets/'+item['id']).status_code==200
    a=client.post('/tickets/'+item['id']+'/approve',json={'note':'reviewed'},
                  headers={'X-API-Key':KEY_REVIEWER})
    assert a.status_code==200 and a.json()['status']=='approved'
    assert a.json()['reviewed_by']=='Human Reviewer'
    assert client.post('/tickets/'+item['id']+'/approve',json={}).status_code==409


def test_bad_ask(client):
    assert client.post('/agent/ask',json={'question':'?'}).status_code==422


def test_reader_cannot_upload_or_create_ticket(client):
    assert client.post('/documents/upload',files={'file':('policy.md',b'anything')},
                       headers={'X-API-Key':KEY_READER}).status_code==403
    assert client.post('/agent/ask',json={'question':'创建工单：这里是什么流程？'},
                       headers={'X-API-Key':KEY_READER}).status_code==403
    assert client.post('/agent/ask',json={'question':'BOM 是什么流程？'},
                       headers={'X-API-Key':KEY_READER}).status_code==200


def test_workspace_isolation(client):
    doc=client.post('/documents/upload',files={'file':('secret.md','供应商A内部报价123.99元'.encode())}).json()
    assert len(client.get('/documents').json())==1
    assert client.get('/documents',headers={'X-API-Key':KEY_B}).json()==[]
    assert client.post('/search',json={'query':'123.99'},headers={'X-API-Key':KEY_B}).json()==[]
    assert client.delete('/documents/'+doc['document_id'],headers={'X-API-Key':KEY_B}).status_code==404
    assert client.delete('/documents/'+doc['document_id']).json()['deleted']
    assert client.post('/search',json={'query':'123.99'}).json()==[]


def test_reviewer_cannot_edit(client):
    assert client.post('/documents/upload',files={'file':('a.md',b'abc')},
                       headers={'X-API-Key':KEY_REVIEWER}).status_code==403


def test_ui_not_embedding_secrets(client):
    res=client.get('/')
    assert res.status_code==200 and 'Agent' in res.text
    assert KEY_ADMIN not in res.text
