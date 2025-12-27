import logging
import os
import uvicorn
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from backend.src.config.settings import OUTPUT_DIR
from backend.src.database.db import init_database
from backend.src.routes import task_routes
from backend.src.adapters.comfyui.adapter import ComfyUIAdapter
from backend.src.init_admin import init_admin_account
from backend.src.jobs.runner import job_runner

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ComfyUI-Flow API",
    description="企业级ComfyUI API生产中台",
    version="0.2.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 智能寻根逻辑 ---
def find_project_root():
    """查找包含 index.html 的项目根目录"""
    # 1. 优先检查 CWD (当前运行目录)
    cwd = Path(os.getcwd())
    if (cwd / "index.html").exists():
        return cwd
    
    # 2. 检查代码文件所在路径的向上层级
    current = Path(__file__).resolve().parent
    for _ in range(5): # 最多往上找5层
        if (current / "index.html").exists():
            return current
        current = current.parent
        
    # 3. 兜底: 假设是标准结构 .../backend/src/main.py -> .../
    return Path(__file__).resolve().parent.parent.parent

BASE_DIR = find_project_root()
logger.info(f"📍 Project Root detected at: {BASE_DIR}")

# --- 静态文件挂载 ---

# 1. 生成图片目录 -> /images
if not OUTPUT_DIR.exists():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/images", StaticFiles(directory=str(OUTPUT_DIR)), name="images")

# 2. 下载目录 -> /downloads
static_downloads = BASE_DIR / "static" / "downloads"
if not static_downloads.exists():
    static_downloads.mkdir(parents=True, exist_ok=True)
app.mount("/downloads", StaticFiles(directory=str(static_downloads)), name="downloads")

# --- 路由注册 ---
app.include_router(task_routes.router)

# --- 生命周期 ---
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 启动服务...")
    try:
        init_database()
        logger.info("✅ 数据库初始化完成")
        init_admin_account() 
        logger.info("✅ 管理员账号检查完成")
        
        await job_runner.start()
        logger.info("✅ 任务调度器已启动")
    except Exception as e:
        logger.error(f"❌ 初始化失败: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 关闭服务...")
    await job_runner.stop()

# --- 页面路由 ---

@app.get("/")
async def root():
    """Landing Page"""
    html_path = BASE_DIR / "index.html"
    if html_path.exists():
        return FileResponse(html_path)
    return {
        "error": "Landing page not found", 
        "path": str(html_path),
        "hint": "Please ensure index.html exists in project root"
    }

@app.get("/v2")
async def get_dashboard_v2():
    """新版控制台入口"""
    html_path = BASE_DIR / "runner_v0.2.html"
    if html_path.exists():
        return FileResponse(html_path)
    return JSONResponse(status_code=404, content={"detail": f"Dashboard not found at {html_path}"})

@app.get("/health")
async def health_check():
    """健康检查"""
    adapter = ComfyUIAdapter()
    comfy_health = await adapter.check_health()
    return {
        "api_server": "online",
        "comfyui_server": comfy_health["status"],
        "comfyui_url": comfy_health.get("url", ""),
        "root_dir": str(BASE_DIR)
    }

if __name__ == "__main__":
    uvicorn.run(
        "backend.src.main:app", 
        host="0.0.0.0", 
        port=8088, 
        reload=False
    )
