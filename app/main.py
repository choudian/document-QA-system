"""
主应用入口
"""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.api.v1 import router as api_router
from app.core.config import settings
from app.core.database import init_db
from app.middleware.audit_middleware import AuditMiddleware
from app.middleware.exception_middleware import ExceptionMiddleware
from app.core.logging_config import setup_logging, get_logger, log_exception

# 设置统一日志配置
setup_logging(log_level="INFO")
logger = get_logger(__name__)

app = FastAPI(
    title="智能文档问答系统",
    description="个人知识库系统",
    version="1.0.0"
)

# 注册异常拦截中间件（最外层，最先执行）
app.add_middleware(ExceptionMiddleware)

# 注册审计日志中间件（在其他中间件之后，路由之前）
app.add_middleware(AuditMiddleware)

app.include_router(api_router, prefix="/api/v1")


# 全局异常处理器
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理请求验证错误"""
    logger.error(f"请求验证失败: {exc.errors()}")
    logger.error(f"请求路径: {request.url.path}")
    logger.error(f"请求方法: {request.method}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body}
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """处理所有未捕获的异常"""
    context = {
        "method": request.method,
        "path": request.url.path,
        "query_params": str(request.query_params),
    }
    log_exception(logger, exc, context)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": f"内部服务器错误: {str(exc)}",
            "error_type": type(exc).__name__,
        }
    )


@app.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库"""
    logger.info("=" * 60)
    logger.info("应用启动，检查数据库表...")
    init_db()
    logger.info("应用启动完成")
    logger.info("=" * 60)


@app.get("/")
async def root():
    return {"message": "智能文档问答系统 API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

