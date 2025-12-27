import aiohttp
import asyncio
import logging
import uuid
import json
from typing import Any, List, Dict
from pathlib import Path

from backend.src.engines.base import EngineAdapter, PreflightReport, TaskStatus
from backend.src.config.settings import COMFYUI_SERVER, OUTPUT_DIR

logger = logging.getLogger(__name__)

class ComfyUIAdapter(EngineAdapter):
    def __init__(self, base_url: str = COMFYUI_SERVER):
        self.base_url = base_url.rstrip("/")
        self.client_id = str(uuid.uuid4())
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=600, connect=10)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def _ensure_session(self):
        """确保 session 可用 (用于非 context manager 模式)"""
        if not self.session or self.session.closed:
             self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=600, connect=10)
            )

    async def preflight(self) -> PreflightReport:
        await self._ensure_session()
        messages = []
        ok = True
        
        # 1. Check Connectivity
        try:
            async with self.session.get(f"{self.base_url}/system_stats") as resp:
                if resp.status == 200:
                    messages.append({"level": "info", "text": "ComfyUI 连接正常"})
                else:
                    ok = False
                    messages.append({"level": "error", "text": f"ComfyUI 返回异常状态码: {resp.status}"})
        except Exception as e:
            ok = False
            messages.append({"level": "error", "text": f"无法连接 ComfyUI: {str(e)}"})
            
        return PreflightReport(ok=ok, messages=messages)

    async def run(self, payload: Any) -> str:
        """
        payload 必须是 ComfyUI 的 prompt JSON (workflow)
        """
        await self._ensure_session()
        
        # 注入 client_id 以便追踪
        data = {
            "prompt": payload,
            "client_id": self.client_id
        }
        
        async with self.session.post(f"{self.base_url}/prompt", json=data) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise Exception(f"任务提交失败 [{resp.status}]: {text}")
            
            res_json = await resp.json()
            return res_json.get("prompt_id")

    async def status(self, engine_job_id: str) -> TaskStatus:
        await self._ensure_session()
        
        # 1. Check History (Done)
        try:
            async with self.session.get(f"{self.base_url}/history/{engine_job_id}") as resp:
                if resp.status == 200:
                    history = await resp.json()
                    if engine_job_id in history:
                        return TaskStatus.COMPLETED
        except Exception:
            pass
        
        # 2. Check Queue (Pending/Running)
        try:
            async with self.session.get(f"{self.base_url}/queue") as resp:
                if resp.status == 200:
                    queue_data = await resp.json()
                    
                    # Check running
                    running = queue_data.get("queue_running", [])
                    for task in running:
                        if task[1] == engine_job_id:
                            return TaskStatus.RUNNING
                            
                    # Check pending
                    pending = queue_data.get("queue_pending", [])
                    for task in pending:
                         if task[1] == engine_job_id:
                            return TaskStatus.PENDING
        except Exception:
            pass
        
        # 如果既不在历史也不在队列，且刚提交不久，可能是网络延迟？
        # 但为了简单起见，如果找不到，认为是 FAILED
        # 改进：如果 ComfyUI 重启了，任务也会消失。
        return TaskStatus.FAILED

    async def result(self, engine_job_id: str) -> List[str]:
        await self._ensure_session()
        
        # Get History again to find outputs
        async with self.session.get(f"{self.base_url}/history/{engine_job_id}") as resp:
            if resp.status != 200:
                raise Exception("无法获取任务历史")
            
            history = await resp.json()
            if engine_job_id not in history:
                raise Exception("任务历史未找到")
                
            task_data = history[engine_job_id]
            outputs = task_data.get("outputs", {})
            
            local_files = []
            
            for node_id, node_output in outputs.items():
                if "images" in node_output:
                    for img in node_output["images"]:
                        filename = img["filename"]
                        subfolder = img["subfolder"]
                        img_type = img["type"]
                        
                        # Download
                        params = {
                            "filename": filename,
                            "subfolder": subfolder,
                            "type": img_type
                        }
                        
                        async with self.session.get(f"{self.base_url}/view", params=params) as img_resp:
                            if img_resp.status == 200:
                                data = await img_resp.read()
                                # Save to local output dir
                                # 使用 engine_job_id 作为前缀防止文件名冲突
                                safe_name = f"{engine_job_id}_{filename}"
                                save_path = OUTPUT_DIR / safe_name
                                with open(save_path, "wb") as f:
                                    f.write(data)
                                local_files.append(str(save_path))
                            else:
                                logger.error(f"下载失败: {filename}")
                                
            return local_files

    async def cancel(self, engine_job_id: str) -> bool:
        await self._ensure_session()
        
        payload = {"delete": [engine_job_id]}
        async with self.session.post(f"{self.base_url}/queue", json=payload) as resp:
            return resp.status == 200

