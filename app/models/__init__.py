"""
数据模型
"""
from app.models.tenant import Tenant
from app.models.user import User
from app.models.permission import Permission
from app.models.role import Role
from app.models.config import SystemConfig, UserConfig, ConfigHistory
from app.models.folder import Folder
from app.models.document import Document
from app.models.document_version import DocumentVersion
from app.models.document_tag import DocumentTag
from app.models.document_tag_association import DocumentTagAssociation
from app.models.document_config import DocumentConfig
from app.models.user_recent_config import UserRecentConfig
from app.models.document_chunk import DocumentChunk
from app.models.document_task import DocumentTask

__all__ = [
    "Tenant", "User", "Permission", "Role", "SystemConfig", "UserConfig", "ConfigHistory",
    "Folder", "Document", "DocumentVersion", "DocumentTag", "DocumentTagAssociation",
    "DocumentConfig", "UserRecentConfig", "DocumentChunk", "DocumentTask"
]

