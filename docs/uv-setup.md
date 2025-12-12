# UV 包管理器使用指南

本项目使用 [uv](https://github.com/astral-sh/uv) 作为 Python 包管理器，uv 是一个极快的 Python 包安装器和解析器。

## 安装 uv

### macOS/Linux

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Windows

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 使用 pip 安装

```bash
pip install uv
```

## 基本使用

### 安装项目依赖

```bash
# 同步所有依赖（推荐）
uv sync

# 或安装到当前环境
uv pip install -e .
```

### 安装可选依赖

```bash
# 安装 MySQL 支持
uv pip install -e ".[mysql]"

# 安装 Oracle 支持
uv pip install -e ".[oracle]"

# 同时安装多个可选依赖
uv pip install -e ".[mysql,oracle]"
```

### 添加新依赖

```bash
# 添加依赖到项目
uv add package-name

# 添加开发依赖
uv add --dev package-name

# 添加可选依赖组
uv add --optional mysql pymysql
```

### 移除依赖

```bash
uv remove package-name
```

### 更新依赖

```bash
# 更新所有依赖
uv sync --upgrade

# 更新特定包
uv pip install --upgrade package-name
```

### 查看依赖

```bash
# 查看已安装的包
uv pip list

# 查看项目依赖树
uv tree
```

## 虚拟环境管理

uv 会自动管理虚拟环境，无需手动创建。

```bash
# 激活虚拟环境（uv 会自动创建）
source .venv/bin/activate  # Linux/macOS
# 或
.venv\Scripts\activate  # Windows

# 在虚拟环境中运行命令
uv run python app/main.py
uv run uvicorn app.main:app --reload
```

## 项目结构

使用 uv 后，项目结构如下：

```
document-QA-system/
├── pyproject.toml      # 项目配置和依赖定义
├── uv.lock            # 锁定的依赖版本（自动生成）
├── .venv/             # 虚拟环境（自动创建）
└── ...
```

## 迁移说明

### 从 requirements.txt 迁移

项目已配置 `pyproject.toml`，可以直接使用 uv：

```bash
# 使用 uv 安装依赖
uv sync

# 或继续使用 pip
pip install -r requirements.txt
```

### 可选依赖组

项目定义了以下可选依赖组：

- `mysql`: MySQL 数据库驱动
- `oracle`: Oracle 数据库驱动

安装方式：
```bash
uv pip install -e ".[mysql]"
uv pip install -e ".[oracle]"
```

## 优势

1. **极快的速度**：比 pip 快 10-100 倍
2. **自动管理虚拟环境**：无需手动创建
3. **依赖解析**：更智能的依赖冲突解决
4. **跨平台**：支持 Windows、macOS、Linux
5. **兼容 pip**：完全兼容 pip 和 requirements.txt

## 常见问题

### Q: uv 和 pip 可以混用吗？

A: 可以，但建议统一使用 uv 以获得最佳体验。

### Q: 如何生成 requirements.txt？

A: 如果需要，可以使用：
```bash
uv pip freeze > requirements.txt
```

### Q: uv.lock 文件需要提交吗？

A: 建议提交，这样可以确保团队使用相同的依赖版本。

## 更多信息

- [uv 官方文档](https://github.com/astral-sh/uv)
- [uv 快速开始](https://github.com/astral-sh/uv#getting-started)

