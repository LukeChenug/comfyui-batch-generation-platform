#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试完整的图片上传和Qwen工作流
"""

import requests
import json
import time
import os
from pathlib import Path

def create_test_image():
    """创建一个测试图片（简单的纯色图片）"""
    try:
        from PIL import Image
        
        # 创建一个简单的测试图片
        img = Image.new('RGB', (512, 512), color=(100, 150, 200))
        test_image_path = "test_image.png"
        img.save(test_image_path)
        
        print(f"✅ 创建测试图片: {test_image_path}")
        return test_image_path
        
    except ImportError:
        print("❌ 需要安装PIL: pip install Pillow")
        return None
    except Exception as e:
        print(f"❌ 创建测试图片失败: {e}")
        return None

def test_image_upload_workflow():
    """测试完整的图片上传和生成流程"""
    
    print("🖼️ 测试图片上传和Qwen工作流")
    print("=" * 60)
    
    # Step 1: 创建或准备测试图片
    test_image_path = create_test_image()
    if not test_image_path:
        print("⚠️ 请手动准备一张图片文件，命名为 test_image.png")
        test_image_path = "test_image.png"
        if not os.path.exists(test_image_path):
            print(f"❌ 图片文件不存在: {test_image_path}")
            return
    
    try:
        # Step 2: 上传图片到我们的后端
        print("📤 上传图片到后端...")
        
        with open(test_image_path, 'rb') as f:
            files = {'file': (test_image_path, f, 'image/png')}
            upload_response = requests.post('http://localhost:8001/upload_image', files=files, timeout=30)
        
        if upload_response.status_code != 200:
            print(f"❌ 图片上传失败: {upload_response.status_code}")
            print(f"响应: {upload_response.text}")
            return
        
        upload_result = upload_response.json()
        uploaded_filename = upload_result['filename']
        print(f"✅ 图片上传成功: {uploaded_filename}")
        
        # Step 3: 提交Qwen图生图任务
        print("🎨 提交Qwen图生图任务...")
        
        task_data = {
            'prompt': '将这张图片变成卡通风格的儿童绘本插画，色彩温暖柔和',
            'negative_prompt': 'ugly, blurry, low quality, distorted',
            'width': 784,
            'height': 496,
            'steps': 4,
            'cfg': 1.0,
            'seed': 123456,
            'batch_size': 2,  # 测试多图生成
            'input_image': uploaded_filename  # 关键：使用上传的图片
        }
        
        generate_response = requests.post('http://localhost:8001/generate', json=task_data, timeout=15)
        
        if generate_response.status_code == 200:
            result = generate_response.json()
            task_id = result.get('task_id')
            print(f"✅ 任务提交成功: {task_id}")
            
            # Step 4: 监控任务进度
            print("⏳ 监控任务进度...")
            print("🔍 请观察服务器终端的详细日志:")
            print("   - 📤 图片上传到ComfyUI")
            print("   - 🔧 工作流类型: Qwen图生图")  
            print("   - 🖼️ 从节点115:116获取到 X 张图片")
            print("   - 💾 保存的图片URL数量")
            
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
                            print(f"\n🎉 任务完成!")
                            print(f"🖼️ 生成图片数量: {len(result_urls)}")
                            print("📸 图片URLs:")
                            for idx, url in enumerate(result_urls, 1):
                                print(f"  {idx}. http://localhost:8001{url}")
                            
                            # 验证Qwen多图生成
                            expected_count = task_data['batch_size']
                            if len(result_urls) == expected_count:
                                print(f"✅ Qwen多图生成成功! 期望{expected_count}张，实际{len(result_urls)}张")
                            else:
                                print(f"⚠️ Qwen多图生成异常: 期望{expected_count}张，实际{len(result_urls)}张")
                            break
                            
                        elif task_status.get('status') == 'failed':
                            print(f"\n❌ 任务失败: {task_status.get('message')}")
                            error = task_status.get('error', '')
                            if error:
                                print(f"错误详情: {error}")
                            break
                            
                except Exception as e:
                    print(f"⚠️ 状态查询异常: {e}")
                    
            else:
                print("⏰ 任务超时")
                
        else:
            print(f"❌ 任务提交失败: {generate_response.status_code}")
            print(f"响应: {generate_response.text}")
            
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
    
    finally:
        # 清理测试文件
        if os.path.exists(test_image_path) and test_image_path == "test_image.png":
            try:
                os.remove(test_image_path)
                print(f"🧹 已清理测试图片: {test_image_path}")
            except:
                pass

def test_flux_workflow():
    """对比测试FLUX文生图工作流（无图片输入）"""
    
    print("\n🔥 对比测试FLUX文生图工作流")
    print("=" * 60)
    
    task_data = {
        'prompt': '一只可爱的小熊猫在竹林中玩耍，卡通风格，儿童绘本插画',
        'negative_prompt': 'ugly, blurry, low quality',
        'width': 768,
        'height': 768,
        'steps': 10,
        'cfg': 2.0,
        'seed': 789012,
        'batch_size': 2,  # 同样测试2张
        'input_image': None  # 关键：不使用输入图片
    }
    
    try:
        print("📤 提交FLUX文生图任务...")
        response = requests.post('http://localhost:8001/generate', json=task_data, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('task_id')
            print(f"✅ 任务提交成功: {task_id}")
            print("🔍 请观察服务器终端对比日志:")
            print("   - 🔧 工作流类型: FLUX文生图")
            print("   - 🖼️ 从节点8获取到 X 张图片")
            
        else:
            print(f"❌ 任务提交失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ FLUX测试失败: {e}")

if __name__ == "__main__":
    print("🧪 完整工作流测试套件")
    print("=" * 70)
    
    print("📋 测试计划:")
    print("1. 测试图片上传 + Qwen图生图工作流")
    print("2. 对比测试FLUX文生图工作流") 
    print("3. 观察多图生成能力差异")
    print()
    
    # 测试1: Qwen图生图
    test_image_upload_workflow()
    
    # 测试2: FLUX文生图
    test_flux_workflow()
    
    print("\n🎯 测试完成!")
    print("📊 请对比服务器终端中两种工作流的日志输出")
    print("🔍 特别关注: 'ComfyUI返回 X 张图片' 的数量差异")
