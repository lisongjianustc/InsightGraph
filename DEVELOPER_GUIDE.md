# InsightGraph 开发者架构与全景文档 (Developer Guide)

欢迎来到 **InsightGraph**！本项目旨在打造一个高度智能化、自动化且支持多租户隔离的个人/团队“第二大脑”系统。
这份文档为从未接触过本项目的开发者编写，旨在让你能够快速理解项目的整体架构、设计哲学、技术选型以及核心模块的具体实现。

---

## 1. 🌟 项目愿景与设计理念 (Design Philosophy)

InsightGraph 的诞生是为了解决知识管理中存在的两个核心痛点：“输入摩擦力过大”与“知识变成死水”。为此，项目贯彻了以下几个核心设计理念：

1.  **Frictionless Capture (零摩擦摄入)**：
    支持全模态的文件拖拽（PDF/Word/Excel）、图片一键粘贴OCR、系统级全局输入框（Spotlight），把知识记录的阻力降至最低。
2.  **AI Librarian (AI 图书管理员)**：
    不依赖人类手动打标签或翻阅历史笔记。在书写每日日记时，系统会在后台通过防抖技术静默调用 Dify 的 RAG（检索增强生成）引擎，将最相关的历史胶囊和文献“主动推送”给用户。
3.  **Block-level Reference (块级高亮引用)**：
    提供比“引用整篇文章”更细颗粒度的块级引用。在阅读文献时划选文字提取为“高亮胶囊”，并在写作时通过 `((` 极客语法呼出，极大降低大模型的 Token 消耗和幻觉。
4.  **Multi-Tenant Privacy (多租户与隐私隔离)**：
    架构支持团队模式。数据库层面通过 `owner_id` 进行数据隔离，AI 引擎（Dify）层面为每个用户动态创建专属的 `Private Dataset`，辅以团队公共库，实现公私知识的安全交融。

---

## 2. 🏗 系统整体架构 (System Architecture)

系统采用前后端完全分离架构，依托 Docker Compose 进行一键编排。

*   **🎨 前端 (Frontend)**：
    *   **框架**：Vue 3 (Composition API) + Vite 5 + TypeScript。
    *   **UI 组件**：Element Plus + Tailwind CSS。
    *   **核心模块**：
        *   `ByteMD`：用于提供 Typora 级别的所见即所得 Markdown 沉浸式编辑体验（支持数学公式、代码高亮）。
        *   `VueOffice`：用于在纯前端实现 PDF、Word、Excel 等原生文档的高清预览，无需繁琐的后端转换。
        *   `ECharts`：用于驱动数千级节点的动态知识图谱和万物引力连线。
    *   **桌面端引擎**：Electron。封装前端代码为原生 Mac/Windows 应用，提供系统级沙盒穿透能力。
*   **⚙️ 后端 (Backend)**：
    *   **框架**：FastAPI。提供极速的异步 RESTful 接口和 SSE 流式推送。
    *   **ORM**：SQLAlchemy 2.0 (配合 Alembic 进行数据库迁移) + Pydantic v2 (数据校验)。
    *   **异步调度**：APScheduler，负责文献拉取、定时摘要生成等守护进程。
*   **🧠 AI 引擎底座 (Dify)**：
    *   所有的文本向量化 (Embedding)、RAG 知识库检索、多模态大模型视觉识别 (OCR) 和大模型重写任务，全部委托给本地或云端的 Dify 实例执行。
    *   后端通过 `DifyService` (`app/services/dify_service.py`) 模块，封装对 Dify 官方 API 的请求。
*   **💾 数据与存储 (Databases)**：
    *   **主关系型数据库**：PostgreSQL (可加载 PgVector 扩展以支持向量索引，但本项目主要将向量托管在 Dify 的 Weaviate/Qdrant 中)。
    *   **键值缓存**：Redis 7 (用于流式状态保持和高频访问缓存)。

---

## 3. 🗄️ 数据库核心模型结构 (Database Schema)

数据库实体均定义在 `backend/app/models/` 目录下，所有核心业务表都包含 `owner_id`（外键关联 `users.id`）和 `visibility`（`public` 或 `private`）以实现权限隔离。

1.  **User (`users`)**
    *   `id`, `username`, `hashed_password`, `email`, `is_admin`
    *   `dify_private_dataset_id`：绑定在 Dify 系统中专属于该用户的私有知识库 ID。
2.  **DailyNote (`daily_notes`)**
    *   `date`: 笔记日期（唯一标识）。
    *   `content`: Markdown 格式正文，可包含 `[[capsule:id]]` 的块级引用语法。
    *   `category`: 所属的分类（如“日常思考”、“项目记录”）。
    *   `dify_document_id`: 同步到 Dify 后返回的索引 ID。
3.  **Capsule (`capsules`)**
    *   用于存储用户的“闪念”或“高亮片段”。
    *   `title`, `content`
    *   `file_url`, `file_type`: 拖拽上传的原生文件路径与格式。
4.  **FeedItem (`feed_items`)**
    *   外部拉取（如 arXiv、RSS）的资讯或精读文献。
    *   `source`, `title`, `content`, `url`, `raw_data`
    *   `full_text`: PDF 解析出的完整正文。
    *   `skim_summary`: AI 泛读提炼出的核心要点摘要。
    *   `translated_content`, `translated_pdf_url`: 文档翻译与双语对照的产物。
5.  **GraphNode & GraphEdge (`graph_nodes`, `graph_edges`)**
    *   **GraphNode**: `node_type` (original, skim, deep, capsule), `title`, `content`, `ref_id` (指向源数据)。
    *   **GraphEdge**: `source_node_id`, `target_node_id`, `relation_type`。记录图谱间的连线逻辑。
