"""
检查并添加缺失的菜单
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal
from app.models.menu import Menu
from app.repositories.menu_repository import MenuRepository
from app.repositories.permission_repository import PermissionRepository
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_and_add_menus():
    """检查并添加缺失的菜单"""
    db = SessionLocal()
    try:
        menu_repo = MenuRepository(db)
        permission_repo = PermissionRepository(db)
        
        # 需要添加的菜单
        required_menus = [
            {"name": "文档管理", "path": "/documents", "icon": "FileTextOutlined", "permission_code": "doc:file:read", "sort_order": 6},
            {"name": "问答", "path": "/qa", "icon": "MessageOutlined", "permission_code": "qa:conversation:menu", "sort_order": 7},
        ]
        
        logger.info("开始检查菜单...")
        
        for menu_data in required_menus:
            # 检查菜单是否已存在
            existing_menu = (
                db.query(Menu)
                .filter(
                    Menu.name == menu_data["name"],
                    Menu.tenant_id.is_(None)
                )
                .first()
            )
            
            if existing_menu:
                logger.info(f"菜单 '{menu_data['name']}' 已存在，跳过")
                continue
            
            # 检查权限是否存在
            if menu_data["permission_code"]:
                permission = permission_repo.get_by_code(menu_data["permission_code"])
                if not permission:
                    logger.warning(f"权限码 '{menu_data['permission_code']}' 不存在，跳过菜单 '{menu_data['name']}'")
                    continue
            
            # 创建菜单
            menu = Menu(
                parent_id=None,
                name=menu_data["name"],
                path=menu_data["path"],
                icon=menu_data["icon"],
                permission_code=menu_data["permission_code"],
                sort_order=menu_data["sort_order"],
                visible=True,
                tenant_id=None,
                status=True,
            )
            menu_repo.add(menu)
            logger.info(f"成功添加菜单: {menu_data['name']}")
        
        db.commit()
        logger.info("菜单检查完成")
        
        # 列出所有系统级菜单
        all_menus = menu_repo.get_by_tenant(None)
        logger.info(f"\n当前系统级菜单列表（共 {len(all_menus)} 个）:")
        for menu in all_menus:
            logger.info(f"  - {menu.name} ({menu.path}) - 权限: {menu.permission_code}")
        
    except Exception as e:
        logger.error(f"检查菜单失败: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    check_and_add_menus()
