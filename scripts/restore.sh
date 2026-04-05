#!/bin/bash

# ==============================================================================
# InsightGraph 自动化恢复脚本 (Restore Script)
# ==============================================================================
# 用于从 backup.sh 生成的备份目录中恢复数据。
# 警告：恢复操作将覆盖当前系统数据，建议先进行一次备份！
# ==============================================================================

PROJECT_ROOT=$(cd "$(dirname "$0")/.." && pwd)
BACKUP_ROOT="${PROJECT_ROOT}/backups"

# 检查参数
if [ -z "$1" ]; then
    echo "❌ 错误: 未指定备份目录！"
    echo "💡 用法: $0 <备份文件夹名或路径>"
    echo "🔍 例如: $0 20260405_120000"
    echo "📂 可用备份列表:"
    ls -1d "${BACKUP_ROOT}"/*/ 2>/dev/null | awk -F/ '{print $NF}'
    exit 1
fi

# 解析备份路径
BACKUP_DIR="$1"
if [[ ! "$BACKUP_DIR" == /* ]]; then
    BACKUP_DIR="${BACKUP_ROOT}/${BACKUP_DIR}"
fi

if [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ 错误: 找不到指定的备份目录: $BACKUP_DIR"
    exit 1
fi

echo "=================================================="
echo "🚨 警告: 准备从备份恢复 InsightGraph 数据！"
echo "📂 备份源: ${BACKUP_DIR}"
echo "⚠️  此操作将覆盖现有的数据库、附件和 n8n 配置！"
echo "=================================================="
read -p "❓ 确认要继续吗？(y/N): " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "🛑 已取消恢复操作。"
    exit 0
fi

echo "=================================================="
echo "⏳ 开始执行恢复流程..."
echo "=================================================="

# 加载当前环境变量，如果不存在则使用备份的
if [ -f "${PROJECT_ROOT}/.env" ]; then
    export $(grep -v '^#' "${PROJECT_ROOT}/.env" | xargs)
elif [ -f "${BACKUP_DIR}/.env.backup" ]; then
    echo "⚠️  当前环境未找到 .env，尝试使用备份的 .env..."
    cp "${BACKUP_DIR}/.env.backup" "${PROJECT_ROOT}/.env"
    export $(grep -v '^#' "${PROJECT_ROOT}/.env" | xargs)
fi

DB_USER="${POSTGRES_USER:-insight_user}"
DB_NAME="${POSTGRES_DB:-insight_graph}"

# 1. 停止业务容器以防写入冲突 (除了 postgres)
echo "[1/6] 🛑 停止相关后端服务 (backend, n8n, redis)..."
cd "${PROJECT_ROOT}"
docker compose stop backend n8n redis
if [ $? -eq 0 ]; then
    echo "  ✅ 服务已停止。"
else
    echo "  ❌ 停止服务失败，请检查 Docker Compose 配置！"
    exit 1
fi

# 2. 恢复 PostgreSQL 数据库
echo "[2/6] 🐘 正在恢复 PostgreSQL 数据库..."
if [ -f "${BACKUP_DIR}/postgres_db.dump" ]; then
    # 检查数据库容器是否在运行
    if ! docker ps | grep -q "insight_postgres"; then
        echo "  ⚠️ postgres 容器未运行，尝试启动..."
        docker compose start postgres
        sleep 5
    fi

    echo "  🔄 正在清理旧数据库并恢复..."
    # 踢掉所有连接并重建数据库
    docker exec insight_postgres psql -U "$DB_USER" -d postgres -c "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = '$DB_NAME' AND pid <> pg_backend_pid();" > /dev/null 2>&1
    docker exec insight_postgres psql -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;" > /dev/null 2>&1
    docker exec insight_postgres psql -U "$DB_USER" -d postgres -c "CREATE DATABASE $DB_NAME;" > /dev/null 2>&1
    
    # 执行 pg_restore
    docker exec -i insight_postgres pg_restore -U "$DB_USER" -d "$DB_NAME" -1 < "${BACKUP_DIR}/postgres_db.dump"
    if [ $? -eq 0 ]; then
        echo "  ✅ 数据库恢复成功！"
    else
        echo "  ⚠️ 数据库恢复过程中出现警告或错误，请检查日志。"
    fi
else
    echo "  ⚠️ 备份目录中未找到 postgres_db.dump，跳过数据库恢复。"
fi

# 3. 恢复本地附件
echo "[3/6] 📎 正在恢复本地附件 (backend/uploads)..."
if [ -f "${BACKUP_DIR}/backend_uploads.tar.gz" ]; then
    echo "  🔄 正在清理当前附件目录..."
    rm -rf "${PROJECT_ROOT}/backend/uploads"
    tar -xzf "${BACKUP_DIR}/backend_uploads.tar.gz" -C "${PROJECT_ROOT}/backend"
    echo "  ✅ 附件恢复成功！"
else
    echo "  ⚠️ 未找到 backend_uploads.tar.gz，跳过附件恢复。"
fi

# 4. 恢复 n8n 数据
echo "[4/6] 🤖 正在恢复 n8n 配置数据 (data/n8n)..."
if [ -f "${BACKUP_DIR}/n8n_data.tar.gz" ]; then
    echo "  🔄 正在清理当前 n8n 目录..."
    # 需要 sudo 权限，因为 n8n 文件通常属于其容器内的用户
    sudo rm -rf "${PROJECT_ROOT}/data/n8n" 2>/dev/null || rm -rf "${PROJECT_ROOT}/data/n8n"
    sudo tar -xzf "${BACKUP_DIR}/n8n_data.tar.gz" -C "${PROJECT_ROOT}/data" 2>/dev/null || tar -xzf "${BACKUP_DIR}/n8n_data.tar.gz" -C "${PROJECT_ROOT}/data"
    echo "  ✅ n8n 配置恢复成功！"
else
    echo "  ⚠️ 未找到 n8n_data.tar.gz，跳过 n8n 恢复。"
fi

# 5. 恢复 Redis 数据
echo "[5/6] 🟥 正在恢复 Redis 缓存数据 (data/redis)..."
if [ -f "${BACKUP_DIR}/redis_data.tar.gz" ]; then
    echo "  🔄 正在清理当前 Redis 目录..."
    rm -rf "${PROJECT_ROOT}/data/redis"
    tar -xzf "${BACKUP_DIR}/redis_data.tar.gz" -C "${PROJECT_ROOT}/data"
    echo "  ✅ Redis 数据恢复成功！"
else
    echo "  ℹ️ 未找到 redis_data.tar.gz，跳过 Redis 恢复。"
fi

# 6. 重启服务
echo "[6/6] 🚀 重启所有后端服务..."
cd "${PROJECT_ROOT}"
docker compose start
if [ $? -eq 0 ]; then
    echo "  ✅ 所有服务已重新启动！"
else
    echo "  ❌ 重启服务失败，请尝试手动运行 'docker compose up -d'"
fi

echo "=================================================="
echo "🎉 恢复流程全部结束！"
echo "💡 提示: 您的环境变量文件 (.env) 已被保留。如果您更换了机器，请记得重新配置 .env 文件中的机器特定参数。"
echo "=================================================="
