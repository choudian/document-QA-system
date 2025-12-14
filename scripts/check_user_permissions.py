"""
检查用户权限和菜单
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal
from app.models.user import User
from app.models.role import Role
from app.models.menu import Menu
from app.repositories.menu_repository import MenuRepository
from app.repositories.permission_repository import PermissionRepository
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_user_permissions():
    """检查用户权限和菜单"""
    db = SessionLocal()
    try:
        menu_repo = MenuRepository(db)
        permission_repo = PermissionRepository(db)
        
        # 查找"成员"角色模板
        member_role = db.query(Role).filter(
            Role.name == "成员",
            Role.tenant_id.is_(None)
        ).first()
        
        if not member_role:
            logger.warning("未找到'成员'角色模板")
            return
        
        logger.info(f"找到'成员'角色: {member_role.id}")
        
        # 获取成员角色的权限
        member_permissions = member_role.permissions
        permission_codes = {p.code for p in member_permissions}
        
        logger.info(f"\n成员角色拥有的权限（共 {len(permission_codes)} 个）:")
        for code in sorted(permission_codes):
            logger.info(f"  - {code}")
        
        # 检查问答相关权限
        qa_permissions = [p for p in permission_codes if p.startswith("qa:")]
        logger.info(f"\n问答相关权限（共 {len(qa_permissions)} 个）:")
        for code in qa_permissions:
            logger.info(f"  - {code}")
        
        # 检查文档相关权限
        doc_permissions = [p for p in permission_codes if p.startswith("doc:")]
        logger.info(f"\n文档相关权限（共 {len(doc_permissions)} 个）:")
        for code in doc_permissions:
            logger.info(f"  - {code}")
        
        # 获取所有系统级菜单
        all_menus = menu_repo.get_by_tenant(None)
        logger.info(f"\n系统级菜单列表（共 {len(all_menus)} 个）:")
        
        for menu in all_menus:
            has_permission = menu.permission_code in permission_codes if menu.permission_code else True
            status = "✓" if has_permission else "✗"
            logger.info(f"  {status} {menu.name} ({menu.path}) - 权限: {menu.permission_code}")
        
        # 检查普通用户（非系统管理员）
        normal_users = db.query(User).filter(
            User.is_system_admin == False
        ).limit(5).all()
        
        if normal_users:
            logger.info(f"\n检查普通用户权限（示例，共 {len(normal_users)} 个）:")
            for user in normal_users:
                user_roles = user.roles
                user_permissions = set()
                for role in user_roles:
                    for perm in role.permissions:
                        user_permissions.add(perm.code)
                
                # 检查用户能看到哪些菜单
                visible_menus = []
                for menu in all_menus:
                    if not menu.permission_code or menu.permission_code in user_permissions:
                        visible_menus.append(menu.name)
                
                logger.info(f"  用户: {user.username} (ID: {user.id})")
                logger.info(f"    角色: {[r.name for r in user_roles]}")
                logger.info(f"    可见菜单: {visible_menus}")
        
    except Exception as e:
        logger.error(f"检查失败: {e}", exc_info=True)
    finally:
        db.close()


if __name__ == "__main__":
    check_user_permissions()
