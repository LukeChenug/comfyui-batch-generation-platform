from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, File, WebSocket, Depends
from fastapi.responses import StreamingResponse
from typing import Dict, Any
import time
import shutil
import zipfile
import io
from pathlib import Path
from backend.src.types import GenerationRequest, BatchRequest
from backend.src.services.task_service import TaskService
from backend.src.config.settings import UPLOAD_DIR, OUTPUT_DIR
from backend.src.auth import get_current_user
from backend.src.jobs.runner import job_runner, JobContext

router = APIRouter()

# 使用 Lazy Singleton 避免导入时实例化带来的潜在副作用
_task_service = None
def get_task_service():
    global _task_service
    if _task_service is None:
        _task_service = TaskService()
    return _task_service

@router.post("/generate")
async def generate_single(
    request: GenerationRequest, 
    user: Dict = Depends(get_current_user)
):
    """单个图像生成 (兼容层 -> 转发给 JobRunner)"""
    service = get_task_service()
    try:
        # 1. 创建 Task 记录
        task_id = service.create_task(request.dict(), request.batch_name, user_id=user["id"])
        
        # 2. 构造 JobContext (映射旧参数到 storybook scene)
        inputs = {
            "prompt": request.prompt,
            "negative_prompt": request.negative_prompt,
            "batch_size": request.batch_size
        }
        if request.seed:
            inputs["seed"] = request.seed
            
        # 尝试获取 aspect_ratio, 如果 request 模型里没有定义则忽略
        req_dict = request.dict()
        if "aspect_ratio" in req_dict:
            inputs["aspect_ratio"] = req_dict["aspect_ratio"]
        elif "width" in req_dict and "height" in req_dict:
            pass

        job = JobContext(
            job_id=task_id,
            scene_id="storybook", # 默认使用 storybook 场景
            user_input=inputs,
            user_id=user["id"]
        )
        
        # 3. 入队
        job_runner.enqueue(job)
        
        return {"task_id": task_id, "message": "任务已排队"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch")
async def generate_batch(
    batch_request: BatchRequest, 
    user: Dict = Depends(get_current_user)
):
    """批量图像生成"""
    service = get_task_service()
    task_ids = []
    batch_name = batch_request.batch_name or f"batch_{int(time.time())}"
    
    try:
        for request in batch_request.requests:
            request.batch_name = batch_name
            task_id = service.create_task(request.dict(), batch_name, user_id=user["id"])
            task_ids.append(task_id)
            
            # 构造 JobContext
            inputs = {
                "prompt": request.prompt,
                "negative_prompt": request.negative_prompt,
                "batch_size": request.batch_size
            }
            if request.seed:
                inputs["seed"] = request.seed
            
            job = JobContext(
                job_id=task_id,
                scene_id="storybook",
                user_input=inputs,
                user_id=user["id"]
            )
            
            # 入队
            job_runner.enqueue(job)
            
        return {
            "batch_name": batch_name,
            "task_ids": task_ids,
            "message": f"已提交 {len(task_ids)} 个任务到队列"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{task_id}")
async def get_task_status(
    task_id: str,
    user: Dict = Depends(get_current_user)
):
    """获取任务状态"""
    service = get_task_service()
    task = service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务未找到")
    
    # 权限检查
    if user["role"] != "admin" and task.get("user_id") != user["id"]:
        if task.get("user_id") is not None:
            raise HTTPException(status_code=403, detail="无权访问此任务")
            
    return task

@router.get("/jobs/{task_id}/zip")
async def download_job_zip(
    task_id: str,
    user: Dict = Depends(get_current_user)
):
    """打包下载任务结果"""
    service = get_task_service()
    task = service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务未找到")
    
    # 权限检查
    if user["role"] != "admin" and task.get("user_id") != user["id"]:
        if task.get("user_id") is not None:
             raise HTTPException(status_code=403, detail="无权访问此任务")

    # 获取结果文件列表
    result_files = task.get("result_urls", [])
    if not result_files and task.get("result_url"):
        result_files = [task.get("result_url")]
        
    if not result_files:
        raise HTTPException(status_code=404, detail="该任务没有生成结果")

    # 创建内存 ZIP
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for filename in result_files:
            file_path = OUTPUT_DIR / filename
            if file_path.exists():
                zip_file.write(file_path, arcname=filename)
            else:
                pass
    
    zip_buffer.seek(0)
    
    return StreamingResponse(
        zip_buffer, 
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=job_{task_id}.zip"}
    )

@router.get("/tasks")
async def get_all_tasks(user: Dict = Depends(get_current_user)):
    """获取任务列表"""
    service = get_task_service()
    if user["role"] == "admin":
        return {"tasks": service.get_all_tasks()}
    else:
        return {"tasks": service.get_user_tasks(user["id"])}

@router.get("/me")
async def get_current_user_info(user: Dict = Depends(get_current_user)):
    """获取当前用户信息"""
    return {
        "id": user["id"],
        "username": user["username"],
        "role": user["role"]
    }

@router.post("/upload_image")
async def upload_image(
    file: UploadFile = File(...),
    user: Dict = Depends(get_current_user)
):
    """上传图片文件"""
    try:
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="文件必须是图片格式")
        
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'png'
        saved_filename = f"{user['id']}_{int(time.time() * 1000)}.{file_extension}"
        file_path = UPLOAD_DIR / saved_filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {"filename": saved_filename, "path": str(file_path)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图片上传失败: {str(e)}")

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket实时更新"""
    service = get_task_service()
    await service.connect_websocket(websocket)
