import json
from pathlib import Path
import pytest
from app.cli import seed

KEY_ADMIN='admin-token-for-ci-testing-00000000'
KEY_EDITOR='editor-token-for-ci-testing-0000000'
KEY_REVIEWER='reviewer-token-for-ci-testing-000'
KEY_READER='reader-token-for-ci-testing-00000'
KEY_B='tenant-b-token-for-ci-testing-00000'

@pytest.fixture(autouse=True)
def isolated_db(tmp_path,monkeypatch):
    monkeypatch.setenv('APP_DB_PATH',str(tmp_path/'test-v2.sqlite3'))
    monkeypatch.setenv('APP_API_KEYS',json.dumps({
        KEY_ADMIN:{'workspace':'demo','role':'admin','name':'Admin Reviewer'},
        KEY_EDITOR:{'workspace':'demo','role':'editor','name':'Editor User'},
        KEY_REVIEWER:{'workspace':'demo','role':'reviewer','name':'Human Reviewer'},
        KEY_READER:{'workspace':'demo','role':'reader','name':'Read Only'},
        KEY_B:{'workspace':'tenant_b','role':'admin','name':'Another Admin'}
    }))
    monkeypatch.setenv('EMBEDDING_BACKEND','off')
    monkeypatch.setenv('MCP_PROTOCOL','fallback') # dedicated CI test verifies official SDK
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    yield

@pytest.fixture
def seeded():
    seed(Path('data/sample_docs'))
