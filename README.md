# 🌌 InsightGraph

<div align="center">
  <img src="https://img.shields.io/badge/Vue-3.x-4fc08d?style=for-the-badge&logo=vue.js" alt="Vue 3" />
  <img src="https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi" alt="FastAPI" />
  <img src="https://img.shields.io/badge/PostgreSQL-PgVector-336791?style=for-the-badge&logo=postgresql" alt="PgVector" />
  <img src="https://img.shields.io/badge/Dify-LLM_Agent-1890ff?style=for-the-badge" alt="Dify" />
</div>

<br/>

**InsightGraph** 是一个**高度智能化、自动化、且真正能将碎片信息“连接”起来的个人第二大脑系统**。它以大模型为核心，将前沿论文追踪、多模态闪念碎片收集、动态知识图谱构建以及全局跨文档检索问答完美融合于一体。

不再让你的知识成为信息孤岛。在 InsightGraph 里，每一篇论文、每一个截屏、每一闪而过的灵感，都将自动凝结成知识图谱中熠熠生辉的星辰，并随时等待你的召唤。

## ✨ 核心特性 (Features)

### 1. 📡 知识发现 (Auto-Feed & Skim Reading)
- **后台自动抓取**：基于 APScheduler 定时（默认每小时）扫描并拉取 arXiv 的前沿论文，或是其他 RSS 订阅源。
- **一键泛读摘要**：系统自动调用 Dify 大模型，在几秒钟内将枯燥的长篇摘要提炼为 3 个最核心的要点（Key Takeaways），帮你实现一目十行的极速初筛。
- **全文精读与翻译**：如果发现值得深挖的文献，点击即可调用大模型对其进行全文级别的深度解析、双语对照翻译，并永久落库至个人的 `ORIGINAL` 与 `DEEP` 知识库中。

### 2. ⚡️ 闪念胶囊 (Multi-Modal Capsules)
- 灵感一闪而过？随时在胶囊界面记下它！
- **全能文档解析**：支持直接将 **PDF、Word、Excel、PPT** 拖入浏览器，后端会自动抽取纯文本入库。
- **多模态图像 OCR**：通过整合带有视觉能力的 Dify Chatbot 模型（如 Qwen-VL、Moondream），你甚至可以**直接 `Ctrl+V` 粘贴系统截图或图片**，大模型将自动提取其中的文本、表格甚至公式，生成精美的 Markdown 并与截图一同入库。

### 3. 🌌 动态知识图谱 (Knowledge Graph)
- **概念级聚类**：这不仅仅是一堆连接线的毛线球。图谱中**只显示由 LLM 自动抽取的“核心专业概念（Tag）”节点**。
- **引力连线**：当你保存的论文或胶囊包含相同的概念时，它们便会形成引力，自动将相关的标签聚拢。
- **AI 专业释义与下钻**：点击图谱上任意一个概念节点，除了展示关联的全部文献外，大模型还会立刻**为你动态生成该词汇的严谨专业释义（定义）**并缓存。
- 点击相关文献，更可一键新标签页直达阅读！

### 4. 🤖 跨源全局问答 (Global Chat Assistant)
- **打通数据孤岛**：我们为你在 Dify 中配置了一个专属全局 Chatbot，它链接了你的“原文库”、“精读库”和“闪念胶囊库”。
- **流式多模态交互**：采用极致流畅的 SSE (Server-Sent Events) 打字机响应。支持带附件（图文）上传提问。
- **严格溯源**：机器人的每一个回答片段，都会在下方生成带有超链接的**引用来源（Citations）标签**，明确告诉你它是参考了你的哪一条胶囊或哪一篇文献得出的结论，杜绝幻觉！

---

## 🛠 技术架构 (Architecture)

