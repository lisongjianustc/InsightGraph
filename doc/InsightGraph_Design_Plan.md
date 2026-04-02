# 设计方案 / 开发方案文档

## 1. 文档信息
- 项目名称：InsightGraph
- 中文名称：研见图谱
- 文档类型：设计方案 / 开发方案
- 版本：MVP v2.0
- 核心框架：n8n + FastAPI + Dify + Vue3
- 文档状态：已更新（移除 LangGraph，转为 n8n + Dify 组合架构，移除飞书推送，完全基于 Web 端管理）

### 1.2 阶段划分

| 阶段 | 重点目标 | 需求适配说明 |
| --- | --- | --- |
| **Stage 1: 基础设施与骨架** | 跑通核心链路（抓取、数据入库、前后端联通、Dify 基础入库） | （已完成）基于 n8n 定时抓取，FastAPI 落库，Vue3 列表展示 |
| **Stage 2: Web 端阅读体验与 AI 赋能** | 优化前端展示，引入泛读/精读模式与多模态闪念胶囊 | 实现分栏展示、卡片标签化、泛读（大模型摘要）/精读（翻译与对话）、支持选择性入库、闪念胶囊支持多模态文件上传 |
| **Stage 3: 知识图谱网络可视化** | 建立知识点关联，前端可视化图谱 | 基于 D3.js/ECharts 实现知识网络渲染与原文穿透 |

---

## 2. 技术目标

构建一个完全本地化、基于 Web 的个人知识管理与自动化追踪系统（PKM），支持：
- arXiv 论文与 GitHub 仓库等数据源的自动化增量抓取。
- 基于大语言模型（通过 Dify 接入）的泛读摘要与精读对话。
- 碎片化知识与多模态闪念胶囊的管理与存储。
- 动态知识库网络可视化图谱，建立文献与知识点的网状关联。
- 完全本地化的前后端隔离 Web 管理端。

---

## 3. 设计原则

### 3.1 n8n + Dify 组合编排
不再使用单一的 Agent 框架（如 LangGraph），而是利用现成且成熟的工具链：
- **n8n** 负责低代码的定时抓取与初步数据处理流。
- **Dify** 负责复杂的 LLM 工作流（如泛读摘要、翻译总结）和 RAG（检索增强生成）知识库存储。

### 3.2 Web 闭环管理
移除原计划中的飞书/企业微信推送功能，所有的配置、数据浏览、交互阅读、知识库管理等均在 Vue3 前端网页中进行闭环。

---

## 4. 关键技术选型

### 4.1 前端与交互 (Frontend)
- **核心框架**: Vue 3 + Vite
- **UI 样式**: TailwindCSS + Element Plus
- **图表与可视化**: D3.js 或 ECharts (用于知识图谱网络渲染)

### 4.2 后端服务 (Backend)
- **语言框架**: Python 3.11+ + FastAPI (异步非阻塞处理)
- **数据验证**: Pydantic
- **ORM 与数据库迁移**: SQLAlchemy + Alembic

### 4.3 数据层 (Database & Storage)
- **关系型数据库**: PostgreSQL (存储 Feed 记录、标签、图谱边关系)
- **向量与知识库**: 交由 Dify 的内置机制（如 Weaviate 或 pgvector）处理
- **文件存储**: 本地文件系统 (存储多模态文件、PDF等)

### 4.4 自动化与 AI 层
- **工作流抓取**: n8n
- **大模型与 Agent**: Dify (提供 Dataset API 和 Chatbot API)

---

## 5. 总体架构流向

```text
[数据源: arXiv / GitHub]      [用户输入: 文本 / 多模态文件]
         ↓                               ↓
    (n8n 定时抓取)                (Vue3 闪念胶囊上传)
         ↓                               ↓
[FastAPI 核心业务后端 (PostgreSQL 存储与去重)]
         |                               |
         |-------------------------------|
         ↓                               ↓
[Vue3 前端 Web 界面]  <-------->  [Dify AI 引擎与知识库]
 (分栏展示 / 卡片标签)             (向量化入库 / 检索)
 (泛读简析 / 精读对话)             (LLM 总结 / 翻译引擎)
 (图谱网络可视化)
```

