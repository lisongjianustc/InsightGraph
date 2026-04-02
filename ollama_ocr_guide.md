# Ollama 本地多模态/OCR 模型配置与接入指南

要在本地通过 Ollama 实现图片文本提取（OCR）、公式识别和复杂图表解析，我们需要使用**多模态大模型（Multimodal LLM）**。传统的纯文本模型无法看图，而多模态模型可以直接接收图片并输出精准的描述、Markdown 甚至代码。

## 1. 推荐的 Ollama 多模态模型

对于 OCR、排版还原和复杂文档解析，强烈推荐以下两个目前在 Ollama 上表现最出色的多模态模型：

### 🥇 轻量级 OCR 首选：Moondream2
Moondream 是目前开源界性价比最高的超轻量视觉语言模型，参数量仅有 **1.8B**。
- **优点**：极低显存占用（普通笔记本无压力运行），速度极快，能够很好地识别图片内容、提取文字。
- **推荐版本**：`moondream`
- **Ollama 下载命令**：
  ```bash
  ollama run moondream
  ```

### 🥈 备选：Moondream2
Moondream 是一个极度轻量级的小型视觉语言模型（仅有 1.8B 参数）。
- **优点**：速度极快，对显存要求极低（普通笔记本甚至没有独显都能流畅运行），简单的文字提取和图片描述足够用。
- **推荐版本**：`moondream`

---

## 2. 安装与运行模型

打开你的终端，执行以下命令拉取并运行模型（以 `moondream` 为例）：

```bash
# 拉取并运行 moondream
ollama run moondream
```

首次运行会自动下载模型权重（约 4GB~8GB），下载完成后你会进入交互式终端，输入 `/bye` 退出即可。模型会在后台驻留。

---

## 3. 在 Dify 中接入 Ollama 多模态模型

由于我们的后端架构深度依赖 Dify，所以**最优雅的做法是把 Ollama 的多模态模型配置到 Dify 中**，然后在 InsightGraph 后端直接通过 Dify 的接口来处理图片和文件。

### 步骤 1：确保 Ollama 允许跨域和网络访问
如果你的 Dify 是跑在 Docker 里的，它需要通过宿主机的 IP 来访问 Ollama。
在 Mac/Linux 上，编辑你的 Ollama 环境变量（或直接在终端启动时注入）：

```bash
OLLAMA_HOST=0.0.0.0 OLLAMA_ORIGINS="*" ollama serve
```

### 步骤 2：在 Dify 中添加模型供应商
1. 登录 Dify 管理后台（`http://localhost:3000`）。
2. 点击右上角头像 -> **设置** -> **模型供应商 (Model Providers)**。
3. 找到 **Ollama** 卡片，点击 **添加模型**。
4. 填写配置：
   - **模型名称**: `moondream`
   - **基础 URL (Base URL)**: `http://host.docker.internal:11434` (Docker 环境下的宿主机地址)
   - **模型类型**: 选择 **`Text Generation`** 或 **`Chat`**。*注意：Dify 会自动识别其具备视觉（Vision）能力。*
   - **最大 Token 数**: 4096（视情况调整）
5. 点击 **保存**。

### 步骤 3：测试视觉能力
在 Dify 的“工作室”中创建一个基础的聊天应用（Chatbot），在模型下拉菜单中选择你刚刚配置的 `moondream` 模型。
你会发现聊天框左下角多了一个**“上传图片”**的图标！
传一张带有文字的截图，问它：“提取图片中的文字并用 Markdown 格式输出”，看看效果。

---

## 4. 后续后端架构规划（Stage 2.4 实现路径）

为了让闪念胶囊支持 PDF、Word、PPT 和图片的上传，我们的后端将采用如下策略：

1. **普通纯文本文件（.md, .txt）**：
   - 后端直接读取字符串，塞入知识库。
2. **结构化文档（.pdf, .docx, .pptx, .xlsx）**：
   - 优先使用现有的 `pdf2zh` 的底层引擎或者 Python 的 `docx` / `PyMuPDF` 库进行原生文本提取。
   - 这类文档本身就包含文本层，通常不需要调用沉重的 OCR，提取速度最快、最准确。
3. **图片文件（.png, .jpg, .jpeg）及无文本层的扫描版 PDF**：
   - 前端将图片转为 Base64。
   - 后端调用配置好的 **Moondream2 (经由 Dify 或直接调 Ollama API)**。
   - 给大模型发送 Prompt："You are an expert OCR and markdown formatter. Extract all text, tables, and formulas from this image and format them in beautiful Markdown. Do not include any other conversational text."
   - 拿到大模型返回的 Markdown 文本后，将其与图片 URL 一同存入闪念胶囊，并送入知识库。

准备好按照这个架构改造后端的上传接口了吗？
