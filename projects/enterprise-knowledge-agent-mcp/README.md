# Enterprise Knowledge Agent · FDE Engineering Portfolio v3

**Document intelligence · RAG · LangGraph · MCP tools · tenant-scoped API · review-gated workflows · reproducible evaluation**

> **Authorship and deployment disclosure.** An AI-assisted engineering portfolio demonstration created at the repository owner's request (October 2026). Source materials and sample procurement policies are synthetic. The owner should run the tests and be able to explain the architecture before representing implementation competency in interviews. **Not an enterprise production service, not real purchasing automation.**

## Watch the whole workflow

```
   Synthetic business policy, supplier memo, BOM change, PDF or DOCX
                          │  upload / parse / size-check / SHA256 dedupe
                          ▼
       Tenant-scoped SQLite document store + source-aware chunks
                          │
                 ┌────────┴─────────┐
                 ▼                  ▼
             BM25 lexical      optional trained dense embeddings
                 │                  │  (local multilingual / OpenAI)
                 └────────┬─────────┘
                       rank fusion (RRF)
                          │
                    citation evidence
                          │
          LangGraph constrained state graph / offline fallback
                          │
            official MCP Python SDK via separate stdio server
                          │
              ┌───────────┴──────────┐
              ▼                      ▼
        grounded answer         local ticket draft
       / justified refusal        (no external side effects)
                                     │
                             human reviewer + API key
                                     │
                            approve / reject locally
                          ┌──────────┴──────────┐
                    audit trace         test + gold-set evaluation
```

### Implemented capabilities and their real limits

| Area | Implementation | Verification |
|---|---|---|
| Data | `.txt`, `.md`, `.pdf`, `.docx`; constrained parsing, chunking, SHA-256 dedup, deletion | Automated tests |
| Baseline RAG | Mixed-language BM25 lexical ranking; source citation and abstention | 10-question **synthetic** retrieval benchmark and eight governance cases |
| Advanced RAG | Opt-in **real embedding provider** via `sentence-transformers` or OpenAI; persistent vectors and reciprocal rank fusion | Vector persistence and fusion tested with deterministic mock embeddings; real model quality **not verified** here |
| Agent | Explicit `route → retrieve → compose → optional draft` state graph via LangGraph; deterministic fallback when package absent | CI matrix runs integration checks under installed dependencies; remote result must be inspected |
| MCP | Separate stdio tool server using **official Python SDK** when installed; limited protocol fallback otherwise | Fallback subprocess tested locally; official client/server smoke test included for CI under SDK 1.x and 2.x |
| Tooling | Knowledge search, document list, draft ticket, ticket lookup | Real stdio subprocess tests |
| Safety | API key RBAC (reader/editor/reviewer/admin), workspace isolation, citations checked, separate human review, no order/payment/email tool | Auth, RBAC, isolation and side-effect tests |
| Observability | Trace UUID, tool trace, request mode, local audit records | Unit/integration tests |
| UI / API | Browser demo + FastAPI Swagger, upload, search, Agent, approvals | HTTP tests |
| Operations | Docker image, localhost-only Compose bind, GitHub Actions test matrix | Docker/CI workflow defined; external deployment not claimed |

## V3 reliability improvements (Oct 21, 2026)

- Official MCP SDK **1.x/2.x** server imports supported; client accepts both camelCase and snake_case result fields. SDK 2.x renamed `FastMCP` to `MCPServer`; the v2 code previously broke at startup with the latest SDK.
- Verified retrieval references now use **immutable document IDs** for ticket evidence. Duplicate filenames are allowed for uploads but **ambiguous old name-only citations cannot authorize a ticket**.
- Dense-vector SQL reads are **workspace-scoped before Python cosine ranking**; a user's search never imports other workspaces' vectors into the ranking pipeline.
- A conservative **prompt-injection quarantine** flags obvious instruction-like text in search results. Flagged snippets are not passed to the LLM and cannot be a basis for autonomous draft creation. This heuristic is not a comprehensive anti-injection solution.
- Added eight reproducible adversarial and governance checks (tenant isolation, ambiguous citations, injection nonexecution, approval replay and abstention). CI treats any failed case as a nonzero exit code.
- Added an SDK-major-version CI matrix and explicit official-MCP/LangGraph checks. **Passing source tests is not proof of deployment quality.**

## Fastest demo (Python 3.11+)