### 5.1 Pipeline / Data Flow
- **数据源获取 (Fetcher)**：n8n 每日定时抓取 arXiv 和 GitHub，通过 HTTP POST 推送到 FastAPI。
- **清理与落库 (Backend Ingestion)**：FastAPI 接收推送，进行去重、标准化，并存入 PostgreSQL。
- **前端展示 (UI Presentation)**：Vue3 从 FastAPI 拉取数据，进行双栏分块展示；将 `keywords` 渲染为 Tag。
- **阅读模式处理 (Analyzer/Reader)**：
  - **泛读**：前端请求 FastAPI，FastAPI 调用 Dify Workflow API，生成简要中文分析返回前端。
  - **精读**：前端请求全文翻译，并在右侧直接嵌入 Dify 的对话窗口（或通过 API 自行实现聊天界面），辅助理解。
- **知识库入库 (Knowledge Ingestion)**：用户点击“整合进知识库”时，FastAPI 将文章内容或泛读/精读的衍生总结通过 Dify Dataset API 推送到知识库，并在本地数据库建立图谱节点关联。

---

## 6. 核心功能模块设计

### 6.1 前端交互模块 (Web UI)
- **分栏资讯流 (Feed View)**：区分来源（arXiv/GitHub），提供论文卡片（标题、摘要、标签化关键字）。
- **泛读/精读视图 (Reading Modal)**：
  - 泛读模式展示大模型概括要点。
  - 精读模式提供翻译对照与互动问答。
- **图谱视图 (Graph View)**：利用 ECharts/D3.js 将知识库中的节点（论文、胶囊、分析提取出的知识点）及其关联进行可视化网络展示。支持点击节点查看详情并穿透原文。
- **闪念胶囊 (Capsule Input)**：支持文本框输入，扩展支持图片、PDF 等多模态文件的上传上传至 FastAPI 处理。

### 6.2 核心后端模块 (FastAPI)
- **`/api/feed` 路由**：处理 n8n 的抓取推送 (`POST`) 和前端的拉取 (`GET`)。
- **`/api/knowledge` 路由**：处理知识入库请求，封装与 Dify API 的交互逻辑。
- **`/api/reader` 路由**：封装泛读和精读所需的翻译与大模型总结接口。
- **`/api/graph` 路由**：提供用于前端渲染图谱的 Nodes 和 Edges 数据结构。
- **`/api/capsule` 路由**：接收多模态文件上传，进行 OCR 或文本提取后保存。

### 6.3 Dify AI 模块
- **Dataset (知识库)**：存储用户主动整合进入的知识切片。
- **Chatbot App**：用于精读模式下的互动问答。
- **Workflow App (可选)**：用于泛读模式下的标准格式总结提取。

---

## 7. 数据模型设计 (PostgreSQL)

### 7.1 FeedItem (资讯流表)
- `id`: 主键
- `source`: 来源 (arxiv / github)
- `title`: 标题
- `abstract`: 摘要/内容
- `url`: 原文链接
- `authors`: 作者信息
- `keywords`: 关键字 (JSON 或 Array)
- `published_at`: 发布时间
- `status`: 状态 (未读 / 泛读过 / 精读过 / 已入库)

### 7.2 Capsule (闪念胶囊表)
- `id`: 主键
- `content_type`: 类型 (text, image, pdf, etc.)
- `content`: 文本内容或文件路径
- `created_at`: 创建时间
- `is_ingested`: 是否已同步至知识库

### 7.3 GraphNode & GraphEdge (知识图谱表 - 简化版)
- **GraphNode**: 
  - `id`: 节点ID
  - `type`: 类型 (paper, concept, capsule)
  - `label`: 节点名称
  - `ref_id`: 关联的具体业务表 ID
- **GraphEdge**: 
  - `id`: 边ID
  - `source_node_id`: 起点
  - `target_node_id`: 终点
  - `relation`: 关系描述 (如 `relates_to`, `extracted_from`)

---

## 8. 系统部署设计

- **完全 Docker 化本地部署**：
  - `docker-compose.yml` 统筹 `postgres`, `redis`, `n8n`, `fastapi_backend`。
  - `dify/docker/docker-compose.yaml` 统筹 Dify 相关微服务栈。
  - 前端 Node.js 本地开发启动 (`npm run dev`)，生产环境可通过 Nginx 静态托管。
- **取消飞书等外网回调要求**，实现纯内网本地闭环。