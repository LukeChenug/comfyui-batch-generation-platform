#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
临时测试FLUX工作流的多图功能
"""

import requests
import json
import time

def test_flux_multi_image():
    """测试FLUX工作流的多图功能"""
    
    print("🔥 临时测试FLUX多图功能")
    print("=" * 50)
    
    # 使用FLUX工作流的测试数据（不需要input_image）
    test_data = {
        'prompt': '一只可爱的小猫咪在花园里玩耍',
        'negative_prompt': 'ugly, blurry, low quality',
        'width': 768,
        'height': 768, 
        'steps': 10,  # 快速测试
        'cfg': 2.0,
        'seed': 12345,
        'batch_size': 3,  # 测试3张图
        'input_image': None  # 不使用输入图片，纯文生图
    }
    
    try:
        print("📤 提交FLUX文生图任务...")
        response = requests.post('http://localhost:8001/generate', json=test_data, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('task_id')
            print(f"✅ 任务提交成功: {task_id}")
            print("🔍 请查看服务器终端的调试日志...")
            print("⏳ 特别关注：🖼️ ComfyUI返回了几张图片")
            
        else:
            print(f"❌ 任务提交失败: {response.status_code}")
            print(f"响应: {response.text}")
            
    except Exception as e:
        print(f"❌ 连接失败: {e}")

if __name__ == "__main__":
    test_flux_multi_image()
