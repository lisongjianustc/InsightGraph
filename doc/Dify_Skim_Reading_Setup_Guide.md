# InsightGraph - Dify AI 泛读模式配置手册

本文档旨在指导你如何在本地部署的 Dify 中创建一个用于“AI 泛读”的大语言模型应用，并将其接入到 InsightGraph 的后端服务中。

---

## 1. 登录 Dify 管理后台

由于你已经在本地 Docker 部署了 Dify 官方社区版：
1. 打开浏览器，访问 `http://localhost:3000`（或你部署的 Dify 实际 Web 端口，如果你改了的话，可能是 `http://localhost` 默认的 80 端口，依据你 docker-compose.yaml 中 web 的映射端口）。
2. 使用你的管理员账号登录。

---

## 2. 配置大模型供应商 (Model Providers)

如果你还没有在 Dify 中配置过大模型，请先完成此步。
1. 点击右上角你的**头像**，选择 **设置 (Settings)**。
2. 在左侧菜单选择 **模型供应商 (Model Providers)**。
3. 选择你要使用的大模型（例如 OpenAI 的 `gpt-4o-mini`，或 DeepSeek 的 `deepseek-chat`，甚至是本地部署的 Ollama 模型）。
4. 输入你的 API Key 并保存，确保模型处于可用状态。

---

## 3. 创建用于泛读的 AI 应用

在 InsightGraph 的泛读模式中，我们期望大模型能接收一段长文本（如论文摘要或项目描述），并按结构输出精炼的中文总结。因此，我们需要创建一个 **聊天助手 (Chatbot)** 或 **文本生成应用 (Text Generator)**。这里推荐使用 **基础聊天助手**，因为接口最通用。

### 3.1 新建应用
1. 在 Dify 主界面，点击顶部导航的 **工作室 (Studio)**。
2. 点击页面右侧的 **创建空白应用 (Create from Blank)**。
3. 在弹出的窗口中：
   - **应用类型**：选择 **聊天助手 (Chatbot)** 或 **基础助手 (Basic Assistant)**。
   - **应用名称**：输入 `InsightGraph 泛读助手`。
   - **描述**：`用于提取论文与资讯主旨要义的 AI 助手。`
4. 点击 **创建**，进入应用编排页面。

### 3.2 配置提示词 (Prompt)
在编排页面的“提示词 (Prompt)”或“系统提示 (System Prompt)”文本框中，输入以下设定（这决定了泛读模式的输出质量）：

```text
你是一位资深科技研究员。你的任务是对用户提供的资讯或论文内容进行快速泛读总结。

请严格按照以下结构输出，使用精炼的中文：
**【主旨要义】**
（用一两句话概括文章的核心思想或项目的主要目的）

**【核心结论/功能】**
（列出 2-3 条最重要的结论或功能特点，使用无序列表）

**【创新点/价值】**
（简述该内容的创新之处或为什么值得关注）

注意：如果内容非常简短，只需输出【主旨要义】即可。保持客观、专业的学术基调，不要输出多余的寒暄语。
```

### 3.3 选择模型与测试
1. 在提示词配置区的右上角，选择你在第 2 步中配置好的大模型（如 `deepseek-chat`）。
2. 将 **上下文长度 (Context Length)** 和 **最大 Token 数 (Max Tokens)** 调大（如 4096），以防论文摘要过长。
3. 在页面右侧的 **调试与预览 (Debug and Preview)** 窗口，随便粘贴一段文字，测试它是否按规定的结构输出。
4. 测试无误后，点击页面右上角的 **发布 (Publish)**。

---

## 4. 获取 API 密钥 (API Key)

这是将该 Dify 应用连接到 InsightGraph 后端的关键步骤。

1. 在刚才发布的“InsightGraph 泛读助手”应用页面中，点击左侧导航栏的 **访问 API (API Access)**。
2. 在右上角点击 **API 密钥 (API Keys)** -> **创建密钥 (Create new Secret Key)**。
3. 复制生成的以 `app-` 开头的密钥字符串（注意：密钥只显示一次，请妥善保存）。

---

## 5. 配置 InsightGraph 后端环境变量

现在回到你的 InsightGraph 项目代码中：

1. 打开 `backend/.env` 文件（如果没有，请在 `/Users/lisongjian/Project/InsightGraph/backend/` 目录下创建一个）。
2. 添加或修改以下环境变量：

```env
# Dify API 的基础地址（注意是 /v1 结尾）
# 如果后端 FastAPI 和 Dify 都在同一个 Docker 网络，可使用 Dify 容器名；如果都在宿主机映射，使用宿主机 IP。
DIFY_API_URL=http://localhost:5001/v1

# （已有配置）如果你之前配置了知识库 Dataset 的 API Key，保留它：
DIFY_API_KEY=dataset-xxxxxxxxxxxxxxxxxxxxx

# 【新增配置】填入你在第 4 步中获取的“聊天助手”应用 API 密钥：
DIFY_READER_API_KEY=app-xxxxxxxxxxxxxxxxxxxxxxx
```

*注意：`DIFY_READER_API_KEY` 专门用于请求大模型进行泛读总结；而 `DIFY_API_KEY` 用于向向量知识库写入数据。它们在 Dify 中是两种不同的 API 密钥。*

---

## 6. 重启后端服务

配置完成后，你需要重启 FastAPI 后端使环境变量生效。

1. 如果你使用的是 Docker Compose 运行的 FastAPI，在终端执行：
   ```bash
   cd /Users/lisongjian/Project/InsightGraph
   docker compose restart fastapi_backend
   ```
2. 如果你是在本地直接用 `uvicorn` 或 Python 运行的，请终止进程并重新启动。

---

## 7. 在 Web 页面测试

1. 打开前端页面 [http://localhost:5173/](http://localhost:5173/)。
2. 在任意一张资讯卡片上，点击 **“AI 泛读”** 按钮。
3. 此时弹窗中应该会出现加载动画，随后展示由 Dify 大模型根据你设定的结构返回的真实的泛读总结！

如果一切顺利，说明 Dify 泛读应用已成功打通！你可以点击弹窗底部的“保存总结至知识库”，将这段 AI 总结直接存入你的知识库中。