"""
系统初始化数据
"""
import logging
from sqlalchemy.orm import Session
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User
from app.models.menu import Menu
from app.models.config import SystemConfig
from app.repositories.permission_repository import PermissionRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.repositories.config_repository import ConfigRepository
from app.repositories.menu_repository import MenuRepository
import base64

logger = logging.getLogger(__name__)


def init_permissions(db: Session):
    """初始化默认权限"""
    # 检查表是否存在
    from sqlalchemy import inspect
    inspector = inspect(db.bind)
    if "permissions" not in inspector.get_table_names():
        logger.info("权限表不存在，跳过权限初始化")
        return
    
    permission_repo = PermissionRepository(db)
    
    # 检查是否已有权限数据
    try:
        existing_count = permission_repo.count()
        if existing_count > 0:
            logger.info(f"权限表已有 {existing_count} 条数据，跳过权限初始化")
            return
    except Exception as e:
        logger.warning(f"检查权限表数据失败: {e}，尝试初始化")
    
    logger.info("开始初始化默认权限...")
    
    # 系统级权限（系统管理员使用）
    system_permissions = [
        # 租户管理
        {"code": "system:tenant:create", "name": "创建租户", "description": "创建新租户", "type": "menu", "module": "system", "tenant_id": None},
        {"code": "system:tenant:read", "name": "查看租户", "description": "查看租户列表和详情", "type": "menu", "module": "system", "tenant_id": None},
        {"code": "system:tenant:update", "name": "更新租户", "description": "更新租户信息", "type": "api", "module": "system", "tenant_id": None},
        {"code": "system:tenant:delete", "name": "删除租户", "description": "删除租户", "type": "api", "module": "system", "tenant_id": None},
        {"code": "system:tenant:create_admin", "name": "创建租户管理员", "description": "创建租户管理员按钮权限", "type": "button", "module": "system", "tenant_id": None},
    ]
    
    # 租户级权限（租户管理员和普通用户使用）
    tenant_permissions = [
        # 用户管理
        {"code": "system:user:create", "name": "创建用户", "description": "创建新用户", "type": "button", "module": "system", "tenant_id": None},
        {"code": "system:user:read", "name": "查看用户", "description": "查看用户列表和详情", "type": "menu", "module": "system", "tenant_id": None},
        {"code": "system:user:update", "name": "更新用户", "description": "更新用户信息", "type": "api", "module": "system", "tenant_id": None},
        {"code": "system:user:delete", "name": "删除用户", "description": "删除用户", "type": "api", "module": "system", "tenant_id": None},
        {"code": "system:user:assign_role", "name": "为用户分配角色", "description": "为用户分配角色", "type": "api", "module": "system", "tenant_id": None},
        
        # 角色管理
        {"code": "system:role:create", "name": "创建角色", "description": "创建新角色", "type": "button", "module": "system", "tenant_id": None},
        {"code": "system:role:read", "name": "查看角色", "description": "查看角色列表和详情", "type": "menu", "module": "system", "tenant_id": None},
        {"code": "system:role:update", "name": "更新角色", "description": "更新角色信息", "type": "api", "module": "system", "tenant_id": None},
        {"code": "system:role:delete", "name": "删除角色", "description": "删除角色", "type": "api", "module": "system", "tenant_id": None},
        {"code": "system:role:assign_permission", "name": "为角色分配权限", "description": "为角色分配权限", "type": "api", "module": "system", "tenant_id": None},
        {"code": "system:role:assign_user", "name": "为角色分配用户", "description": "为角色分配用户", "type": "api", "module": "system", "tenant_id": None},
        
        # 权限管理
        {"code": "system:permission:create", "name": "创建权限", "description": "创建新权限", "type": "button", "module": "system", "tenant_id": None},
        {"code": "system:permission:read", "name": "查看权限", "description": "查看权限列表和详情", "type": "menu", "module": "system", "tenant_id": None},
        {"code": "system:permission:update", "name": "更新权限", "description": "更新权限信息", "type": "api", "module": "system", "tenant_id": None},
        {"code": "system:permission:delete", "name": "删除权限", "description": "删除权限", "type": "api", "module": "system", "tenant_id": None},

        # 配置管理
        {"code": "system:config:menu", "name": "配置管理菜单", "description": "查看配置菜单", "type": "menu", "module": "system", "tenant_id": None},
        {"code": "system:config:read", "name": "查看配置", "description": "查看配置项", "type": "api", "module": "system", "tenant_id": None},
        {"code": "system:config:update", "name": "更新配置", "description": "更新配置项", "type": "api", "module": "system", "tenant_id": None},
        
        # 审计日志
        {"code": "system:audit:read", "name": "查看审计日志", "description": "查看审计日志", "type": "menu", "module": "system", "tenant_id": None},
        
        # 系统管理（额度/速率限制等）
        {"code": "system:admin:read", "name": "查看系统管理信息", "description": "查看额度、速率限制等系统管理信息", "type": "api", "module": "system", "tenant_id": None},
        {"code": "system:admin:update", "name": "更新系统管理配置", "description": "更新额度、速率限制等系统管理配置", "type": "api", "module": "system", "tenant_id": None},
    ]
    
    all_permissions = system_permissions + tenant_permissions
    
    for perm_data in all_permissions:
        permission = Permission(
            code=perm_data["code"],
            name=perm_data["name"],
            description=perm_data["description"],
            type=perm_data["type"],
            module=perm_data["module"],
            tenant_id=perm_data["tenant_id"],
            status=True,
        )
        permission_repo.add(permission)
    
    permission_repo.commit()
    logger.info(f"成功初始化 {len(all_permissions)} 个默认权限")


