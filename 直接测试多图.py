#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接测试多图生成功能（不需要requests库）
"""

import json
import urllib.request
import urllib.parse
import time

API_BASE = "http://localhost:8000"

def http_request(url, data=None, method="GET"):
    """简单的HTTP请求函数"""
    try:
        if data:
            data = json.dumps(data).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers={
                'Content-Type': 'application/json'
            })
            req.get_method = lambda: method
        else:
            req = urllib.request.Request(url)
        
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
            
    except Exception as e:
        print(f"❌ HTTP请求失败: {e}")
        return None

def test_multi_image():
    """测试多图生成"""
    print("🧪 直接测试多图生成功能")
    print("=" * 50)
    
    # 测试数据 - 关键是batch_size=3
    test_request = {
        "prompt": "a simple red apple on white background, clean",
        "negative_prompt": "ugly, blurry, low quality",
        "width": 512,
        "height": 512,
        "steps": 15,  # 减少步数加快测试
        "cfg": 2.0,
        "seed": 12345,  # 固定种子便于调试
        "batch_size": 3,  # 关键参数！
        "batch_name": "debug_multi_test"
    }
    
    print(f"📤 提交测试任务...")
    print(f"🎯 关键参数: batch_size = {test_request['batch_size']}")
    
    # 提交任务
    result = http_request(f"{API_BASE}/generate", test_request, "POST")
    
    if not result:
        print("❌ 任务提交失败")
        return
    
    task_id = result.get("task_id")
    print(f"✅ 任务提交成功！任务ID: {task_id}")
    
    # 轮询任务状态
    print("\n⏳ 监控任务状态...")
    max_wait = 60  # 最多等待60次 (约2分钟)
    
    for i in range(max_wait):
        time.sleep(2)
        
        # 获取任务状态
        task_status = http_request(f"{API_BASE}/status/{task_id}")
        
        if not task_status:
            print("❌ 无法获取任务状态")
            continue
        
        status = task_status.get("status", "unknown")
        progress = task_status.get("progress", 0)
        message = task_status.get("message", "")
        
        print(f"  📊 [{i+1:2d}] {status} - {progress:.1f}% - {message}")
        
        if status == "completed":
            print("\n🎉 任务完成！开始分析结果...")
            
            # 分析结果
            result_url = task_status.get("result_url")
            result_urls = task_status.get("result_urls")
            
            print(f"📋 结果分析:")
            print(f"  单图URL: {result_url}")
            print(f"  多图URLs: {result_urls}")
            print(f"  多图URLs类型: {type(result_urls)}")
            
            if result_urls and isinstance(result_urls, list) and len(result_urls) > 1:
                print(f"✅ 成功！生成了 {len(result_urls)} 张图片")
                for i, url in enumerate(result_urls, 1):
                    print(f"    图片{i}: {API_BASE}{url}")
                return True
            elif result_url:
                print(f"⚠️  只生成了1张图片，多图功能未工作")
                return False
            else:
                print(f"❌ 没有生成任何图片")
                return False
                
        elif status == "failed":
            error = task_status.get("error", "未知错误")
            print(f"❌ 任务失败: {error}")
            return False
    
    print("⏰ 任务超时")
    return False

def check_logs():
    """检查日志输出"""
    print("\n📋 检查API服务器日志...")
    try:
        with open("api_debug.log", "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        # 只显示最后20行日志
        recent_logs = lines[-20:] if len(lines) > 20 else lines
        
        for line in recent_logs:
            if "🎯" in line or "🔧" in line or "📋" in line or "🖼️" in line or "💾" in line or "✅" in line:
                print(f"  {line.strip()}")
                
    except FileNotFoundError:
        print("  📄 日志文件不存在")
    except Exception as e:
        print(f"  ❌ 读取日志失败: {e}")

def main():
    print("🔍 多图生成直接测试工具")
    print("=" * 50)
    
    # 先检查服务器是否运行
    health = http_request(f"{API_BASE}/health")
    if not health:
        print("❌ API服务器未运行，请先启动服务器")
        return
    
    print("✅ API服务器正在运行")
    
    # 执行测试
    success = test_multi_image()
    
    # 检查日志
    check_logs()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 多图功能测试成功！")
    else:
        print("❌ 多图功能测试失败，请检查日志输出")

if __name__ == "__main__":
    main()
