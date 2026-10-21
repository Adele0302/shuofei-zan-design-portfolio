import pytest
from pathlib import Path
from app.cli import seed

@pytest.fixture(autouse=True)
def isolated_db(tmp_path,monkeypatch):
    monkeypatch.setenv('APP_DB_PATH',str(tmp_path/'test.sqlite3'))
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    yield

@pytest.fixture
def seeded():
    seed(Path('data/sample_docs'))
