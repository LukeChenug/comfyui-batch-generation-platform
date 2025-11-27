from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class GenerationRequest(BaseModel):
    """单个生成请求"""
    prompt: str
    negative_prompt: Optional[str] = ""
    width: int = 1024
    height: int = 1024
    steps: int = 8
    cfg: float = 1.0
    seed: Optional[int] = None
    batch_size: int = 1
    batch_name: Optional[str] = None
    input_image: Optional[str] = None  # 输入图片的文件名

class BatchRequest(BaseModel):
    """批量生成请求"""
    requests: List[GenerationRequest]
    batch_name: Optional[str] = None
    priority: int = 0

class TaskStatusModel(BaseModel):
    """任务状态"""
    task_id: str
    status: str  # pending, running, completed, failed
    progress: float
    message: str
    created_at: str
    completed_at: Optional[str] = None
    result_url: Optional[str] = None
    result_urls: Optional[List[str]] = None  # 支持多张图片
    error: Optional[str] = None
    request_data: Optional[Dict] = None  # 生成参数

