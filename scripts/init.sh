#!/bin/bash

# ==============================================================================
# InsightGraph 自动初始化脚本 (Init Script)
# ==============================================================================
# 用于在新设备/服务器上一键部署 InsightGraph 的全部运行环境。
# 此脚本将：
# 1. 检查 Docker & Node.js 环境
# 2. 自动生成所需的本地数据挂载目录
# 3. 复制 .env 配置文件模板并提示用户填入大模型 Key
# 4. 初始化容器并设置目录权限
# ==============================================================================

# 获取项目根目录
PROJECT_ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "${PROJECT_ROOT}"

echo "=================================================="
echo "🚀 开始初始化 InsightGraph 部署环境..."
echo "=================================================="

# 1. 环境检查
echo "[1/4] 🔍 检查依赖环境..."
if ! command -v docker &> /dev/null; then
    echo "  ❌ 错误: 未检测到 Docker，请先安装 Docker Desktop 或 Docker Engine！"
    exit 1
fi
echo "  ✅ Docker 已安装: $(docker --version)"

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "  ❌ 错误: 未检测到 Docker Compose！"
    exit 1
fi
echo "  ✅ Docker Compose 已安装。"

# 2. 创建本地数据目录并设置权限
echo "[2/4] 📁 创建本地数据挂载目录..."
mkdir -p "${PROJECT_ROOT}/data/postgres"
mkdir -p "${PROJECT_ROOT}/data/redis"
mkdir -p "${PROJECT_ROOT}/data/n8n"
mkdir -p "${PROJECT_ROOT}/backend/uploads/capsules"
mkdir -p "${PROJECT_ROOT}/backend/uploads/documents"

echo "  ✅ 目录创建完成。"

# 为 n8n 设置特定的权限 (n8n 容器内部通常使用 node 用户的 UID 1000)
# 这可以防止启动时遇到 permission denied 的问题
echo "  🔑 正在配置目录权限 (可能需要 sudo 密码)..."
sudo chown -R 1000:1000 "${PROJECT_ROOT}/data/n8n" 2>/dev/null || echo "  ⚠️ 警告: n8n 目录权限设置失败，如果您在 Windows/Mac 下可忽略此警告。"

# 3. 环境变量配置
echo "[3/4] ⚙️ 配置文件初始化..."
if [ -f "${PROJECT_ROOT}/.env" ]; then
    echo "  ✅ 检测到已存在 .env 文件，跳过模板复制。"
else
    if [ -f "${PROJECT_ROOT}/.env.example" ]; then
        cp "${PROJECT_ROOT}/.env.example" "${PROJECT_ROOT}/.env"
        echo "  ✅ 已将 .env.example 复制为 .env。"
    else
        echo "  ⚠️ 未找到 .env.example 模板文件，请确保您的项目完整！"
    fi
fi

# 提示用户填入 Dify 密钥
echo "=================================================="
echo "⚠️ 注意: 在启动服务之前，您必须配置 .env 文件中的大模型 Key！"
echo "  路径: ${PROJECT_ROOT}/.env"
echo "  必须填写的字段包括："
echo "    - DIFY_API_KEY"
echo "    - DIFY_READER_API_KEY"
echo "    - DIFY_DEEP_READER_API_KEY"
echo "    - DIFY_OCR_WORKFLOW_API_KEY"
echo "    - DIFY_GLOBAL_CHAT_API_KEY"
echo "=================================================="

# 4. 询问是否启动服务
read -p "❓ 是否现在立即通过 Docker Compose 启动基础后端服务？(y/N): " start_now
if [[ "$start_now" =~ ^[Yy]$ ]]; then
    echo "[4/4] 🐳 正在拉起后端容器..."
    docker compose up -d --build
    if [ $? -eq 0 ]; then
        echo "  ✅ 容器启动成功！"
    else
        echo "  ❌ 容器启动失败，请检查 Docker 日志。"
        exit 1
    fi
else
    echo "[4/4] 🐳 已跳过容器启动。"
    echo "  💡 准备就绪后，请手动执行: docker compose up -d"
fi

echo "=================================================="
echo "🎉 InsightGraph 初始化完成！"
echo "=================================================="
echo "💻 接下来您可以:"
echo "1. 编辑 .env 文件，填入您的大模型 Key"
echo "2. 进入 frontend 目录，执行 npm install & npm run dev 体验网页端"
echo "3. 或者执行 npm run electron:build 打包属于您的桌面端应用"
echo "=================================================="
