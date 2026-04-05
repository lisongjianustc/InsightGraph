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

## 2. 环境部署

本项目已经实现了极度优雅的容器化整合部署。整个系统（包含后端服务、向量数据库以及内置的 Dify AI 大脑）全部集成在一个 Docker Compose 编排网络中，提供“一键拉起”的极简体验。

### 2.1 一键初始化 (推荐)

针对全新的服务器或本地开发环境，我们提供了一键初始化的脚本。它会自动检查环境、创建挂载目录并分配必要的权限。

在项目根目录下执行：
```bash
./scripts/init.sh
```

脚本执行完成后，会自动为您复制 `.env.example` 到 `.env`（如果您本地还没有的话），并询问您是否立即拉起所有的 Docker 容器。

### 2.2 手动部署 (如果未使用 init.sh)

如果您希望手动控制部署流程，请按照以下步骤执行：

1. **环境准备**
   确保您的设备已安装 `Docker` 和 `Docker Compose`。

2. **创建数据挂载目录**
   为了防止数据丢失，必须在宿主机创建持久化目录：
   ```bash
   mkdir -p data/postgres data/redis dify-source/docker/volumes
   mkdir -p backend/uploads/capsules backend/uploads/documents
   ```

3. **配置文件准备**
   由于我们已经将 Dify 引擎内置到了网络中，您需要关注两份配置文件：
   - 复制根目录的 `.env.example` 到 `.env`（主系统配置）
   - 进入 `dify-source/docker`，将其中的 `.env.example` 复制为 `.env`（Dify 引擎配置）

4. **启动服务**
   回到项目根目录，只需执行一行命令，即可拉起由 14 个容器组成的庞大生态（包括 InsightGraph 后端、主 PG 数据库、Dify 全家桶等）：
   ```bash
   docker compose up -d --build
   ```

启动后，您可以使用 `docker ps` 查看容器状态，或通过浏览器访问 `http://localhost:5001` 来初始化您的 Dify 后台。

---

## 3. 系统灾备与运维 (DevOps)

针对个人知识库这类极度重要的数据资产，我们内置了企业级的运维脚本集。它们位于 `scripts/` 目录下。

### 3.1 一键完整备份 (`backup.sh`)
本脚本会将整个系统（包括关系数据库、向量图谱、所有本地附件、以及内置 Dify 产生的所有配置与对话数据）打包成一个时间戳文件夹。

**手动执行**：
```bash
./scripts/backup.sh
```
执行后，您将在项目根目录的 `backups/` 下看到类似 `20260405_120000/` 的完整备份包。

**自动化定时备份 (Cron)**：
如果您希望每天凌晨 3 点自动备份，并在 7 天后自动清理旧数据，请通过 `crontab -e` 添加：
```bash
0 3 * * * bash /您的完整项目路径/scripts/backup.sh >> /您的完整项目路径/backups/backup.log 2>&1
```

### 3.2 灾难恢复 (`restore.sh`)
当发生数据损坏或迁移到新电脑时，您可以通过此脚本一键从备份包中安全恢复。

**用法**：
```bash
./scripts/restore.sh <备份文件夹名>
# 例如: ./scripts/restore.sh 20260405_120000
```
*注意：恢复操作会自动停止所有业务容器、清空现有的数据库及所有本地挂载数据，并从备份文件中覆盖恢复。请谨慎操作。*

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

## 4. 常见问题排查 (Troubleshooting)

### 4.1 端口占用问题
在执行 `docker compose up -d` 时，如果遇到类似 `Bind for 0.0.0.0:xxxx failed: port is already allocated` 的错误，说明该端口被其他服务占用。
**解决办法**：编辑根目录的 `docker-compose.yml`，找到冲突的服务并修改映射端口。例如将 `5433:5432` 修改为 `5434:5432`。

### 4.2 权限不足 (Permission Denied)
如果在挂载 `data/n8n` 或 `dify-source/docker/volumes/` 目录时遇到权限错误。
**解决办法**：使用随项目提供的 `scripts/init.sh` 进行初始化，它会自动为您分配正确的 UID（如 1000）。

### 4.3 查看后台日志
如果您在界面上点击操作后没有反应，可以通过查看 Docker 日志来排查问题：
```bash
# 查看主业务后端日志
docker logs -f insight_backend

# 查看自动抓取与飞书推送日志
docker logs -f insight_n8n

# 查看 Dify 核心接口日志
docker logs -f insightgraph-api-1
```
