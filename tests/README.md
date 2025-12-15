# 测试文档

## 测试框架

- **后端**: pytest + pytest-asyncio + pytest-cov
- **前端**: Vitest (待添加)

## 运行测试

### 后端测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_auth.py

# 运行特定测试函数
pytest tests/test_auth.py::test_login_success

# 运行并显示覆盖率
pytest --cov=app --cov-report=html

# 运行单元测试（排除集成测试）
pytest -m unit

# 运行集成测试
pytest -m integration
```

### 前端测试

```bash
cd frontend

# 运行所有测试
npm test

# 运行测试并显示覆盖率
npm run test:coverage

# 监听模式
npm run test:watch
```

## 测试结构

```
tests/
├── __init__.py
├── conftest.py          # pytest配置和fixtures
├── test_main.py         # 主应用测试
├── test_auth.py         # 认证测试
├── test_tenants.py      # 租户管理测试
├── test_users.py        # 用户管理测试
├── test_services.py     # 服务层测试
└── test_repositories.py # Repository层测试
```

## 测试标记

- `@pytest.mark.unit` - 单元测试
- `@pytest.mark.integration` - 集成测试
- `@pytest.mark.slow` - 慢速测试

## 测试覆盖率目标

- 总体覆盖率: >= 80%
- 核心业务逻辑: >= 90%
- API端点: >= 85%

## 编写测试指南

1. **命名规范**: 测试文件以 `test_` 开头，测试函数以 `test_` 开头
2. **使用fixtures**: 复用测试数据和设置
3. **隔离测试**: 每个测试应该独立，不依赖其他测试
4. **清理资源**: 使用fixtures的teardown清理测试数据
5. **断言清晰**: 使用明确的断言消息

## 持续集成

测试会在CI/CD流程中自动运行，确保代码质量。