def init_roles(db: Session):
    """初始化默认角色"""
    # 检查表是否存在
    from sqlalchemy import inspect
    inspector = inspect(db.bind)
    if "roles" not in inspector.get_table_names():
        logger.info("角色表不存在，跳过角色初始化")
        return
    
    role_repo = RoleRepository(db)
    permission_repo = PermissionRepository(db)
    
    # 检查是否已存在系统管理员角色
    system_admin_role = role_repo.get_by_name_in_tenant(None, "系统管理员")
    
    if not system_admin_role:
        logger.info("开始创建系统管理员角色...")
        
        # 创建系统管理员角色（系统级角色，tenant_id=None）
        system_admin_role = Role(
            tenant_id=None,  # 系统级角色
            name="系统管理员",
            description="系统管理员角色，可以管理租户、用户、角色",
            status=True,
        )
        role_repo.add(system_admin_role)
        role_repo.flush()  # 获取角色ID
        
        # 系统管理员需要的权限：租户管理、用户管理、角色管理、配置管理的权限
        system_admin_permission_codes = [
            # 租户管理
            "system:tenant:create",
            "system:tenant:read",
            "system:tenant:update",
            "system:tenant:delete",
            "system:tenant:create_admin",
            # 用户管理
            "system:user:create",
            "system:user:read",
            "system:user:update",
            "system:user:delete",
            "system:user:assign_role",
            # 角色管理
            "system:role:create",
            "system:role:read",
            "system:role:update",
            "system:role:delete",
            "system:role:assign_permission",
            "system:role:assign_user",
            # 配置管理
            "system:config:menu",
            "system:config:read",
            "system:config:update",
            # 审计日志
            "system:audit:read",
        ]
        
        # 查询这些权限
        permissions = []
        for code in system_admin_permission_codes:
            permission = permission_repo.get_by_code(code)
            if permission:
                permissions.append(permission)
        
        # 为角色分配权限
        system_admin_role.permissions = permissions
        role_repo.commit()
        logger.info(f"成功创建系统管理员角色，并分配了 {len(permissions)} 个权限")
    else:
        logger.info("系统管理员角色已存在，检查权限分配...")
        # 即使角色已存在，也要确保权限已分配（如果需要更新权限，可以在这里处理）
    
    # 为所有已存在的系统管理员用户分配该角色（无论角色是新创建还是已存在）
    user_repo = UserRepository(db)
    from app.models.user import User
    system_admin_users = db.query(User).filter(User.is_system_admin == True).all()
    if system_admin_users:
        assigned_count = 0
        for user in system_admin_users:
            # 检查用户是否已经有这个角色
            user_has_role = any(role.id == system_admin_role.id for role in user.roles)
            if not user_has_role:
                # 如果用户还没有这个角色，添加角色（保留其他角色）
                if user.roles:
                    user.roles.append(system_admin_role)
                else:
                    user.roles = [system_admin_role]
                # 自动更新 is_tenant_admin 状态
                user.update_tenant_admin_status()
                assigned_count += 1
        if assigned_count > 0:
            user_repo.commit()
            logger.info(f"为 {assigned_count} 个系统管理员用户分配了角色")
        else:
            logger.info("所有系统管理员用户已分配角色")


