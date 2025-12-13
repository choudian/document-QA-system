"""
数据库连接和会话管理
"""
from sqlalchemy import create_engine, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=True  # 开发环境打印SQL
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    初始化数据库表结构
    使用 Alembic 迁移确保所有表都是最新版本
    """
    from app.models.tenant import Tenant
    from app.models.user import User
    from app.models.audit_log import AuditLog
    
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    # 检查核心表是否存在
    required_tables = ["tenants", "users"]
    missing_tables = [table for table in required_tables if table not in existing_tables]
    
    # 如果核心表缺失，或者audit_logs表不存在，运行迁移
    if missing_tables or "audit_logs" not in existing_tables:
        logger.info(f"检测到缺失的表，开始运行数据库迁移...")
        try:
            # 使用 Alembic 运行迁移到最新版本
            from alembic import command
            from alembic.config import Config
            
            alembic_cfg = Config("alembic.ini")
            # 确保使用正确的数据库 URL
            alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
            
            # 运行迁移到最新版本
            command.upgrade(alembic_cfg, "head")
            logger.info("数据库迁移完成")
        except Exception as e:
            logger.error(f"数据库迁移失败: {e}", exc_info=True)
            # 如果 Alembic 迁移失败，回退到直接创建表
            logger.warning("回退到直接创建表...")
            Base.metadata.create_all(bind=engine)
            logger.info("数据库表创建完成（使用 create_all）")
    else:
        logger.info("数据库表已存在，跳过初始化")
    
    # 初始化默认数据（权限、角色等）
    try:
        from app.core.init_data import init_default_data
        db_session = SessionLocal()
        try:
            init_default_data(db_session)
        finally:
            db_session.close()
    except Exception as e:
        logger.error(f"初始化默认数据失败: {e}", exc_info=True)

