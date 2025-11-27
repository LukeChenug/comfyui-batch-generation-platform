#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ComfyUI批量生图API服务器
企业级ComfyUI API封装，支持批量远程生图

功能特点：
- 🚀 批量任务处理
- 📊 实时进度监控  
- 🔄 任务队列管理
- 📁 自动文件管理
- 🔗 RESTful API接口
- ⚡ 异步高性能

作者: AI助手
版本: 1.0
"""

from fastapi import FastAPI, BackgroundTasks, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import asyncio
import aiohttp
import websockets
import json
import uuid
import time
import os
import shutil
from pathlib import Path
import logging
from datetime import datetime
import sqlite3
from contextlib import asynccontextmanager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 配置
COMFYUI_SERVER = "http://106.75.213.77:8188"
COMFYUI_WS = "ws://106.75.213.77:8188/ws"
OUTPUT_DIR = Path("./generated_images")
DB_PATH = "./tasks.db"

# 创建必要目录
OUTPUT_DIR.mkdir(exist_ok=True)

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

class TaskStatus(BaseModel):
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

class ComfyUIManager:
    """ComfyUI连接管理器"""
    
    def __init__(self):
        self.client_id = str(uuid.uuid4())
        self.session = None
        self.ws = None
        
    async def __aenter__(self):
        # 设置超时时间：连接超时30秒，读取超时300秒
        timeout = aiohttp.ClientTimeout(total=300, connect=30)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        if self.ws:
            await self.ws.close()
    
    async def submit_prompt(self, workflow: Dict) -> str:
        """提交工作流到ComfyUI（带重试机制）"""
        url = f"{COMFYUI_SERVER}/prompt"
        data = {
            "prompt": workflow,
            "client_id": self.client_id
        }
        
        # 验证工作流有输出节点（SaveImage）
        has_save_image = any(
            node.get("class_type") == "SaveImage" 
            for node in workflow.values() 
            if isinstance(node, dict)
        )
        if not has_save_image:
            logger.error("❌ 错误：工作流中没有SaveImage节点！")
            logger.error(f"   工作流节点: {list(workflow.keys())}")
            raise HTTPException(status_code=500, detail="工作流缺少输出节点（SaveImage）")
        
        # 确保工作流节点ID是字符串格式（ComfyUI要求）
        normalized_workflow = {}
        for node_id, node_data in workflow.items():
            normalized_workflow[str(node_id)] = node_data
        
        data = {
            "prompt": normalized_workflow,
            "client_id": self.client_id
        }
        
        logger.info(f"📡 提交工作流到ComfyUI: {url}")
        logger.info(f"   工作流节点数: {len(normalized_workflow)}")
        logger.info(f"   工作流节点ID: {list(normalized_workflow.keys())}")
        logger.info(f"   ✅ 工作流包含SaveImage输出节点")
        
        max_retries = 3
        for retry in range(max_retries):
            try:
                async with self.session.post(url, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        prompt_id = result.get("prompt_id")
                        logger.info(f"✅ ComfyUI工作流提交成功, prompt_id: {prompt_id}")
                        return prompt_id
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ 提交任务失败，状态码: {response.status}, 错误: {error_text}")
                        
                        # 如果是"no outputs"错误，记录工作流详情
                        if "no outputs" in error_text.lower() or "prompt_no_outputs" in error_text:
                            logger.error(f"❌ 工作流缺少输出节点！")
                            logger.error(f"   工作流节点: {list(workflow.keys())}")
                            # 检查SaveImage节点
                            save_nodes = [k for k, v in workflow.items() if isinstance(v, dict) and v.get("class_type") == "SaveImage"]
                            logger.error(f"   SaveImage节点: {save_nodes}")
                            # 记录工作流结构（前500字符）
                            workflow_str = json.dumps(workflow, indent=2, ensure_ascii=False)
                            logger.error(f"   工作流内容（前1000字符）:\n{workflow_str[:1000]}")
                        
                        if retry < max_retries - 1:
                            await asyncio.sleep(2)
                            continue
                        raise HTTPException(status_code=500, detail=f"ComfyUI提交失败: {response.status}, {error_text[:500]}")
            except asyncio.TimeoutError:
                logger.warning(f"⏰ 提交任务超时，重试 {retry+1}/{max_retries}")
                if retry < max_retries - 1:
                    await asyncio.sleep(2)
                    continue
                raise HTTPException(status_code=500, detail="ComfyUI提交超时")
            except aiohttp.ClientError as e:
                logger.error(f"🔌 连接错误: {e}, 重试 {retry+1}/{max_retries}")
                if retry < max_retries - 1:
                    await asyncio.sleep(2)
                    continue
                raise HTTPException(status_code=500, detail=f"ComfyUI连接失败: {str(e)}")
            except Exception as e:
                if retry < max_retries - 1:
                    logger.warning(f"⚠️ 提交任务异常: {e}, 重试 {retry+1}/{max_retries}")
                    await asyncio.sleep(2)
                    continue
                logger.error(f"❌ 提交任务最终失败: {e}")
                raise
    
    async def get_history(self, prompt_id: str) -> Dict:
        """获取任务历史（带重试机制）"""
        url = f"{COMFYUI_SERVER}/history/{prompt_id}"
        
        max_retries = 3
        for retry in range(max_retries):
            try:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        # 任务还未完成，返回空字典
                        return {}
                    else:
                        logger.warning(f"获取历史失败，状态码: {response.status}, 重试 {retry+1}/{max_retries}")
                        if retry < max_retries - 1:
                            await asyncio.sleep(1)  # 等待1秒后重试
                            continue
                        return {}
            except asyncio.TimeoutError:
                logger.warning(f"获取历史超时，重试 {retry+1}/{max_retries}")
                if retry < max_retries - 1:
                    await asyncio.sleep(1)
                    continue
                return {}
            except Exception as e:
                logger.error(f"获取历史异常: {e}, 重试 {retry+1}/{max_retries}")
                if retry < max_retries - 1:
                    await asyncio.sleep(1)
                    continue
                return {}
        
        return {}
    
    async def download_image(self, filename: str, subfolder: str = "", type: str = "output") -> bytes:
        """下载生成的图像（带重试机制）"""
        url = f"{COMFYUI_SERVER}/view"
        params = {
            "filename": filename,
            "subfolder": subfolder,
            "type": type
        }
        
        max_retries = 3
        for retry in range(max_retries):
            try:
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.read()
                    else:
                        logger.warning(f"下载图像失败，状态码: {response.status}, 重试 {retry+1}/{max_retries}")
                        if retry < max_retries - 1:
                            await asyncio.sleep(1)
                            continue
                        raise HTTPException(status_code=404, detail=f"图像下载失败: {response.status}")
            except asyncio.TimeoutError:
                logger.warning(f"下载图像超时，重试 {retry+1}/{max_retries}")
                if retry < max_retries - 1:
                    await asyncio.sleep(1)
                    continue
                raise HTTPException(status_code=504, detail="图像下载超时")
            except Exception as e:
                if retry < max_retries - 1:
                    logger.warning(f"下载图像异常: {e}, 重试 {retry+1}/{max_retries}")
                    await asyncio.sleep(1)
                    continue
                raise
    
    async def upload_image_to_comfyui(self, image_data: bytes, filename: str) -> str:
        """上传图片到ComfyUI服务器"""
        url = f"{COMFYUI_SERVER}/upload/image"
        
        # 创建FormData
        data = aiohttp.FormData()
        data.add_field('image', image_data, filename=filename, content_type='image/jpeg')
        data.add_field('overwrite', 'true')
        
        try:
            async with self.session.post(url, data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"✅ 图片上传到ComfyUI成功: {result}")
                    return result.get('name', filename)
                else:
                    logger.error(f"❌ ComfyUI图片上传失败: {response.status}")
                    raise Exception(f"ComfyUI图片上传失败: {response.status}")
        except Exception as e:
            logger.error(f"❌ ComfyUI图片上传异常: {e}")
            raise e

class TaskManager:
    """任务管理器"""
    
    def __init__(self):
        self.init_database()
        self.active_tasks: Dict[str, TaskStatus] = {}
        self.websocket_connections: List[WebSocket] = []
        self.load_tasks_from_database()  # 启动时加载数据库中的任务
    
    def init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                progress REAL DEFAULT 0,
                message TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                completed_at TEXT,
                result_url TEXT,
                result_urls TEXT,
                error TEXT,
                request_data TEXT,
                batch_name TEXT
            )
        ''')
        
        # 检查并添加result_urls字段（数据库迁移）
        try:
            cursor.execute("SELECT result_urls FROM tasks LIMIT 1")
        except sqlite3.OperationalError:
            # 字段不存在，添加它
            cursor.execute("ALTER TABLE tasks ADD COLUMN result_urls TEXT")
            conn.commit()
            logger.info("已添加result_urls字段到数据库")
        
        conn.commit()
        conn.close()
    
    def load_tasks_from_database(self):
        """从数据库加载所有任务到内存"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT task_id, status, progress, message, created_at, completed_at, 
                   result_url, result_urls, error, request_data
            FROM tasks
            ORDER BY created_at DESC
            LIMIT 100  -- 只加载最近100个任务避免内存过载
        ''')
        
        for row in cursor.fetchall():
            task_id, status, progress, message, created_at, completed_at, result_url, result_urls_json, error, request_data_json = row
            
            # 解析result_urls JSON
            result_urls = None
            if result_urls_json:
                try:
                    result_urls = json.loads(result_urls_json)
                except json.JSONDecodeError:
                    logger.warning(f"无法解析任务 {task_id} 的result_urls JSON: {result_urls_json}")
            
            # 解析request_data JSON
            request_data = None
            if request_data_json:
                try:
                    request_data = json.loads(request_data_json)
                except json.JSONDecodeError:
                    logger.warning(f"无法解析任务 {task_id} 的request_data JSON: {request_data_json}")
            
            # 创建TaskStatus对象
            task = TaskStatus(
                task_id=task_id,
                status=status,
                progress=progress,
                message=message or "",
                created_at=created_at,
                completed_at=completed_at,
                result_url=result_url,
                result_urls=result_urls,
                error=error,
                request_data=request_data
            )
            
            self.active_tasks[task_id] = task
        
        conn.close()
        logger.info(f"从数据库加载了 {len(self.active_tasks)} 个任务")
    
    def create_task(self, request_data: Dict, batch_name: Optional[str] = None) -> str:
        """创建新任务"""
        task_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        task = TaskStatus(
            task_id=task_id,
            status="pending",
            progress=0,
            message="任务已创建",
            created_at=now
        )
        
        self.active_tasks[task_id] = task
        
        # 保存到数据库
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO tasks (task_id, status, progress, message, created_at, request_data, batch_name)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (task_id, "pending", 0, "任务已创建", now, json.dumps(request_data), batch_name))
        
        conn.commit()
        conn.close()
        
        return task_id
    
    def update_task(self, task_id: str, status: Optional[str] = None, 
                   progress: Optional[float] = None, message: Optional[str] = None,
                   result_url: Optional[str] = None, result_urls: Optional[List[str]] = None,
                   error: Optional[str] = None):
        """更新任务状态"""
        if task_id not in self.active_tasks:
            return
        
        task = self.active_tasks[task_id]
        
        if status:
            task.status = status
        if progress is not None:
            task.progress = progress
        if message:
            task.message = message
        if result_url:
            task.result_url = result_url
        if result_urls:
            task.result_urls = result_urls
        if error:
            task.error = error
        
        if status in ["completed", "failed"]:
            task.completed_at = datetime.now().isoformat()
        
        # 更新数据库
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 将result_urls转换为JSON字符串存储
        result_urls_json = json.dumps(task.result_urls) if task.result_urls else None
        
        cursor.execute('''
            UPDATE tasks SET status=?, progress=?, message=?, completed_at=?, result_url=?, error=?, result_urls=?
            WHERE task_id=?
        ''', (task.status, task.progress, task.message, task.completed_at, 
              task.result_url, task.error, result_urls_json, task_id))
        
        conn.commit()
        conn.close()
        
        # 通知WebSocket客户端
        asyncio.create_task(self.broadcast_update(task))
    
    async def broadcast_update(self, task: TaskStatus):
        """广播任务更新"""
        if not self.websocket_connections:
            return
        
        message = {
            "type": "task_update",
            "data": task.dict()
        }
        
        disconnected = []
        for ws in self.websocket_connections:
            try:
                await ws.send_text(json.dumps(message))
            except:
                disconnected.append(ws)
        
        # 移除断开的连接
        for ws in disconnected:
            self.websocket_connections.remove(ws)
    
    def get_task(self, task_id: str) -> Optional[TaskStatus]:
        """获取任务状态（先从内存查找，找不到则从数据库查询）"""
        # 先从内存中查找
        if task_id in self.active_tasks:
            return self.active_tasks[task_id]
        
        # 如果内存中没有，从数据库查询
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT task_id, status, progress, message, created_at, completed_at, 
                   result_url, result_urls, error, request_data
            FROM tasks
            WHERE task_id = ?
        ''', (task_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        # 解析数据
        task_id_db, status, progress, message, created_at, completed_at, result_url, result_urls_json, error, request_data_json = row
        
        # 解析result_urls JSON
        result_urls = None
        if result_urls_json:
            try:
                result_urls = json.loads(result_urls_json)
            except json.JSONDecodeError:
                logger.warning(f"无法解析任务 {task_id} 的result_urls JSON: {result_urls_json}")
        
        # 解析request_data JSON
        request_data = None
        if request_data_json:
            try:
                request_data = json.loads(request_data_json)
            except json.JSONDecodeError:
                logger.warning(f"无法解析任务 {task_id} 的request_data JSON: {request_data_json}")
        
        # 创建TaskStatus对象
        task = TaskStatus(
            task_id=task_id_db,
            status=status,
            progress=progress,
            message=message or "",
            created_at=created_at,
            completed_at=completed_at,
            result_url=result_url,
            result_urls=result_urls,
            error=error,
            request_data=request_data
        )
        
        # 将任务加载到内存中（如果状态是进行中）
        if status in ["pending", "running", "generating"]:
            self.active_tasks[task_id] = task
        
        return task
    
    def get_all_tasks(self) -> List[TaskStatus]:
        """获取所有任务"""
        return list(self.active_tasks.values())

def create_workflow(request: GenerationRequest) -> Dict:
    """根据请求创建ComfyUI工作流（自适应FLUX/Qwen）"""
    seed = request.seed if request.seed else int(time.time() * 1000000) % 1000000000
    
    # 如果没有输入图片，使用Qwen文生图工作流
    if not request.input_image:
        return create_qwen_text_to_image_workflow(request, seed)
    else:
        return create_qwen_workflow(request, seed)

def load_workflow_from_json(json_path: str) -> Optional[Dict]:
    """从JSON文件加载工作流模板"""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            workflow = json.load(f)
        logger.info(f"✅ 成功加载工作流模板: {json_path}")
        return workflow
    except FileNotFoundError:
        logger.warning(f"⚠️ 工作流文件不存在: {json_path}，使用默认硬编码工作流")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON解析失败: {json_path}, 错误: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ 加载工作流文件失败: {json_path}, 错误: {e}")
        return None

def create_qwen_text_to_image_workflow(request: GenerationRequest, seed: int) -> Dict:
    """创建Qwen文生图工作流（优先从JSON文件加载，失败则使用硬编码）"""
    # 尝试从JSON文件加载工作流模板
    json_path = Path("Qwen-Image 文生图（API）.json")
    workflow = load_workflow_from_json(json_path)
    
    # 如果加载失败，使用硬编码的工作流
    if workflow is None:
        logger.info("使用硬编码的Qwen文生图工作流")
        workflow = {
            "3": {
                "inputs": {
                    "seed": seed,
                    "steps": request.steps,
                    "cfg": request.cfg,
                    "sampler_name": "euler_cfg_pp",
                    "scheduler": "sgm_uniform",
                    "denoise": 1,
                    "model": ["66", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["58", 0]
                },
                "class_type": "KSampler",
                "_meta": {"title": "K采样器"}
            },
            "6": {
                "inputs": {
                    "text": request.prompt,
                    "clip": ["38", 0]
                },
                "class_type": "CLIPTextEncode",
                "_meta": {"title": "CLIP Text Encode (Positive Prompt)"}
            },
            "7": {
                "inputs": {
                    "text": request.negative_prompt or "变形脸，奇怪五官，夸张动漫，大头，塑料皮肤，3D渲染，超现实主义皮肤，恐怖眼神，低质量，畸形，额外的手，额外的手指，奇怪光影，避免高饱和亮色，避免塑料感的鲜艳颜色",
                    "clip": ["38", 0]
                },
                "class_type": "CLIPTextEncode",
                "_meta": {"title": "CLIP Text Encode (Negative Prompt)"}
            },
            "8": {
                "inputs": {
                    "samples": ["3", 0],
                    "vae": ["39", 0]
                },
                "class_type": "VAEDecode",
                "_meta": {"title": "VAE解码"}
            },
            "37": {
                "inputs": {
                    "unet_name": "Qwen-Image_ComfyUI/qwen_image_bf16.safetensors",
                    "weight_dtype": "default"
                },
                "class_type": "UNETLoader",
                "_meta": {"title": "UNet加载器"}
            },
            "38": {
                "inputs": {
                    "clip_name": "qwen_2.5_vl_7b_fp8_scaled.safetensors",
                    "type": "qwen_image",
                    "device": "default"
                },
                "class_type": "CLIPLoader",
                "_meta": {"title": "加载CLIP"}
            },
            "39": {
                "inputs": {
                    "vae_name": "qwen_image_vae.safetensors"
                },
                "class_type": "VAELoader",
                "_meta": {"title": "加载VAE"}
            },
            "58": {
                "inputs": {
                    "width": request.width,
                    "height": request.height,
                    "batch_size": request.batch_size
                },
                "class_type": "EmptySD3LatentImage",
                "_meta": {"title": "空Latent图像（SD3）"}
            },
            "60": {
                "inputs": {
                    "filename_prefix": "ComfyUI",
                    "images": ["8", 0]
                },
                "class_type": "SaveImage",
                "_meta": {"title": "保存图像"}
            },
            "66": {
                "inputs": {
                    "shift": 3,
                    "model": ["73", 0]
                },
                "class_type": "ModelSamplingAuraFlow",
                "_meta": {"title": "采样算法（AuraFlow）"}
            },
            "73": {
                "inputs": {
                    "lora_name": "Qwen-Image-Lightning/Qwen-Image-Lightning-8steps-V1.0.safetensors",
                    "strength_model": 1,
                    "model": ["37", 0]
                },
                "class_type": "LoraLoaderModelOnly",
                "_meta": {"title": "LoRA加载器（仅模型）"}
            }
        }
    
    # 更新工作流中的动态参数
    # 更新K采样器参数（节点3）
    if "3" in workflow and "inputs" in workflow["3"]:
        workflow["3"]["inputs"]["seed"] = seed
        workflow["3"]["inputs"]["steps"] = request.steps
        workflow["3"]["inputs"]["cfg"] = request.cfg
    
    # 更新正提示词（节点6）
    if "6" in workflow and "inputs" in workflow["6"]:
        workflow["6"]["inputs"]["text"] = request.prompt
    
    # 更新负提示词（节点7）
    if "7" in workflow and "inputs" in workflow["7"]:
        workflow["7"]["inputs"]["text"] = request.negative_prompt or "变形脸，奇怪五官，夸张动漫，大头，塑料皮肤，3D渲染，超现实主义皮肤，恐怖眼神，低质量，畸形，额外的手，额外的手指，奇怪光影，避免高饱和亮色，避免塑料感的鲜艳颜色"
    
    # 更新图像尺寸和批次大小（节点58）
    if "58" in workflow and "inputs" in workflow["58"]:
        workflow["58"]["inputs"]["width"] = request.width
        workflow["58"]["inputs"]["height"] = request.height
        workflow["58"]["inputs"]["batch_size"] = request.batch_size
    
    # 验证工作流有输出节点（SaveImage）
    has_output = False
    for node_id, node_data in workflow.items():
        if isinstance(node_data, dict) and node_data.get("class_type") == "SaveImage":
            has_output = True
            logger.debug(f"✅ 找到输出节点: {node_id} (SaveImage)")
            break
    
    if not has_output:
        logger.error("❌ 警告：工作流中没有找到SaveImage输出节点！")
        # 确保节点60存在
        if "60" not in workflow:
            logger.error("❌ 节点60 (SaveImage) 不存在，添加默认输出节点")
            workflow["60"] = {
                "inputs": {
                    "filename_prefix": "ComfyUI",
                    "images": ["8", 0]
                },
                "class_type": "SaveImage",
                "_meta": {"title": "保存图像"}
            }
    
    logger.info(f"✅ Qwen文生图工作流已创建: seed={seed}, steps={request.steps}, cfg={request.cfg}, size={request.width}x{request.height}, batch={request.batch_size}, 节点数={len(workflow)}")
    return workflow

def create_flux_workflow(request: GenerationRequest, seed: int) -> Dict:
    """创建FLUX文生图工作流"""
    workflow = {
        "1": {
            "inputs": {
                "seed": seed,
                "steps": request.steps,
                "cfg": request.cfg,
                "sampler_name": "dpmpp_2m_sde",
                "scheduler": "simple", 
                "denoise": 1,
                "model": ["2", 0],
                "positive": ["13", 0],
                "negative": ["4", 0],
                "latent_image": ["5", 0]
            },
            "class_type": "KSampler",
            "_meta": {"title": "K采样器"}
        },
        "2": {
            "inputs": {
                "unet_name": "flux1-dev-fp8.safetensors",
                "weight_dtype": "fp8_e4m3fn"
            },
            "class_type": "UNETLoader",
            "_meta": {"title": "UNet加载器"}
        },
        "4": {
            "inputs": {
                "text": request.negative_prompt,
                "clip": ["9", 0]
            },
            "class_type": "CLIPTextEncode",
            "_meta": {"title": "CLIP文本编码"}
        },
        "5": {
            "inputs": {
                "width": request.width,
                "height": request.height,
                "batch_size": request.batch_size
            },
            "class_type": "EmptyLatentImage",
            "_meta": {"title": "空Latent图像"}
        },
        "6": {
            "inputs": {
                "samples": ["1", 0],
                "vae": ["7", 0]
            },
            "class_type": "VAEDecode",
            "_meta": {"title": "VAE解码"}
        },
        "7": {
            "inputs": {
                "vae_name": "ae.safetensors"
            },
            "class_type": "VAELoader",
            "_meta": {"title": "加载VAE"}
        },
        "8": {
            "inputs": {
                "images": ["6", 0]
            },
            "class_type": "PreviewImage",
            "_meta": {"title": "预览图像"}
        },
        "9": {
            "inputs": {
                "clip_name1": "clip_l.safetensors",
                "clip_name2": "t5xxl_fp8_e4m3fn.safetensors",
                "type": "flux",
                "device": "default"
            },
            "class_type": "DualCLIPLoader",
            "_meta": {"title": "双CLIP加载器"}
        },
        "13": {
            "inputs": {
                "text": request.prompt,
                "clip": ["9", 0]
            },
            "class_type": "CLIPTextEncode",
            "_meta": {"title": "CLIP文本编码"}
        }
    }
    return workflow

def create_qwen_workflow(request: GenerationRequest, seed: int) -> Dict:
    """创建Qwen图生图工作流"""
    input_image = request.input_image
    
    workflow = {
        "60": {
            "inputs": {
                "filename_prefix": "ComfyUI",
                "images": ["115:8", 0]
            },
            "class_type": "SaveImage",
            "_meta": {"title": "保存图像"}
        },
        "78": {
            "inputs": {
                "image": input_image
            },
            "class_type": "LoadImage",
            "_meta": {"title": "加载图像"}
        },
        "115:75": {
            "inputs": {
                "strength": 1,
                "model": ["115:66", 0]
            },
            "class_type": "CFGNorm",
            "_meta": {"title": "CFGNorm"}
        },
        "115:39": {
            "inputs": {
                "vae_name": "qwen_image_vae.safetensors"
            },
            "class_type": "VAELoader",
            "_meta": {"title": "加载VAE"}
        },
        "115:38": {
            "inputs": {
                "clip_name": "qwen_2.5_vl_7b_fp8_scaled.safetensors",
                "type": "qwen_image",
                "device": "default"
            },
            "class_type": "CLIPLoader",
            "_meta": {"title": "加载CLIP"}
        },
        "115:37": {
            "inputs": {
                "unet_name": "Qwen-Image-Edit_ComfyUI/qwen_image_edit_2509_fp8_e4m3fn.safetensors",
                "weight_dtype": "default"
            },
            "class_type": "UNETLoader",
            "_meta": {"title": "UNet加载器"}
        },
        "115:110": {
            "inputs": {
                "prompt": request.negative_prompt,
                "clip": ["115:38", 0],
                "vae": ["115:39", 0],
                "image1": ["115:93", 0]
            },
            "class_type": "TextEncodeQwenImageEditPlus",
            "_meta": {"title": "TextEncodeQwenImageEditPlus"}
        },
        "115:93": {
            "inputs": {
                "upscale_method": "lanczos",
                "megapixels": 1,
                "image": ["78", 0]
            },
            "class_type": "ImageScaleToTotalPixels",
            "_meta": {"title": "缩放图像（像素）"}
        },
        "115:66": {
            "inputs": {
                "shift": 3,
                "model": ["115:89", 0]
            },
            "class_type": "ModelSamplingAuraFlow",
            "_meta": {"title": "采样算法（AuraFlow）"}
        },
        "115:8": {
            "inputs": {
                "samples": ["115:3", 0],
                "vae": ["115:39", 0]
            },
            "class_type": "VAEDecode",
            "_meta": {"title": "VAE解码"}
        },
        "115:88": {
            "inputs": {
                "pixels": ["115:93", 0],
                "vae": ["115:39", 0]
            },
            "class_type": "VAEEncode",
            "_meta": {"title": "VAE编码"}
        },
        "115:112": {
            "inputs": {
                "width": request.width,
                "height": request.height,
                "batch_size": request.batch_size
            },
            "class_type": "EmptySD3LatentImage",
            "_meta": {"title": "空Latent图像（SD3）"}
        },
        "115:89": {
            "inputs": {
                "lora_name": "Qwen-Image-Lightning/Qwen-Image-Lightning-4steps-V1.0.safetensors",
                "strength_model": 1,
                "model": ["115:37", 0]
            },
            "class_type": "LoraLoaderModelOnly",
            "_meta": {"title": "LoRA加载器（仅模型）"}
        },
        "115:116": {
            "inputs": {
                "images": ["115:8", 0]
            },
            "class_type": "PreviewImage",
            "_meta": {"title": "预览图像"}
        },
        "115:111": {
            "inputs": {
                "prompt": request.prompt,
                "clip": ["115:38", 0],
                "vae": ["115:39", 0],
                "image1": ["115:93", 0]
            },
            "class_type": "TextEncodeQwenImageEditPlus",
            "_meta": {"title": "TextEncodeQwenImageEditPlus"}
        },
        "115:3": {
            "inputs": {
                "seed": seed,
                "steps": request.steps,
                "cfg": request.cfg,
                "sampler_name": "euler_cfg_pp",
                "scheduler": "sgm_uniform",
                "denoise": 0.8,
                "model": ["115:75", 0],
                "positive": ["115:111", 0],
                "negative": ["115:110", 0],
                "latent_image": ["115:112", 0]
            },
            "class_type": "KSampler",
            "_meta": {"title": "K采样器"}
        }
    }
    
    return workflow

async def process_single_task(task_id: str, request: GenerationRequest, task_manager: TaskManager):
    """处理单个生成任务"""
    try:
        task_manager.update_task(task_id, status="running", progress=5, message="准备输入数据...")
        
        # 调试日志：记录请求参数
        logger.info(f"🎯 任务 {task_id} - 请求参数: batch_size={request.batch_size}, 尺寸={request.width}x{request.height}, input_image={request.input_image}")
        
        # 如果有输入图片，先上传到ComfyUI服务器
        comfyui_image_name = None
        if request.input_image:
            task_manager.update_task(task_id, progress=10, message="上传图片到ComfyUI...")
            
            # 读取本地上传的图片文件
            local_image_path = Path("./uploaded_images") / request.input_image
            if local_image_path.exists():
                with open(local_image_path, "rb") as f:
                    image_data = f.read()
                
                async with ComfyUIManager() as comfy:
                    try:
                        comfyui_image_name = await comfy.upload_image_to_comfyui(image_data, request.input_image)
                        logger.info(f"✅ 任务 {task_id} - 图片已上传到ComfyUI: {comfyui_image_name}")
                        
                        # 更新request中的图片名称为ComfyUI中的名称
                        request.input_image = comfyui_image_name
                    except Exception as e:
                        logger.error(f"❌ 任务 {task_id} - ComfyUI图片上传失败: {e}")
                        task_manager.update_task(task_id, status="failed", error=f"图片上传失败: {str(e)}")
                        return
            else:
                logger.error(f"❌ 任务 {task_id} - 本地图片文件不存在: {local_image_path}")
                task_manager.update_task(task_id, status="failed", error="本地图片文件不存在")
                return
        
        task_manager.update_task(task_id, progress=15, message="创建工作流...")
        
        # 创建工作流
        workflow = create_workflow(request)
        
        # 调试日志：记录工作流关键节点
        workflow_type = "Qwen文生图" if not request.input_image else "Qwen图生图"
        batch_node = '58' if not request.input_image else '115:112'
        output_node = '60'  # 新工作流统一使用节点60作为SaveImage输出
        batch_size_in_workflow = workflow.get(batch_node, {}).get('inputs', {}).get('batch_size', 'N/A')
        
        logger.info(f"🔧 任务 {task_id} - 工作流类型: {workflow_type}")
        logger.info(f"🔧 任务 {task_id} - 请求参数 batch_size: {request.batch_size}")
        logger.info(f"🔧 任务 {task_id} - 批量节点({batch_node})的batch_size: {batch_size_in_workflow}")
        logger.info(f"🔧 任务 {task_id} - 输出节点: {output_node} (SaveImage)")
        
        # 验证 batch_size 是否正确设置
        if batch_size_in_workflow != request.batch_size:
            logger.warning(f"⚠️ 任务 {task_id} - batch_size 不匹配！请求: {request.batch_size}, 工作流: {batch_size_in_workflow}")
        
        async with ComfyUIManager() as comfy:
            task_manager.update_task(task_id, progress=25, message="提交任务到ComfyUI...")
            
            # 调试日志：记录工作流信息
            logger.info(f"📤 任务 {task_id} - 准备提交工作流到ComfyUI")
            logger.debug(f"   工作流节点数: {len(workflow)}")
            logger.debug(f"   工作流节点: {list(workflow.keys())[:5]}...")
            
            # 提交任务
            try:
                prompt_id = await comfy.submit_prompt(workflow)
                logger.info(f"✅ 任务 {task_id} - 工作流已提交到ComfyUI, prompt_id: {prompt_id}")
            except Exception as e:
                logger.error(f"❌ 任务 {task_id} - 提交工作流失败: {e}")
                logger.error(f"   工作流内容: {json.dumps(workflow, indent=2)[:500]}...")
                raise
            
            task_manager.update_task(task_id, progress=35, message="等待ComfyUI处理...")
            
            # 等待任务完成
            max_attempts = 150  # 5分钟超时
            consecutive_failures = 0
            max_consecutive_failures = 10  # 连续失败10次后报错
            
            for attempt in range(max_attempts):
                await asyncio.sleep(2)
                
                progress = 35 + (attempt / max_attempts) * 55  # 35% 到 90%
                task_manager.update_task(task_id, progress=progress, message="ComfyUI生成中...")
                
                try:
                    history = await comfy.get_history(prompt_id)
                    consecutive_failures = 0  # 重置连续失败计数
                except Exception as e:
                    consecutive_failures += 1
                    logger.warning(f"⚠️ 任务 {task_id} - 获取历史失败 ({consecutive_failures}/{max_consecutive_failures}): {e}")
                    
                    if consecutive_failures >= max_consecutive_failures:
                        logger.error(f"❌ 任务 {task_id} - 连续失败次数过多，可能连接已断开")
                        task_manager.update_task(task_id, status="failed", error=f"连接ComfyUI服务器失败: {str(e)}")
                        return
                    
                    # 继续尝试，但使用空历史
                    history = {}
                
                if prompt_id in history:
                    task_manager.update_task(task_id, progress=90, message="下载生成结果...")
                    
                    # 调试日志：记录ComfyUI返回的完整历史数据
                    logger.info(f"📋 任务 {task_id} - ComfyUI历史数据: {json.dumps(history[prompt_id], indent=2, ensure_ascii=False)}")
                    
                    # 获取生成的图像（支持多张）- 自适应不同工作流
                    outputs = history[prompt_id]["outputs"]
                    
                    # 尝试不同的输出节点
                    images = None
                    output_node = None
                    
                    if "60" in outputs and outputs["60"]["images"]:
                        # Qwen工作流SaveImage输出节点（新配置）
                        images = outputs["60"]["images"]
                        output_node = "60"
                    elif "8" in outputs and outputs["8"]["images"]:
                        # 兼容旧的Qwen文生图工作流输出节点
                        images = outputs["8"]["images"]
                        output_node = "8"
                    elif "115:116" in outputs and outputs["115:116"]["images"]:
                        # 兼容Qwen图生图工作流输出节点
                        images = outputs["115:116"]["images"]
                        output_node = "115:116"
                    
                    if images:
                        # 调试日志：记录图像数量和输出节点
                        logger.info(f"🖼️ 任务 {task_id} - 从节点{output_node}获取到 {len(images)} 张图片")
                        logger.info(f"🖼️ 任务 {task_id} - 请求的batch_size: {request.batch_size}, 实际生成: {len(images)} 张")
                        if len(images) != request.batch_size:
                            logger.warning(f"⚠️ 任务 {task_id} - 生成数量不匹配！请求: {request.batch_size} 张, 实际: {len(images)} 张")
                        
                        result_urls = []
                        
                        # 处理所有生成的图像
                        for i, image_info in enumerate(images):
                            # 下载图像
                            image_data = await comfy.download_image(
                                image_info["filename"], 
                                image_info.get("subfolder", ""),
                                image_info.get("type", "output")
                            )
                            
                            # 保存图像（添加序号区分）
                            base_name = image_info['filename'].rsplit('.', 1)[0]
                            extension = image_info['filename'].rsplit('.', 1)[1] if '.' in image_info['filename'] else 'png'
                            filename = f"{task_id}_{base_name}_{i+1:02d}.{extension}"
                            file_path = OUTPUT_DIR / filename
                            
                            with open(file_path, "wb") as f:
                                f.write(image_data)
                            
                            result_urls.append(f"/images/{filename}")
                        
                        # 调试日志：记录保存的图片URLs
                        logger.info(f"💾 任务 {task_id} - 保存了 {len(result_urls)} 个图片URL: {result_urls}")
                        
                        # 更新任务状态（包含所有图片URL）
                        task_manager.update_task(
                            task_id, 
                            status="completed", 
                            progress=100, 
                            message=f"生成完成 ({len(result_urls)}张图片)",
                            result_url=result_urls[0] if result_urls else None,
                            result_urls=result_urls  # 添加多图片支持
                        )
                        
                        # 调试日志：确认任务状态更新
                        logger.info(f"✅ 任务 {task_id} - 状态更新完成，多图URLs已保存")
                        return
                    else:
                        # 调试日志：显示所有可用的输出节点
                        available_nodes = list(outputs.keys())
                        logger.error(f"❌ 任务 {task_id} - 未找到图像输出节点，可用节点: {available_nodes}")
                        raise Exception(f"未找到生成的图像，可用节点: {available_nodes}")
            
            # 超时
            task_manager.update_task(task_id, status="failed", error="任务超时")
            
    except Exception as e:
        logger.error(f"任务 {task_id} 处理失败: {e}")
        task_manager.update_task(task_id, status="failed", error=str(e))

# 全局任务管理器
task_manager = TaskManager()

# 创建FastAPI应用
app = FastAPI(
    title="ComfyUI批量生图API",
    description="企业级ComfyUI API封装，支持批量远程生图",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务
app.mount("/images", StaticFiles(directory=str(OUTPUT_DIR)), name="images")

# 添加HTML文件服务
from fastapi.responses import FileResponse
import os

@app.get("/batch_generation_dashboard.html")
async def get_dashboard():
    """提供批量生图管理界面"""
    html_path = os.path.join(os.path.dirname(__file__), "batch_generation_dashboard.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    else:
        raise HTTPException(status_code=404, detail="Dashboard file not found")

@app.get("/")
async def root():
    """API根路径"""
    return {
        "message": "ComfyUI批量生图API服务",
        "version": "1.0.0",
        "endpoints": {
            "generate": "/generate - 单个图像生成",
            "batch": "/batch - 批量图像生成", 
            "status": "/status/{task_id} - 查询任务状态",
            "tasks": "/tasks - 获取所有任务",
            "ws": "/ws - WebSocket实时更新"
        }
    }

@app.post("/upload_image")
async def upload_image(file: UploadFile = File(...)):
    """上传图片文件"""
    try:
        # 检查文件类型
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="文件必须是图片格式")
        
        # 创建上传目录
        upload_dir = Path("./uploaded_images")
        upload_dir.mkdir(exist_ok=True)
        
        # 保存文件
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'png'
        saved_filename = f"{int(time.time() * 1000)}.{file_extension}"
        file_path = upload_dir / saved_filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {"filename": saved_filename, "path": str(file_path)}
        
    except Exception as e:
        logger.error(f"图片上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"图片上传失败: {str(e)}")

@app.post("/generate")
async def generate_single(request: GenerationRequest, background_tasks: BackgroundTasks):
    """单个图像生成"""
    task_id = task_manager.create_task(request.dict(), request.batch_name)
    
    # 后台处理任务
    background_tasks.add_task(process_single_task, task_id, request, task_manager)
    
    return {"task_id": task_id, "message": "任务已提交"}

@app.post("/batch")
async def generate_batch(batch_request: BatchRequest, background_tasks: BackgroundTasks):
    """批量图像生成"""
    task_ids = []
    batch_name = batch_request.batch_name or f"batch_{int(time.time())}"
    
    for request in batch_request.requests:
        request.batch_name = batch_name
        task_id = task_manager.create_task(request.dict(), batch_name)
        task_ids.append(task_id)
        
        # 后台处理任务
        background_tasks.add_task(process_single_task, task_id, request, task_manager)
        
        # 添加小延迟避免服务器压力过大
        await asyncio.sleep(0.1)
    
    return {
        "batch_name": batch_name,
        "task_ids": task_ids,
        "message": f"已提交 {len(task_ids)} 个任务"
    }

@app.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """获取任务状态"""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务未找到")
    
    return task

@app.get("/tasks")
async def get_all_tasks():
    """获取所有任务"""
    return {"tasks": task_manager.get_all_tasks()}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket实时更新"""
    await websocket.accept()
    task_manager.websocket_connections.append(websocket)
    
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        task_manager.websocket_connections.remove(websocket)

@app.get("/health")
async def health_check():
    """健康检查"""
    comfyui_status = "offline"
    comfyui_error = None
    
    try:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{COMFYUI_SERVER}/system_stats", timeout=aiohttp.ClientTimeout(total=10, connect=5)) as response:
                    if response.status == 200:
                        comfyui_status = "online"
                        # 尝试解析响应以确认服务器正常
                        try:
                            data = await response.json()
                            logger.debug(f"ComfyUI健康检查成功: {data.get('system', {}).get('comfyui_version', 'unknown')}")
                        except:
                            pass
                    else:
                        comfyui_status = "offline"
                        comfyui_error = f"HTTP {response.status}"
            except asyncio.TimeoutError:
                comfyui_status = "offline"
                comfyui_error = "连接超时（5秒）"
            except aiohttp.ClientConnectorError as e:
                comfyui_status = "offline"
                comfyui_error = f"连接失败: {str(e)}"
            except Exception as e:
                comfyui_status = "offline"
                comfyui_error = f"错误: {str(e)}"
    except Exception as e:
        comfyui_status = "offline"
        comfyui_error = f"异常: {str(e)}"
    
    result = {
        "api_server": "online",
        "comfyui_server": comfyui_status,
        "comfyui_url": COMFYUI_SERVER,
        "active_tasks": len(task_manager.active_tasks)
    }
    
    if comfyui_error:
        result["comfyui_error"] = comfyui_error
    
    return result

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 启动ComfyUI批量生图API服务器")
    print(f"📡 ComfyUI服务器: {COMFYUI_SERVER}")
    print(f"📁 图像输出目录: {OUTPUT_DIR}")
    print("🌐 API文档: http://localhost:8001/docs")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8001,
        log_level="info"
    )
