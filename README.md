# 智能文档问答系统

个人知识库系统，包含系统管理、文档管理、问答功能三个大的模块。

## 项目结构

```
document-QA-system/
├── app/                    # 后端应用主目录
│   ├── api/               # API路由
│   │   └── v1/           # API v1版本
│   │       ├── tenants.py # 租户管理API
│   │       └── users.py   # 用户管理API
│   ├── core/             # 核心配置
│   │   ├── config.py     # 应用配置
│   │   └── database.py   # 数据库连接
│   ├── models/           # 数据模型
│   │   ├── tenant.py     # 租户模型
│   │   └── user.py       # 用户模型
│   ├── schemas/          # Pydantic Schema
│   │   ├── tenant.py     # 租户Schema
│   │   └── user.py       # 用户Schema
│   └── main.py           # 应用入口
├── frontend/              # 前端项目
│   ├── src/              # 源代码
│   │   ├── api/          # API接口
│   │   ├── components/   # 组件
│   │   ├── pages/        # 页面
│   │   └── App.tsx       # 应用入口
│   ├── package.json      # 前端依赖
│   └── vite.config.ts    # Vite配置
├── alembic/              # 数据库迁移
├── docs/                  # 文档
├── requirements.txt      # Python依赖
├── pyproject.toml        # Python项目配置（uv）
└── README.md             # 项目说明
```

## 技术栈

### 后端

- **框架**: FastAPI
- **数据库**: PostgreSQL / MySQL / SQLite / Oracle
- **ORM**: SQLAlchemy
- **密码加密**: passlib + bcrypt
- **数据库迁移**: Alembic
- **包管理**: uv（推荐）或 pip

### 前端

- **框架**: React 18 + TypeScript
- **构建工具**: Vite
- **UI组件库**: Ant Design
- **路由**: React Router
- **HTTP客户端**: Axios

## 快速开始

### 1. 安装 uv（如果还没有安装）

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 或使用 pip
pip install uv
```

### 2. 安装依赖

**使用 uv（推荐）**：
```bash
# 安装所有依赖
uv sync

# 或安装到当前环境
uv pip install -e .
```

**使用传统 pip**：
```bash
pip install -r requirements.txt
```

### 3. 配置数据库

创建 `.env` 文件，参考 `env.example.txt` 配置数据库连接：

```bash
# 复制示例文件
cp env.example.txt .env
```

编辑 `.env` 文件，选择并配置数据库连接信息：

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

**Oracle**：
```env
DATABASE_URL=oracle+cx_oracle://user:password@localhost:1521/xe
```

**注意**：
- `.env` 文件已添加到 `.gitignore`，不会被提交到版本库
- 根据选择的数据库，需要安装对应的数据库驱动：
  - MySQL: `uv pip install -e ".[mysql]"`
  - Oracle: `uv pip install -e ".[oracle]"`
- 详细的数据库配置说明请参考 `docs/database-setup.md`

### 4. 初始化数据库

```bash
# 创建迁移文件
alembic revision --autogenerate -m "init"

# 执行迁移
alembic upgrade head
```

### 5. 启动后端服务

```bash
python -m app.main
# 或
uvicorn app.main:app --reload
```

访问 http://localhost:8000/docs 查看API文档

### 6. 启动前端服务

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:3000 查看前端页面

**注意**：前端开发服务器已配置代理，API 请求会自动转发到后端（http://localhost:8000）

## API接口

### 租户管理

- `POST /api/v1/tenants` - 创建租户
- `GET /api/v1/tenants` - 查询租户列表
- `GET /api/v1/tenants/{tenant_id}` - 查询单个租户
- `PUT /api/v1/tenants/{tenant_id}` - 更新租户
- `DELETE /api/v1/tenants/{tenant_id}` - 删除租户
- `PATCH /api/v1/tenants/{tenant_id}/status` - 启用/停用租户

### 用户管理

- `POST /api/v1/users` - 创建用户
- `GET /api/v1/users?tenant_id=xxx` - 查询用户列表（必须指定tenant_id）
- `GET /api/v1/users/{user_id}` - 查询单个用户
- `PUT /api/v1/users/{user_id}` - 更新用户
- `DELETE /api/v1/users/{user_id}` - 删除用户
- `PATCH /api/v1/users/{user_id}/status` - 启用/冻结用户

## 功能模块

### 已实现

- ✅ 租户管理（CRUD）
- ✅ 用户管理（CRUD）
- ✅ 前端页面（租户管理、用户管理）

### 待开发

- ⏳ 认证与会话管理
- ⏳ 角色与权限管理
- ⏳ 菜单与资源管理
- ⏳ AI服务提供商配置
- ⏳ 配置管理模块
- ⏳ 文档管理
- ⏳ 问答功能

## 开发计划

详见 `docs/` 目录下的需求文档。

## 前端项目说明

前端项目位于 `frontend/` 目录，使用 React + TypeScript + Vite + Ant Design 构建。

### 前端快速开始

```bash
cd frontend
npm install
npm run dev
```

### 前端项目结构

```
frontend/
├── src/
│   ├── api/              # API接口定义
│   │   ├── client.ts    # Axios客户端配置
│   │   ├── tenant.ts    # 租户API
│   │   └── user.ts      # 用户API
│   ├── components/      # 组件
│   │   └── Layout/      # 布局组件
│   ├── pages/           # 页面
│   │   ├── TenantList.tsx    # 租户列表
│   │   ├── TenantForm.tsx     # 租户表单
│   │   ├── UserList.tsx       # 用户列表
│   │   └── UserForm.tsx       # 用户表单
│   ├── App.tsx          # 应用入口
│   └── main.tsx         # 入口文件
├── package.json         # 依赖配置
└── vite.config.ts       # Vite配置
```

详细的前端开发说明请参考 `frontend/README.md`

