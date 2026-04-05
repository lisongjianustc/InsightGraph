<div align="center">
  <img src="frontend/build/icon.png" width="160" height="160" alt="InsightGraph Logo" style="border-radius: 22.5%; box-shadow: 0 10px 30px rgba(0,0,0,0.15); margin-bottom: 20px;">
  
  <h1>🌌 InsightGraph</h1>
  
  <p><b>一个高度智能化、自动化的个人第二大脑系统</b></p>

  <p>
    <img src="https://img.shields.io/badge/Vue-3.x-4fc08d?style=for-the-badge&logo=vue.js" alt="Vue 3" />
    <img src="https://img.shields.io/badge/Electron-Desktop-47848f?style=for-the-badge&logo=electron" alt="Electron" />
    <img src="https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi" alt="FastAPI" />
    <img src="https://img.shields.io/badge/PostgreSQL-PgVector-336791?style=for-the-badge&logo=postgresql" alt="PgVector" />
    <img src="https://img.shields.io/badge/Dify-LLM_Agent-1890ff?style=for-the-badge" alt="Dify" />
  </p>
</div>

<br/>

> **不再让你的知识成为信息孤岛。**
> 在 InsightGraph 里，每一篇论文、每一个截屏、每一闪而过的灵感，都将自动凝结成知识图谱中熠熠生辉的星辰，并随时等待你的召唤。通过前沿大模型与本地知识库的深度融合，InsightGraph 实现了从“信息收集”到“知识内化”的无缝闭环。

---

## ✨ 核心特性 (Core Features)

### 📡 知识发现 (Auto-Feed & Skim Reading)
- **🤖 全自动信息聚合**：基于 APScheduler 定时扫描 arXiv 前沿论文或 RSS 订阅源。
- **⚡ 一键泛读摘要**：调用 Dify 大模型，数秒内将万字长文提炼为 **3 个核心要点 (Key Takeaways)**，实现一目十行的极速初筛。
- **📚 原生文件沉浸阅读**：一键拉起高清 PDF/Word 预览，并支持在“原文件排版”与“AI 解析文本”间丝滑切换。

### ⚡️ 闪念胶囊 (Multi-Modal Capsules)
- **✍️ 所见即所得的极客编辑**：基于 ByteMD 打造的 Typora 级体验，支持 GitHub 风格语法、代码高亮与 LaTeX 公式实时渲染。
- **📎 全能文档解析**：支持将 **PDF、Word、Excel、PPT** 直接拖入入库。
- **👁️ 多模态视觉 OCR**：整合视觉大模型（如 Qwen-VL），支持 **`Ctrl+V` 直接粘贴图片**，自动提取表格、公式并生成精美 Markdown。

### 🌌 动态知识图谱 (Knowledge Graph)
- **🧠 概念级高维聚类**：剔除无意义的连线，仅展示由 LLM 自动抽取的“核心专业概念”节点。
- **🔗 万物引力连线**：文献与胶囊通过相同的概念自动聚拢，形成网状结构的知识图谱。
- **🚀 快捷穿梭与下钻**：点击图谱节点，呼出关联文献列表，一键拉起原生 PDF 阅读器，无缝下钻知识。

### 🤖 跨源全局问答 (Global Chat)
- **💬 打通数据孤岛**：专属全局 Chatbot 穿透你的“原文库”、“精读库”和“闪念胶囊库”。
- **⚡ 流式多模态交互**：极致流畅的 SSE 打字机响应，支持带附件/图文上传提问。
- **🎯 严格溯源机制**：机器人的每一个结论都会生成带有超链接的**引用来源 (Citations)**，彻底杜绝大模型幻觉。

### 💻 跨平台桌面端体验 (Desktop App)
- **🍏 原生级桌面应用**：基于 Electron 打包，告别浏览器标签页的束缚，享受纯粹、免干扰的第二大脑沉浸感。
- **🪟 独立窗口管理**：原生 PDF 独立窗口渲染、专属 Dock 图标、极致优雅的 UI 交互。

---

## 📸 界面纵览 (Showcase)

*(提示：你可以在项目目录创建 `docs/images/` 文件夹，放入你真实的系统截图来替换下方的高质感预览图。)*

<table align="center">
  <tr>
    <td align="center" width="50%">
      <b>1. 🖥️ 桌面端沉浸阅读与编辑</b><br/>
      <img src="https://images.unsplash.com/photo-1618477247222-accd0e1ae22d?auto=format&fit=crop&w=600&q=80" alt="Capsule Editor" style="border-radius: 8px; margin-top: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
    </td>
    <td align="center" width="50%">
      <b>2. 🌌 动态交互知识图谱</b><br/>
      <img src="https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=600&q=80" alt="Knowledge Graph" style="border-radius: 8px; margin-top: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
    </td>
  </tr>
  <tr>
    <td align="center" width="50%">
      <b>3. 📄 智能原文件/解析切换</b><br/>
      <img src="https://images.unsplash.com/photo-1586281380349-632531db7ed4?auto=format&fit=crop&w=600&q=80" alt="PDF Preview" style="border-radius: 8px; margin-top: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
    </td>
    <td align="center" width="50%">
      <b>4. 🤖 溯源级全局多模态问答</b><br/>
      <img src="https://images.unsplash.com/photo-1655720828018-edd2daec9349?auto=format&fit=crop&w=600&q=80" alt="Global Chat" style="border-radius: 8px; margin-top: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
    </td>
  </tr>
