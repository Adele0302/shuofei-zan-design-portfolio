"""Database, retrieval, ingestion, and procurement-tool domain logic.

All supplied documents are untrusted reference data. The only side effects are
local SQLite draft and approval records; no email, payment, or purchase is sent.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sqlite3
import time
import uuid
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DB_DEFAULT = 'local_data/knowledge.sqlite3'
ALLOWED_EXTENSIONS = {'.txt', '.md', '.pdf', '.docx'}
MAX_FILE_BYTES = 8 * 1024 * 1024
MAX_TEXT_CHARS = 1_000_000
STOPWORDS = {'and', 'the', 'is', 'of', 'to', 'a', 'in', 'with', 'for', 'what', 'how', 'we',
             'on', 'my', 'does', 'are', 'do', 'can', 'about', 'i', 'an', 'from', 'that', 'this',
             '请问', '什么', '如何', '请', '一下', '关于'}


def db_path() -> Path:
    return Path(os.environ.get('APP_DB_PATH') or DB_DEFAULT)


def connect() -> sqlite3.Connection:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(path), timeout=10)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA foreign_keys=ON')
    c.execute('PRAGMA busy_timeout=5000')
    return c


def initialize() -> None:
    with connect() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS documents (
          id TEXT PRIMARY KEY, filename TEXT NOT NULL, sha256 TEXT NOT NULL UNIQUE,
          added_at TEXT NOT NULL DEFAULT (datetime('now')));
        CREATE TABLE IF NOT EXISTS chunks (
          id INTEGER PRIMARY KEY AUTOINCREMENT, document_id TEXT NOT NULL,
          ordinal INTEGER NOT NULL, text TEXT NOT NULL,
          FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS tickets (
          id TEXT PRIMARY KEY, title TEXT NOT NULL, reason TEXT NOT NULL,
          source TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('draft','approved')),
          created_at TEXT NOT NULL DEFAULT (datetime('now')),
          approved_by TEXT, approved_at TEXT);
        CREATE TABLE IF NOT EXISTS audit (
          id INTEGER PRIMARY KEY AUTOINCREMENT, trace_id TEXT NOT NULL,
          action TEXT NOT NULL, detail TEXT NOT NULL,
          created_at TEXT NOT NULL DEFAULT (datetime('now')));
        ''')


def audit(trace_id: str, action: str, data: dict[str, Any]) -> None:
    initialize()
    with connect() as c:
        c.execute('INSERT INTO audit(trace_id, action, detail) VALUES (?,?,?)',
                  (trace_id[:80], action[:80], json.dumps(data, ensure_ascii=False)[:4000]))


def tokens(text: str) -> list[str]:
    """Mixed Chinese-English lexical tokens; Chinese overlapping bigrams."""
    parts = re.findall(r'[\u3400-\u9fff]+|[a-zA-Z][a-zA-Z0-9_\-]*|\d+(?:\.\d+)?', text.lower())
    out = []
    for part in parts:
        if re.fullmatch('[\u3400-\u9fff]+', part):
            if len(part) == 1:
                out.append(part)
            else:
                out.extend(part[i:i+2] for i in range(len(part)-1))
        elif part not in STOPWORDS and len(part) > 1:
            out.append(part)
    return out


def chunk_text(text: str, size: int = 650, overlap: int = 90) -> list[str]:
    """Char-based chunks, suitable for mixed CJK/English documents."""
    text = re.sub(r'\r\n?', '\n', text).strip()
    if not text:
        return []
    if not 0 <= overlap < size:
        raise ValueError('overlap must be >=0 and <size')
    results, start = [], 0
    while start < len(text):
        end = min(len(text), start + size)
        if end < len(text):
            pivot = max(text.rfind('\n', start + size // 2, end),
                        text.rfind('。', start + size // 2, end))
            if pivot > start:
                end = pivot + 1
        results.append(text[start:end])
        if end == len(text):
            break
        start = max(start+1, end-overlap)
    return results


def read_document(filename: str, contents: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError('file type must be txt, md, pdf or docx')
    if len(contents) > MAX_FILE_BYTES:
        raise ValueError('file exceeds 8 MiB limit')
    if suffix in {'.txt', '.md'}:
        text = contents.decode('utf-8-sig')
    elif suffix == '.pdf':
        from io import BytesIO
        from pypdf import PdfReader
        text = '\n'.join(p.extract_text() or '' for p in PdfReader(BytesIO(contents)).pages)
    else:
        from io import BytesIO
        from docx import Document
        text = '\n'.join(p.text for p in Document(BytesIO(contents)).paragraphs)
    if len(text) > MAX_TEXT_CHARS:
        raise ValueError('parsed text too large')
    if not text.strip():
        raise ValueError('document contains no extractable text')
    return text


def add_document(filename: str, contents: bytes) -> dict[str, Any]:
    initialize()
    safe = Path(filename.replace('\\', '/')).name[:180]
    text = read_document(safe, contents)
    digest = hashlib.sha256(contents).hexdigest()
    docid = digest[:16]
    with connect() as c:
        if c.execute('SELECT id FROM documents WHERE sha256=?', (digest,)).fetchone():
            return {'document_id': docid, 'filename': safe, 'duplicate': True, 'chunks': 0}
        c.execute('INSERT INTO documents(id,filename,sha256) VALUES (?,?,?)', (docid, safe, digest))
        items = chunk_text(text)
        c.executemany('INSERT INTO chunks(document_id,ordinal,text) VALUES (?,?,?)',
                      [(docid, i+1, chunk) for i, chunk in enumerate(items)])
    return {'document_id': docid, 'filename': safe, 'duplicate': False, 'chunks': len(items)}


def list_documents() -> list[dict[str, Any]]:
    initialize()
    with connect() as c:
        return [dict(row) for row in c.execute(
            'SELECT d.id,d.filename,d.added_at,COUNT(c.id) AS chunks '
            'FROM documents d LEFT JOIN chunks c ON c.document_id=d.id '
            'GROUP BY d.id ORDER BY d.added_at DESC,d.filename')]


def search_knowledge(query: str, top_k: int = 4) -> list[dict[str, Any]]:
    initialize()
    if not isinstance(query, str) or not query.strip():
        raise ValueError('query is required')
    if not 1 <= top_k <= 10 or len(query) > 1000:
        raise ValueError('invalid top_k or query length')
    q = Counter(tokens(query))
    if not q:
        return []
    with connect() as c:
        rows = c.execute('SELECT c.id,c.ordinal,c.text,d.filename,d.id AS document_id '
                         'FROM chunks c JOIN documents d ON d.id=c.document_id').fetchall()
    if not rows:
        return []
    corp = [Counter(tokens(r['text'])) for r in rows]
    avg_len = max(1, sum(sum(x.values()) for x in corp)/len(corp))
    df = Counter()
    for ct in corp:
        df.update(set(ct))
    found = []
    for r, counts in zip(rows, corp):
        score = 0.0
        size = sum(counts.values())
        for term in q:
            tf = counts.get(term, 0)
            if tf:
                idf = math.log(1 + (len(rows)-df[term]+0.5)/(df[term]+0.5))
                score += idf * (tf * 2.2) / (tf + 1.2 * (0.25+0.75*size/avg_len))
        if score > 0:
            found.append({'source': r['filename'], 'document_id':r['document_id'],
                          'chunk_id':r['ordinal'], 'citation':f"[{r['filename']}#c{r['ordinal']}]",
                          'snippet':r['text'][:800], 'score':round(score,4)})
    found.sort(key=lambda x: (-x['score'], x['source'], x['chunk_id']))
    return found[:top_k]


def draft_ticket(title: str, reason: str, source: str, trace_id: str) -> dict[str, Any]:
    initialize()
    title, reason, source = (str(x).strip() for x in (title, reason, source))
    if not (5 <= len(title) <= 160 and 10 <= len(reason) <= 1200):
        raise ValueError('ticket title/reason length invalid')
    if not source or len(source) > 250:
        raise ValueError('a source citation is required')
    ticket_id = 'T-' + uuid.uuid4().hex[:10].upper()
    with connect() as c:
        c.execute('INSERT INTO tickets(id,title,reason,source,status) VALUES (?,?,?,?,?)',
                  (ticket_id,title,reason,source,'draft'))
    audit(trace_id, 'ticket_drafted', {'ticket_id':ticket_id,'source':source})
    return get_ticket(ticket_id)


def get_ticket(ticket_id: str) -> dict[str, Any]:
    initialize()
    with connect() as c:
        row = c.execute('SELECT * FROM tickets WHERE id=?', (ticket_id,)).fetchone()
    if not row:
        raise KeyError('ticket not found')
    return dict(row)


def approve_ticket(ticket_id: str, approved_by: str, trace_id: str) -> dict[str, Any]:
    initialize()
    approver = approved_by.strip()
    if not 2 <= len(approver) <= 100:
        raise ValueError('approved_by must be 2–100 characters')
    with connect() as c:
        cur = c.execute("UPDATE tickets SET status='approved',approved_by=?,approved_at=datetime('now') "
                        "WHERE id=? AND status='draft'", (approver,ticket_id))
        if cur.rowcount != 1:
            raise ValueError('ticket missing or already approved')
    audit(trace_id, 'ticket_approved', {'ticket_id':ticket_id,'approved_by':approver})
    return get_ticket(ticket_id)


def recent_audit(limit: int = 30) -> list[dict[str, Any]]:
    initialize()
    with connect() as c:
        return [dict(r) for r in c.execute('SELECT trace_id,action,detail,created_at FROM audit '
                                          'ORDER BY id DESC LIMIT ?', (min(100,max(1,limit)),))]
