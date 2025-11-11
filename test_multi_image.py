#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试多图生成功能
"""

import requests
import json
import time

API_BASE = "http://localhost:8000"

def test_multi_image_generation():
    """测试多图生成"""
    print("🧪 测试多图生成功能")
    print("=" * 50)
    
    # 测试数据
    test_request = {
        "prompt": "a cute red apple on white background",
        "negative_prompt": "ugly, blurry",
        "width": 768,
        "height": 768,
        "steps": 20,
        "cfg": 2.0,
        "batch_size": 3,  # 生成3张图片
        "batch_name": "multi_test"
    }
    
    try:
        print("📤 提交多图生成任务...")
        print(f"请求参数: {json.dumps(test_request, indent=2, ensure_ascii=False)}")
        
        response = requests.post(f"{API_BASE}/generate", json=test_request)
        
        if response.status_code == 200:
            result = response.json()
            task_id = result["task_id"]
            print(f"✅ 任务提交成功！任务ID: {task_id}")
            
            # 轮询任务状态
            print("\n⏳ 等待任务完成...")
            for i in range(30):  # 最多等待5分钟
                time.sleep(10)
                
                status_response = requests.get(f"{API_BASE}/task/{task_id}")
                if status_response.status_code == 200:
                    task = status_response.json()
                    print(f"  📊 进度: {task['progress']:.1f}% - {task['message']}")
                    
                    if task["status"] == "completed":
                        print("\n🎉 任务完成！")
                        print(f"单图URL: {task.get('result_url', 'N/A')}")
                        print(f"多图URLs: {task.get('result_urls', 'N/A')}")
                        
                        if task.get('result_urls'):
                            print(f"✅ 成功生成 {len(task['result_urls'])} 张图片！")
                            for i, url in enumerate(task['result_urls'], 1):
                                print(f"  图片{i}: {API_BASE}{url}")
                        else:
                            print("❌ 没有找到多图URLs")
                        break
                    elif task["status"] == "failed":
                        print(f"❌ 任务失败: {task.get('error', '未知错误')}")
                        break
                else:
                    print(f"❌ 无法获取任务状态: {status_response.status_code}")
                    break
        else:
            print(f"❌ 任务提交失败: {response.status_code}")
            print(f"响应: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到API服务器，请确认服务器已启动")
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def check_tasks_api():
    """检查任务列表API"""
    print("\n📋 检查任务列表...")
    try:
        response = requests.get(f"{API_BASE}/tasks")
        if response.status_code == 200:
            data = response.json()
            tasks = data.get("tasks", [])
            print(f"✅ 获取到 {len(tasks)} 个任务")
            
            # 显示前3个已完成的任务
            completed_tasks = [t for t in tasks if t.get('status') == 'completed'][:3]
            for i, task in enumerate(completed_tasks, 1):
                print(f"\n--- 任务 {i} ---")
                print(f"ID: {task.get('task_id', 'N/A')[:8]}")
                print(f"状态: {task.get('status', 'N/A')}")
                print(f"消息: {task.get('message', 'N/A')}")
                print(f"单图URL: {task.get('result_url', 'N/A')}")
                print(f"多图URLs: {task.get('result_urls', 'N/A')}")
                if task.get('result_urls'):
                    print(f"多图数量: {len(task['result_urls'])}")
        else:
            print(f"❌ 获取任务列表失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 检查失败: {e}")

if __name__ == "__main__":
    # 先检查现有任务
    check_tasks_api()
    
    # 询问是否要测试新的多图生成
    print("\n" + "=" * 50)
    user_input = input("是否要测试新的多图生成？(y/n): ").lower().strip()
    
    if user_input == 'y':
        test_multi_image_generation()
    else:
        print("测试结束！")
