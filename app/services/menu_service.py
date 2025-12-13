"""
菜单领域服务
"""
from typing import Optional, List, Set
from fastapi import HTTPException, status
from app.models.menu import Menu
from app.schemas.menu import MenuCreate, MenuUpdate, MenuSortRequest
from app.repositories.menu_repository import MenuRepository
from app.repositories.permission_repository import PermissionRepository
from app.core.permissions import PermissionChecker


class MenuService:
    def __init__(
        self,
        menu_repo: MenuRepository,
        permission_repo: PermissionRepository,
    ):
        self.menu_repo = menu_repo
        self.permission_repo = permission_repo

    def create_menu(self, menu: MenuCreate, created_by: Optional[str] = None) -> Menu:
        """创建菜单"""
        # 如果指定了父菜单，检查父菜单是否存在
        if menu.parent_id:
            parent = self.menu_repo.get(menu.parent_id)
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"父菜单 ID '{menu.parent_id}' 不存在",
                )
            # 子菜单的租户ID应该与父菜单一致
            if menu.tenant_id != parent.tenant_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="子菜单的租户ID必须与父菜单一致",
                )

        # 如果指定了权限码，检查权限是否存在且类型为menu
        if menu.permission_code:
            permission = self.permission_repo.get_by_code(menu.permission_code)
            if not permission:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"权限码 '{menu.permission_code}' 不存在",
                )
            if permission.type != "menu":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"权限码 '{menu.permission_code}' 的类型不是 'menu'",
                )

        db_menu = Menu(
            parent_id=menu.parent_id,
            name=menu.name,
            path=menu.path,
            icon=menu.icon,
            permission_code=menu.permission_code,
            sort_order=menu.sort_order,
            visible=menu.visible,
            tenant_id=menu.tenant_id,
            status=True,
            created_by=created_by,
        )

        try:
            self.menu_repo.add(db_menu)
            self.menu_repo.commit()
            self.menu_repo.refresh(db_menu)
            return db_menu
        except Exception as e:
            self.menu_repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"创建菜单失败: {str(e)}",
            )

    def list_menus(
        self,
        tenant_id: Optional[str] = None,
        include_invisible: bool = False,
    ) -> List[Menu]:
        """查询菜单列表"""
        return self.menu_repo.get_by_tenant(tenant_id)

    def get_menu_tree(
        self,
        tenant_id: Optional[str] = None,
        user_permissions: Optional[Set[str]] = None,
        include_invisible: bool = False,
    ) -> List[Menu]:
        """
        获取菜单树
        
        Args:
            tenant_id: 租户ID（None表示系统级菜单）
            user_permissions: 用户权限集合（用于过滤）
            include_invisible: 是否包含不可见菜单
        
        Returns:
            菜单树列表
        """
        # 获取所有菜单（系统级 + 租户级）
        all_menus = []
        if tenant_id is None:
            # 只获取系统级菜单
            all_menus = self.menu_repo.get_by_tenant(None)
        else:
            # 获取系统级菜单 + 租户级菜单
            system_menus = self.menu_repo.get_by_tenant(None)
            tenant_menus = self.menu_repo.get_by_tenant(tenant_id)
            all_menus = system_menus + tenant_menus

        # 构建菜单树
        return self.menu_repo.build_menu_tree(
            all_menus,
            parent_id=None,
            user_permissions=user_permissions,
            include_invisible=include_invisible,
        )

    def get_user_menus(
        self,
        user_id: str,
        tenant_id: Optional[str] = None,
    ) -> List[Menu]:
        """
        获取当前用户的可见菜单树
        
        Args:
            user_id: 用户ID
            tenant_id: 租户ID
        
        Returns:
            用户可见的菜单树
        """
        # 获取用户权限
        user_permissions = PermissionChecker.get_user_permissions(
            user_id,
            self.menu_repo.db
        )

        # 获取菜单树（根据权限过滤）
        return self.get_menu_tree(
            tenant_id=tenant_id,
            user_permissions=user_permissions,
            include_invisible=False,
        )

    def get_menu(self, menu_id: str) -> Menu:
        """获取菜单详情"""
        menu = self.menu_repo.get(menu_id)
        if not menu:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"菜单 ID '{menu_id}' 不存在",
            )
        return menu

    def update_menu(self, menu_id: str, payload: MenuUpdate) -> Menu:
        """更新菜单"""
        menu = self.get_menu(menu_id)

        # 如果更新父菜单，检查父菜单是否存在
        if payload.parent_id is not None:
            if payload.parent_id == menu_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="菜单不能将自己设为父菜单",
                )
            parent = self.menu_repo.get(payload.parent_id)
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"父菜单 ID '{payload.parent_id}' 不存在",
                )
            # 检查是否会形成循环引用
            if self._would_create_cycle(menu_id, payload.parent_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="不能将菜单移动到其子菜单下，这会导致循环引用",
                )
            menu.parent_id = payload.parent_id

        # 如果更新权限码，检查权限是否存在且类型为menu
        if payload.permission_code is not None:
            permission = self.permission_repo.get_by_code(payload.permission_code)
            if not permission:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"权限码 '{payload.permission_code}' 不存在",
                )
            if permission.type != "menu":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"权限码 '{payload.permission_code}' 的类型不是 'menu'",
                )
            menu.permission_code = payload.permission_code

        # 更新其他字段
        if payload.name is not None:
            menu.name = payload.name
        if payload.path is not None:
            menu.path = payload.path
        if payload.icon is not None:
            menu.icon = payload.icon
        if payload.sort_order is not None:
            menu.sort_order = payload.sort_order
        if payload.visible is not None:
            menu.visible = payload.visible
        if payload.status is not None:
            menu.status = payload.status

        try:
            self.menu_repo.commit()
            self.menu_repo.refresh(menu)
            return menu
        except Exception as e:
            self.menu_repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"更新菜单失败: {str(e)}",
            )

    def delete_menu(self, menu_id: str):
        """删除菜单"""
        menu = self.get_menu(menu_id)

        # 检查是否有子菜单
        if self.menu_repo.has_children(menu_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该菜单下有子菜单，请先删除子菜单",
            )

        try:
            self.menu_repo.delete(menu)
            self.menu_repo.commit()
        except Exception as e:
            self.menu_repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"删除菜单失败: {str(e)}",
            )

    def update_status(self, menu_id: str, status: bool) -> Menu:
        """启用/停用菜单"""
        menu = self.get_menu(menu_id)
        menu.status = status
        try:
            self.menu_repo.commit()
            self.menu_repo.refresh(menu)
            return menu
        except Exception as e:
            self.menu_repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"更新菜单状态失败: {str(e)}",
            )

    def update_sort_order(self, menu_orders: List[dict]):
        """
        批量更新菜单排序
        
        Args:
            menu_orders: 菜单排序列表，格式：[{'id': 'menu_id', 'sort_order': 0}]
        """
        try:
            for order in menu_orders:
                menu_id = order.get('id')
                sort_order = order.get('sort_order')
                if menu_id and sort_order is not None:
                    menu = self.menu_repo.get(menu_id)
                    if menu:
                        menu.sort_order = sort_order
            self.menu_repo.commit()
        except Exception as e:
            self.menu_repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"更新菜单排序失败: {str(e)}",
            )

    def _would_create_cycle(self, menu_id: str, new_parent_id: str) -> bool:
        """
        检查将菜单移动到新父菜单下是否会形成循环引用
        
        Args:
            menu_id: 要移动的菜单ID
            new_parent_id: 新的父菜单ID
        
        Returns:
            是否会形成循环引用
        """
        # 从新父菜单开始向上查找，如果找到要移动的菜单，则形成循环
        current_id = new_parent_id
        visited = set()
        while current_id:
            if current_id == menu_id:
                return True
            if current_id in visited:
                break
            visited.add(current_id)
            parent = self.menu_repo.get(current_id)
            if not parent or not parent.parent_id:
                break
            current_id = parent.parent_id
        return False

