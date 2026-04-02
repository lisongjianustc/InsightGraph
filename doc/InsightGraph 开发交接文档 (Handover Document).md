# InsightGraph 开发交接文档 (Handover Document)

> **当前项目路径**：`/Users/lisongjian/Project/InsightGraph`
> **项目定位**：本地化部署的个人知识管理与自动化追踪系统（PKM）

## 1. 原始需求回顾
用户希望开发一个知识库系统，具备以下核心能力：
1. **碎片知识管理**：协助整理、归类平时遇到的碎片化知识与概念。
2. **自动化信息追踪**：跟踪 Arxiv 论文和 GitHub 高星项目，提供日报，并可选择性整合进知识库。
3. **AI 知识库大脑**：接入 Dify 作为核心引擎，提供文档向量化存储与工作流能力。
4. **完全本地化 Web 管理端**：取消接入飞书，改为完全通过一个 Vue3 网页后台进行信息流展示、碎片录入和问答交互。
5. **本地 Docker 部署**：所有服务均需在本地通过 Docker 容器运行。

## 2. 系统架构选型
- **数据抓取层**：`n8n` (Docker 部署，端口 5678)
- **核心业务后端**：`FastAPI` + `PostgreSQL` + `SQLAlchemy` (Docker 部署，端口 8000)
- **AI 知识库与问答引擎**：`Dify` 官方社区版 (Docker 部署，端口 5001)
- **Web 前端管理端**：`Vue 3` + `Vite` + `TailwindCSS` + `Element Plus` (本地 Node 运行，端口 5173)

## 3. 当前已完成进度 (100% 打通核心骨架)

### 3.1 基础设施与自动化抓取
- 编写了主 `docker-compose.yml`，成功运行 PostgreSQL、Redis、n8n 和 FastAPI。
- 成功部署了 Dify 官方 Docker 环境（端口修改为 5001）。
- 在 n8n 部署了每天定时抓取 GitHub 和 Arxiv 并通过 HTTP POST 推送到 FastAPI 的工作流。

### 3.2 FastAPI 后端开发
- 创建了 `FeedItem` 数据库表。
- 完成接口：接收 n8n 推送 (`POST /api/feed/incoming`)、前端拉取列表 (`GET /api/feed/list`)、前端触发整合 (`POST /api/feed/{id}/save_to_kb`)。
- 编写了 `dify_service.py` 封装了 Dify Dataset API 的异步文本入库请求。

### 3.3 Vue3 前端开发 (基础版)
- 编写了 `MainLayout.vue` 侧边栏布局和 `FeedView.vue` 资讯流页面。
- 资讯流页面已实现从后端拉取数据，并实现了“📥 整合进知识库”按钮点击调用后端的逻辑。

## 4. 目录结构说明
```text