import asyncio
import logging
import json
import time
import uuid
import aiohttp  # 确保全局可用
import subprocess  # 🆕 引入子进程模块，用于调用 curl
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union
from fastapi import WebSocket

from backend.src.database import db
from backend.src.types import GenerationRequest, TaskStatusModel
from backend.src.adapters.comfyui.adapter import ComfyUIAdapter
from backend.src.adapters.comfy_deploy.adapter import ComfyDeployAdapter
from backend.src.adapters.storage import get_storage_adapter
from backend.src.services.workflow_service import WorkflowService
from backend.src.config.settings import OUTPUT_DIR, USE_COMFY_DEPLOY

logger = logging.getLogger(__name__)

class TaskService:
    def __init__(self):
        self.active_tasks = {}  # 本地缓存，用于WebSocket广播等
        self.websocket_connections: List[WebSocket] = []

    # ... existing websocket methods ...
    async def connect_websocket(self, websocket: WebSocket):
        """处理WebSocket连接"""
        await websocket.accept()
        self.websocket_connections.append(websocket)
        try:
            while True:
                await websocket.receive_text()
        except Exception:
            if websocket in self.websocket_connections:
                self.websocket_connections.remove(websocket)

    async def _broadcast_update(self, task_data: Dict):
        """广播任务更新"""
        if not self.websocket_connections:
            return
            
        message = {"type": "task_update", "data": task_data}
        disconnected = []
        
        for ws in self.websocket_connections:
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.append(ws)
                
        for ws in disconnected:
            if ws in self.websocket_connections:
                self.websocket_connections.remove(ws)

    # ... existing create/get task methods ...
    def create_task(self, request_data: Dict, batch_name: Optional[str] = None) -> str:
        task_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        task_data = {
            "task_id": task_id, "status": "pending", "progress": 0,
            "message": "任务已创建", "created_at": now,
            "request_data": request_data, "batch_name": batch_name
        }
        db.save_task(task_data)
        return task_id

    def get_task(self, task_id: str) -> Optional[Dict]:
        return db.get_task(task_id)

    def get_all_tasks(self) -> List[Dict]:
        return db.get_recent_tasks()

    # ... process task ...
    async def process_task(self, task_id: str, request: GenerationRequest):
        try:
            self._update_task(task_id, status="running", progress=5, message="准备任务...")
            if USE_COMFY_DEPLOY:
                await self._process_with_deploy(task_id, request)
            else:
                await self._process_with_local(task_id, request)
        except Exception as e:
            logger.error(f"任务 {task_id} 执行异常: {e}")
            self._update_task(task_id, status="failed", error=str(e))

    async def _process_with_deploy(self, task_id: str, request: GenerationRequest):
        deploy = ComfyDeployAdapter()
        self._update_task(task_id, progress=10, message="提交到 ComfyDeploy...")
        
        inputs = {"input_text": request.prompt}
        run_id = await deploy.run_deployment(inputs)
        self._update_task(task_id, progress=20, message="ComfyDeploy 云端生成中...")
        
        max_attempts = 300
        for attempt in range(max_attempts):
            await asyncio.sleep(2)
            progress = 20 + (attempt / max_attempts) * 70
            if attempt % 5 == 0:
                self._update_task(task_id, progress=progress)
                
            status_data = await deploy.get_run_status(run_id)
            status = status_data.get("status")
            
            if status == "success":
                # 🐛 强制抓包调试
                with open("debug_comfy_response.json", "w") as f:
                    json.dump(status_data, f, indent=2, ensure_ascii=False)
                logger.info(f"✅ 云端任务成功，数据已写入 debug_comfy_response.json")
                
                self._update_task(task_id, progress=90, message="生成成功，下载结果...")
                
                # 💡 智能解析 outputs
                outputs = status_data.get("outputs", {})
                image_urls = []
                
                # 情况1：outputs 是列表 (e.g. [{"data": {"images": [{"url":...}]}}])
                if isinstance(outputs, list):
                    for item in outputs:
                        # 优先尝试 ComfyDeploy 标准结构: item.data.images[].url
                        if isinstance(item, dict) and "data" in item:
                            data_obj = item.get("data", {})
                            if isinstance(data_obj, dict) and "images" in data_obj:
                                images_list = data_obj.get("images", [])
                                for img in images_list:
                                    if isinstance(img, dict) and "url" in img:
                                        image_urls.append(img["url"])
                        
                        # 备用尝试: item.url
                        elif isinstance(item, dict) and "url" in item:
                            image_urls.append(item["url"])
                        # 备用尝试: item 是字符串
                        elif isinstance(item, str) and item.startswith("http"):
                            image_urls.append(item)
                            
                # 情况2：outputs 是字典 (e.g. {"output_images": [{"url":...}]})
                elif isinstance(outputs, dict):
                    for key, value in outputs.items():
                        if isinstance(value, list):
                            for item in value:
                                if isinstance(item, dict) and "url" in item:
                                    image_urls.append(item["url"])
                        elif isinstance(value, dict) and "url" in value:
                            image_urls.append(value["url"])
                        # 💡 新增：支持直接是字符串列表的情况 (e.g. output_images: ["http://..."])
                        elif isinstance(value, list):
                            for item in value:
                                if isinstance(item, str) and item.startswith("http"):
                                    image_urls.append(item)

                if not image_urls:
                    # 再次检查是否直接在 outputs 列表里有字符串URL
                     if isinstance(outputs, list):
                         for item in outputs:
                             if isinstance(item, str) and item.startswith("http"):
                                 image_urls.append(item)

                # 策略：只保留最后一张图片 (解决多节点重复输出问题)
                if len(image_urls) > 1:
                    logger.info(f"检测到 {len(image_urls)} 张图片，自动只保留最后一张")
                    image_urls = [image_urls[-1]]

                # 去重逻辑：根据 URL 去重
                unique_urls = []
                seen_urls = set()
                
                storage = get_storage_adapter()

                for i, img_url in enumerate(image_urls):
                    if img_url in seen_urls:
                        continue
                    seen_urls.add(img_url)
                    
                    # 恢复下载模式 (Download Mode)
                    try:
                        # 1. 优先尝试 aiohttp (禁用SSL验证)
                        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
                            async with session.get(img_url) as resp:
                                if resp.status == 200:
                                    image_data = await resp.read()
                                    filename = f"{task_id}_{i}.png"
                                    new_url = await storage.upload(image_data, filename)
                                    unique_urls.append(new_url)
                                    logger.info(f"✅ 图片下载成功 (aiohttp): {new_url}")
                                else:
                                    logger.error(f"❌ 图片下载失败 HTTP {resp.status}: {img_url}")
                                    raise Exception(f"HTTP {resp.status}")
                                    
                    except Exception as e:
                        logger.error(f"❌ aiohttp 下载异常: {e}，尝试 curl 兜底...")
                        
                        # 2. 终极兜底：调用系统 curl 命令 (彻底无视 SSL 和环境问题)
                        try:
                            filename = f"{task_id}_{i}.png"
                            local_path = Path(OUTPUT_DIR) / filename
                            
                            # 确保输出目录存在
                            local_path.parent.mkdir(parents=True, exist_ok=True)
                            
                            # 构造 curl 命令: -k (insecure), -L (follow redirects), -o (output)
                            cmd = ["curl", "-k", "-L", img_url, "-o", str(local_path)]
                            
                            # 同步执行 (虽然会阻塞一下，但为了稳定性值得)
                            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                            
                            if result.returncode == 0 and local_path.exists() and local_path.stat().st_size > 0:
                                # 读取下载的文件并上传到 storage (保持接口一致性)
                                with open(local_path, "rb") as f:
                                    image_data = f.read()
                                new_url = await storage.upload(image_data, filename)
                                unique_urls.append(new_url)
                                logger.info(f"✅ 图片下载成功 (curl 兜底): {new_url}")
                                
                                # 可选：删除临时文件 (storage.upload如果是本地存储，其实就是覆盖了一次，如果是S3则上传后删除)
                                # local_path.unlink() 
                            else:
                                logger.error(f"❌ curl 下载失败: {result.stderr}")
                                
                        except Exception as e2:
                            logger.error(f"❌ curl 兜底也失败: {e2}")

                if unique_urls:
                    self._update_task(
                        task_id, status="completed", progress=100, 
                        message="生成完成", result_url=unique_urls[0], result_urls=unique_urls
                    )
                else:
                    # 如果没找到URL，把原始 outputs 打印出来方便调试
                    error_msg = f"未找到图片URL，原始outputs: {json.dumps(outputs)}"
                    logger.error(error_msg)
                    raise Exception(error_msg)
                return
                
            elif status in ["failed", "error"]:
                raise Exception(f"云端任务失败: {status}")
        
        raise Exception("云端任务超时")

    # ... (keep _process_with_local and other methods as is) ...
    async def _process_with_local(self, task_id: str, request: GenerationRequest):
        """使用本地/自建 ComfyUI 处理任务 (原逻辑)"""
        # 1. 处理图片上传 (如果是图生图)
        if request.input_image:
            await self._handle_image_upload(task_id, request)

        self._update_task(task_id, progress=15, message="构建工作流...")
        
        # 2. 构建工作流
        workflow = WorkflowService.create_workflow(request)
        
        # 3. 提交到ComfyUI
        async with ComfyUIAdapter() as comfy:
            self._update_task(task_id, progress=25, message="提交任务到ComfyUI...")
            
            try:
                prompt_id = await comfy.submit_prompt(workflow)
            except Exception as e:
                logger.error(f"任务提交失败: {e}")
                raise

            self._update_task(task_id, progress=35, message="等待ComfyUI生成...")
            
            # 4. 轮询状态
            await self._poll_status(task_id, prompt_id, comfy, request)

    async def _handle_image_upload(self, task_id: str, request: GenerationRequest):
        """处理输入图片上传"""
        self._update_task(task_id, progress=10, message="上传图片到ComfyUI...")
        
        local_image_path = Path("./uploaded_images") / request.input_image
        if not local_image_path.exists():
             raise Exception(f"本地图片文件不存在: {request.input_image}")

        with open(local_image_path, "rb") as f:
            image_data = f.read()
            
        async with ComfyUIAdapter() as comfy:
            comfyui_image_name = await comfy.upload_image(image_data, request.input_image)
            logger.info(f"✅ 任务 {task_id} - 图片已上传到ComfyUI: {comfyui_image_name}")
            # 更新request中的图片名称为ComfyUI中的名称
            request.input_image = comfyui_image_name

    async def _poll_status(self, task_id: str, prompt_id: str, comfy: ComfyUIAdapter, request: GenerationRequest):
        """轮询任务状态"""
        logger.info(f"⏳ 开始轮询任务 {task_id} (prompt_id: {prompt_id})")
        max_attempts = 300 # 10分钟
        
        for attempt in range(max_attempts):
            await asyncio.sleep(2)
            
            # 模拟进度 (35% -> 90%)
            progress = 35 + (attempt / max_attempts) * 55
            # 只有进度变化较大时才更新数据库，减少IO
            if attempt % 5 == 0:
                self._update_task(task_id, progress=progress, message="ComfyUI生成中...")
            
            history = await comfy.get_history(prompt_id)
            
            if prompt_id in history:
                logger.info(f"✅ 任务 {task_id} ComfyUI已完成，开始处理结果")
                await self._handle_completion(task_id, history[prompt_id], comfy, request)
                return

        logger.error(f"❌ 任务 {task_id} 轮询超时")
        self._update_task(task_id, status="failed", error="任务超时")

    async def _handle_completion(self, task_id: str, history_data: Dict, comfy: ComfyUIAdapter, request: GenerationRequest):
        """处理任务完成，下载图片"""
        outputs = history_data.get("outputs", {})
        images = []
        
        # 查找输出节点 (兼容多种工作流)
        for node_id in ["60", "8", "115:116"]:
            if node_id in outputs:
                images = outputs[node_id].get("images", [])
                break
        
        if not images:
            raise Exception("未找到输出图像")

        result_urls = []
        storage = get_storage_adapter()
        
        for i, img_info in enumerate(images):
            image_data = await comfy.download_image(
                img_info["filename"],
                img_info.get("subfolder", ""),
                img_info.get("type", "output")
            )
            
            # 使用存储适配器保存
            filename = f"{task_id}_{i}.png"
            url = await storage.upload(image_data, filename)
            
            result_urls.append(url)

        self._update_task(
            task_id, 
            status="completed", 
            progress=100, 
            message="生成完成",
            result_url=result_urls[0],
            result_urls=result_urls
        )

    def _update_task(self, task_id: str, **kwargs):
        """更新任务状态并写入数据库"""
        task = db.get_task(task_id) or {"task_id": task_id}
        task.update(kwargs)
        
        if kwargs.get("status") in ["completed", "failed"]:
            task["completed_at"] = datetime.now().isoformat()
            
        db.save_task(task)
        # 触发WebSocket广播
        asyncio.create_task(self._broadcast_update(task))
