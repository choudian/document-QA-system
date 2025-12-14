"""
应用配置
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""
    # 数据库配置
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/document_qa"
    
    # JWT配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 应用配置
    PROJECT_NAME: str = "智能文档问答系统"
    API_V1_PREFIX: str = "/api/v1"
    
    # 存储配置
    STORAGE_TYPE: str = "filesystem"
    STORAGE_BASE_PATH: str = "./storage"
    
    # 向量库配置
    VECTOR_STORE_BASE_PATH: str = "./vector_store"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

