"""
文件夹服务（应用服务层）
"""
from typing import List, Optional
from app.repositories.folder_repository import FolderRepository
from app.models.folder import Folder
from app.core.exceptions import (
    FolderNotFoundException,
    FolderPermissionDeniedException,
    FolderLevelExceededException
)


class FolderService:
    """文件夹应用服务层"""
    
    def __init__(self, folder_repo: FolderRepository):
        self.folder_repo = folder_repo
    
    def create_folder(
        self,
        name: str,
        parent_id: Optional[str],
        tenant_id: str,
        user_id: str
    ) -> Folder:
        """创建文件夹"""
        # 验证父文件夹
        parent = None
        if parent_id:
            parent = self.folder_repo.get_by_id(parent_id, tenant_id)
            if not parent:
                raise FolderNotFoundException(parent_id)
            if not parent.is_owned_by(user_id):
                raise FolderPermissionDeniedException(parent_id)
            if not parent.can_create_subfolder():
                raise FolderLevelExceededException(Folder.MAX_LEVEL)
        
        # 检查名称是否已存在
        if self.folder_repo.check_name_exists(name, parent_id, tenant_id, user_id):
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"文件夹名称 '{name}' 已存在"
            )
        
        # 生成路径和层级
        if parent:
            path = parent.generate_child_path()
            level = parent.calculate_child_level()
        else:
            path = f"{tenant_id}/{user_id}"
            level = 0
        
        # 创建文件夹
        folder = Folder(
            tenant_id=tenant_id,
            user_id=user_id,
            parent_id=parent_id,
            name=name,
            path=path,
            level=level
        )
        
        return self.folder_repo.create(folder)
    
    def list_folders(
        self,
        tenant_id: str,
        user_id: str,
        parent_id: Optional[str] = None
    ) -> List[Folder]:
        """查询文件夹列表"""
        return self.folder_repo.list_by_user(user_id, tenant_id, parent_id)
    
    def get_folder(self, folder_id: str, tenant_id: str, user_id: str) -> Folder:
        """获取文件夹详情"""
        folder = self.folder_repo.get_by_id(folder_id, tenant_id)
        if not folder:
            raise FolderNotFoundException(folder_id)
        
        # 验证权限（只有拥有者可以查看）
        if not folder.is_owned_by(user_id):
            raise FolderPermissionDeniedException(folder_id)
        
        return folder
    
    def update_folder(
        self,
        folder_id: str,
        name: str,
        tenant_id: str,
        user_id: str
    ) -> Folder:
        """重命名文件夹"""
        folder = self.get_folder(folder_id, tenant_id, user_id)
        
        # 检查新名称是否已存在（在同一父文件夹下）
        if name != folder.name and self.folder_repo.check_name_exists(name, folder.parent_id, tenant_id, user_id):
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"文件夹名称 '{name}' 已存在"
            )
        
        folder.rename(name)
        return self.folder_repo.update(folder)
    
    def delete_folder(
        self,
        folder_id: str,
        tenant_id: str,
        user_id: str,
        confirm_text: Optional[str] = None
    ) -> bool:
        """删除文件夹（需二次确认）"""
        folder = self.get_folder(folder_id, tenant_id, user_id)
        
        # 二次确认
        expected_text = f"我确认删除{folder.name}文件夹"
        if confirm_text != expected_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"确认文字不正确，请输入: {expected_text}"
            )
        
        # 检查是否有子文件夹
        children_count = self.folder_repo.get_children_count(folder_id)
        if children_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件夹下存在子文件夹，请先删除子文件夹"
            )
        
        # 检查是否有文档（通过文档repository检查，这里先简化）
        # TODO: 实际应该检查文件夹下的文档数量
        
        return self.folder_repo.delete(folder_id)

