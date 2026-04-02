# InsightGraph 个人知识管理系统操作手册

InsightGraph 是一个将自动化信息获取（RSS/爬虫）、信息整理与智能检索（RAG 知识库）结合的本地化个人知识管理平台。

## 一、 系统架构

系统由三个独立但相互协同的模块组成：
1. **自动化中枢 (n8n)**：负责定时任务、调用外部 API（如 GitHub、Arxiv）抓取数据，并将数据发送到后端。
2. **核心业务后端与前端 (FastAPI + Vue3)**：
   - **Backend**：接收 n8n 推送的数据，存入本地数据库，并处理向 Dify 知识库发送文档的异步请求。
   - **Frontend**：提供可视化的 Web 管理页面，用于查看今日资讯、快捷录入闪念胶囊、以及执行“一键入库”操作。
3. **AI 知识大脑 (Dify)**：负责存储碎片知识、进行文档向量化、提供 RAG 检索以及智能体问答 API。

---

## 二、 基础运维操作

系统的所有后端及自动化服务均运行在 Docker 容器中。我们有两个 Docker Compose 编排文件：
- 主编排文件：`InsightGraph/docker-compose.yml` (包含 PostgreSQL, Redis, n8n, FastAPI)
- Dify 编排文件：`InsightGraph/dify-source/docker/docker-compose.yaml`

### 1. 启动服务

**启动主业务服务 (n8n + FastAPI + 数据库)**
在项目根目录 `InsightGraph/` 下执行：
```bash
docker compose up -d --build
```

**启动 Dify 服务**
进入 Dify 目录执行：
```bash
cd dify-source/docker
docker compose up -d
```

**启动前端 Web 界面 (开发模式)**
目前前端尚未打包进 Docker，需要在本地运行：
```bash
cd frontend
npm run dev
```
前端启动后，访问：[http://localhost:5173](http://localhost:5173)

### 2. 停止服务

停止主业务服务：
```bash
# 在 InsightGraph 根目录执行
docker compose down
```

停止 Dify 服务：
```bash
# 在 dify-source/docker 目录执行
docker compose down
```

### 3. 重启单个模块

如果你只修改了 FastAPI 的代码（比如 `backend/main.py`），不需要重启整个系统，只需重启该容器：
```bash
# 在 InsightGraph 根目录执行
docker restart insight_backend
```

重启 n8n：
```bash
docker restart insight_n8n
```

### 4. 查看日志排错

如果你发现点击“整合进知识库”没有反应，可以查看 FastAPI 的日志：
```bash
docker logs -f insight_backend
```

查看 n8n 抓取日志：
```bash
docker logs -f insight_n8n
```

---

## 三、 核心配置与操作流程

### 1. n8n 自动化抓取配置
1. **访问地址**：[http://localhost:5678](http://localhost:5678)
2. **默认账号**：
   - 用户名：`admin`
   - 密码：`insight_admin_123` (配置在根目录的 `.env` 中)
3. **导入工作流**：
   - 在左侧菜单选择 **Workflows** -> 右上角 **Add Workflow**
   - 点击右上角菜单 `...` -> **Import from File**
   - 选择项目中的 `data/n8n_workflows/arxiv_github_to_local_db.json`
4. **测试与启用**：
   - 点击底部的 `Test Workflow` 测试抓取。
   - 确认无误后，打开右上角的 `Active` 开关，让其每天定时执行。

### 2. Dify 知识库配置
1. **访问地址**：[http://localhost:5001](http://localhost:5001) (默认的 80 端口已修改为 5001)
2. **初始设置**：首次访问需注册管理员账号并登录。
3. **创建知识库**：
   - 顶部导航栏点击 **“知识库” (Knowledge)** -> **“创建知识库”**
   - 选择“创建空白知识库”，命名为 `InsightGraph DB`
4. **获取并配置 API Key**：
   - 进入创建好的知识库，左侧点击 **“API 访问”**
   - 点击右上角生成 **API 密钥** (`app-xxxxx` 格式)
   - 打开 `InsightGraph/.env` 文件，将密钥填入：
     ```env
     DIFY_API_KEY=app-xxxxxxxxxxxxxxxxxxxx
     DIFY_API_URL=http://localhost:5001/v1
     ```
   - *配置完成后，重启后端容器生效：`docker restart insight_backend`*

### 3. 前端 Web 管理界面操作
1. **访问地址**：[http://localhost:5173](http://localhost:5173)
2. **今日资讯 (Feeds)**：
   - 页面会自动展示 n8n 抓取并存入 PostgreSQL 的内容。
   - 点击每张卡片右下角的 **“📥 整合进知识库”** 按钮，FastAPI 将提取卡片内容，加上来源和标题，异步发送给 Dify 进行向量化存储。
   - 按钮变灰显示“已入库”，即代表该信息已被 AI 大脑永久记忆。

---

## 四、 常见问题 (FAQ)

**Q: 为什么点击“整合进知识库”后，Dify 里面没有内容？**
A: 请检查两点：
1. 确保 `.env` 中的 `DIFY_API_KEY` 是正确知识库的密钥，并且重启了 `insight_backend`。
2. 使用 `docker logs insight_backend` 查看日志，是否有报错提示（如连接被拒绝或 401 权限错误）。如果在 Docker 内部无法通过 `localhost` 访问 Dify，请将 `.env` 中的 `DIFY_API_URL` 修改为宿主机的内网 IP，例如 `http://192.168.x.x:5001/v1`。

**Q: 如何清空或重置数据库？**
A: 如果需要彻底清理所有抓取的数据，可以删除持久化挂载的目录：
```bash
docker compose down
sudo rm -rf data/postgres
docker compose up -d
```
*(警告：这将清空所有未入库的 Feed 记录)*
