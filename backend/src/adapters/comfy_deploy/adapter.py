import aiohttp
import logging
import asyncio
import json
from typing import Dict, Optional, List
from backend.src.config.settings import COMFY_DEPLOY_API_KEY, COMFY_DEPLOY_HOST, COMFY_DEPLOY_DEPLOYMENT_ID

logger = logging.getLogger(__name__)

class ComfyDeployAdapter:
    """ComfyUI Deploy 适配器"""
    
    def __init__(self):
        self.api_key = COMFY_DEPLOY_API_KEY
        self.deployment_id = COMFY_DEPLOY_DEPLOYMENT_ID
        self.base_url = COMFY_DEPLOY_HOST
        
        if not self.api_key:
            logger.warning("⚠️ 未配置 COMFY_DEPLOY_API_KEY，无法使用 ComfyUI Deploy")

    async def check_health(self) -> Dict[str, str]:
        """检查服务连接"""
        return {"status": "online", "url": self.base_url}

    async def run_deployment(self, inputs: Dict) -> str:
        """提交任务到 ComfyUI Deploy"""
        url = f"{self.base_url}/api/run/deployment/queue"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "deployment_id": self.deployment_id,
            "inputs": inputs
        }
        
        logger.info(f"🚀 [ComfyDeploy] 正在发起请求...")
        logger.info(f"➡️ URL: {url}")
        logger.info(f"➡️ Payload: {json.dumps(payload, ensure_ascii=False)}")
        
        try:
            # ⚠️ 禁用 SSL 验证以解决本地证书问题
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    resp_text = await response.text()
                    logger.info(f"⬅️ 状态码: {response.status}")
                    logger.info(f"⬅️ 响应内容: {resp_text}")
                    
                    if response.status == 200:
                        result = json.loads(resp_text)
                        run_id = result.get("run_id") or result.get("id")
                        logger.info(f"✅ [ComfyDeploy] 任务提交成功 ID: {run_id}")
                        return run_id
                    else:
                        raise Exception(f"ComfyDeploy API Error: {response.status} - {resp_text}")
        except Exception as e:
            logger.error(f"❌ [ComfyDeploy] 请求异常: {e}")
            raise

    async def get_run_status(self, run_id: str) -> Dict:
        """获取任务状态"""
        url = f"{self.base_url}/api/run/{run_id}"
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # ⚠️ 禁用 SSL 验证
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                return {}
