# Interview and CV wording (accurate scope)

## 中文（适合 FDE/AI 应用开发类简历）

**Enterprise Knowledge Agent｜企业采购知识库与 MCP 工具原型**（AI 辅助开发个人技术作品，2026）

- 围绕供应商、采购审批与 BOM 变更的合成业务场景，搭建 Python/FastAPI 文档入库、分块去重、来源引用检索与工单草稿工作流；引入工作区隔离和基于 API Key 的角色权限控制。
- 实现本地 BM25 检索基线、可选向量嵌入和 RRF 混合检索接口，以及隔离运行的 MCP 工具调用；将采购问题工单限制为草稿状态，审批由独立人工角色完成。
- 编写单元/API/集成测试与 10 条合成数据检索评测；**本地 32 项通过、2 项可选依赖检查跳过**。LangGraph/官方 MCP SDK 适配代码已提交，需在安装依赖的环境完成复验。

**面试限定：** 项目使用合成资料，属于 AI 协助开发的工程原型；无真实客户部署或实际采购执行能力；默认词法检索，真实向量模型需另行启用。

## English (for MSRA, Feishu and forward-deployed engineering applications)

**Enterprise Knowledge Agent — AI-assisted engineering demonstration (2026)**

- Built a reproducible procurement and supplier-issue workflow using Python, FastAPI and SQLite: document ingestion, chunk-level citations, role-scoped API access, isolated workspaces and human-reviewed ticket drafts.
- Implemented lexical retrieval with an opt-in dense-embedding/RRF extension, MCP tool interfaces and a constrained Agent state graph; excluded external purchasing and autonomous approvals.
- Added automated API, security, retrieval and tool-call tests: **32 passing locally, two optional SDK/graph checks skipped** in the constrained local environment; evaluated retrieval against ten synthetic examples.

**Interview caveat:** AI-assisted portfolio implementation, not personally authored from scratch or deployed for a real enterprise. Official MCP SDK/LangGraph code paths require independent reproduction with installed packages; no production accuracy/security claims.