InsightGraph 的架构设计崇尚解耦与灵活性：
- **前端 (Frontend)**: Vue 3 + TypeScript + Vite + TailwindCSS + Element Plus + ECharts (力引导图可视化)。
- **后端核心 (Backend)**: FastAPI (Python) 提供极速并发的 REST API 与 SSE 流式数据推送。
- **知识处理中枢 (Brain)**: **Dify**。所有的文本 Embedding 向量化、RAG 检索、图片 OCR 工作流以及 Chatbot 会话，均依托本地/云端的 Dify 实例来驱动大模型（支持 Ollama, OpenAI 等任意 LLM）。
- **存储层 (Database)**: PostgreSQL + PgVector。存储应用级的关系数据以及知识图谱的节点（GraphNode）与边（GraphEdge）。

---

## 🚀 快速开始 (Quick Start)

### 前置要求
1. 安装 **Docker** 和 **Docker Compose**。
2. 确保你已经部署好了一个 **Dify** 实例（本地 Docker 或云端服务皆可）。
3. 确保你已经安装了 Node.js（仅用于启动前端开发服务器）。

### 1. 环境变量配置
在项目根目录创建 `.env` 文件，并填入你的 Dify API 凭证：
```env
# Dify 服务的接口地址 (如果 Dify 运行在宿主机的 5001 端口，Docker 容器内需通过 host.docker.internal 访问)
DIFY_API_URL=http://host.docker.internal:5001/v1

# 基础知识库 API Key (必填)
DIFY_API_KEY=dataset-xxxxxxxxxxxxxxxxx

# 以下为各大模型应用的 API Key (必填)
DIFY_READER_API_KEY=app-xxxxxxxxxxxxxxxxx           # 泛读与定义生成
DIFY_DEEP_READER_API_KEY=app-xxxxxxxxxxxxxxxxx      # 精读与翻译
DIFY_OCR_WORKFLOW_API_KEY=app-xxxxxxxxxxxxxxxxx     # 带有视觉模型 (如 Qwen-VL) 的多模态聊天助手
DIFY_GLOBAL_CHAT_API_KEY=app-xxxxxxxxxxxxxxxxx      # 链接了全量知识库的综合全局问答助手
```

### 2. 一键启动
在 Mac 或 Linux 环境下，直接在根目录执行一键部署脚本：
```bash
chmod +x setup.sh
./setup.sh
```

如果你使用的是 Windows，或希望手动部署，请执行：
```bash
# 启动后端与数据库容器
docker compose up -d --build

# 安装并启动前端
cd frontend
npm install
npm run dev
```

### 3. 访问应用
- 前端交互界面：[http://localhost:5173](http://localhost:5173)
- 后端 API 文档：[http://localhost:8000/docs](http://localhost:8000/docs)
- (可选) Dify 后台：[http://localhost:5001](http://localhost:5001)

---

## 📸 界面预览 (Screenshots)

*(提示：你可以在此上传并将项目实际截图链接替换到下方)*

<details>
<summary><b>1. 知识发现 (Feed)</b> - 一键获取前沿论文泛读摘要</summary>
<img src="https://via.placeholder.com/800x400.png?text=Feed+Screenshot" alt="Feed">
</details>

<details>
<summary><b>2. 闪念胶囊 (Capsule)</b> - 拖拽多格式文档、直接粘贴图片 OCR 解析</summary>
<img src="https://via.placeholder.com/800x400.png?text=Capsule+Screenshot" alt="Capsule">
</details>

<details>
<summary><b>3. 知识图谱 (Graph)</b> - ECharts 力引导聚类，AI 动态生成概念定义与下钻</summary>
<img src="https://via.placeholder.com/800x400.png?text=Graph+Screenshot" alt="Graph">
</details>

<details>
<summary><b>4. 全局问答 (Chat)</b> - 多模态流式对话，穿透全库数据并严格附带溯源链接</summary>
<img src="https://via.placeholder.com/800x400.png?text=Chat+Screenshot" alt="Chat">
</details>

---

## ⚙️ 设置与维护
InsightGraph 提供了内置的 **[系统设置]** 页面，你可以：
- 自由切换 **Dark Mode (深色模式)**，享受沉浸式阅读。
- 一键手动触发后台 APScheduler 进行最新文献的抓取。
- 可视化管理知识图谱标签：一键剔除大模型生成的冗余或错误标签。

## 📄 License
MIT License
