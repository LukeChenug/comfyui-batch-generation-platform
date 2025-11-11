#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证ComfyUI批量生成能力的测试工具
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

def test_different_batch_sizes():
    """测试不同的批量大小"""
    print("🧪 批量大小能力验证测试")
    print("=" * 60)
    
    batch_sizes = [1, 2, 3, 4]  # 测试不同的批量大小
    results = {}
    
    for batch_size in batch_sizes:
        print(f"\n🎯 测试 batch_size = {batch_size}")
        print("-" * 40)
        
        # 构造测试请求
        test_request = {
            "prompt": f"a simple {['red', 'blue', 'green', 'yellow'][batch_size-1]} apple on white background",
            "negative_prompt": "ugly, blurry",
            "width": 512,
            "height": 512,
            "steps": 10,  # 极短步数加快测试
            "cfg": 2.0,
            "seed": 12345 + batch_size,  # 不同的种子
            "batch_size": batch_size,
            "batch_name": f"batch_test_{batch_size}"
        }
        
        print(f"📤 提交 batch_size={batch_size} 的任务...")
        
        # 提交任务
        result = http_request(f"{API_BASE}/generate", test_request, "POST")
        
        if not result:
            print(f"❌ batch_size={batch_size} 任务提交失败")
            results[batch_size] = {"status": "submit_failed", "images": 0}
            continue
        
        task_id = result.get("task_id")
        print(f"✅ 任务ID: {task_id}")
        
        # 等待完成
        max_wait = 30  # 最多等待30次
        task_result = None
        
        for i in range(max_wait):
            time.sleep(2)
            
            task_status = http_request(f"{API_BASE}/status/{task_id}")
            if not task_status:
                continue
            
            status = task_status.get("status", "unknown")
            progress = task_status.get("progress", 0)
            
            print(f"  📊 {status} - {progress:.1f}%", end="\r")
            
            if status == "completed":
                task_result = task_status
                break
            elif status == "failed":
                print(f"\n❌ 任务失败: {task_status.get('error', '未知错误')}")
                break
        
        print()  # 换行
        
        # 分析结果
        if task_result:
            result_url = task_result.get("result_url")
            result_urls = task_result.get("result_urls")
            
            if result_urls and isinstance(result_urls, list):
                actual_count = len(result_urls)
                print(f"✅ 实际生成: {actual_count} 张图片")
                results[batch_size] = {
                    "status": "completed", 
                    "expected": batch_size,
                    "actual": actual_count,
                    "success": actual_count == batch_size,
                    "urls": result_urls
                }
            elif result_url:
                print(f"⚠️  只有单图URL，实际生成: 1 张图片")
                results[batch_size] = {
                    "status": "completed",
                    "expected": batch_size, 
                    "actual": 1,
                    "success": batch_size == 1,
                    "urls": [result_url]
                }
            else:
                print(f"❌ 没有生成任何图片")
                results[batch_size] = {
                    "status": "no_images",
                    "expected": batch_size,
                    "actual": 0,
                    "success": False
                }
        else:
            print(f"❌ 任务超时或失败")
            results[batch_size] = {
                "status": "timeout",
                "expected": batch_size,
                "actual": 0, 
                "success": False
            }
    
    return results

def analyze_results(results):
    """分析测试结果"""
    print("\n📊 批量能力分析报告")
    print("=" * 60)
    
    success_count = 0
    
    for batch_size, result in results.items():
        expected = result.get("expected", batch_size)
        actual = result.get("actual", 0)
        success = result.get("success", False)
        
        status_icon = "✅" if success else "❌"
        print(f"{status_icon} batch_size={batch_size}: 期望{expected}张 → 实际{actual}张")
        
        if success:
            success_count += 1
    
    print(f"\n📈 成功率: {success_count}/{len(results)} ({success_count/len(results)*100:.1f}%)")
    
    # 结论分析
    print(f"\n🔍 结论分析:")
    
    if all(r.get("actual", 0) == 1 for r in results.values() if r.get("status") == "completed"):
        print("❌ ComfyUI始终只生成1张图片，不支持批量生成")
        print("💡 建议: 实施循环生成方案（为每个batch_size循环调用单图生成）")
    elif success_count == len(results):
        print("✅ ComfyUI完美支持批量生成！")
        print("💡 之前的问题可能是偶发性的，多图功能应该正常工作")
    elif success_count > 0:
        print("⚠️  ComfyUI部分支持批量生成")
        print("💡 可能在某些条件下支持，需要进一步调试")
    else:
        print("❌ ComfyUI完全不支持批量生成或存在其他问题")
        print("💡 建议: 检查ComfyUI版本和模型兼容性")

def main():
    print("🔍 ComfyUI批量生成能力验证工具")
    print("=" * 60)
    
    # 检查API服务器
    health = http_request(f"{API_BASE}/health")
    if not health:
        print("❌ API服务器未运行，请先启动服务器")
        return
    
    print("✅ API服务器正在运行")
    print("⏳ 开始批量能力测试，预计需要2-3分钟...")
    
    # 执行测试
    results = test_different_batch_sizes()
    
    # 分析结果
    analyze_results(results)
    
    print(f"\n🎯 如果ComfyUI不支持批量，我们可以实施循环生成方案")
    print(f"📋 详细结果已保存，可以根据测试结果决定下一步行动")

if __name__ == "__main__":
    main()
