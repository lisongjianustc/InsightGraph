#!/bin/bash

# InsightGraph 重启脚本
# 这个脚本仅负责重启当前项目的关联服务，并且安全地重启前端的 npm 进程。

echo "====================================="
echo "🔄 正在重启 InsightGraph 系统..."
echo "====================================="

# 1. 重启 Docker Compose 定义的服务（Backend, Postgres, Redis, n8n）
echo "📦 重启 InsightGraph 核心服务群 (Docker Compose)..."
cd "$(dirname "$0")"
docker compose restart

# 2. 如果存在前台运行的 Node 进程，杀掉它
echo "🌐 停止旧的前端服务进程..."
if [ -f .frontend_pid ]; then
    PID=$(cat .frontend_pid)
    if ps -p $PID > /dev/null; then
       kill $PID
       echo "已停止进程: $PID"
    fi
    rm .frontend_pid
fi

# 尝试根据端口清理遗留进程 (Mac 特有)
LSOF_PID=$(lsof -ti:5173)
if [ ! -z "$LSOF_PID" ]; then
    echo "强制清理占用 5173 端口的遗留进程: $LSOF_PID"
    kill -9 $LSOF_PID
fi

# 3. 重新启动前端服务
echo "🚀 重新启动前端服务..."
cd frontend
npm run dev > ../frontend_dev.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../.frontend_pid

echo "====================================="
echo "✨ 重启完成！前端已重新挂载至后台。"
echo "👉 后端 API 地址: http://localhost:8000"
echo "👉 前端访问地址: http://localhost:5173"
echo "👉 n8n 工作流: http://localhost:5678"
echo "====================================="
