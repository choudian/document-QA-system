"""
Langfuse 辅助函数
用于后续 LLM 调用时记录 Generation、Feedback 和评分
"""
import logging
from typing import Optional, Dict, Any
from app.core.langfuse_client import _langfuse_client

logger = logging.getLogger(__name__)


def create_generation(
    trace_id: str,
    name: str,
    model: Optional[str] = None,
    input: Optional[Any] = None,
    output: Optional[Any] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """
    创建 Generation 记录，关联到 Trace
    
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
    return _langfuse_client.generation(
        trace_id=trace_id,
        name=name,
        model=model,
        input=input,
        output=output,
        metadata=metadata,
    )


def update_generation(
    generation_id: str,
    output: Optional[Any] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    更新 Generation（用于流式响应）
    
    Args:
        generation_id: Generation ID
        output: 更新的输出
        metadata: 更新的元数据
    
    Returns:
        是否成功
    """
    try:
        client = _langfuse_client.get_client()
        if not client:
            return False
        
        # Langfuse SDK 可能不支持直接更新，这里预留接口
        # 实际使用时可能需要使用其他方式（如创建新的 Generation）
        logger.warning("update_generation 功能待实现")
        return False
    except Exception as e:
        logger.error(f"更新 Langfuse Generation 失败: {e}", exc_info=True)
        return False


def create_feedback(
    trace_id: str,
    score: Optional[float] = None,
    comment: Optional[str] = None,
) -> Optional[str]:
    """
    创建用户反馈记录
    
    Args:
        trace_id: 关联的 Trace ID
        score: 评分（0-1）
        comment: 评论
    
    Returns:
        Feedback ID，如果失败则返回 None
    """
    return _langfuse_client.feedback(
        trace_id=trace_id,
        score=score,
        comment=comment,
    )


def create_score(
    trace_id: str,
    name: str,
    value: float,
    comment: Optional[str] = None,
) -> Optional[str]:
    """
    创建评分记录
    
    Args:
        trace_id: 关联的 Trace ID
        name: 评分名称
        value: 评分值
        comment: 评论
    
    Returns:
        Score ID，如果失败则返回 None
    """
    return _langfuse_client.score(
        trace_id=trace_id,
        name=name,
        value=value,
        comment=comment,
    )

