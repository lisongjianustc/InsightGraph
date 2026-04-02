# InsightGraph 后续开发计划 (Roadmap)

当前我们已经完成了前两阶段的核心功能，包括基于 FastAPI + Vue3 + PostgreSQL(pgvector) 的前后端架构，集成了 Dify 的泛读摘要生成、PDF 全文双语翻译与精读对话，以及支持多种文档格式（PDF, Word, Excel, PPT 等）的闪念胶囊入库。

接下来，我们将继续完善**多模态支持**、**全局检索与问答**、**图谱可视化**等高阶功能。

## Stage 2.5: 闪念胶囊的多模态 OCR 增强
**目标**：解锁闪念胶囊的终极形态，支持图片拖拽和截图粘贴的 OCR 识别入库。
* **[ ] 前端改造**：移除图片上传限制，支持图片文件的拖拽、粘贴（Clipboard API）以及预览。将图片转为 Base64 或表单上传至后端。
* **[ ] 后端 OCR 引擎集成**：
  * 对接已在 Dify 配置好的 **Moondream / PaddleOCR** 工作流/大模型。
  * 对于图片文件，自动提取 Markdown 格式的文本（包含表格、公式解析）。
  * 将原图与提取出的文本一并存入 `Capsule` 表及 Dify 知识库中。

## Stage 3: 全局知识图谱与多源信息检索 (Global Graph & Search)
**目标**：将沉淀在数据库和 Dify 知识库中的 Feed 资讯、论文精读记录、闪念胶囊碎片连接起来，形成真正的 "InsightGraph"。
* **[ ] 图谱数据关联构建**：
  * 利用大模型对 Feed 和 Capsule 中的核心实体（Entity）和标签（Tags）进行抽取，并在本地 `GraphNode` 和 `GraphEdge` 表中建立关联。
* **[ ] 图谱可视化 (Graph Visualization)**：
  * 前端引入 `echarts` 或 `vis.js`，新增一个专门的 `[知识图谱]` 视图页面。
  * 将本地的关系数据以交互式节点网络图的形式展示，支持缩放、拖拽和点击下钻查看源文档。

## Stage 4: 跨文档全局智能问答 (Global Chat)
**目标**：打通 Dify 的全量知识库，提供一个类似 ChatGPT 的全局对话入口。
* **[ ] 全局 Chat UI**：
  * 激活侧边栏预留的 `[全局问答 (Chat)]` 页面。
  * 提供一个清爽的全屏对话流界面，支持保存多个会话 (Sessions)。
* **[ ] 后端 Dify 路由集成**：
  * 在 Dify 中创建一个链接了 `ORIGINAL`、`DEEP`、`CAPSULE` 三个知识库的“综合问答应用”。
  * 后端新增 `/api/chat/global` 接口进行流式（Streaming）对话转发，并返回带有来源引用（Citations）的回答。
  * 前端支持点击来源链接直接跳转到对应的 Feed 详情或 Capsule 记录。

## Stage 5: 系统设置与高级特性 (Settings & Advanced Features)
* **[ ] 标签与分类管理**：支持对所有入库内容的 Tag 手动管理与批量修改。
* **[ ] RSS/飞书等信息源自动同步**：完善后端的 `apscheduler` 任务，实现真正的定时抓取机制（目前依赖手动触发）。
* **[ ] 黑暗模式 (Dark Mode)**：前端界面的样式适配。
* **[ ] 部署优化**：将 Python 的静态包与 Dify 环境进行剥离或优化打包，提供一键安装脚本（`setup.sh`），方便在其他机器上快速复刻。

