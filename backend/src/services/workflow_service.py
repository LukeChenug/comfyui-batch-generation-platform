import json
import logging
import time
from pathlib import Path
from typing import Dict, Optional
from backend.src.types import GenerationRequest

logger = logging.getLogger(__name__)

class WorkflowService:
    @staticmethod
    def load_from_json(json_path: str) -> Optional[Dict]:
        """从JSON文件加载工作流模板"""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                workflow = json.load(f)
            logger.info(f"✅ 成功加载工作流模板: {json_path}")
            return workflow
        except Exception as e:
            logger.warning(f"⚠️ 加载工作流文件失败: {json_path}, 错误: {e}")
            return None

    @staticmethod
    def create_workflow(request: GenerationRequest) -> Dict:
        """根据请求创建ComfyUI工作流"""
        seed = request.seed if request.seed else int(time.time() * 1000000) % 1000000000
        
        if not request.input_image:
            return WorkflowService.create_text_to_image(request, seed)
        else:
            # TODO: 迁移图生图逻辑
            return WorkflowService.create_image_to_image(request, seed)

    @staticmethod
    def create_text_to_image(request: GenerationRequest, seed: int) -> Dict:
        """创建文生图工作流"""
        # 尝试加载JSON模板
        json_path = Path("Qwen-Image 文生图（API）.json")
        workflow = WorkflowService.load_from_json(str(json_path))
        
        if not workflow:
            # 简单的硬编码回退
            logger.error("❌ 无法加载文生图工作流模板")
            raise FileNotFoundError("Missing Qwen-Image workflow template")

        # 更新动态参数
        # KSampler (节点3)
        if "3" in workflow:
            inputs = workflow["3"]["inputs"]
            inputs["seed"] = seed
            inputs["steps"] = request.steps
            inputs["cfg"] = request.cfg

        # 正向提示词 (节点6)
        if "6" in workflow:
            workflow["6"]["inputs"]["text"] = request.prompt

        # 负向提示词 (节点7)
        if "7" in workflow:
            neg = request.negative_prompt or "变形脸，奇怪五官，夸张动漫，大头，塑料皮肤，3D渲染，超现实主义皮肤，恐怖眼神，低质量，畸形，额外的手，额外的手指，奇怪光影，避免高饱和亮色，避免塑料感的鲜艳颜色"
            workflow["7"]["inputs"]["text"] = neg

        # 空Latent (节点58)
        if "58" in workflow:
            inputs = workflow["58"]["inputs"]
            inputs["width"] = request.width
            inputs["height"] = request.height
            inputs["batch_size"] = request.batch_size

        # 确保有SaveImage节点 (节点60)
        if "60" not in workflow:
            logger.warning("⚠️ 添加缺失的SaveImage节点")
            workflow["60"] = {
                "inputs": {"filename_prefix": "ComfyUI", "images": ["8", 0]},
                "class_type": "SaveImage",
                "_meta": {"title": "保存图像"}
            }

        return workflow

    @staticmethod
    def create_image_to_image(request: GenerationRequest, seed: int) -> Dict:
        """创建图生图工作流 - 待实现完整迁移"""
        # 这里需要把原comfyui_api_server.py里的create_qwen_workflow逻辑搬过来
        # 为了MVP快速上线，暂时简化或保留占位
        logger.warning("图生图工作流尚未完全迁移")
        return {}

