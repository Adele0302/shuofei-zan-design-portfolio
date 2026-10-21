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
