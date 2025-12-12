"""
权限校验核心模块
支持装饰器和依赖注入两种方式，可配置AND/OR逻辑
"""
from typing import Union, List, Set, Optional, Callable
from functools import wraps
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload
from app.core.database import get_db
from app.api.v1.me import get_current_user
from app.models.user import User
from app.models.role import Role


# 权限缓存：key为user_id，value为权限码集合
_permission_cache: dict[str, Set[str]] = {}


class PermissionChecker:
    """权限检查和缓存管理"""
    
    @staticmethod
    def get_user_permissions(user_id: str, db: Session) -> Set[str]:
        """
        获取用户权限列表（带缓存）
        
        Args:
            user_id: 用户ID
            db: 数据库会话
            
        Returns:
            用户权限码集合
        """
        # 检查缓存
        if user_id in _permission_cache:
            return _permission_cache[user_id]
        
        # 从数据库加载权限
        # 使用selectinload预加载角色和权限关系
        user_with_roles = db.query(User).options(
            selectinload(User.roles).selectinload(Role.permissions)
        ).filter(User.id == user_id).first()
        
        if not user_with_roles:
            return set()
        
        permissions = set()
        if user_with_roles.roles:
            for role in user_with_roles.roles:
                if role.status:  # 只获取启用角色的权限
                    if role.permissions:
                        for permission in role.permissions:
                            if permission.status:  # 只获取启用状态的权限
                                permissions.add(permission.code)
        
        # 存入缓存
        _permission_cache[user_id] = permissions
        return permissions
    
    @staticmethod
    def has_permission(
        user_id: str,
        permission_codes: Union[str, List[str]],
        logic: str = "any",
        db: Optional[Session] = None
    ) -> bool:
        """
        检查用户是否拥有指定权限
        
        Args:
            user_id: 用户ID
            permission_codes: 权限码（单个或列表）
            logic: 逻辑类型，"any"表示OR逻辑（任意一个），"all"表示AND逻辑（全部需要）
            db: 数据库会话（如果提供则使用，否则从缓存获取）
            
        Returns:
            是否拥有权限
        """
        # 标准化权限码列表
        if isinstance(permission_codes, str):
            required_permissions = {permission_codes}
        else:
            required_permissions = set(permission_codes)
        
        if not required_permissions:
            return True  # 如果没有要求权限，则允许访问
        
        # 获取用户权限
        if db:
            user_permissions = PermissionChecker.get_user_permissions(user_id, db)
        else:
            # 如果没有提供db，尝试从缓存获取
            if user_id in _permission_cache:
                user_permissions = _permission_cache[user_id]
            else:
                # 缓存中没有，无法检查，返回False
                return False
        
        # 根据逻辑类型检查
        if logic == "all":
            # AND逻辑：必须拥有所有权限
            return required_permissions.issubset(user_permissions)
        else:
            # OR逻辑（默认）：拥有任意一个权限即可
            return bool(required_permissions & user_permissions)
    
    @staticmethod
    def clear_cache(user_id: Optional[str] = None):
        """
        清除权限缓存
        
        Args:
            user_id: 用户ID，如果为None则清除所有缓存
        """
        if user_id:
            _permission_cache.pop(user_id, None)
        else:
            _permission_cache.clear()


def require_permission(
    permission_codes: Union[str, List[str]],
    logic: str = "any"
) -> Callable:
    """
    权限校验依赖注入函数
    
    使用方式：
        @router.get("/users")
        def list_users(
            current_user = Depends(get_current_user),
            _ = Depends(require_permission("system:user:read"))
        ):
            ...
    
    Args:
        permission_codes: 权限码（单个或列表）
        logic: 逻辑类型，"any"表示OR逻辑，"all"表示AND逻辑
        
    Returns:
        FastAPI依赖函数
    """
    def permission_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        # 标准化权限码列表
        if isinstance(permission_codes, str):
            required_permissions = [permission_codes]
        else:
            required_permissions = permission_codes
        
        # 获取用户权限
        user_permissions = PermissionChecker.get_user_permissions(current_user.id, db)
        
        # 检查权限
        has_access = PermissionChecker.has_permission(
            current_user.id,
            permission_codes,
            logic,
            db
        )
        
        if not has_access:
            # 格式化权限码显示
            perm_str = ", ".join(required_permissions)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足：需要权限 {perm_str}"
            )
        
        return current_user
    
    return permission_checker


def require_permission_decorator(
    permission_codes: Union[str, List[str]],
    logic: str = "any"
):
    """
    权限校验装饰器
    
    使用方式：
        @router.get("/users")
        @require_permission_decorator("system:user:read")
        def list_users(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
            ...
    
    注意：装饰器方式需要在函数内部手动获取current_user和db，不如依赖注入方式方便
    支持同步和异步函数
    
    Args:
        permission_codes: 权限码（单个或列表）
        logic: 逻辑类型，"any"表示OR逻辑，"all"表示AND逻辑
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable):
        import inspect
        is_async = inspect.iscoroutinefunction(func)
        
        if is_async:
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # 从kwargs中获取current_user和db
                current_user = kwargs.get("current_user")
                db = kwargs.get("db")
                
                if not current_user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="未认证"
                    )
                
                if not db:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="数据库会话未找到"
                    )
                
                # 检查权限
                has_access = PermissionChecker.has_permission(
                    current_user.id,
                    permission_codes,
                    logic,
                    db
                )
                
                if not has_access:
                    # 格式化权限码显示
                    if isinstance(permission_codes, str):
                        required_permissions = [permission_codes]
                    else:
                        required_permissions = permission_codes
                    perm_str = ", ".join(required_permissions)
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"权限不足：需要权限 {perm_str}"
                    )
                
                return await func(*args, **kwargs)
            
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                # 从kwargs中获取current_user和db
                current_user = kwargs.get("current_user")
                db = kwargs.get("db")
                
                if not current_user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="未认证"
                    )
                
                if not db:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="数据库会话未找到"
                    )
                
                # 检查权限
                has_access = PermissionChecker.has_permission(
                    current_user.id,
                    permission_codes,
                    logic,
                    db
                )
                
                if not has_access:
                    # 格式化权限码显示
                    if isinstance(permission_codes, str):
                        required_permissions = [permission_codes]
                    else:
                        required_permissions = permission_codes
                    perm_str = ", ".join(required_permissions)
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"权限不足：需要权限 {perm_str}"
                    )
                
                return func(*args, **kwargs)
            
            return sync_wrapper
    
    return decorator



