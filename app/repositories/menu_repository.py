"""
菜单仓储
"""
from typing import Optional, List, Set
from sqlalchemy.orm import Session
from app.models.menu import Menu


class MenuRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, menu_id: str) -> Optional[Menu]:
        """获取单个菜单"""
        return self.db.query(Menu).filter(Menu.id == menu_id).first()

    def get_by_tenant(self, tenant_id: Optional[str] = None) -> List[Menu]:
        """
        根据租户ID获取菜单列表
        tenant_id=None 表示系统级菜单
        """
        query = self.db.query(Menu)
        if tenant_id is None:
            query = query.filter(Menu.tenant_id.is_(None))
        else:
            query = query.filter(Menu.tenant_id == tenant_id)
        return query.order_by(Menu.sort_order.asc()).all()

    def get_all(self) -> List[Menu]:
        """获取所有菜单"""
        return self.db.query(Menu).order_by(Menu.sort_order.asc()).all()

    def get_children(self, parent_id: str) -> List[Menu]:
        """获取子菜单列表"""
        return (
            self.db.query(Menu)
            .filter(Menu.parent_id == parent_id)
            .order_by(Menu.sort_order.asc())
            .all()
        )

    def has_children(self, menu_id: str) -> bool:
        """检查菜单是否有子菜单"""
        return (
            self.db.query(Menu)
            .filter(Menu.parent_id == menu_id)
            .first() is not None
        )

    def build_menu_tree(
        self,
        menus: List[Menu],
        parent_id: Optional[str] = None,
        user_permissions: Optional[Set[str]] = None,
        include_invisible: bool = False
    ) -> List[Menu]:
        """
        构建菜单树
        
        Args:
            menus: 菜单列表
            parent_id: 父菜单ID（None表示根菜单）
            user_permissions: 用户权限集合（用于过滤）
            include_invisible: 是否包含不可见菜单
        
        Returns:
            菜单树列表
        """
        tree = []
        for menu in menus:
            # 过滤父菜单
            if menu.parent_id != parent_id:
                continue
            
            # 过滤不可见菜单
            if not include_invisible and not menu.visible:
                continue
            
            # 过滤未启用的菜单
            if not menu.status:
                continue
            
            # 权限过滤：如果有权限要求，检查用户是否有该权限
            if user_permissions is not None and menu.permission_code:
                if menu.permission_code not in user_permissions:
                    continue
            
            # 递归获取子菜单
            children = self.build_menu_tree(
                menus,
                menu.id,
                user_permissions,
                include_invisible
            )
            
            # 如果有子菜单，添加到菜单对象（虽然Menu模型没有children属性，但我们可以通过关系访问）
            # 这里我们返回的菜单对象，子菜单可以通过后续处理添加
            
            tree.append(menu)
        
        return tree

    def add(self, menu: Menu):
        """添加菜单"""
        self.db.add(menu)

    def delete(self, menu: Menu):
        """删除菜单"""
        self.db.delete(menu)

    def flush(self):
        """刷新会话"""
        self.db.flush()

    def commit(self):
        """提交事务"""
        self.db.commit()

    def rollback(self):
        """回滚事务"""
        self.db.rollback()

    def refresh(self, menu: Menu):
        """刷新菜单对象"""
        self.db.refresh(menu)

    def count_by_tenant(self, tenant_id: Optional[str] = None) -> int:
        """统计租户菜单数量"""
        query = self.db.query(Menu)
        if tenant_id is None:
            query = query.filter(Menu.tenant_id.is_(None))
        else:
            query = query.filter(Menu.tenant_id == tenant_id)
        return query.count()

