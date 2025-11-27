#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Qwen图生图工作流
"""

import requests
import json
import time

def test_qwen_workflow():
    """测试Qwen图生图工作流"""
    
    print("🎨 测试Qwen图生图工作流")
    print("=" * 50)
    
    # 测试数据
    test_data = {
        'prompt': '两个小熊来到了森林中的一条小溪边，清澈的溪水闪着亮光',
        'negative_prompt': 'ugly, blurry, low quality',
        'width': 784,
        'height': 496,
        'steps': 4,
        'cfg': 1.0,
        'seed': 12345,
        'batch_size': 2,  # 测试多图生成
        'input_image': None  # 使用默认图片
    }
    
    try:
        # 提交任务
        print("📤 提交Qwen图生图任务...")
        response = requests.post('http://localhost:8001/generate', json=test_data, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('task_id')
            print(f"✅ 任务提交成功: {task_id}")
            
            # 监控任务进度
            print("⏳ 监控任务进度...")
            for i in range(60):  # 最多等待2分钟
                time.sleep(2)
                
                try:
                    status_response = requests.get(f'http://localhost:8001/tasks/{task_id}', timeout=5)
                    if status_response.status_code == 200:
                        task_status = status_response.json()
                        progress = task_status.get('progress', 0)
                        message = task_status.get('message', '')
                        print(f"📊 {progress:.1f}% - {message}")
                        
                        if task_status.get('status') == 'completed':
                            result_urls = task_status.get('result_urls', [])
                            print(f"🎉 任务完成!")
                            print(f"🖼️ 生成图片数量: {len(result_urls)}")
                            print("📸 图片URLs:")
                            for i, url in enumerate(result_urls, 1):
                                print(f"  {i}. {url}")
                            
                            # 验证多图生成
                            if len(result_urls) == test_data['batch_size']:
                                print(f"✅ 多图生成成功! 期望{test_data['batch_size']}张，实际{len(result_urls)}张")
                            else:
                                print(f"⚠️ 多图生成异常: 期望{test_data['batch_size']}张，实际{len(result_urls)}张")
                            break
                            
                        elif task_status.get('status') == 'failed':
                            print(f"❌ 任务失败: {task_status.get('message')}")
                            break
                            
                except Exception as e:
                    print(f"⚠️ 状态查询异常: {e}")
                    
            else:
                print("⏰ 任务超时")
                
        else:
            print(f"❌ 任务提交失败: {response.status_code}")
            print(f"响应: {response.text}")
            
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        print("💡 确保后端服务器正在运行: python3 comfyui_api_server.py")

def test_workflow_generation():
    """测试工作流生成"""
    print("\n🔧 测试工作流生成...")
    
    from comfyui_api_server import create_workflow, GenerationRequest
    
    # 创建测试请求
    class TestRequest:
        def __init__(self):
            self.prompt = "测试提示词"
            self.negative_prompt = "ugly"
            self.width = 784
            self.height = 496
            self.steps = 4
            self.cfg = 1.0
            self.seed = 12345
            self.batch_size = 3
            self.input_image = None
    
    request = TestRequest()
    workflow = create_workflow(request)
    
    print("✅ 工作流生成成功")
    print(f"🎯 批量节点(115:112)的batch_size: {workflow['115:112']['inputs']['batch_size']}")
    print(f"🖼️ 输出节点: 115:116")
    print(f"📝 提示词节点: 115:111")

if __name__ == "__main__":
    print("🚀 Qwen工作流测试套件")
    print("=" * 60)
    
    # 测试1: 工作流生成
    test_workflow_generation()
    
    # 测试2: 完整API调用
    print("\n" + "=" * 60)
    test_qwen_workflow()
    
    print("\n🎯 测试完成!")
    print("📋 请查看服务器终端的调试日志以获取更多信息")
