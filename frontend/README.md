# 前端项目

智能文档问答系统的前端项目，使用 React + TypeScript + Vite + Ant Design 构建。

## 技术栈

- **React 18** - UI 框架
- **TypeScript** - 类型安全
- **Vite** - 构建工具
- **Ant Design** - UI 组件库
- **React Router** - 路由管理
- **Axios** - HTTP 客户端
- **Day.js** - 日期处理

## 快速开始

### 安装依赖

```bash
npm install
# 或
yarn install
# 或
pnpm install
```

### 开发

```bash
npm run dev
```

访问 http://localhost:3000

### 构建

```bash
npm run build
```

### 预览构建结果

```bash
npm run preview
```

## 项目结构

```
frontend/
├── src/
│   ├── api/              # API 接口定义
│   │   ├── client.ts    # Axios 客户端配置
│   │   ├── tenant.ts    # 租户 API
│   │   └── user.ts      # 用户 API
│   ├── components/      # 组件
│   │   └── Layout/      # 布局组件
│   ├── pages/           # 页面
│   │   ├── TenantList.tsx    # 租户列表
│   │   ├── TenantForm.tsx     # 租户表单
│   │   ├── UserList.tsx       # 用户列表
│   │   └── UserForm.tsx       # 用户表单
│   ├── App.tsx          # 应用入口
│   ├── main.tsx         # 入口文件
│   └── index.css        # 全局样式
├── index.html           # HTML 模板
├── package.json         # 依赖配置
├── tsconfig.json        # TypeScript 配置
└── vite.config.ts       # Vite 配置
```

## 环境变量

创建 `.env` 文件（可选）：

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

如果不设置，默认使用代理配置（`/api` -> `http://localhost:8000`）

## 功能模块

### 租户管理

- 租户列表查询
- 创建租户
- 编辑租户
- 删除租户
- 启用/停用租户

### 用户管理

- 用户列表查询（按租户筛选）
- 创建用户
- 编辑用户
- 删除用户
- 启用/冻结用户

## 开发说明

### API 调用

所有 API 调用都通过 `src/api/client.ts` 配置的 axios 实例，支持：

- 自动添加认证 token
- 统一错误处理
- 请求/响应拦截

### 路由配置

路由配置在 `src/App.tsx` 中，使用 React Router v6。

### 样式

- 使用 Ant Design 组件库的默认样式
- 全局样式在 `src/index.css`
- 组件样式使用 Ant Design 的样式系统

## 后续开发

- [ ] 登录/认证页面
- [ ] 权限管理
- [ ] 角色管理
- [ ] 菜单管理
- [ ] 配置管理
- [ ] 文档管理
- [ ] 问答功能

