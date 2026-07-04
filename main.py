"""
FastAPI应用入口
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import init_db
from app.api import api_router
from config import settings

# 启动时初始化数据库
@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"正在启动服务:{settings.APP_NAME} v{settings.APP_VERSION}...")
    try:
        init_db()
    except Exception as e:
        print(f"数据库初始化失败:{e}")
    yield
    # 关闭数据库
    print("服务正在关闭，释放资源...")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="企业知识库系统",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "服务器内部错误",
            "detail": str(exc) if settings.DEBUG else None
        }
    )

# 健康检查


# 注册路由
app.include_router(api_router, prefix="/api")

if __name__ == '__main__':
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)