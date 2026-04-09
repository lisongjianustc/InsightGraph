# InsightGraph v2.0 详细技术实现方案 (Implementation Plan)

本文档基于 `Roadmap_v2.0.md` 的五大核心战役，为研发团队提供精确到代码文件级、数据库表结构级、以及 API 接口级的设计思路与实施步骤。

---

## 🛡️ 战役一：底层基建与多租户权限架构

### 1. 账号体系与双重 Dataset 物理隔离
**【数据库层面】**
- **新增 User 模型**: 在 `backend/app/models/user.py` 创建 `User` 表（包含 `id`, `username`, `hashed_password`, `dify_private_dataset_id`）。
- **修改实体表**: `capsules`, `daily_notes`, `feed_items`, `graph_nodes`, `graph_edges` 必须增加 `owner_id` (Integer, FK -> users.id) 和 `visibility` (Enum: 'public', 'private') 字段。
- **数据库迁移**: 编写 Alembic 迁移脚本，将现有单机版数据默认归属于 `user_id = 1`，并设置默认 `visibility = 'private'`。

**【后端接口层面 (FastAPI)】**
- **JWT 认证拦截**: 在 `backend/app/core/security.py` 实现 OAuth2PasswordBearer，颁发 JWT token。所有的业务 Router（如 `/api/capsules`）必须注入 `Depends(get_current_user)`，并在 SQLAlchemy 查询时强制附带 `.filter(Model.owner_id == current_user.id)`。
- **Dify 知识库动态管理**:
  - 在用户注册时，调用 Dify OpenAPI (`POST /datasets`) 自动创建以用户名为前缀的 Dataset，并将返回的 `id` 存入 `users.dify_private_dataset_id`。
  - 在 `dify_service.py` 中，重构大模型检索逻辑。向 Dify 发起检索请求时，动态组装 `dataset_ids: [SYSTEM_PUBLIC_DATASET_ID, current_user.dify_private_dataset_id]`。
- **对话记忆隔离**: 在向 Dify Chat 接口发起请求时，必须将 `user` 字段的值从硬编码修改为 `user: f"insight_user_{current_user.id}"`。

### 2. 混合知识图谱与权限视觉映射
**【前端层面 (Vue 3 + ECharts)】**
- **数据获取**: ECharts 组件请求 `/api/graph/data` 时，后端返回的节点 JSON 需包含 `visibility` 属性。
- **ECharts 渲染逻辑**:
  - 在 `frontend/src/views/GraphView.vue` 中，修改 `itemStyle` 的回调函数。
  - 判定：如果 `visibility === 'public'`，给节点添加蓝色的发光特效 (`shadowColor: '#1890ff', shadowBlur: 20`)；如果为 `private`，则保持常规的粉色/紫色。

---

## 📥 战役二：零阻力与自动化的知识摄入

### 3. 无感知的“黑洞”全局录入 (Spotlight Capture)
**【Electron 层面】**
- **全局快捷键注册**: 在 `frontend/electron/main.ts` 中，使用 `globalShortcut.register('Option+Space', () => { ... })`。
- **悬浮窗 UI**: 创建一个无边框、透明背景的极简 BrowserWindow (Spotlight Window)。
- **剪贴板读取**: 利用 Electron 的 `clipboard` 模块，支持用户在悬浮窗内一键粘贴纯文本或图片，并通过 IPC 通信发送给后端 `/api/capsules`。

### 4. 团队级多模态自动化抓取管道
**【n8n 自动化引擎】**
- **Webhook 节点配置**: 在 n8n 中配置一个 Webhook Trigger 接收来自飞书机器人或企业微信的推送。
- **RSS 节点配置**: 配置 Schedule Trigger + RSS Feed Read 节点，每日 8 点定时抓取 arXiv 指定分类的最新论文。
- **后端对接**: n8n 抓取清洗数据后，调用 InsightGraph 的 `POST /api/feed_items` (Header 中需配置专用 Bot Token)。
- **多模态提取**: FastAPI 接收到含有图片的 PDF 或消息后，调用已集成的 Qwen-VL 模型提取图表和公式，并将入库的 `visibility` 设置为 `public` 供全员共享。

