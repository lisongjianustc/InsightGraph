#!/bin/bash

# ==============================================================================
# InsightGraph 自动化备份脚本 (Backup Script)
# ==============================================================================
# 支持手动执行，也可配置在 crontab 中实现定时备份。
# 备份内容包括：
# 1. PostgreSQL 数据库 (包含关系型数据和知识图谱向量)
# 2. Redis 缓存数据 (可选，主要为了快速恢复状态)
# 3. 本地上传的附件 (backend/uploads)
# 4. n8n 自动化工作流配置与数据 (data/n8n)
# 5. Dify 核心挂载数据 (dify-source/docker/volumes)
# 6. .env 环境配置文件
# ==============================================================================

# 基础目录配置
PROJECT_ROOT=$(cd "$(dirname "$0")/.." && pwd)
BACKUP_ROOT="${PROJECT_ROOT}/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="${BACKUP_ROOT}/${TIMESTAMP}"

# 保留最近的备份天数
KEEP_DAYS=7

echo "=================================================="
echo "🚀 开始 InsightGraph 数据备份 [${TIMESTAMP}]"
echo "=================================================="

# 1. 创建备份目录
mkdir -p "${BACKUP_DIR}"
echo "[1/6] 📁 已创建备份目录: ${BACKUP_DIR}"

# 加载环境变量 (获取数据库密码等信息)
if [ -f "${PROJECT_ROOT}/.env" ]; then
    export $(grep -v '^#' "${PROJECT_ROOT}/.env" | xargs)
else
    echo "⚠️ 警告: 未找到 .env 文件，可能会影响数据库备份。"
fi

# 2. 备份 PostgreSQL 数据库
echo "[2/6] 🐘 正在备份 PostgreSQL 数据库..."
# 使用 docker exec 调用 pg_dump，生成自定义格式的 dump 文件
if docker ps | grep -q "insight_postgres"; then
    docker exec -t insight_postgres pg_dump -U "${POSTGRES_USER:-insight_user}" -d "${POSTGRES_DB:-insight_graph}" -F c > "${BACKUP_DIR}/postgres_db.dump"
    if [ $? -eq 0 ]; then
        echo "  ✅ 数据库备份成功。"
    else
        echo "  ❌ 数据库备份失败！"
    fi
else
    echo "  ⚠️ 数据库容器 (insight_postgres) 未运行，跳过备份。"
fi

# 3. 备份本地上传的附件 (PDF, 截图等)
echo "[3/6] 📎 正在备份本地附件 (backend/uploads)..."
if [ -d "${PROJECT_ROOT}/backend/uploads" ]; then
    tar -czf "${BACKUP_DIR}/backend_uploads.tar.gz" -C "${PROJECT_ROOT}/backend" uploads
    echo "  ✅ 附件备份成功。"
else
    echo "  ℹ️ 附件目录不存在，跳过备份。"
fi

# 4. 备份 n8n 数据与配置
echo "[4/6] 🤖 正在备份 n8n 数据 (data/n8n)..."
if [ -d "${PROJECT_ROOT}/data/n8n" ]; then
    # 使用 sudo 避免权限问题（n8n 挂载出来的目录通常属于 node 用户的 uid）
    tar -czf "${BACKUP_DIR}/n8n_data.tar.gz" -C "${PROJECT_ROOT}/data" n8n 2>/dev/null || \
    sudo tar -czf "${BACKUP_DIR}/n8n_data.tar.gz" -C "${PROJECT_ROOT}/data" n8n
    echo "  ✅ n8n 数据备份成功。"
else
    echo "  ℹ️ n8n 数据目录不存在，跳过备份。"
fi

# 5. 备份 Redis (可选)
echo "[5/7] 🟥 正在备份 Redis 缓存数据 (data/redis)..."
if [ -d "${PROJECT_ROOT}/data/redis" ]; then
    tar -czf "${BACKUP_DIR}/redis_data.tar.gz" -C "${PROJECT_ROOT}/data" redis
    echo "  ✅ Redis 数据备份成功。"
else
    echo "  ℹ️ Redis 数据目录不存在，跳过备份。"
fi

# 6. 备份 Dify 核心数据
echo "[6/7] 🤖 正在备份 Dify 核心数据 (dify-source/docker/volumes)..."
if [ -d "${PROJECT_ROOT}/dify-source/docker/volumes" ]; then
    # 使用 sudo 避免遇到各种 root 容器的数据读写权限问题
    tar -czf "${BACKUP_DIR}/dify_volumes.tar.gz" -C "${PROJECT_ROOT}/dify-source/docker" volumes 2>/dev/null || \
    sudo tar -czf "${BACKUP_DIR}/dify_volumes.tar.gz" -C "${PROJECT_ROOT}/dify-source/docker" volumes
    echo "  ✅ Dify 数据备份成功。"
else
    echo "  ℹ️ Dify 数据目录不存在，跳过备份。"
fi

# 7. 备份环境变量文件 (非常重要)
echo "[7/7] 🔑 正在备份环境变量配置 (.env)..."
if [ -f "${PROJECT_ROOT}/.env" ]; then
    cp "${PROJECT_ROOT}/.env" "${BACKUP_DIR}/.env.backup"
    echo "  ✅ 主环境变量文件备份成功。"
fi
if [ -f "${PROJECT_ROOT}/dify-source/docker/.env" ]; then
    cp "${PROJECT_ROOT}/dify-source/docker/.env" "${BACKUP_DIR}/dify.env.backup"
    echo "  ✅ Dify 环境变量文件备份成功。"
fi

# 7. 清理过期备份
echo "🧹 正在清理 ${KEEP_DAYS} 天前的旧备份..."
# 查找 backups 目录下符合格式的文件夹，修改时间在 KEEP_DAYS 之前的，进行删除
find "${BACKUP_ROOT}" -maxdepth 1 -type d -name "20*" -mtime +${KEEP_DAYS} -exec rm -rf {} \;
echo "  ✅ 旧备份清理完成。"

echo "=================================================="
echo "🎉 备份全部完成！"
echo "📂 备份文件保存在: ${BACKUP_DIR}"
echo "=================================================="
echo "💡 提示: 如果想配置定时备份，请运行 'crontab -e' 并添加以下行:"
echo "0 3 * * * bash ${PROJECT_ROOT}/scripts/backup.sh >> ${PROJECT_ROOT}/backups/backup.log 2>&1"
echo "=================================================="
