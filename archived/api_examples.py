#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ComfyUI批量生图API使用示例
演示如何使用API进行批量图像生成

作者: AI助手
版本: 1.0
"""

import requests
import json
import time
import asyncio
import websockets
from typing import List, Dict

# API服务器地址
API_SERVER = "http://localhost:8000"

class ComfyUIBatchClient:
    """ComfyUI批量生图客户端"""
    
    def __init__(self, api_server: str = API_SERVER):
        self.api_server = api_server.rstrip('/')
    
    def submit_single_task(self, prompt: str, **kwargs) -> str:
        """提交单个生成任务"""
        data = {
            "prompt": prompt,
            "negative_prompt": kwargs.get("negative_prompt", ""),
            "width": kwargs.get("width", 960),
            "height": kwargs.get("height", 544),
            "steps": kwargs.get("steps", 30),
            "cfg": kwargs.get("cfg", 1.0),
            "seed": kwargs.get("seed"),
            "batch_name": kwargs.get("batch_name")
        }
        
        response = requests.post(f"{self.api_server}/generate", json=data)
        response.raise_for_status()
        
        result = response.json()
        return result["task_id"]
    
    def submit_batch_tasks(self, prompts: List[str], batch_name: str = None, **kwargs) -> List[str]:
        """提交批量生成任务"""
        requests_data = []
        
        for prompt in prompts:
            request_data = {
                "prompt": prompt,
                "negative_prompt": kwargs.get("negative_prompt", ""),
                "width": kwargs.get("width", 960),
                "height": kwargs.get("height", 544),
                "steps": kwargs.get("steps", 30),
                "cfg": kwargs.get("cfg", 1.0),
                "seed": kwargs.get("seed")
            }
            requests_data.append(request_data)
        
        batch_data = {
            "requests": requests_data,
            "batch_name": batch_name or f"batch_{int(time.time())}"
        }
        
        response = requests.post(f"{self.api_server}/batch", json=batch_data)
        response.raise_for_status()
        
        result = response.json()
        return result["task_ids"]
    
    def get_task_status(self, task_id: str) -> Dict:
        """获取任务状态"""
        response = requests.get(f"{self.api_server}/status/{task_id}")
        response.raise_for_status()
        return response.json()
    
    def get_all_tasks(self) -> List[Dict]:
        """获取所有任务"""
        response = requests.get(f"{self.api_server}/tasks")
        response.raise_for_status()
        return response.json()["tasks"]
    
    def wait_for_task(self, task_id: str, timeout: int = 300) -> Dict:
        """等待任务完成"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_task_status(task_id)
            
            if status["status"] in ["completed", "failed"]:
                return status
            
            print(f"任务 {task_id[:8]} - {status['status']}: {status['progress']:.1f}% - {status['message']}")
            time.sleep(2)
        
        raise TimeoutError(f"任务 {task_id} 超时")
    
    def wait_for_batch(self, task_ids: List[str], timeout: int = 600) -> List[Dict]:
        """等待批量任务完成"""
        results = []
        
        for task_id in task_ids:
            try:
                result = self.wait_for_task(task_id, timeout)
                results.append(result)
            except TimeoutError as e:
                print(f"警告: {e}")
                results.append({"task_id": task_id, "status": "timeout", "error": str(e)})
        
        return results
    
    async def monitor_tasks_realtime(self, task_ids: List[str]):
        """实时监控任务进度（WebSocket）"""
        ws_url = self.api_server.replace("http", "ws") + "/ws"
        
        try:
            async with websockets.connect(ws_url) as websocket:
                print("✅ WebSocket连接成功，开始实时监控...")
                
                completed_tasks = set()
                
                while len(completed_tasks) < len(task_ids):
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        data = json.loads(message)
                        
                        if data["type"] == "task_update":
                            task_data = data["data"]
                            task_id = task_data["task_id"]
                            
                            if task_id in task_ids:
                                print(f"📊 任务更新 {task_id[:8]}: {task_data['status']} - {task_data['progress']:.1f}% - {task_data['message']}")
                                
                                if task_data["status"] in ["completed", "failed"]:
                                    completed_tasks.add(task_id)
                                    
                                    if task_data["status"] == "completed" and task_data["result_url"]:
                                        print(f"🎉 任务完成: {self.api_server}{task_data['result_url']}")
                                    elif task_data["status"] == "failed":
                                        print(f"❌ 任务失败: {task_data.get('error', '未知错误')}")
                    
                    except asyncio.TimeoutError:
                        # 检查任务状态
                        for task_id in task_ids:
                            if task_id not in completed_tasks:
                                status = self.get_task_status(task_id)
                                if status["status"] in ["completed", "failed"]:
                                    completed_tasks.add(task_id)
                
                print("✅ 所有任务监控完成")
                
        except Exception as e:
            print(f"❌ WebSocket连接失败: {e}")
            print("🔄 回退到轮询模式...")
            return self.wait_for_batch(task_ids)

def example_single_generation():
    """示例1: 单个图像生成"""
    print("🎯 示例1: 单个图像生成")
    print("-" * 40)
    
    client = ComfyUIBatchClient()
    
    # 提交任务
    task_id = client.submit_single_task(
        prompt="A cute cat sitting on a windowsill, warm sunlight, cartoon style",
        negative_prompt="ugly, blurry, low quality",
        width=1024,
        height=1024,
        steps=25,
        cfg=7.0
    )
    
    print(f"✅ 任务已提交: {task_id}")
    
    # 等待完成
    result = client.wait_for_task(task_id)
    
    if result["status"] == "completed":
        print(f"🎉 生成成功: http://localhost:8000{result['result_url']}")
    else:
        print(f"❌ 生成失败: {result.get('error', '未知错误')}")