---

## 🧠 战役三：让 AI 成为全职图书管理员

### 5. 图谱漫游与跨维度“知识涌现”
**【后端推荐算法】**
- **向量相似度计算**: 
  - 方案 A (强依赖 Dify): 调用 Dify 的 `POST /datasets/{id}/retrieve` 接口，将用户当前正在写的日记片段作为 Query，让 Dify 召回最相关的 Document 列表返回给前端。
  - 方案 B (本地 PgVector): 在保存日记时，通过 `Sentence-Transformers` 模型将文本 Embedding 后存入 PgVector 字段，前端实时发起 `SELECT ... ORDER BY embedding <-> query_embedding LIMIT 3` 获取相关历史笔记。
- **孤岛 Tag 聚合**: 定期任务 (APScheduler) 调用 LLM 传入全量 Tag 列表，让 LLM 输出建议合并的同义词对 (如 `[{"from": "LLM", "to": "大语言模型"}]`)，在管理员界面供人工确认合并。

### 6. 动态遗忘与智能降噪机制
**【后端与图谱逻辑】**
- **热度衰减模型**: 在 `graph_nodes` 增加 `last_accessed_at` (最后访问时间) 和 `hit_count` (被 RAG 命中的次数)。
- **ECharts 视觉降噪**: 前端获取节点时，计算 `(当前时间 - last_accessed_at)`。如果超过 90 天且 `hit_count < 2`，则在 ECharts 的 `symbolSize` 映射中将其缩小 50%，并调低 `opacity` 至 0.3。

---

## 🗣️ 战役四：对话重组与块级精准引用

### 7. 记忆回溯问答与动态成文
**【前后端交互】**
- **Dify 强关联问答**: 在全局问答界面，用户发送“总结我的思考”。后端将此请求发给绑定了公私混合库的 Dify Agent。
- **一键落库按钮**: 在前端聊天气泡底部新增 `[✨ 沉淀为每日笔记]` 按钮。点击后，提取当前气泡的 Markdown 文本，直接调用 `PUT /api/daily-notes/{today}` 将 AI 的回答保存为今日日记的草稿。

### 8. 双向链接增强与“块级”引用
**【前端阅读器深度开发】**
- **高亮事件拦截**: 在 PDF/Markdown 阅读器组件中监听 `mouseup` 事件，获取 `window.getSelection().toString()`。
- **生成 Anchor**: 为高亮的文本生成一个唯一 Hash (如 `#anchor-a1b2`)，并保存为一条特殊的 Capsule，内容为高亮文本，`ref_url` 指向源文档的该 Hash 位置。
- **编辑器解析增强**: 修改 ByteMD 的正则解析器，除了支持 `[[original:123]]` 外，新增对 `((capsule:hash))` 块级双链的渲染与解析，使得大模型重写时仅抓取这几十字的高亮片段而非万字长文。

---

## 🛡️ 战役五：终极隐私与离线生存

### 9. 端侧小模型接入与完全离线模式
**【系统架构演进】**
- **Ollama 集成**: 在系统设置中增加【模型提供商】切换：`[ Dify (Cloud/Local) | Ollama (Offline) ]`。
- **本地 API 桥接**: 如果用户切换到 Ollama，后端的 `dify_service.py` 不再发起对 Dify 的 HTTP 请求，而是通过 `ollama-python` 库调用 `http://localhost:11434/api/generate`。
- **本地检索增强 (Local RAG)**: 引入轻量级的 `ChromaDB` 作为本地后备向量库。离线模式下，由本地嵌入模型 (如 `m3e-base`) 对私密日记进行向量化，并在本地 ChromaDB 中完成检索召回，彻底切断外网数据交互。