6.  **GlobalConversation (`global_conversations`)**
    *   保存全局 AI 问答的历史记录。
    *   `dify_conversation_id`: 对齐 Dify 的连续会话 ID。

---

## 4. 🧩 核心功能模块与算法实现细节

### 4.1. AI 魔法重写 (AI Writer) - `backend/app/routers/daily_note.py`
为用户的粗糙草稿提供 11 种预设模板和自定义 Prompt 支持。
*   **交互逻辑**：前端发送选中的“参考素材 (Capsules/Feeds)”以及“用户草稿”到 `/api/daily-notes/ai-rewrite`。
*   **模式支持**：
    *   `template` 模式：系统根据 `template_id` 注入预设 Prompt（如 `expand` 扩写、`action_items` 提炼待办）。
    *   `custom` 模式：直接采用用户前台输入的 Custom Prompt。
*   **流式输出 (SSE)**：后端组合 System Prompt 后，通过 `httpx` 向 Dify 发起 SSE 流式请求，并在接收到 `data: ` 块后原样 yield 给前端的打字机特效。

### 4.2. 块级高亮引用 (Block-level Reference)
彻底消除大模型阅读数万字长文时的上下文丢失和幻觉。
*   **文献高亮提取 (`FeedView.vue`)**：
    在阅读器界面监听 `mouseup` 事件，利用 `window.getSelection()` 捕获选中文本（>5 字符）。在选区上方弹出悬浮菜单。点击后调用 `/api/capsules` 接口，自动追加文献原文溯源 URL 并保存为私有胶囊。
*   **编辑器引用 (`DailyNoteView.vue`)**：
    监听 ByteMD 内容变化，当检测到用户输入 `((` 时，立即拦截并弹出搜索组件 `showBlockRefDialog`，实时模糊检索 Capsules。选中后将对应的文本作为引用块（Markdown Quote `>`）直接插入光标处。

### 4.3. AI 图书管理员 (AI Librarian)
写作过程中的主动知识推荐，避免知识生灰。
*   **防抖检索机制**：
    在 `DailyNoteView.vue` 中，当用户停止敲击键盘 2000 毫秒后，前端主动截取当前段落文本，调用 `/api/daily-notes/recommendations` 接口。
*   **后端检索 (`DifyService.retrieve_recommendations`)**：
    后端获取当前登录用户的 `dify_private_dataset_id`，利用 Dify 的 Semantic Search API 将用户正在写的内容转化为向量，并在知识库中召回 Top-K 的历史胶囊或文献片段，返回给前端侧边栏高亮显示。

### 4.4. 智能拖拽分类树与 Few-shot Learning
*   **拖拽实现**：
    前端利用原生的 HTML5 Drag & Drop API。左侧分类树 (Category Tree) 接收到 `drop` 事件后，发起对对应 `note_date` 的 `category` 字段的 PUT 更新。
*   **自动分类算法 (Auto-Categorization)**：
    后端 `POST /auto-categorize` 接收用户笔记内容和**现存的分类树数组**。Prompt 指导 Dify：“请根据现有的分类列表，将这段文字归入最合适的一类；如果都不合适，你可以根据历史分类风格自创一个不超过4个字的新分类名”。这就是通过上下文传递实现的 Few-shot Learning。

---

## 5. 📡 核心 API 路由概览 (API Routes)

所有的 API 路由都挂载在 `backend/app/main.py` 的 `/api/` 路径下。由于使用了 FastAPI，系统会自动生成 OpenAPI 文档。启动项目后，可直接访问 `http://localhost:8000/docs` 进行接口调试。

*   **Auth & Users** (`/auth`, `/users`)：JWT Token 下发、注册、管理员管理面板。
*   **Daily Notes** (`/daily-notes`)：
    *   `GET /{date}`, `PUT /{date}`: 按日期读写日记。
    *   `POST /ai-rewrite`: 触发 Dify 大模型重写（SSE 流式接口）。
    *   `POST /recommendations`: AI 图书管理员的后台向量检索。
    *   `POST /auto-categorize`: 触发自动分类计算。
*   **Capsules** (`/capsules`)：增删改查碎片知识，支持文件上传 (`/upload`) 提取。
*   **Feed & Reader** (`/feed`, `/reader`)：拉取外部资讯，发起 `/skim` 泛读总结和 `/translate` 全文翻译。
*   **Graph** (`/graph`)：获取 ECharts 渲染所需的节点和边数据。
*   **Chat** (`/chat`)：全局对话。

---

## 6. 🚀 快速启动与开发指南 (Getting Started)

1.  **环境准备**：
    安装 Node.js (v18+) 与 Docker 环境。
2.  **后端启动**：
    根目录下的 `docker-compose.yml` 包含了 FastAPI 后端、PostgreSQL 数据库以及 Redis。
    复制 `.env.example` 为 `.env` 并填入您的 Dify API Key 凭证。
    执行 `docker compose up -d --build` 即可启动整套后端生态。
3.  **前端调试**：
    进入 `frontend` 目录，执行 `npm install`。
    使用 `npm run dev` 可以在浏览器中进行网页端调试（地址 `http://localhost:5173`）。
    使用 `npm run electron:serve` 可以启动 Electron 原生桌面端环境进行调试。
4.  **构建打包**：
    使用 `npm run electron:build` 即可为您的操作系统生成专属的 `.dmg` 或 `.exe` 安装包。

---
> 编纂者：Solo AI Agent
> 最后更新：2026年4月
