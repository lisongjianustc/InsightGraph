#!/bin/bash
# InsightGraph 一键安装与启动脚本

set -e

echo "🚀 开始安装与部署 InsightGraph..."

# 1. 检查 Docker 是否安装
if ! command -v docker &> /dev/null
then
    echo "❌ Docker 未安装！请先安装 Docker Desktop (Mac/Windows) 或 Docker Engine (Linux)."
    exit 1
fi

# 2. 检查 .env 文件
if [ ! -f .env ]; then
    echo "⚠️ 未找到 .env 文件，正从 .env.example 复制..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ 已生成 .env 文件，请务必在运行前填入 Dify 相关的 API Key！"
    else
        echo "⚠️ 既没有 .env 也没有 .env.example，系统将创建空的 .env 文件。"
        touch .env
    fi
fi

# 3. 拉取 Dify 子模块 (如果有)
echo "📦 正在拉取最新的子模块..."
git submodule update --init --recursive || echo "⚠️ 子模块拉取失败或未配置子模块，忽略..."

# 4. 构建并启动后端与基础环境
echo "🐳 正在构建并启动 Docker 容器..."
docker compose up -d --build

# 5. 安装前端依赖
echo "🌐 正在安装前端依赖..."
cd frontend
if command -v npm &> /dev/null
then
    npm install
    echo "✅ 前端依赖安装完成！"
    echo "👉 若要启动前端开发服务器，请在 frontend 目录执行: npm run dev"
else
    echo "⚠️ 未找到 npm 命令，请手动安装 Node.js 后执行 frontend 的依赖安装。"
fi

echo ""
echo "🎉 InsightGraph 部署完成！"
echo "-----------------------------------"
echo "👉 后端 API 服务: http://localhost:8000"
echo "👉 Dify 管理后台: http://localhost:5001"
echo "👉 n8n 自动化流: http://localhost:5678"
echo "👉 数据库(PgVector): localhost:5432"
echo "-----------------------------------"
echo "💡 请记得在 .env 中填入大模型 API Key 并重启 backend: docker compose restart backend"
