"""
Langfuse 客户端封装
用于记录追踪、生成、反馈和评分
"""
import logging
from typing import Optional, Dict, Any
from langfuse import Langfuse
from app.core.database import SessionLocal
from app.repositories.config_repository import ConfigRepository
from app.services.config_service import ConfigService
import base64

logger = logging.getLogger(__name__)


class LangfuseClient:
    """Langfuse 客户端单例类"""
    
    _instance: Optional['LangfuseClient'] = None
    _client: Optional[Langfuse] = None
    _enabled: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def _get_config(self) -> Optional[Dict[str, Any]]:
        """从数据库获取 Langfuse 配置"""
        try:
            db = SessionLocal()
            try:
                config_repo = ConfigRepository(db)
                config_service = ConfigService(config_repo)
                
                # 获取系统级配置
                system_configs = config_service.list_scope_configs("system", None)
                langfuse_config = system_configs.get("langfuse", {}).get("default")
                
                if not langfuse_config:
                    return None
                
                # 检查是否启用
                if not langfuse_config.get("enabled", False):
                    return None
                
                # 解密敏感字段
                public_key = langfuse_config.get("public_key", "")
                secret_key = langfuse_config.get("secret_key", "")
                host = langfuse_config.get("host", "https://cloud.langfuse.com")
                
                # 解密（如果以 ENC: 开头）
                if public_key.startswith("ENC:"):
                    try:
                        public_key = base64.b64decode(public_key[4:]).decode("utf-8")
                    except Exception:
                        pass
                
                if secret_key.startswith("ENC:"):
                    try:
                        secret_key = base64.b64decode(secret_key[4:]).decode("utf-8")
                    except Exception:
                        pass
                
                if not public_key or not secret_key:
                    logger.warning("Langfuse 配置不完整：缺少 public_key 或 secret_key")
                    return None
                
                return {
                    "public_key": public_key,
                    "secret_key": secret_key,
                    "host": host,
                }
            finally:
                db.close()
        except Exception as e:
            logger.error(f"获取 Langfuse 配置失败: {e}", exc_info=True)
            return None
    
    def get_client(self) -> Optional[Langfuse]:
        """获取 Langfuse 客户端实例"""
        try:
            config = self._get_config()
            if not config:
                self._enabled = False
                self._client = None
                return None
            
            # 如果配置相同，返回缓存的客户端
            if self._client is not None and self._enabled:
                return self._client
            
            # 创建新的客户端
            self._client = Langfuse(
                public_key=config["public_key"],
                secret_key=config["secret_key"],
                host=config["host"],
            )
            self._enabled = True
            return self._client
        except Exception as e:
            logger.error(f"创建 Langfuse 客户端失败: {e}", exc_info=True)
            self._enabled = False
            self._client = None
            return None
    
    def is_enabled(self) -> bool:
        """检查 Langfuse 是否已启用"""
        if not self._enabled:
            self.get_client()  # 尝试获取客户端以更新状态
        return self._enabled
    
    def trace(
        self,
        name: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        input: Optional[Any] = None,
        output: Optional[Any] = None,
    ) -> Optional[str]:
        """
        创建 Trace 记录（同步方法，内部会异步发送）
        
        Args:
            name: 追踪名称（通常是请求路径）
            user_id: 用户 ID
            metadata: 元数据（租户 ID、请求方法、状态码、耗时等）
            input: 输入（请求体，已脱敏）
            output: 输出（响应体，已脱敏）
        
        Returns:
            Trace ID，如果失败则返回 None
        """
        try:
            client = self.get_client()
            if not client:
                return None
            
            trace = client.trace(
                name=name,
                user_id=user_id,
                metadata=metadata or {},
                input=input,
                output=output,
            )
            
            return trace.id if trace else None
        except Exception as e:
            logger.error(f"创建 Langfuse Trace 失败: {e}", exc_info=True)
            return None
    
    def generation(
        self,
        trace_id: str,
        name: str,
        model: Optional[str] = None,
        input: Optional[Any] = None,
        output: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        记录 Generation（用于 LLM 调用）
        
        Args:
            trace_id: 关联的 Trace ID
            name: Generation 名称
            model: 模型名称
            input: 输入（提示词等）
            output: 输出（生成的文本）
            metadata: 元数据
        
        Returns:
            Generation ID，如果失败则返回 None
        """
        try:
            client = self.get_client()
            if not client:
                return None
            
            generation = client.generation(
                trace_id=trace_id,
                name=name,
                model=model,
                input=input,
                output=output,
                metadata=metadata or {},
            )
            
            return generation.id if generation else None
        except Exception as e:
            logger.error(f"创建 Langfuse Generation 失败: {e}", exc_info=True)
            return None
    
    def feedback(
        self,
        trace_id: str,
        score: Optional[float] = None,
        comment: Optional[str] = None,
    ) -> Optional[str]:
        """
        记录用户反馈
        
        Args:
            trace_id: 关联的 Trace ID
            score: 评分（0-1）
            comment: 评论
        
        Returns:
            Feedback ID，如果失败则返回 None
        """
        try:
            client = self.get_client()
            if not client:
                return None
            
            feedback = client.feedback(
                trace_id=trace_id,
                score=score,
                comment=comment,
            )
            
            return feedback.id if feedback else None
        except Exception as e:
            logger.error(f"创建 Langfuse Feedback 失败: {e}", exc_info=True)
            return None
    
    def score(
        self,
        trace_id: str,
        name: str,
        value: float,
        comment: Optional[str] = None,
    ) -> Optional[str]:
        """
        记录评分
        
        Args:
            trace_id: 关联的 Trace ID
            name: 评分名称
            value: 评分值
            comment: 评论
        
        Returns:
            Score ID，如果失败则返回 None
        """
        try:
            client = self.get_client()
            if not client:
                return None
            
            score = client.score(
                trace_id=trace_id,
                name=name,
                value=value,
                comment=comment,
            )
            
            return score.id if score else None
        except Exception as e:
            logger.error(f"创建 Langfuse Score 失败: {e}", exc_info=True)
            return None


# 全局单例实例
_langfuse_client = LangfuseClient()

