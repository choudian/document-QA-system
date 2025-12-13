"""
认证领域服务
"""
import secrets
import pyotp
from fastapi import HTTPException, status
from app.repositories.user_repository import UserRepository
from app.repositories.tenant_repository import TenantRepository
from app.core.security import create_access_token, password_hasher
from app.services.auth_providers.password_provider import PasswordAuthProvider
from app.services.auth_providers.sso_provider import SSOAuthProvider
from app.services.auth_providers.system_admin_provider import SystemAdminPasswordProvider
from app.services.auth_providers.base import AuthProvider
from app.models.user import User


class AuthService:
    """
    认证服务，支持多种认证提供方（策略模式），默认使用 password
    """

    def __init__(self, user_repo: UserRepository, tenant_repo: TenantRepository):
        self.user_repo = user_repo
        self.tenant_repo = tenant_repo
        # 注册可用的认证提供方
        self.providers: dict[str, AuthProvider] = {
            PasswordAuthProvider.name: PasswordAuthProvider(user_repo, tenant_repo),
            SSOAuthProvider.name: SSOAuthProvider(),
            SystemAdminPasswordProvider.name: SystemAdminPasswordProvider(user_repo),
        }

    def login(self, phone: str, credential: str, auth_type: str = "password") -> str:
        provider = self.providers.get(auth_type)
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的认证方式: {auth_type}",
            )

        # 通过手机号查询用户（手机号全局唯一）
        user = self.user_repo.get_by_phone(phone)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="手机号或密码错误",
            )
        
        # 验证密码
        from app.core.security import password_hasher
        if not password_hasher.verify_password(credential, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="手机号或密码错误",
            )
        
        # 检查用户状态
        if user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="用户已停用或冻结",
            )
        
        # 如果是系统管理员（tenant_id 为空），检查租户状态（不需要）
        # 如果是普通用户，检查租户状态
        if user.tenant_id:
            tenant = self.tenant_repo.get(user.tenant_id)
            if not tenant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="用户所属租户不存在",
                )
            if not tenant.status:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="用户所属租户已停用",
                )
        
        # 加载用户角色关系以确保数据最新
        from sqlalchemy.orm import selectinload
        user_with_roles = self.user_repo.db.query(User).options(
            selectinload(User.roles)
        ).filter(User.id == user.id).first()
        
        if user_with_roles:
            user_with_roles.update_tenant_admin_status()
            self.user_repo.db.commit()
            is_tenant_admin = user_with_roles.is_tenant_admin
            is_system_admin = user_with_roles.is_system_administrator()
        else:
            is_tenant_admin = user.is_tenant_admin if hasattr(user, 'is_tenant_admin') else False
            is_system_admin = False
        
        # 生成 token
        token = create_access_token({
            "sub": user.id,
            "tenant_id": user.tenant_id,
            "is_system_admin": is_system_admin,
            "is_tenant_admin": is_tenant_admin,
        })
        return token
    
    def register(self, tenant_id: str, username: str, phone: str, password: str) -> User:
        """
        用户注册（占位实现）
        
        注意：此功能为占位实现，实际注册功能需要根据业务需求完善
        """
        # 检查租户是否存在
        tenant = self.tenant_repo.get_by_id(tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="租户不存在",
            )
        
        # 检查手机号是否已存在
        existing_user = self.user_repo.get_by_phone(phone)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该手机号已被注册",
            )
        
        # 检查租户内用户名是否已存在（需要实现此方法）
        # existing_username = self.user_repo.get_by_tenant_and_username(tenant_id, username)
        # if existing_username:
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail="该用户名已被使用",
        #     )
        
        # 创建用户
        from app.core.security import password_hasher
        password_hash = password_hasher.hash_password(password)
        user = User(
            tenant_id=tenant_id,
            username=username,
            phone=phone,
            password_hash=password_hash,
            status="active",
        )
        self.user_repo.create(user)
        return user
    
    def request_password_reset(self, phone: str, tenant_id: str = None) -> dict:
        """
        请求重置密码（发送验证码）（占位实现）
        
        注意：此功能为占位实现，实际实现需要集成短信/邮件服务
        """
        user = self.user_repo.get_by_phone(phone)
        if not user:
            # 为了安全，不暴露用户是否存在
            return {"message": "如果该手机号已注册，验证码已发送"}
        
        # 占位：生成验证码（实际应该通过短信/邮件发送）
        verification_code = "123456"  # 占位验证码，实际应该随机生成并存储
        
        # TODO: 实际实现应该：
        # 1. 生成随机验证码
        # 2. 存储验证码（带过期时间）
        # 3. 通过短信/邮件发送验证码
        
        return {
            "message": "验证码已发送（占位实现）",
            "verification_code": verification_code,  # 仅占位，实际不应返回
        }
    
    def confirm_password_reset(
        self, phone: str, verification_code: str, new_password: str, tenant_id: str = None
    ) -> dict:
        """
        确认重置密码（占位实现）
        
        注意：此功能为占位实现，实际实现需要验证验证码
        """
        user = self.user_repo.get_by_phone(phone)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在",
            )
        
        # 占位：验证验证码（实际应该从存储中验证）
        if verification_code != "123456":  # 占位验证
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="验证码错误或已过期",
            )
        
        # 更新密码
        from app.core.security import password_hasher
        user.password_hash = password_hasher.hash_password(new_password)
        self.user_repo.update(user)
        
        return {"message": "密码重置成功"}
    
    def enable_mfa(self, user_id: str, mfa_type: str = "otp") -> dict:
        """
        启用 MFA（占位实现）
        
        注意：此功能为占位实现，实际实现需要生成并存储 MFA secret
        """
        import pyotp
        
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在",
            )
        
        if user.mfa_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MFA 已启用",
            )
        
        # 生成 OTP secret
        secret = pyotp.random_base32()
        user.mfa_secret = secret
        user.mfa_enabled = True
        self.user_repo.update(user)
        
        # 生成二维码 URL（占位）
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user.username,
            issuer_name="Document QA System"
        )
        
        return {
            "enabled": True,
            "secret": secret,  # 仅首次启用时返回
            "qr_code_url": f"data:image/png;base64,占位二维码",  # 占位，实际应该生成二维码图片
            "totp_uri": totp_uri,  # 用于生成二维码
        }
    
    def disable_mfa(self, user_id: str) -> dict:
        """
        禁用 MFA（占位实现）
        """
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在",
            )
        
        user.mfa_enabled = False
        user.mfa_secret = None
        self.user_repo.update(user)
        
        return {"message": "MFA 已禁用"}
    
    def verify_mfa(self, user_id: str, code: str) -> bool:
        """
        验证 MFA 代码（占位实现）
        
        注意：此功能为占位实现，实际实现需要验证 OTP 代码
        """
        import pyotp
        
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在",
            )
        
        if not user.mfa_enabled or not user.mfa_secret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MFA 未启用",
            )
        
        # 验证 OTP 代码
        totp = pyotp.TOTP(user.mfa_secret)
        if not totp.verify(code, valid_window=1):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="MFA 验证码错误",
            )
        
        return True

