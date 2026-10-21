# System Architecture & Safety Boundary

```text
Synthetic Markdown/PDF/DOCX/TXT --upload/CLI--> Document parser + validation
                                             | SHA-256 deduplication + chunking
                                             v
                                      SQLite documents/chunks
                                             |
Browser/API (/agent/ask) --> constrained Agent planner
                                  | MCP stdio JSON-RPC (initialize/tools/call)
                                  v
                          MCP server search_knowledge
                                  |       
                                  v
                        Mixed-language BM25 retrieval
                                  |
                                  v
                  Evidence snippets + file/chunk citation
                                  |
                +-----------------+-----------------+
                |                                   |
           Offline extractive                     Optional LLM
           evidence answer                   (answer wording only)
                |                                   |
                +-----------------+-----------------+
                                  |
                       Client explicitly requests draft?
                           /                  \
                         No                    Yes
                         |                  MCP create_ticket_draft
                         |                    status=draft
                         +----------+-------------+
                                    |
                    Human manually POSTs /tickets/{id}/approve
                              (records local state ONLY)
                                    |
                          Audit log, eval & tests
```

## Threat and failure model

- Uploaded documents are reference data, never executable instructions.
- Agent uses a fixed set of explicit MCP tools; arbitrary shell commands and outbound connectors do not exist.
- Unanswerable questions abstain; optional LLM replies must include citations from retrieved chunks.
- Draft creation requires explicit user intent, and approval is a separate authenticated-in-production human action (demo accepts approver name only).
- The approval endpoint has **no authentication**, so this project must not be exposed publicly or used with real purchasing data.
- SQLite content stays local; no encryption, tenant isolation, rate limiting or production observability included.
- MCP stdio implements core protocol messages; official MCP SDK compatibility was not independently verified in this offline build environment.
- BM25 is lexical (with Chinese bigrams), not a trained embedding model or hybrid dense-vector retriever.
- Model generation is optional; without OPENAI_API_KEY the system returns labeled evidence extracts, not synthetic AI-generated conclusions.
- Synthetic evaluation covers source hit@k and empty retrieval, not business accuracy, fairness, or hallucination resistance guarantees.
