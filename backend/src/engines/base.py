from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class PreflightReport:
    ok: bool
    messages: List[Dict[str, str]]  # [{"level": "error", "text": "..."}]

class EngineAdapter(ABC):
    """引擎适配器抽象基类"""

    @abstractmethod
    async def preflight(self) -> PreflightReport:
        """环境检查：连接性、模型存在性"""
        pass

    @abstractmethod
    async def run(self, payload: Any) -> str:
        """提交任务，返回 engine_job_id"""
        pass

    @abstractmethod
    async def status(self, engine_job_id: str) -> TaskStatus:
        """查询任务状态"""
        pass

    @abstractmethod
    async def result(self, engine_job_id: str) -> List[str]:
        """获取生成结果（下载并返回本地路径）"""
        pass
    
    @abstractmethod
    async def cancel(self, engine_job_id: str) -> bool:
        """取消任务"""
        pass