```bash
cd projects/enterprise-knowledge-agent-mcp
python -m venv .venv
# macOS/Linux: source .venv/bin/activate
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/setup_local.py  # securely generates local demo .env keys (ignored by git)
python -m app.cli seed
python -m app.cli ask '采购预算超过5000元需要谁审批？'
python -m app.cli ask '创建工单：供应商A打样出现尺寸偏差，如何处理？'
python -m app.evaluate
python -m app.evaluate_safety
python scripts/demo_acceptance.py  # complete offline tool + review journey
python -m pytest -q
uvicorn app.api:app --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000/**. Enter one of the API keys printed by `scripts/setup_local.py` for the appropriate action; the browser does not persist the key in localStorage. HTTP API schema is at `/docs`.

> `python -m app.cli` is intended for **local trusted terminal use**. API endpoints refuse requests without configured `APP_API_KEYS`; their workspace is derived from the verified token, not user-controlled request payloads. Human approval takes the authenticated reviewer identity, not an arbitrary field from the request.

### Switch on trained semantic embeddings (optional)

The default mode is **lexical only** and needs no model download, paid API or account.

```bash
pip install -r requirements-semantic.txt
# Set in .env: EMBEDDING_BACKEND=sentence-transformers
# Optional: LOCAL_EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
python -m app.cli reindex  # index previously ingested documents
python -m app.cli search '工程变更的审批记录'
```

This downloads an actual multilingual sentence embedding model on first use. Alternative: `EMBEDDING_BACKEND=openai`, with a valid `OPENAI_API_KEY` and `OPENAI_EMBEDDING_MODEL`. Chunk vectors persist in SQLite per model and are **not** mixed across models. Search combines BM25 and cosine similarity by reciprocal rank fusion. When the provider fails, the ingest API explicitly reports `vector_index: unavailable:<error_type>` and search falls back to lexical. **Do not publish real internal documents or use external model providers on confidential data without authorization.**

### SDK / LangGraph verification

`requirements.txt` includes the official `mcp` Python SDK and `langgraph`; when installed, the Agent automatically uses these. For a separate official MCP server:

```bash
python -m app.mcp_official    # stdio protocol, meant to be started by an MCP client
# CLI/API invokes it in an isolated subprocess automatically.
```

`MCP_PROTOCOL=official` requires the SDK and errors if unavailable. `MCP_PROTOCOL=fallback` chooses the smaller educational stdio bridge. Every Agent response reports its actual `mcp_protocol` and `agent_engine`. The core-tools fallback is explicitly **not** a certificate of full MCP protocol compliance.

### Web API example

```bash
# Use the generated editor key locally, never put actual keys in committed files.
curl -H 'X-API-Key: YOUR_EDITOR_KEY' \
  -F 'file=@data/sample_docs/01_采购审批规则.md' \
  http://127.0.0.1:8000/documents/upload

curl -H 'X-API-Key: YOUR_EDITOR_KEY' -H 'Content-Type: application/json' \
  -d '{"question":"创建工单：供应商A打样尺寸偏差怎么办？","create_draft":true}' \
  http://127.0.0.1:8000/agent/ask

# After a human examines the draft, use the distinct REVIEWER key:
curl -X POST -H 'X-API-Key: YOUR_REVIEWER_KEY' \
  -H 'Content-Type: application/json' -d '{}' \
  http://127.0.0.1:8000/tickets/T_REPLACE/approve
```

No real purchase, payment, external ticket system write, email or ERP connection exists. For a standalone, automatically checked proof of the full workflow run `python scripts/demo_acceptance.py`. Its example transcript is in `docs/demo_acceptance_v3.json`.

### Docker on localhost

```bash
python scripts/setup_local.py
mkdir -p local_data
# On Linux, adjust the local_data directory owner to UID 10001 for the non-root image.
docker compose up --build
```

Compose binds `127.0.0.1:8000` only. Do not publish this application over the internet: its API-key demonstration does **not** replace production SSO/OIDC, TLS, centralized rate limiting, encryption at rest, vault-backed credentials, tenant lifecycle, formal audit retention, DLP, or penetration testing.

## Evaluation and debugging

```bash
python -m pytest -q
python -m app.evaluate
python -m app.evaluate_safety
```

The reference evaluation dataset has **8 answerable + 2 unanswerable** questions against **four fictional policy files**. It computes measured `source_hit_at_k`, `MRR@k`, `empty_result_accuracy` and retrieval latency from the code on each run. There is no borrowed benchmark score. This does **not** establish real-world answer correctness, prompt injection immunity, recall under large corpora, or causal agent decision quality. Tests also check tenant isolation, unauthenticated API denial, forbidden approval, missing citations, untrusted document instructions and MCP subprocess calls.

The full integration suite contains `pytest.importorskip` checks for official MCP SDK and LangGraph; installing `requirements.txt` (as CI does) is necessary to run those checks. Local constrained environments may skip them. See [`docs/architecture.md`](docs/architecture.md), [`docs/security.md`](docs/security.md), and [`docs/FDE_resume_bullets.md`](docs/FDE_resume_bullets.md).

## GitHub FDE portfolio / interview use

**Evidence-backed truthful summary:** An AI-assisted, locally testable procurement knowledge Agent demo that parses synthetic procurement/BOM documents, retrieves cited evidence, orchestrates MCP tools, drafts issue tickets for human review, applies API-key workspace scoping and reports reproducible synthetic evaluation metrics. The offline default uses lexical retrieval; a real embedding model and official MCP SDK/LangGraph paths are configurable but should only be claimed as personally verified after reproducing them.

**Never claim:** production-grade SOC2, a deployed customer's data, fully autonomous ordering, personally written independent source code, measured production RAG precision, or official SDK interoperability verified on a machine where the SDK was not installed.

## Reference implementations / acknowledgments

- [Official MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [LangGraph](https://github.com/langchain-ai/langgraph)
- [Sentence Transformers](https://github.com/UKPLab/sentence-transformers)
- [Agentic RAG knowledge assistant (architecture reference)](https://github.com/jayanthlocam/agentic-rag-postgres-mcp)
- [Agentic RAG + MCP (architecture reference)](https://github.com/akulapranisha/agentic-rag-mcp)

The code here is not a wholesale fork of those repositories. Licensing of external implementations and pretrained models remains with their respective maintainers.
