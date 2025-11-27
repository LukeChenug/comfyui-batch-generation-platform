import logging
import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from backend.src.config.settings import OUTPUT_DIR
from backend.src.database.db import init_database
from backend.src.routes import task_routes
from backend.src.adapters.comfyui.adapter import ComfyUIAdapter

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ComfyUI-Flow API",
    description="企业级ComfyUI API生产中台",
    version="0.1.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务
app.mount("/images", StaticFiles(directory=str(OUTPUT_DIR)), name="images")

# 注册路由
app.include_router(task_routes.router)

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 启动服务...")
    init_database()
    logger.info("✅ 数据库初始化完成")

@app.get("/health")
async def health_check():
    """健康检查"""
    adapter = ComfyUIAdapter()
    comfy_health = await adapter.check_health()
    
    # 保持与旧版前端完全兼容的返回结构
    return {
        "api_server": "online",
        "comfyui_server": comfy_health["status"],
        "comfyui_url": comfy_health.get("url", ""),
        "comfyui_error": comfy_health.get("error", ""),
        "active_tasks": 0, # 暂时写死
        "comfyui_info": comfy_health # 保留新字段
    }

# 兼容旧的前端页面服务
@app.get("/batch_generation_dashboard.html")
async def get_dashboard():
    """提供批量生图管理界面"""
    html_path = os.path.abspath("batch_generation_dashboard.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return JSONResponse(status_code=404, content={"detail": "Dashboard not found"})

@app.get("/")
async def root():
    return {
        "message": "ComfyUI-Flow API Service",
        "docs": "/docs",
        "dashboard": "/batch_generation_dashboard.html"
    }

if __name__ == "__main__":
    uvicorn.run(
        "backend.src.main:app", 
        host="0.0.0.0", 
        port=8001, 
        reload=True
    )
