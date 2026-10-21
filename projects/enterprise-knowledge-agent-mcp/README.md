# Enterprise Procurement Knowledge Agent · MCP · RAG

**FDE portfolio case study (synthetic data; local demo, not a deployed enterprise product).**

**Authorship disclosure:** Built with AI assistance in October 2026 at the repository owner’s request. Implementation, demo, and test results should be independently reviewed and reproduced by the owner before describing this as their personal engineering work in a job application.

A reproducible workflow based on a procurement/BOM/prototyping use case:

**Ingest documents → retrieve evidence → route through Agent → call real MCP stdio tools → prepare a ticket draft → require separate human approval → log and evaluate.**

## What is implemented

| Capability | Implementation / proof |
|---|---|
| Document input | FastAPI multipart upload or CLI; `.txt`, `.md`, `.pdf`, `.docx`; 8 MiB limit and SHA-256 deduplication |
| Knowledge retrieval | SQLite chunks, mixed Chinese/English tokenization and BM25-style lexical ranking, source+chunk citation |
| Agent | Explicit fixed tool orchestration, abstention, tool trace, safe fallback; optional OpenAI answer phrasing |
| Real MCP calls | Separate MCP stdio JSON-RPC 2024-11-05 server and client: handshake, `tools/list`, `tools/call` |
| MCP tools | `search_knowledge`, `list_documents`, `create_ticket_draft`, `get_ticket` |
| Error handling | File validation, missing evidence refusal, invalid tool, timeouts, duplicate submission checks |
| Human-in-the-loop | Local draft by Agent, separate `POST /tickets/{id}/approve` with approver name; never sends orders/payments |
| Evaluation | Synthetic source-hit@k + abstention cases; unit/integration tests include real MCP subprocess |
| Traceability | Per-request UUID, action trace, SQLite audit events, source citations |

**Scope & honesty:** This is a lightweight **lexical-RAG** baseline, not semantic vector search. It is not a production-grade autonomous LLM agent. `OPENAI_API_KEY` adds constrained grounded answer generation; otherwise answers are explicitly labeled **offline extractive**. The MCP implementation uses core stdio protocol rather than the official SDK. No real company records or credentials are included.

## Quick start

Requires Python **3.11+**. On an internet-connected machine:

```bash
cd projects/enterprise-knowledge-agent-mcp # if opened inside the portfolio repository
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
python -m app.cli seed
python -m app.cli ask '采购预算超过5000元需要谁审批？'
python -m app.cli ask '创建工单：供应商A打样尺寸偏差如何处理？'
python -m app.evaluate
pytest -q
```

Run HTTP API:

```bash
uvicorn app.api:app --reload --host 127.0.0.1 --port 8000
# Interactive API: http://127.0.0.1:8000/docs
```

Demo HTTP:

```bash
curl -F 'file=@data/sample_docs/03_BOM变更与验收.md' http://127.0.0.1:8000/documents/upload
curl -H 'Content-Type: application/json' -d '{"question":"BOM变更需要记录什么？"}' http://127.0.0.1:8000/agent/ask
# Only after explicitly inspecting a draft, approve it manually:
# curl -H 'Content-Type: application/json' -d '{"approved_by":"demo reviewer"}' -X POST http://127.0.0.1:8000/tickets/T-REPLACE/approve
```

MCP tool protocol (core stdio):

```bash
python -m app.mcp_stdio
# Send one JSON request per line, for example:
# {"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"demo","version":"1.0"}}}
```

> The demo contains **fictional procurement rules, prices, suppliers and sample processes**. Do not expose it to the internet: no user authentication/authorization, tenant isolation or encrypted storage have been implemented. API approval modifies a local record only. Never upload confidential real-world enterprise files.

## Demo interview scenario

1. Explain a fictional supplier quote or BOM change scenario and ingest sample documents.
2. Ask a question that requires retrieval; show citation `[filename#c1]` and `tool_trace`.
3. Ask to **create** a supplier issue ticket: its status remains `draft`.
4. Show that approval is a separate operation requiring a human approver.
5. Demonstrate refusal for a question absent from the knowledge base.
6. Run the evaluation suite and explain limitations (small synthetic dataset, BM25 lexical baseline).

## Test evidence & provenance

Run `pytest -q` and `python -m app.evaluate` to reproduce metrics **on your own machine**. No benchmark from other GitHub projects is represented as this project's result. Architecture influenced by the public ecosystem around LangGraph, OpenAI Agents, RAG and MCP; this demonstration's implementation is a self-contained original sample, not a copy of another repository.

For a stronger next version, add official MCP SDK interoperability tests, tenant-isolated authentication, semantic vector retrieval, threat-model-driven prompt-injection evaluations, and a frontend (e.g. Streamlit).

Local verification (2026-10-21): **20/20 automated tests passed**, **10/10 synthetic source-hit/empty-result checks passed**. These are small synthetic baseline results, not a production benchmark. See [`docs/evaluation_summary.json`](docs/evaluation_summary.json) and [`docs/demo_run.json`](docs/demo_run.json).

See [`docs/architecture.md`](docs/architecture.md) for architecture and safety boundaries.