def example_batch_generation():
    """示例2: 批量图像生成"""
    print("\n🎯 示例2: 批量图像生成")
    print("-" * 40)
    
    client = ComfyUIBatchClient()
    
    # 准备批量提示词
    prompts = [
        "A cute cat playing in a garden, sunny day",
        "A little girl flying a kite in the park, blue sky",
        "A red car driving on a mountain road, scenic view",
        "A cozy coffee shop interior, warm lighting",
        "A peaceful lake surrounded by mountains, sunset"
    ]
    
    # 提交批量任务
    task_ids = client.submit_batch_tasks(
        prompts,
        batch_name="example_batch",
        width=960,
        height=544,
        steps=30
    )
    
    print(f"✅ 批量任务已提交: {len(task_ids)} 个任务")
    
    # 等待所有任务完成
    results = client.wait_for_batch(task_ids)
    
    # 统计结果
    completed = len([r for r in results if r["status"] == "completed"])
    failed = len([r for r in results if r["status"] == "failed"])
    
    print(f"\n📊 批量生成结果:")
    print(f"   ✅ 成功: {completed}")
    print(f"   ❌ 失败: {failed}")
    
    # 显示成功的结果
    for result in results:
        if result["status"] == "completed":
            print(f"   🖼️  {result['task_id'][:8]}: http://localhost:8000{result['result_url']}")

async def example_realtime_monitoring():
    """示例3: 实时监控（WebSocket）"""
    print("\n🎯 示例3: 实时监控")
    print("-" * 40)
    
    client = ComfyUIBatchClient()
    
    # 提交一些任务
    prompts = [
        "A magical forest with glowing mushrooms",
        "A futuristic city skyline at night",
        "A vintage train station in the countryside"
    ]
    
    task_ids = client.submit_batch_tasks(prompts, batch_name="realtime_demo")
    print(f"✅ 已提交 {len(task_ids)} 个任务")
    
    # 实时监控
    await client.monitor_tasks_realtime(task_ids)

def example_api_integration():
    """示例4: API集成到现有系统"""
    print("\n🎯 示例4: API集成示例")
    print("-" * 40)
    
    client = ComfyUIBatchClient()
    
    # 模拟用户数据
    user_requests = [
        {
            "user_id": "user_001",
            "description": "为我的咖啡店生成Logo",
            "prompt": "A modern coffee shop logo, minimalist design, warm colors",
            "requirements": {"width": 512, "height": 512, "steps": 40}
        },
        {
            "user_id": "user_002", 
            "description": "儿童绘本插图",
            "prompt": "A friendly dragon reading a book to forest animals, children's book illustration",
            "requirements": {"width": 1024, "height": 768, "steps": 35}
        }
    ]
    
    # 处理用户请求
    user_tasks = {}
    
    for request in user_requests:
        print(f"📝 处理用户 {request['user_id']} 的请求: {request['description']}")
        
        task_id = client.submit_single_task(
            prompt=request["prompt"],
            batch_name=f"user_{request['user_id']}",
            **request["requirements"]
        )
        
        user_tasks[request["user_id"]] = {
            "task_id": task_id,
            "description": request["description"]
        }
    
    # 等待并处理结果
    for user_id, task_info in user_tasks.items():
        result = client.wait_for_task(task_info["task_id"])
        
        if result["status"] == "completed":
            print(f"✅ 用户 {user_id} 的任务完成: {task_info['description']}")
            print(f"   📁 结果: http://localhost:8000{result['result_url']}")
            
            # 这里可以集成到你的系统中：
            # - 发送邮件通知用户
            # - 更新数据库记录
            # - 调用其他服务处理结果
            
        else:
            print(f"❌ 用户 {user_id} 的任务失败: {result.get('error', '未知错误')}")

def check_api_health():
    """检查API服务健康状态"""
    try:
        response = requests.get(f"{API_SERVER}/health")
        response.raise_for_status()
        
        health = response.json()
        print("🏥 API服务健康检查:")
        print(f"   API服务器: {health['api_server']}")
        print(f"   ComfyUI服务器: {health['comfyui_server']}")
        print(f"   活跃任务: {health['active_tasks']}")
        
        if health['comfyui_server'] == 'offline':
            print("⚠️  警告: ComfyUI服务器离线，请检查连接")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ API服务不可用: {e}")
        return False

def main():
    """主函数 - 运行所有示例"""
    print("🚀 ComfyUI批量生图API使用示例")
    print("=" * 50)
    
    # 检查服务状态
    if not check_api_health():
        print("\n💡 请确保API服务器正在运行:")
        print("   python comfyui_api_server.py")
        return
    
    try:
        # 运行示例
        example_single_generation()
        example_batch_generation()
        
        # 实时监控示例（需要asyncio）
        print("\n🔄 启动实时监控示例...")
        asyncio.run(example_realtime_monitoring())
        
        example_api_integration()
        
        print("\n🎉 所有示例运行完成！")
        print("💡 访问 http://localhost:8000/docs 查看完整API文档")
        
    except KeyboardInterrupt:
        print("\n👋 用户中断，示例结束")
    except Exception as e:
        print(f"\n❌ 示例运行出错: {e}")

if __name__ == "__main__":
    main()
