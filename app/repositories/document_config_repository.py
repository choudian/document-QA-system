"""
文档配置Repository
"""
from typing import Optional
from sqlalchemy.orm import Session
from app.models.document_config import DocumentConfig
from app.models.user_recent_config import UserRecentConfig


class DocumentConfigRepository:
    """文档配置数据访问层"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, config: DocumentConfig) -> DocumentConfig:
        """创建文档配置"""
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        return config
    
    def get_by_document_id(self, document_id: str) -> Optional[DocumentConfig]:
        """根据文档ID查询配置"""
        return self.db.query(DocumentConfig).filter(
            DocumentConfig.document_id == document_id
        ).first()
    
    def update(self, config: DocumentConfig) -> DocumentConfig:
        """更新文档配置"""
        self.db.commit()
        self.db.refresh(config)
        return config
    
    def delete(self, document_id: str) -> bool:
        """删除文档配置"""
        config = self.get_by_document_id(document_id)
        if config:
            self.db.delete(config)
            self.db.commit()
            return True
        return False
    
    def get_user_recent_config(self, user_id: str) -> Optional[UserRecentConfig]:
        """获取用户最近配置"""
        return self.db.query(UserRecentConfig).filter(
            UserRecentConfig.user_id == user_id
        ).first()
    
    def create_or_update_user_recent_config(self, user_id: str, **config_data) -> UserRecentConfig:
        """创建或更新用户最近配置"""
        recent_config = self.get_user_recent_config(user_id)
        
        if recent_config:
            # 更新
            for key, value in config_data.items():
                if hasattr(recent_config, key):
                    setattr(recent_config, key, value)
            self.db.commit()
            self.db.refresh(recent_config)
        else:
            # 创建
            recent_config = UserRecentConfig(
                user_id=user_id,
                **config_data
            )
            self.db.add(recent_config)
            self.db.commit()
            self.db.refresh(recent_config)
        
        return recent_config

