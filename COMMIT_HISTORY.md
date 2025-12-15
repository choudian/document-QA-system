# Git Commit 历史记录

## 2025-12-14

### 693b1f7 - 修复引用来源显示：补充文档信息到metadata并优化前端显示逻辑
- 在 `RetrievalService` 中补充文档信息到 metadata
- 优化前端显示逻辑，优先显示文档名称而非 ID
- 添加重排序服务 (`reranker_service.py`)
- 添加问答模块前端页面和 API 客户端
- 添加调试脚本

### 15004d7 - chore: add langchain dependencies to pyproject.toml
- 添加 LangChain 相关依赖到 pyproject.toml

### 485c321 - refactor: migrate LLM service from httpx to LangChain
- 将 LLM 服务从 httpx 迁移到 LangChain
- 使用 LangChain 的 ChatOpenAI 进行 LLM 调用

### dd1d18f - feat: implement QA module - conversation, message, retrieval, LLM chat and API endpoints
- 实现问答模块核心功能
- 会话管理、消息管理
- 检索服务、LLM 聊天
- API 端点实现

### 73c9347 - feat: add QA module foundation - conversation and message models, repositories and services
- 添加问答模块基础架构
- 会话和消息模型
- 数据访问层（Repository）
- 服务层（Service）

### 39396e6 - docs: improve documentation for document management module
- 完善文档管理模块的文档
- 更新功能文档、接口文档、用户文档

### 2e44a3a - feat: implement version coverage logic - delete old version vectors after new version vectorization succeeds
- 实现版本覆盖逻辑
- 新版本向量化成功后删除旧版本向量

### 81aca55 - feat: complete document task placeholder interfaces
- 完成文档任务占位接口
- 待办表功能占位实现

### 72ec7e4 - refactor: 优化代码结构，遵循DDD和面向对象原则
- 创建领域异常类（DomainException及其子类）
- 创建值对象（Value Objects）：DocumentStatus、FileUploadConfig、ChunkConfig、DocumentQuery
- 增强领域模型：Document和Folder添加业务方法
- 提取领域服务：DocumentDomainService处理跨实体业务逻辑
- 重构应用服务层：DocumentService和FolderService使用领域异常和值对象
- 统一错误处理：使用领域异常替代HTTPException
- 改进代码可维护性：业务逻辑封装在领域模型中

### 9c57625 - feat: add placeholder interfaces for system management module and update docs
- 添加系统管理模块占位接口
- 更新文档

### cc96a55 - feat: implement placeholder interfaces (register, reset password, MFA, probe, quota, rate limit)
- 实现占位接口
- 注册、重置密码、MFA、探针、配额、限流等功能占位

## 2025-12-13

### b13be9e - 集成langfuse
- 集成 Langfuse 用于对话日志记录

### 67cfec1 - 完成配置管理模块、审计中间件功能开发
- 完成配置管理模块开发
- 完成审计中间件功能

## 2025-12-12

### df07ee7 - feat: 实现权限校验中间件
- 新增权限校验核心模块 `app/core/permissions.py`
- 实现 PermissionChecker 类，支持权限检查和缓存管理
- 实现依赖注入方式 `require_permission`，支持单个/多个权限码和AND/OR逻辑
- 实现装饰器方式 `require_permission_decorator`，支持同步和异步函数
- 使用内存缓存优化权限查询性能
- 在API接口中应用权限校验
  - users.py: 为所有用户管理接口添加权限校验
  - tenants.py: 为所有租户管理接口添加权限校验和认证
  - roles.py: 为所有角色管理接口添加权限校验
- 权限校验特性
  - 支持单个权限码或权限码列表
  - 支持AND逻辑（logic='all'）和OR逻辑（logic='any'）
  - 权限缓存机制，减少数据库查询
  - 无权限时返回403 Forbidden错误

### ba0bb80 - feat: 完成系统管理基础功能开发
- 实现多租户架构和RBAC权限模型
- 完成用户认证和授权功能
  - 统一登录接口，通过手机号自动识别租户
  - JWT Token认证
  - 基于角色的权限控制
- 完成租户管理功能
  - 租户CRUD操作
  - 租户状态管理
  - 自动创建租户管理员角色
- 完成用户管理功能
  - 用户CRUD操作
  - 用户状态管理
  - 租户数据隔离
- 完成角色管理功能
  - 角色CRUD操作
  - 系统级角色和租户级角色
  - 角色权限分配
  - 角色用户分配
- 完成权限管理功能
  - 权限CRUD操作
  - 权限自动初始化
  - 权限类型（菜单/接口/按钮）
- 完成系统初始化功能
  - 系统管理员初始化
  - 默认权限和角色初始化
- 优化代码结构
  - 移除废弃字段（is_tenant_admin手动设置）
  - 通过角色自动管理用户类型
  - 优化面向对象设计
- 完善文档
  - 功能文档
  - 用户文档
  - 接口文档

---

## 提交统计

- **总计提交数**: 16
- **主要功能模块**:
  - 系统管理基础功能
  - 权限校验中间件
  - 配置管理模块
  - 文档管理模块
  - 问答模块（QA Module）
  - LangChain 集成
  - 引用来源显示优化

## 提交规范

提交消息遵循以下格式：
- `feat:` - 新功能
- `fix:` - 修复bug
- `refactor:` - 重构代码
- `docs:` - 文档更新
- `chore:` - 构建/工具相关

部分提交使用中文描述，部分使用英文描述（遵循 Conventional Commits 规范）。