</table>

---

## 🛠 技术架构与生态树 (Tech Stack & Ecosystem)

InsightGraph 的架构设计崇尚“解耦、自动化与极致的视觉体验”。我们严选了当前最具生命力的开源框架来构建这套系统：

### 🎨 前端与桌面端 (Frontend & Desktop)
- **核心框架**: Vue 3 (Composition API) + TypeScript + Vite 5。
- **桌面端引擎**: **Electron** + Electron Builder。提供无缝的原生窗口体验与沙盒穿透能力。
- **UI 与视觉**: Element Plus + TailwindCSS 3。
- **沉浸式编辑器**: **ByteMD**。字节跳动开源的高性能 Markdown 编辑器，支持 GFM、代码高亮 (highlight.js) 与数学公式 (KaTeX)，并搭配了 `juejin-markdown-themes` 打造顶级阅读排版。
- **原生文档预览**: `@vue-office` 生态 (`docx`, `excel`, `pdf`, `pptx`)，实现无需转换的纯前端高清文档渲染。
- **动态图谱引擎**: Apache **ECharts** 6。负责驱动千万级知识节点与万物引力连线的流畅渲染。

### ⚙️ 核心业务后端 (Backend)
- **Web 框架**: **FastAPI**。基于 ASGI 提供极速并发的 REST API 与 SSE 流式数据推送服务。
- **ORM 与数据建模**: SQLAlchemy 2.0 + Pydantic v2。
- **任务调度**: APScheduler。负责系统后台的文献拉取、定时摘要生成等守护进程。
- **文档解析矩阵**: `PyMuPDF` (底层 PDF 解析), `pdf2zh` (文档翻译), `python-docx/pptx` 等构建的强力解析管道。
- **第三方集成**: Lark (飞书) 官方 Python SDK，用于将知识卡片无缝推送到飞书工作流。

### 🧠 数据库与中间件 (Data & Middleware)
- **主关系库与向量引擎**: **PostgreSQL + PgVector**。利用 PgVector 插件，使 PG 完美兼顾了高维 RAG 知识向量检索与复杂关系型业务数据的存储。
- **高速缓存**: Redis 7。用于高频图谱数据缓存与流式会话状态保持。
- **工作流编排**: **n8n**。内置于 Docker 环境中的节点化自动化平台，可轻松定制对 arXiv、GitHub 的监控与飞书推送流。

### 🤖 AI 大脑核心 (The AI Engine)
- **大模型底座平台**: **Dify**。InsightGraph 所有的文本 Embedding、RAG 混合检索、多模态视觉 OCR 工作流以及具有记忆的 Chatbot 会话，均完全托管于本地或云端的 Dify 实例。这种设计使得你可以随时在 Dify 后台零代码无缝切换底层大模型（如 GPT-4o, Claude 3.5, Qwen, DeepSeek 等）。

---

## 🚀 快速开始 (Quick Start)

### 前置要求
1. 安装 **Docker** 和 **Docker Compose**。
2. 确保你已经部署好了一个 **Dify** 实例（本地 Docker 或云端服务皆可）。
3. 确保你已经安装了 Node.js（用于编译前端与打包 Electron）。

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

### 2. 一键启动后端
在根目录执行一键部署脚本，或手动拉起 Docker：
```bash
docker compose up -d --build
```

### 3. 体验桌面端 App (推荐)
想要获得最佳的“第二大脑”沉浸体验，请进入 `frontend` 目录并打包桌面应用：
```bash
cd frontend
npm install
npm run electron:build
```
*编译完成后，可在 `frontend/dist_electron/` 中找到你专属的独立 App 安装包！*

### 4. 体验网页端
如果你更喜欢在浏览器中运行：
```bash
cd frontend
npm install
npm run dev
```
打开浏览器访问 [http://localhost:5173](http://localhost:5173) 即可。

---

## ⚙️ 系统维护与自定义
- **深色模式 (Dark Mode)**：在系统设置中一键切换，享受暗夜沉浸阅读。
- **数据抓取调度**：支持在 UI 界面手动触发 APScheduler，立即拉取 arXiv 最新文献。
- **知识图谱修剪**：可视化管理标签库，一键剔除大模型生成的冗余节点，保持图谱纯净。

## 📄 License
MIT License
