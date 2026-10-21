# Security model, limitations and FDE deployment checklist

## Implemented for the portfolio

- Multiple API keys, each mapped server-side to a **role** and **workspace**; constant-time comparison.
- Default fail-closed on unconfigured API keys; health and static UI can be loaded without exposing documents.
- Role-sensitive upload, query, ticket creation and human review.
- Per-workspace SQL queries and validated ticket source references.
- Upload cap: 8 MiB; UTF-8 or parsed PDF/DOCX text only; malformed file rejection.
- No dynamic code execution from corpus content. No arbitrary file-path reads via the API.
- Source-limited answer format, abstention fallback, audit events and individual trace IDs.
- Offline synthetic data and no corporate secrets in git. `.env` ignored by git.

## Known gaps — production blockers

- Static API-key RBAC is a demo substitute, not SSO/OIDC, token expiry or rotation service.
- No centralized rate limiting, encrypted data at rest, per-tenant quota, DLP, multi-factor authentication or SIEM export.
- SQLite is local and single-host; embedding index searches scan rows in Python, without a vector DB index.
- HTTP API is intended for `127.0.0.1` only; no TLS in Compose.
- Official MCP stdio process is trusted locally, not a remote authenticated MCP endpoint.
- No guarantee against prompt injection from documents. Citation presence does not prove every claim's correctness.
- No automated malware scanning of uploaded documents or document-level ACLs inside a workspace.
- No supervised procurement review policies, legal signature workflow or ERP write integrations.
- No formal adversarial red teaming or scale benchmarks; the evaluation set is only ten synthetic queries.

## Production upgrade checklist (not represented as completed)

OIDC & SCIM; TLS reverse proxy; cryptographic per-tenant isolation; short-lived service tokens; async ingestion workers; pgvector/HNSW; distributed tracing; signed document provenance; comprehensive non-LLM policy engine; audit retention; load tests; red-team prompt-injection suite; human-in-the-loop approval via actual business identities; monitoring and rollback.

## V3 regression defenses (2026-10-21)

- Citation-based ticket evidence uses `source_ref` with an immutable document ID. Legacy `[filename#cN]` citations work only when they identify exactly one chunk in the workspace.
- The dense index loads only chunk vectors joined to an authorized workspace's documents. The ranking query no longer loads vectors from all tenants first.
- Source snippets containing obvious adversarial commands are quarantined before optional LLM synthesis or draft-ticket creation. This is a heuristic, **not** a guarantee against indirect prompt injection, document poisoning or jailbreaking.
- The optional paid LLM is kept read-only; the deterministic application code owns every write action. There are no external purchase, email or finance tools.
- Evaluation includes eight scoped negative-case checks: `python -m app.evaluate_safety`; individual cases and limitations are returned in JSON.
- Official MCP Python SDK 2.x renamed the server class. This release attempts v2 import first and provides the v1 fallback, with a version-split CI matrix. The host used for local tests did not have the official SDK installed; only remote CI can verify those integrations.