def init_system_configs(db: Session):
    """初始化系统默认配置"""
    from sqlalchemy import inspect
    inspector = inspect(db.bind)
    if "system_configs" not in inspector.get_table_names():
        logger.info("系统配置表不存在，跳过初始化")
        return

    config_repo = ConfigRepository(db)

    def _enc(val: str) -> str:
        return "ENC:" + base64.b64encode(val.encode("utf-8")).decode("utf-8")

    # 检查是否已有配置
    existing = config_repo.list_system_configs(None)
    if existing and len(existing) > 0:
        logger.info("系统配置已存在，跳过初始化")
        return

    default_configs = [
        # LLM（对象）
        {
            "category": "llm",
            "key": "default",
            "value": {
                "provider": "openai",
                "base_url": "https://api.openai.com/v1",
                "api_key": _enc("dummy-api-key"),
                "model": "gpt-4o-mini",
                "timeout": 30,
                "temperature": 0.7,
            },
        },
        # Rerank
        {
            "category": "rerank",
            "key": "default",
            "value": {
                "provider": "openai",
                "base_url": "https://api.openai.com/v1",
                "api_key": _enc("dummy-api-key"),
                "model": "bge-rerank-base",
            },
        },
        # Embedding
        {
            "category": "embedding",
            "key": "default",
            "value": {
                "provider": "openai",
                "base_url": "https://api.openai.com/v1",
                "api_key": _enc("dummy-api-key"),
                "model": "text-embedding-3-small",
            },
        },
        # 向量库
        {
            "category": "vector_store",
            "key": "default",
            "value": {
                "provider": "pgvector",
                "base_url": "http://localhost:5432",
                "api_key": _enc("dummy-api-key"),
                "collection_prefix": "",
            },
        },
        # 文档上传
        {
            "category": "doc",
            "key": "upload",
            "value": {"upload_types": ["txt", "md", "pdf", "word"], "max_file_size_mb": 50},
        },
        # 文本切分
        {
            "category": "doc",
            "key": "chunk",
            "value": {"strategy": "fixed", "size": 400, "overlap": 100},
        },
        # 检索
        {"category": "retrieval", "key": "default", "value": {"top_k": 5, "similarity_threshold": 0.6}},
        # Langfuse
        {
            "category": "langfuse",
            "key": "default",
            "value": {
                "enabled": False,
                "public_key": "",
                "secret_key": "",
                "host": "https://cloud.langfuse.com",
            },
        },
    ]

    try:
        config_repo.upsert_system_configs(None, default_configs, operator_id=None)
        config_repo.commit()
        logger.info(f"初始化系统默认配置 {len(default_configs)} 条")
    except Exception as e:
        config_repo.rollback()
        logger.error(f"初始化系统配置失败: {e}")
        raise


def init_menus(db: Session):
    """初始化默认菜单"""
    from sqlalchemy import inspect
    inspector = inspect(db.bind)
    if "menus" not in inspector.get_table_names():
        logger.info("菜单表不存在，跳过菜单初始化")
        return

    menu_repo = MenuRepository(db)
    permission_repo = PermissionRepository(db)

    # 检查是否已有菜单数据（系统级）
    try:
        existing_count = menu_repo.count_by_tenant(None)
        if existing_count > 0:
            logger.info(f"菜单表已有 {existing_count} 条系统级菜单数据，跳过菜单初始化")
            return
    except Exception as e:
        logger.warning(f"检查菜单表数据失败: {e}，尝试初始化")

    logger.info("开始初始化默认菜单...")

    default_menus = [
        {"name": "租户管理", "path": "/tenants", "icon": "TeamOutlined", "permission_code": "system:tenant:read", "sort_order": 1},
        {"name": "用户管理", "path": "/users", "icon": "UserOutlined", "permission_code": "system:user:read", "sort_order": 2},
        {"name": "权限管理", "path": "/permissions", "icon": "SafetyOutlined", "permission_code": "system:permission:read", "sort_order": 3},
        {"name": "角色管理", "path": "/roles", "icon": "UsergroupAddOutlined", "permission_code": "system:role:read", "sort_order": 4},
        {"name": "配置管理", "path": "/configs", "icon": "SettingOutlined", "permission_code": "system:config:menu", "sort_order": 5},
    ]

    created_count = 0
    for menu_data in default_menus:
        # 权限存在性检查
        if menu_data["permission_code"]:
            permission = permission_repo.get_by_code(menu_data["permission_code"])
            if not permission:
                logger.warning(f"权限码 '{menu_data['permission_code']}' 不存在，跳过菜单 '{menu_data['name']}'")
                continue

        # 防重复
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
        created_count += 1

    menu_repo.commit()
    logger.info(f"成功初始化 {created_count} 个默认菜单")

def init_default_data(db: Session):
    """初始化所有默认数据"""
    try:
        # 1. 初始化权限
        init_permissions(db)
        
        # 2. 初始化角色（创建系统管理员角色）
        init_roles(db)
        
        # 3. 初始化系统默认配置
        init_system_configs(db)

        # 4. 初始化菜单（依赖权限）
        init_menus(db)
        
        logger.info("默认数据初始化完成")
    except Exception as e:
        logger.error(f"初始化默认数据失败: {e}", exc_info=True)
        db.rollback()
        raise

