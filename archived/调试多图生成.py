#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试多图生成 - 提交测试任务并观察日志
"""

import requests
import json
import time

def test_batch_generation():
    """测试批量生成功能"""
    
    print("🧪 调试多图生成功能")
    print("=" * 50)
    
    # 测试数据
    test_cases = [
        {"batch_size": 1, "desc": "单图测试"},
        {"batch_size": 2, "desc": "双图测试"}, 
        {"batch_size": 3, "desc": "三图测试"}
    ]
    
    for case in test_cases:
        print(f"\n🎯 {case['desc']} (batch_size={case['batch_size']})")
        
        test_data = {
            'prompt': f'一只可爱的小猫咪，batch_size={case["batch_size"]}',
            'negative_prompt': 'ugly, bad quality',
            'width': 512,  # 小尺寸快速测试
            'height': 512,
            'steps': 8,    # 少步数快速测试
            'cfg': 2.0,
            'seed': int(time.time()),  # 随机种子
            'batch_size': case['batch_size']
        }
        
        try:
            # 提交任务
            response = requests.post('http://localhost:8000/generate', json=test_data, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                task_id = result.get('task_id')
                print(f"✅ 任务提交成功: {task_id}")
                print("📋 请观察服务器终端的调试日志输出...")
                print("🔍 特别关注以下日志:")
                print("   - 🎯 任务参数 (batch_size)")
                print("   - 🔧 工作流中的batch_size")
                print("   - 🖼️ ComfyUI返回图片数量") 
                print("   - 💾 保存的图片URL数量")
                
                # 等待任务完成并检查结果
                print("⏳ 等待任务完成...")
                for i in range(30):  # 最多等待60秒
                    time.sleep(2)
                    
                    try:
                        status_response = requests.get(f'http://localhost:8000/tasks/{task_id}', timeout=5)
                        if status_response.status_code == 200:
                            task_status = status_response.json()
                            print(f"📊 进度: {task_status.get('progress', 0):.1f}% - {task_status.get('message', '')}")
                            
                            if task_status.get('status') == 'completed':
                                result_urls = task_status.get('result_urls', [])
                                print(f"🎉 任务完成! 实际生成图片数量: {len(result_urls)}")
                                print(f"📸 图片URLs: {result_urls}")
                                break
                            elif task_status.get('status') == 'failed':
                                print(f"❌ 任务失败: {task_status.get('message')}")
                                break
                    except:
                        pass
                
            else:
                print(f"❌ 请求失败: {response.status_code}")
                print(f"响应: {response.text}")
                
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            print("💡 确保后端服务器正在运行!")
            break
        
        print("-" * 30)
    
    print("\n🎯 调试完成!")
    print("📋 请检查服务器终端的详细日志来诊断问题")

if __name__ == "__main__":
    test_batch_generation()
