#!/bin/bash

# InsightGraph 停止脚本
# 仅关闭当前目录下 docker-compose 启动的服务以及相关的前端进程，不会停止其他任何 Docker 容器或宿主机进程。

echo "====================================="
echo "🛑 正在安全停止 InsightGraph 系统..."
echo "====================================="

# 1. 关闭由当前 docker-compose 管理的后端服务 (Postgres, Redis, Backend, n8n)
echo "📦 正在关闭 InsightGraph 核心服务群..."
cd "$(dirname "$0")"
docker compose down

# 注意：为了安全起见，Dify 容器不会在这里被 stop，因为它是由另一个 docker-compose 独立管理的。
# 如果你需要彻底关闭 Dify，请到你原本安装 Dify 的目录下执行 `docker compose down`。

# 2. 查找并杀掉 npm 启动的前端 dev 进程
echo "🌐 正在停止前端开发服务器..."
if [ -f .frontend_pid ]; then
    PID=$(cat .frontend_pid)
    # 检查进程是否存在
    if ps -p $PID > /dev/null; then
       echo "找到后台前端进程 PID: $PID，正在停止..."
       kill $PID
       echo "✅ 前端服务已停止。"
    else
       echo "⚠️ 记录的进程 $PID 不存在，可能已经退出。"
    fi
    rm .frontend_pid
fi

# 双重保险：检查 5173 端口是否被占用，如果是，则安全杀掉 (适配 macOS / Linux)
LSOF_PID=$(lsof -ti:5173)
if [ ! -z "$LSOF_PID" ]; then
    echo "⚠️ 发现遗留占用 5173 端口的进程: $LSOF_PID，强制清理中..."
    kill -9 $LSOF_PID
fi

echo "====================================="
echo "✅ InsightGraph 系统已全部安全关闭！"
echo "   (注意: 此操作不会影响 Dify 及宿主机其他应用)"
echo "====================================="
