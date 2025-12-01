from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, File, WebSocket, Depends
from typing import Dict
import time
import shutil
from pathlib import Path
from backend.src.types import GenerationRequest, BatchRequest
from backend.src.services.task_service import TaskService
from backend.src.config.settings import UPLOAD_DIR
from backend.src.auth import get_current_user

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
    background_tasks: BackgroundTasks,
    user: Dict = Depends(get_current_user)
):
    """单个图像生成"""
    service = get_task_service()
    try:
        task_id = service.create_task(request.dict(), request.batch_name, user_id=user["id"])
        background_tasks.add_task(service.process_task, task_id, request)
        return {"task_id": task_id, "message": "任务已提交"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch")
async def generate_batch(
    batch_request: BatchRequest, 
    background_tasks: BackgroundTasks,
    user: Dict = Depends(get_current_user)
):
    """批量图像生成"""
    service = get_task_service()
    task_ids = []
    batch_name = batch_request.batch_name or f"batch_{int(time.time())}"
    
    for request in batch_request.requests:
        request.batch_name = batch_name
        task_id = service.create_task(request.dict(), batch_name, user_id=user["id"])
        task_ids.append(task_id)
        
        background_tasks.add_task(service.process_task, task_id, request)
        
    return {
        "batch_name": batch_name,
        "task_ids": task_ids,
        "message": f"已提交 {len(task_ids)} 个任务"
    }

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
