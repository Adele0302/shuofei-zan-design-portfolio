import pytest
from fastapi.testclient import TestClient
from app.api import app

@pytest.fixture
def client(): return TestClient(app)


def test_health(client):
    assert client.get('/health').json()['purchase_actions']=='disabled'


def test_upload_rejects_binary(client):
    r=client.post('/documents/upload',files={'file':('evil.exe',b'content')})
    assert r.status_code==400


def test_upload_query_and_approve(client):
    data='采购预算超出5000元需要部门负责人和财务审批。'
    r=client.post('/documents/upload',files={'file':('policy.md',data.encode('utf8'))})
    assert r.status_code==200
    ask=client.post('/agent/ask',json={'question':'请创建工单：超过5000元的审批？','create_draft':True})
    assert ask.status_code==200
    item=ask.json()['ticket']
    assert item['status']=='draft'
    a=client.post('/tickets/'+item['id']+'/approve',json={'approved_by':'QA reviewer'})
    assert a.status_code==200 and a.json()['status']=='approved'
    assert client.post('/tickets/'+item['id']+'/approve',json={'approved_by':'QA reviewer'}).status_code==409


def test_bad_ask(client):
    assert client.post('/agent/ask',json={'question':'?' }).status_code==422
