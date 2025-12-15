# Docker 部署指南

本项目支持使用 Docker 和 Docker Compose 进行部署。

## 前置要求

- Docker >= 20.10
- Docker Compose >= 2.0

## 快速开始

### 生产环境部署

1. 复制环境变量文件（可选，docker-compose.yml中已包含默认配置）：
   ```bash
   cp env.example.txt .env
   ```

2. 修改 `docker-compose.yml` 中的环境变量（特别是数据库密码和SECRET_KEY）

3. 启动所有服务：
   ```bash
   docker-compose up -d
   ```

4. 查看日志：
   ```bash
   docker-compose logs -f
   ```

5. 访问应用：
   - 前端: http://localhost:3000
   - 后端API: http://localhost:8000
   - API文档: http://localhost:8000/docs

### 开发环境部署

使用开发配置，支持热重载：

```bash
docker-compose -f docker-compose.dev.yml up -d
```

## 服务说明

### 数据库服务 (db)
- 使用 PostgreSQL 15
- 数据持久化在 `postgres_data` volume
- 端口: 5432

### 后端服务 (backend)
- FastAPI 应用
- 自动运行数据库迁移
- 端口: 8000
- 数据目录挂载:
  - `./storage` -> `/app/storage` (文档存储)
  - `./vector_store` -> `/app/vector_store` (向量库)

### 前端服务 (frontend)
- React + Vite 应用
- Nginx 作为静态文件服务器
- 端口: 3000
- API请求自动代理到后端

## 常用命令

### 启动服务
```bash
docker-compose up -d
```

### 停止服务
```bash
docker-compose down
```

### 查看日志
```bash
# 所有服务
docker-compose logs -f

# 特定服务
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f db
```

### 重启服务
```bash
docker-compose restart backend
```

### 进入容器
```bash
# 后端容器
docker-compose exec backend bash

# 数据库容器
docker-compose exec db psql -U document_qa -d document_qa
```

### 运行数据库迁移
```bash
docker-compose exec backend alembic upgrade head
```

### 清理数据（谨慎操作）
```bash
# 停止并删除容器、网络
docker-compose down

# 同时删除数据卷（会删除数据库数据）
docker-compose down -v
```

## 环境变量配置

主要环境变量在 `docker-compose.yml` 中配置：

- `DATABASE_URL`: 数据库连接字符串
- `SECRET_KEY`: JWT密钥（生产环境必须修改）
- `STORAGE_BASE_PATH`: 文档存储路径
- `VECTOR_STORE_BASE_PATH`: 向量库存储路径

## 数据持久化

以下数据会持久化到宿主机：

- 数据库数据: Docker volume `postgres_data`
- 文档文件: `./storage` 目录
- 向量库: `./vector_store` 目录

## 故障排查

### 后端无法连接数据库
1. 检查数据库服务是否正常：`docker-compose ps`
2. 检查数据库日志：`docker-compose logs db`
3. 确认 `DATABASE_URL` 配置正确

### 前端无法访问后端API
1. 检查后端服务是否运行：`docker-compose ps backend`
2. 检查后端日志：`docker-compose logs backend`
3. 确认前端环境变量 `VITE_API_BASE_URL` 配置正确

### 数据库迁移失败
1. 进入后端容器：`docker-compose exec backend bash`
2. 手动运行迁移：`alembic upgrade head`
3. 查看迁移历史：`alembic history`

## 生产环境建议

1. **修改默认密码和密钥**
   - 修改 `docker-compose.yml` 中的数据库密码
   - 修改 `SECRET_KEY` 为强随机字符串

2. **使用外部数据库**
   - 生产环境建议使用独立的数据库服务
   - 修改 `DATABASE_URL` 指向外部数据库

3. **配置HTTPS**
   - 在Nginx配置中添加SSL证书
   - 或使用反向代理（如Traefik、Nginx Proxy Manager）

4. **资源限制**
   - 在 `docker-compose.yml` 中添加资源限制：
     ```yaml
     deploy:
       resources:
         limits:
           cpus: '2'
           memory: 2G
     ```

5. **日志管理**
   - 配置日志驱动和日志轮转
   - 使用集中式日志收集（如ELK、Loki）

6. **备份策略**
   - 定期备份数据库volume
   - 备份 `storage` 和 `vector_store` 目录
