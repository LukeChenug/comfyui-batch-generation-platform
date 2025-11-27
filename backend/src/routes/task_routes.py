from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, File, WebSocket
from typing import Dict
import time
import shutil
from pathlib import Path
from backend.src.types import GenerationRequest, BatchRequest
from backend.src.services.task_service import TaskService
from backend.src.config.settings import UPLOAD_DIR

router = APIRouter()
task_service = TaskService()

@router.post("/generate")
async def generate_single(request: GenerationRequest, background_tasks: BackgroundTasks):
    """单个图像生成"""
    try:
        task_id = task_service.create_task(request.dict(), request.batch_name)
        background_tasks.add_task(task_service.process_task, task_id, request)
        return {"task_id": task_id, "message": "任务已提交"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch")
async def generate_batch(batch_request: BatchRequest, background_tasks: BackgroundTasks):
    """批量图像生成"""
    task_ids = []
    batch_name = batch_request.batch_name or f"batch_{int(time.time())}"
    
    for request in batch_request.requests:
        request.batch_name = batch_name
        task_id = task_service.create_task(request.dict(), batch_name)
        task_ids.append(task_id)
        
        background_tasks.add_task(task_service.process_task, task_id, request)
        
    return {
        "batch_name": batch_name,
        "task_ids": task_ids,
        "message": f"已提交 {len(task_ids)} 个任务"
    }

@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """获取任务状态"""
    task = task_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务未找到")
    return task

@router.get("/tasks")
async def get_all_tasks():
    """获取所有任务"""
    return {"tasks": task_service.get_all_tasks()}

@router.post("/upload_image")
async def upload_image(file: UploadFile = File(...)):
    """上传图片文件"""
    try:
        # 检查文件类型
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="文件必须是图片格式")
        
        # 保存文件
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'png'
        saved_filename = f"{int(time.time() * 1000)}.{file_extension}"
        file_path = UPLOAD_DIR / saved_filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {"filename": saved_filename, "path": str(file_path)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图片上传失败: {str(e)}")

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket实时更新"""
    await task_service.connect_websocket(websocket)
