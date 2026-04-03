#!/bin/bash

# InsightGraph 启动脚本
# 此脚本只启动本项目的相关服务，不影响系统中的其他 Docker 容器

echo "====================================="
echo "🚀 正在启动 InsightGraph 系统..."
echo "====================================="

# 1. 检查 Docker 是否运行
if ! docker info >/dev/null 2>&1; then
    echo "❌ 错误: Docker 未运行，请先启动 Docker Desktop"
    exit 1
fi

# 2. 检查 Dify 服务状态
echo "🔍 检查 Dify 服务状态..."
DIFY_CONTAINER=$(docker ps -a --filter "name=docker-api-1" --format "{{.Status}}")

if [ -z "$DIFY_CONTAINER" ]; then
    echo "⚠️ 警告: 未找到 Dify 容器。请确保 Dify 已在其他目录部署并运行。"
    echo "   (通常在 dify/docker 目录下运行: docker compose up -d)"
elif echo "$DIFY_CONTAINER" | grep -q "Exited"; then
    echo "🔄 尝试唤醒休眠的 Dify 服务..."
    # 假设 Dify 容器的 network 仍在，直接启动存在的容器
    docker start docker-api-1 docker-worker-1 docker-worker_beat-1 docker-web-1 docker-db_postgres-1 docker-redis-1 docker-weaviate-1 docker-sandbox-1 docker-plugin_daemon-1 docker-ssrf_proxy-1 >/dev/null 2>&1
    echo "✅ Dify 服务唤醒指令已发送"
else
    echo "✅ Dify 服务正在运行中"
fi

# 3. 启动 InsightGraph 后端与基础服务 (Postgres, Redis, n8n, Backend)
echo "📦 正在启动 InsightGraph 核心服务群 (Docker Compose)..."
cd "$(dirname "$0")"
docker compose up -d

# 4. 检查后端健康状态
echo "⏳ 等待核心服务就绪..."
sleep 5

# 5. 启动前端服务
echo "🌐 正在启动前端开发服务器..."
cd frontend
# 检查 node_modules
if [ ! -d "node_modules" ]; then
    echo "📦 首次运行，正在安装前端依赖..."
    npm install
fi

# 在后台启动 npm run dev，并将日志重定向到文件
echo "🖥️  前端服务启动中... (可通过 http://localhost:5173 访问)"
npm run dev > ../frontend_dev.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../.frontend_pid

echo "====================================="
echo "✨ 启动完成！"
echo "👉 后端 API 地址: http://localhost:8000"
echo "👉 前端访问地址: http://localhost:5173"
echo "👉 n8n 工作流: http://localhost:5678"
echo "====================================="
echo "如果前端页面无法访问，请查看项目根目录下的 frontend_dev.log 文件"
