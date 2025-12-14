"""
统一日志配置
"""
import logging
import sys
from datetime import datetime
from typing import Any
import traceback


class ColoredFormatter(logging.Formatter):
    """带颜色的日志格式化器"""
    
    # ANSI颜色代码
    COLORS = {
        'DEBUG': '\033[36m',      # 青色
        'INFO': '\033[32m',       # 绿色
        'WARNING': '\033[33m',    # 黄色
        'ERROR': '\033[31m',       # 红色
        'CRITICAL': '\033[35m',    # 紫色
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        # 添加颜色
        log_color = self.COLORS.get(record.levelname, '')
        reset_color = self.RESET
        
        # 格式化时间
        record.asctime = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        # 格式化日志消息
        if record.exc_info:
            # 如果有异常信息，格式化异常堆栈
            exc_text = self.formatException(record.exc_info)
            message = f"{record.getMessage()}\n{exc_text}"
        else:
            message = record.getMessage()
        
        # 构建日志行
        log_line = (
            f"{log_color}[{record.asctime}] "
            f"[{record.levelname:8s}] "
            f"[{record.name}] "
            f"{message}{reset_color}"
        )
        
        return log_line


def setup_logging(log_level: str = "INFO"):
    """
    设置统一的日志配置
    
    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # 清除现有的处理器
    root_logger.handlers.clear()
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # 设置格式化器
    formatter = ColoredFormatter(
        fmt='[%(asctime)s] [%(levelname)-8s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # 添加处理器到根日志记录器
    root_logger.addHandler(console_handler)
    
    # 设置第三方库的日志级别
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    
    return root_logger


def log_exception(logger: logging.Logger, exc: Exception, context: dict = None):
    """
    统一记录异常信息
    
    Args:
        logger: 日志记录器
        exc: 异常对象
        context: 额外的上下文信息
    """
    exc_type = type(exc).__name__
    exc_message = str(exc)
    exc_traceback = traceback.format_exc()
    
    # 构建错误消息
    error_msg = f"异常类型: {exc_type}\n异常消息: {exc_message}"
    
    if context:
        context_str = "\n".join([f"  {k}: {v}" for k, v in context.items()])
        error_msg += f"\n上下文信息:\n{context_str}"
    
    error_msg += f"\n堆栈跟踪:\n{exc_traceback}"
    
    logger.error(error_msg, exc_info=False)


def get_logger(name: str) -> logging.Logger:
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称（通常是模块名）
    
    Returns:
        配置好的日志记录器
    """
    return logging.getLogger(name)

