import aiohttp
import asyncio
import json
import logging
import uuid
from typing import Dict, Optional, List
from fastapi import HTTPException
from backend.src.config.settings import COMFYUI_SERVER

logger = logging.getLogger(__name__)

class ComfyUIAdapter:
    """ComfyUI适配器 - 负责与ComfyUI服务器通信"""
    
    def __init__(self):
        self.client_id = str(uuid.uuid4())
        self.session = None
        
    async def __aenter__(self):
        # 设置更长的超时时间：总超时 10 分钟，连接超时 30 秒
        timeout = aiohttp.ClientTimeout(total=600, connect=30)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def check_health(self) -> Dict[str, str]:
        """检查ComfyUI健康状态"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{COMFYUI_SERVER}/system_stats", 
                    timeout=aiohttp.ClientTimeout(total=5, connect=3)
                ) as response:
                    if response.status == 200:
                        return {"status": "online", "url": COMFYUI_SERVER}
                    return {"status": "offline", "error": f"HTTP {response.status}", "url": COMFYUI_SERVER}
        except Exception as e:
            # logger.warning(f"ComfyUI健康检查失败: {e}") # 降级为warning避免刷屏
            return {"status": "offline", "error": str(e), "url": COMFYUI_SERVER}

    async def submit_prompt(self, workflow: Dict) -> str:
        """提交工作流到ComfyUI"""
        url = f"{COMFYUI_SERVER}/prompt"
        
        # 规范化工作流节点ID
        normalized_workflow = {str(k): v for k, v in workflow.items()}
        
        data = {
            "prompt": normalized_workflow,
            "client_id": self.client_id
        }
        
        logger.info(f"📡 正在提交工作流到 {url}...")
        
        max_retries = 3
        for retry in range(max_retries):
            try:
                async with self.session.post(url, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        prompt_id = result.get("prompt_id")
                        logger.info(f"✅ ComfyUI任务提交成功: {prompt_id}")
                        return prompt_id
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ ComfyUI返回错误 ({response.status}): {error_text[:200]}")
                        if retry == max_retries - 1:
                            raise HTTPException(status_code=500, detail=f"ComfyUI提交失败: {error_text[:500]}")
            except Exception as e:
                logger.warning(f"⚠️ 提交重试 {retry+1}/{max_retries}: {e}")
                if retry == max_retries - 1:
                    logger.error(f"❌ 提交任务最终失败: {e}")
                    raise
                await asyncio.sleep(1)
        
    async def get_history(self, prompt_id: str) -> Dict:
        """获取任务历史"""
        url = f"{COMFYUI_SERVER}/history/{prompt_id}"
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    history = await response.json()
                    # logger.debug(f"🔍 查询历史 {prompt_id}: {'找到' if prompt_id in history else '未完成'}")
                    return history
                else:
                    logger.warning(f"⚠️ 获取历史失败 HTTP {response.status}: {url}")
                    return {}
        except Exception as e:
            logger.error(f"❌ 获取历史异常: {e}")
            return {}

    async def download_image(self, filename: str, subfolder: str = "", type: str = "output") -> bytes:
        """下载生成的图像"""
        url = f"{COMFYUI_SERVER}/view"
        params = {"filename": filename, "subfolder": subfolder, "type": type}
        
        # logger.info(f"⬇️ 正在下载图片: {filename}")
        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                return await response.read()
            
            logger.error(f"❌ 图片下载失败 HTTP {response.status}: {filename}")
            raise HTTPException(status_code=404, detail=f"图像下载失败: {response.status}")

    async def upload_image(self, image_data: bytes, filename: str) -> str:
        """上传图片到ComfyUI服务器"""
        url = f"{COMFYUI_SERVER}/upload/image"
        
        data = aiohttp.FormData()
        data.add_field('image', image_data, filename=filename, content_type='image/jpeg')
        data.add_field('overwrite', 'true')
        
        async with self.session.post(url, data=data) as response:
            if response.status == 200:
                result = await response.json()
                return result.get('name', filename)
            raise Exception(f"ComfyUI图片上传失败: {response.status}")
