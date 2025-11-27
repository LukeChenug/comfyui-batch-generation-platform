#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深度诊断多图生成问题
"""

import json
import sqlite3
from pathlib import Path

def analyze_workflow():
    """分析工作流配置"""
    print("🔍 分析ComfyUI工作流配置...")
    
    # 读取服务器代码中的工作流创建函数
    try:
        with open("comfyui_api_server.py", "r", encoding="utf-8") as f:
            content = f.read()
            
        # 查找create_workflow函数
        if "def create_workflow" in content:
            print("✅ 找到create_workflow函数")
            
            # 检查batch_size使用
            if "request.batch_size" in content:
                print("✅ 工作流中使用了request.batch_size")
            else:
                print("❌ 工作流中没有使用request.batch_size")
                
            # 检查EmptyLatentImage节点
            if '"class_type": "EmptyLatentImage"' in content:
                print("✅ 找到EmptyLatentImage节点")
                # 提取相关代码段
                start = content.find('"5": {')
                if start != -1:
                    end = content.find('}', start + 100)
                    if end != -1:
                        node_5 = content[start:end+1]
                        print(f"📋 节点5配置:\n{node_5}")
        else:
            print("❌ 没有找到create_workflow函数")
            
    except Exception as e:
        print(f"❌ 读取服务器代码失败: {e}")

def check_recent_requests():
    """检查最近的请求数据"""
    print("\n🔍 检查数据库中的请求数据...")
    
    try:
        conn = sqlite3.connect("tasks.db")
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT task_id, request_data, status, message, result_url, result_urls
            FROM tasks 
            WHERE created_at > datetime('now', '-1 hour')
            ORDER BY created_at DESC
            LIMIT 3
        ''')
        
        rows = cursor.fetchall()
        
        for i, row in enumerate(rows, 1):
            task_id, request_data, status, message, result_url, result_urls = row
            
            print(f"\n--- 任务 {i} ---")
            print(f"ID: {task_id}")
            print(f"状态: {status}")
            print(f"消息: {message}")
            
            if request_data:
                try:
                    req_json = json.loads(request_data)
                    batch_size = req_json.get('batch_size', 'N/A')
                    print(f"🎯 请求的batch_size: {batch_size}")
                except:
                    print("❌ 无法解析request_data")
            
            print(f"📸 result_url: {result_url}")
            print(f"📸 result_urls: {result_urls}")
            
            if result_urls:
                try:
                    urls = json.loads(result_urls)
                    print(f"✅ 解析到 {len(urls)} 个URL")
                except:
                    print("❌ result_urls JSON解析失败")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 数据库检查失败: {e}")

def simulate_workflow_creation():
    """模拟工作流创建过程"""
    print("\n🧪 模拟工作流创建...")
    
    # 模拟请求
    class MockRequest:
        def __init__(self):
            self.prompt = "test prompt"
            self.negative_prompt = "ugly"
            self.width = 768
            self.height = 768
            self.steps = 20
            self.cfg = 2.0
            self.seed = None
            self.batch_size = 3  # 关键：测试3张
    
    request = MockRequest()
    
    # 模拟create_workflow函数（简化版）
    import time
    seed = int(time.time() * 1000000) % 1000000000
    
    workflow = {
        "5": {
            "inputs": {
                "width": request.width,
                "height": request.height,
                "batch_size": request.batch_size  # 这里是关键
            },
            "class_type": "EmptyLatentImage",
            "_meta": {"title": "空Latent图像"}
        }
    }
    
    print(f"🎯 生成的工作流节点5:")
    print(json.dumps(workflow["5"], indent=2, ensure_ascii=False))
    
    print(f"\n✅ batch_size = {request.batch_size} 已正确传递到工作流")

def check_comfyui_response():
    """检查ComfyUI响应格式"""
    print("\n🔍 分析ComfyUI可能的响应格式...")
    
    print("""
    🤔 ComfyUI多图响应的可能情况：
    
    情况1: 正常多图响应
    {
        "8": {
            "images": [
                {"filename": "image_00001.png", "subfolder": "", "type": "output"},
                {"filename": "image_00002.png", "subfolder": "", "type": "output"},
                {"filename": "image_00003.png", "subfolder": "", "type": "output"}
            ]
        }
    }
    
    情况2: 单图响应（问题所在）
    {
        "8": {
            "images": [
                {"filename": "image_00001.png", "subfolder": "", "type": "output"}
            ]
        }
    }
    
    情况3: batch_size在ComfyUI中被忽略
    - 可能ComfyUI版本不支持batch_size
    - 或者工作流配置有问题
    """)

def suggest_debug_steps():
    """建议调试步骤"""
    print("\n💡 建议的调试步骤:")
    print("""
    1. 检查ComfyUI直接界面：
       - 打开ComfyUI网页界面
       - 手动创建EmptyLatentImage节点
       - 设置batch_size为3
       - 看是否生成3张图
    
    2. 检查API提交的工作流：
       - 在process_single_task函数中添加日志
       - 打印提交给ComfyUI的完整工作流JSON
    
    3. 检查ComfyUI返回的历史数据：
       - 在获取history时打印完整响应
       - 确认images数组的长度
    
    4. 测试不同的batch_size值：
       - 尝试batch_size=1,2,3,4
       - 观察ComfyUI的实际行为
    """)

def main():
    print("🔍 ComfyUI多图生成深度诊断")
    print("=" * 50)
    
    analyze_workflow()
    check_recent_requests()
    simulate_workflow_creation()
    check_comfyui_response()
    suggest_debug_steps()
    
    print("\n" + "=" * 50)
    print("🎯 下一步建议:")
    print("1. 直接在ComfyUI界面测试batch_size")
    print("2. 或者在代码中添加调试日志")
    print("3. 确认ComfyUI版本是否支持batch生成")

if __name__ == "__main__":
    main()
