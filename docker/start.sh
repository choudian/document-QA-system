#!/bin/bash
# 启动脚本 - 用于容器内初始化

set -e

echo "=========================================="
echo "启动智能文档问答系统"
echo "=========================================="

# 等待数据库就绪
echo "等待数据库就绪..."
until pg_isready -h db -p 5432 -U document_qa > /dev/null 2>&1; do
  echo "数据库未就绪，等待中..."
  sleep 2
done
echo "数据库已就绪！"

# 运行数据库迁移
echo "运行数据库迁移..."
alembic upgrade head

# 初始化数据（如果需要）
# echo "初始化系统数据..."
# python scripts/init_data.py

echo "=========================================="
echo "启动应用服务器..."
echo "=========================================="

# 启动应用
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
