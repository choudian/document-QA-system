# 数据库配置指南

本文档说明如何配置不同的数据库。

## 支持的数据库

- PostgreSQL（推荐）
- MySQL
- SQLite（开发测试用）
- Oracle

## 数据库驱动安装

根据选择的数据库，需要安装对应的驱动：

### PostgreSQL

```bash
pip install psycopg2-binary
```

### MySQL

**选项1：PyMySQL（纯Python实现，推荐）**
```bash
pip install pymysql
```

**选项2：mysqlclient（需要系统依赖）**
```bash
# Ubuntu/Debian
sudo apt-get install default-libmysqlclient-dev
pip install mysqlclient

# macOS
brew install mysql
pip install mysqlclient

# Windows
# 下载预编译的wheel文件或使用PyMySQL
```

### SQLite

SQLite 是 Python 内置的，无需安装额外驱动。

### Oracle

**选项1：cx_Oracle（传统方式）**
```bash
pip install cx_Oracle
```

**选项2：oracledb（Oracle官方推荐，Python 3.6+）**
```bash
pip install oracledb
```

## 数据库连接字符串格式

### PostgreSQL

```
postgresql://用户名:密码@主机:端口/数据库名
postgresql+psycopg2://用户名:密码@主机:端口/数据库名
```

示例：
```
postgresql://postgres:mypassword@localhost:5432/document_qa
```

### MySQL

```
mysql+pymysql://用户名:密码@主机:端口/数据库名
mysql://用户名:密码@主机:端口/数据库名
```

示例：
```
mysql+pymysql://root:mypassword@localhost:3306/document_qa
```

### SQLite

```
sqlite:///相对路径/文件名.db
sqlite:////绝对路径/文件名.db
```

示例：
```
sqlite:///./document_qa.db
sqlite:////home/user/document_qa.db
```

### Oracle

```
oracle+cx_oracle://用户名:密码@主机:端口/服务名
oracle://用户名:密码@主机:端口/服务名
```

示例：
```
oracle+cx_oracle://scott:tiger@localhost:1521/xe
```

## 配置步骤

1. 复制 `.env.example` 为 `.env`
2. 在 `.env` 文件中取消注释对应的数据库配置
3. 修改连接字符串中的用户名、密码、主机、端口、数据库名
4. 安装对应的数据库驱动（见上方）
5. 运行数据库迁移：`alembic upgrade head`

## 注意事项

1. **SQLite**：仅适用于开发测试，生产环境不推荐使用
2. **MySQL**：确保数据库字符集为 `utf8mb4`，排序规则为 `utf8mb4_unicode_ci`
3. **Oracle**：需要安装 Oracle Instant Client（cx_Oracle）或使用 oracledb
4. **PostgreSQL**：推荐使用，功能完整，性能优秀
5. 生产环境请使用强密码，并限制数据库访问IP

## 数据库初始化

配置完成后，运行以下命令初始化数据库：

```bash
# 创建迁移文件
alembic revision --autogenerate -m "init"

# 执行迁移
alembic upgrade head
```

## 常见问题

### MySQL 字符集问题

如果使用 MySQL，建议在创建数据库时指定字符集：

```sql
CREATE DATABASE document_qa CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Oracle 连接问题

如果使用 Oracle，确保：
1. Oracle 服务正在运行
2. 监听器配置正确
3. 防火墙允许连接
4. 用户有足够的权限

### SQLite 文件权限问题

如果使用 SQLite，确保应用有读写权限：

```bash
chmod 666 document_qa.db
```

