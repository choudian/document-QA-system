# 安装和运行指南

本文档提供详细的安装和运行说明，适用于不同操作系统和环境。

## 目录

1. [系统要求](#系统要求)
2. [快速开始（Docker）](#快速开始docker)
3. [本地开发环境](#本地开发环境)
4. [生产环境部署](#生产环境部署)
5. [验证安装](#验证安装)
6. [常见问题](#常见问题)

## 系统要求

### 最低要求

- **操作系统**: Linux、macOS、Windows 10+
- **Python**: 3.9 或更高版本
- **Node.js**: 18.0 或更高版本
- **数据库**: PostgreSQL 12+、MySQL 8+、SQLite 3+（开发用）
- **内存**: 至少 4GB RAM
- **磁盘**: 至少 10GB 可用空间

### 推荐配置

- **Python**: 3.11+
- **Node.js**: 20+
- **数据库**: PostgreSQL 15+
- **内存**: 8GB+ RAM
- **磁盘**: 50GB+ 可用空间（用于文档和向量存储）

## 快速开始（Docker）

这是最简单的部署方式，适合快速体验和开发。

### 前置要求

- Docker >= 20.10
- Docker Compose >= 2.0

### 步骤

1. **克隆仓库**

```bash
git clone <repository-url>
cd document-QA-system
```

2. **启动服务**

```bash
# 生产环境
docker-compose up -d

# 开发环境（支持热重载）
docker-compose -f docker-compose.dev.yml up -d
```

3. **查看日志**

```bash
docker-compose logs -f
```

4. **访问应用**

- 前端: http://localhost:3000
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

### 停止服务

```bash
docker-compose down

# 同时删除数据卷（会删除数据库数据）
docker-compose down -v
```

详细说明请参考 [docker/README.md](../docker/README.md)

## 本地开发环境

### 后端设置

#### 1. 安装Python依赖管理工具

**使用uv（推荐）**：

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**或使用pip**：

```bash
pip install --upgrade pip
```

#### 2. 安装项目依赖

**使用uv**：

```bash
# 安装所有依赖
uv sync

# 或安装到当前环境
uv pip install -e .
```

**使用pip**：

```bash
pip install -r requirements.txt
```

#### 3. 配置数据库

创建 `.env` 文件：

```bash
cp env.example.txt .env
```

编辑 `.env` 文件，配置数据库连接：

**PostgreSQL（推荐）**：

```env
DATABASE_URL=postgresql://user:password@localhost:5432/document_qa
```

**MySQL**：

```env
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/document_qa
```

**SQLite（开发测试用）**：

```env
DATABASE_URL=sqlite:///./document_qa.db
```

#### 4. 初始化数据库

```bash
# 运行数据库迁移
alembic upgrade head

# 初始化默认数据（权限、角色等）
python -c "from app.core.database import init_db; init_db()"
```

#### 5. 启动后端服务

```bash
# 开发模式（支持热重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或使用Python模块
python -m app.main
```

后端服务将在 http://localhost:8000 启动

### 前端设置

#### 1. 安装Node.js

确保已安装Node.js 18+：

```bash
node --version
npm --version
```

#### 2. 安装依赖

```bash
cd frontend
npm install
```

#### 3. 配置环境变量（可选）

创建 `frontend/.env.local`：

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

#### 4. 启动开发服务器

```bash
npm run dev
```

前端服务将在 http://localhost:3000 启动

## 生产环境部署

### 使用Docker Compose（推荐）

1. **修改配置**

编辑 `docker-compose.yml`，修改以下配置：

```yaml
environment:
  DATABASE_URL: postgresql://user:password@db:5432/document_qa
  SECRET_KEY: your-strong-secret-key-here  # 修改为强密钥
  POSTGRES_PASSWORD: your-db-password      # 修改数据库密码
```

2. **构建镜像**

```bash
docker-compose build
```

3. **启动服务**

```bash
docker-compose up -d
```

4. **查看状态**

```bash
docker-compose ps
```

### 手动部署

#### 后端部署

1. **安装依赖**

```bash
pip install -r requirements.txt
```

2. **配置环境变量**

```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/document_qa"
export SECRET_KEY="your-secret-key"
```

3. **初始化数据库**

```bash
alembic upgrade head
```

4. **使用进程管理器启动**

**使用systemd**（Linux）：

创建 `/etc/systemd/system/document-qa.service`：

```ini
[Unit]
Description=Document QA System API
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/document-QA-system
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl start document-qa
sudo systemctl enable document-qa
```

**使用PM2**（Node.js进程管理器）：

```bash
npm install -g pm2
pm2 start "uvicorn app.main:app --host 0.0.0.0 --port 8000" --name document-qa-api
pm2 save
pm2 startup
```

#### 前端部署

1. **构建生产版本**

```bash
cd frontend
npm run build
```

2. **使用Nginx部署**

创建Nginx配置 `/etc/nginx/sites-available/document-qa`：

```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /path/to/document-QA-system/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

启用配置：

```bash
sudo ln -s /etc/nginx/sites-available/document-qa /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 验证安装

### 1. 检查后端服务

```bash
# 检查健康状态
curl http://localhost:8000/

# 应该返回: {"message":"智能文档问答系统 API"}
```

### 2. 检查API文档

访问 http://localhost:8000/docs 应该看到Swagger UI

### 3. 检查前端服务

访问 http://localhost:3000 应该看到登录页面

### 4. 运行测试

```bash
# 后端测试
pytest

# 前端测试
cd frontend && npm test
```

## 常见问题

### 问题1: 数据库连接失败

**症状**: 启动时提示数据库连接错误

**解决方案**:
1. 检查数据库服务是否运行
2. 检查 `DATABASE_URL` 配置是否正确
3. 检查数据库用户权限
4. 检查防火墙设置

### 问题2: 端口被占用

**症状**: 启动时提示端口已被占用

**解决方案**:
```bash
# 查找占用端口的进程
# Linux/macOS
lsof -i :8000
lsof -i :3000

# Windows
netstat -ano | findstr :8000
netstat -ano | findstr :3000

# 修改端口（在.env或docker-compose.yml中）
```

### 问题3: 依赖安装失败

**症状**: `pip install` 或 `npm install` 失败

**解决方案**:
1. 检查网络连接
2. 使用国内镜像源：
   ```bash
   # Python
   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
   
   # Node.js
   npm install --registry=https://registry.npmmirror.com
   ```
3. 升级pip/npm到最新版本

### 问题4: 前端无法连接后端

**症状**: 前端页面显示API错误

**解决方案**:
1. 检查后端服务是否运行
2. 检查 `VITE_API_BASE_URL` 配置
3. 检查CORS设置（开发环境已配置代理）
4. 检查浏览器控制台错误信息

### 问题5: Docker容器无法启动

**症状**: `docker-compose up` 失败

**解决方案**:
1. 检查Docker和Docker Compose版本
2. 检查端口是否被占用
3. 查看详细错误日志：
   ```bash
   docker-compose logs
   ```
4. 尝试重建镜像：
   ```bash
   docker-compose build --no-cache
   ```

### 问题6: 数据库迁移失败

**症状**: `alembic upgrade head` 失败

**解决方案**:
1. 检查数据库连接
2. 检查数据库用户权限
3. 查看迁移历史：
   ```bash
   alembic history
   ```
4. 手动执行迁移：
   ```bash
   alembic upgrade <revision>
   ```

## 获取帮助

如果遇到其他问题：

1. 查看日志文件
2. 检查 [PROGRESS.md](../PROGRESS.md) 了解已知问题
3. 查看 [docs/](../docs/) 目录下的其他文档
4. 提交Issue到GitHub仓库
