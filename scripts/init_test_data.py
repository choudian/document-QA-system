"""
测试数据初始化脚本
用于快速创建测试环境，不提交到代码仓库
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User
from app.models.tenant import Tenant
from app.models.role import Role
from app.core.security import PasswordHasher
from app.repositories.user_repository import UserRepository
from app.repositories.tenant_repository import TenantRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.permission_repository import PermissionRepository
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

password_hasher = PasswordHasher()


def init_system_admin(db: Session):
    """初始化系统管理员"""
    logger.info("=" * 60)
    logger.info("1. 初始化系统管理员...")
    
    user_repo = UserRepository(db)
    role_repo = RoleRepository(db)
    
    # 检查是否已存在
    existing_user = db.query(User).filter(User.phone == "18610814240").first()
    if existing_user:
        logger.info(f"系统管理员已存在: {existing_user.username} (ID: {existing_user.id})")
        return existing_user
    
    # 创建系统管理员用户
    system_admin = User(
        tenant_id=None,
        username="超级管理员",
        phone="18610814240",
        password_hash=password_hasher.hash_password("admin@123"),
        status="active",
        is_system_admin=True,
        is_tenant_admin=False,
    )
    user_repo.add(system_admin)
    db.flush()
    
    # 分配系统管理员角色
    system_admin_role = role_repo.get_by_name_in_tenant(None, "系统管理员")
    if system_admin_role:
        system_admin.roles = [system_admin_role]
        system_admin.update_tenant_admin_status()
        db.commit()
        logger.info(f"✓ 系统管理员创建成功: {system_admin.username} (ID: {system_admin.id})")
        logger.info(f"  - 已分配角色: {system_admin_role.name}")
    else:
        logger.warning("系统管理员角色不存在，请先运行 init_roles()")
        db.commit()
    
    return system_admin


def create_tenant(db: Session):
    """创建租户"""
    logger.info("=" * 60)
    logger.info("2. 创建租户...")
    
    tenant_repo = TenantRepository(db)
    
    # 检查是否已存在
    existing_tenant = tenant_repo.get_by_code("GP")
    if existing_tenant:
        logger.info(f"租户已存在: {existing_tenant.name} (ID: {existing_tenant.id})")
        return existing_tenant
    
    # 创建租户
    tenant = Tenant(
        code="GP",
        name="高租",
        description="高租测试租户",
        status=True,
    )
    tenant_repo.add(tenant)
    db.commit()
    db.refresh(tenant)
    
    logger.info(f"✓ 租户创建成功: {tenant.name} (ID: {tenant.id})")
    return tenant


def create_tenant_admin_user(db: Session, tenant_id: str):
    """创建租户管理员用户"""
    logger.info("=" * 60)
    logger.info("3. 创建租户管理员用户...")
    
    user_repo = UserRepository(db)
    role_repo = RoleRepository(db)
    
    # 检查是否已存在
    existing_user = db.query(User).filter(
        User.tenant_id == tenant_id,
        User.username == "高租"
    ).first()
    if existing_user:
        logger.info(f"租户管理员用户已存在: {existing_user.username} (ID: {existing_user.id})")
        return existing_user
    
    # 创建用户
    user = User(
        tenant_id=tenant_id,
        username="高租",
        phone="15966965693",
        password_hash=password_hasher.hash_password("admin@123"),
        status="active",
        is_tenant_admin=False,  # 通过角色分配后自动更新
        is_system_admin=False,
    )
    user_repo.add(user)
    db.flush()
    
    # 分配租户管理员角色
    tenant_admin_role = role_repo.get_by_name_in_tenant(None, "租户管理员")
    if tenant_admin_role:
        user.roles = [tenant_admin_role]
        user.update_tenant_admin_status()
        db.commit()
        db.refresh(user)
        logger.info(f"✓ 租户管理员用户创建成功: {user.username} (ID: {user.id})")
        logger.info(f"  - 已分配角色: {tenant_admin_role.name}")
        logger.info(f"  - is_tenant_admin: {user.is_tenant_admin}")
    else:
        logger.warning("租户管理员角色不存在，请先运行 init_roles()")
        db.commit()
    
    return user


def create_normal_user(db: Session, tenant_id: str):
    """创建普通用户"""
    logger.info("=" * 60)
    logger.info("5. 创建普通用户...")
    
    user_repo = UserRepository(db)
    role_repo = RoleRepository(db)
    
    # 检查是否已存在
    existing_user = db.query(User).filter(
        User.tenant_id == tenant_id,
        User.username == "gaopan"
    ).first()
    if existing_user:
        logger.info(f"普通用户已存在: {existing_user.username} (ID: {existing_user.id})")
        return existing_user
    
    # 创建用户
    user = User(
        tenant_id=tenant_id,
        username="gaopan",
        phone="13792196051",
        password_hash=password_hasher.hash_password("admin@123"),
        status="active",
        is_tenant_admin=False,
        is_system_admin=False,
    )
    user_repo.add(user)
    db.flush()
    
    # 分配成员角色（查找租户下的成员角色，如果没有则使用系统级模板）
    member_role = role_repo.get_by_name_in_tenant(tenant_id, "成员")
    if not member_role:
        # 使用系统级模板
        member_role = role_repo.get_by_name_in_tenant(None, "成员")
    
    if member_role:
        # 如果是系统级模板，需要为租户创建副本
        if member_role.tenant_id is None:
            from app.models.role import Role
            permission_repo = PermissionRepository(db)
            
            # 创建租户级的成员角色
            tenant_member_role = Role(
                tenant_id=tenant_id,
                name="成员",
                description="普通用户角色，可以上传文档、管理自己的文档和文件夹",
                status=True,
            )
            role_repo.add(tenant_member_role)
            db.flush()
            
            # 复制权限
            if member_role.permissions:
                tenant_member_role.permissions = list(member_role.permissions)
                db.flush()
            
            member_role = tenant_member_role
        
        user.roles = [member_role]
        db.commit()
        db.refresh(user)
        logger.info(f"✓ 普通用户创建成功: {user.username} (ID: {user.id})")
        logger.info(f"  - 已分配角色: {member_role.name}")
    else:
        logger.warning("成员角色不存在，请先运行 init_roles()")
        db.commit()
    
    return user


def main():
    """主函数"""
    logger.info("开始初始化测试数据...")
    logger.info("=" * 60)
    
    db: Session = SessionLocal()
    try:
        # 1. 初始化系统管理员
        system_admin = init_system_admin(db)
        
        # 2. 创建租户
        tenant = create_tenant(db)
        
        # 3. 创建租户管理员用户
        tenant_admin_user = create_tenant_admin_user(db, tenant.id)
        
        # 4. 创建普通用户
        normal_user = create_normal_user(db, tenant.id)
        
        logger.info("=" * 60)
        logger.info("测试数据初始化完成！")
        logger.info("=" * 60)
        logger.info("系统管理员:")
        logger.info(f"  - 用户名: {system_admin.username}")
        logger.info(f"  - 手机号: {system_admin.phone}")
        logger.info(f"  - 密码: admin@123")
        logger.info("")
        logger.info("租户管理员:")
        logger.info(f"  - 用户名: {tenant_admin_user.username}")
        logger.info(f"  - 手机号: {tenant_admin_user.phone}")
        logger.info(f"  - 密码: admin@123")
        logger.info(f"  - 租户: {tenant.name} ({tenant.code})")
        logger.info("")
        logger.info("普通用户:")
        logger.info(f"  - 用户名: {normal_user.username}")
        logger.info(f"  - 手机号: {normal_user.phone}")
        logger.info(f"  - 密码: admin@123")
        logger.info(f"  - 租户: {tenant.name} ({tenant.code})")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"初始化失败: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

