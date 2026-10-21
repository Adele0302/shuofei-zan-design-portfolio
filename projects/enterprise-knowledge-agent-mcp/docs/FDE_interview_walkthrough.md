# FDE interview walkthrough | 企业知识库与采购问题协同

## 30 秒中文介绍

这是一个针对采购、供应商打样与 BOM 变更流程的 **AI 辅助开发工程演示**，使用完全合成的数据来复现企业客户的知识检索和工单处理问题。我组织了文档导入、分块去重、来源引用、检索、Agent/MCP 工具流程以及独立审核角色，所有工单先保存草稿、不调用真实采购系统。基线是可离线运行的 BM25；可选择启用真实向量编码与 RRF 融合，但没有在本机测试大规模企业数据的向量准确率。测试覆盖权限隔离、来源歧义、提示注入拦截、审批重放和拒答。

## 90-second English explanation

I built and tested an AI-assisted engineering demonstrator for supplier and procurement knowledge workflows, using fictional policy documents rather than confidential company data. A user can ingest a document, retrieve evidence with chunk-level citations, route an issue through a constrained agent and MCP tool interface, and create a ticket draft that requires a separate human review step. The application enforces API-key roles and workspace boundaries and records local audit traces. The default offline retrieval baseline uses lexical BM25; trained embeddings and reciprocal-rank fusion are optional, and I would not claim their accuracy without a representative evaluation dataset. The main engineering trade-off is to keep write operations deterministic and outside of retrieved-document instructions. This is a demonstration and AI-assisted implementation, not a production enterprise deployment.

## Live demo: 4 minutes

1. **Show architecture** in `README.md` and explain why purchasing actions are deliberately absent.
2. **Run** `python scripts/demo_acceptance.py`. It seeds four synthetic documents, calls the subprocess MCP tool, generates a traceable draft and simulates separate human approval. Confirm `passed: true` and `external_purchase_actions: 0`.
3. **Run** `python -m app.evaluate` and `python -m app.evaluate_safety`. Explain the difference between 10 retrieval questions and eight security/governance regression cases, and why those are not statistical confidence estimates.
4. **Show** a duplicated filename test and the change to an immutable document-ID `source_ref`: users can read a friendly filename citation while write actions require a unique source reference.
5. **Discuss next production constraints:** enterprise SSO/OIDC, rate limits, encryption, vector database, document ACLs, prompt-injection red teaming, monitoring, customer data integration and deployment evidence.

## Technical questions and boundaries

**Why not let the LLM approve a purchase?** Approval needs a separately authenticated human with an independent policy boundary. A source document might contain adversarial instructions; retrieved text must never grant privileges.

**How is this RAG if the default is BM25?** Retrieval-augmented answers can use lexical retrieval; this prototype's offline default is explicitly a lexical RAG baseline, with optional trained semantic embeddings. A vector search result cannot be claimed without enabling and testing a real encoder.

**Why LangGraph and MCP?** LangGraph can express the state machine and tool sequencing. MCP separates the tools into a subprocess and gives a standard interface. When optional dependencies are absent, the project uses a clearly labeled deterministic graph and minimal stdio protocol. Do not mistake that fallback for an official SDK interoperability certification.

**What did you personally do?** This repo was developed with AI assistance at the request of the owner. Be prepared to explain the code and your own testing/modifications, without claiming sole manual authorship.
