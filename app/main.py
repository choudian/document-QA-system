"""
主应用入口
"""
from fastapi import FastAPI
from app.api.v1 import router as api_router
from app.core.config import settings
from app.core.database import init_db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="智能文档问答系统",
    description="个人知识库系统",
    version="1.0.0"
)

app.include_router(api_router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库"""
    logger.info("应用启动，检查数据库表...")
    init_db()


@app.get("/")
async def root():
    return {"message": "智能文档问答系统 API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

