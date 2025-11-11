#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库调试工具 - 检查任务表中的数据
"""

import sqlite3
import json
from datetime import datetime

DB_PATH = "./tasks.db"

def check_database():
    """检查数据库中的任务数据"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 检查表结构
        print("=== 数据库表结构 ===")
        cursor.execute("PRAGMA table_info(tasks)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        print("\n=== 最近的任务数据 ===")
        cursor.execute('''
            SELECT task_id, status, message, result_url, result_urls, created_at
            FROM tasks
            ORDER BY created_at DESC
            LIMIT 5
        ''')
        
        tasks = cursor.fetchall()
        if not tasks:
            print("  数据库中没有任务")
            return
        
        for i, task in enumerate(tasks, 1):
            task_id, status, message, result_url, result_urls_json, created_at = task
            print(f"\n--- 任务 {i} ---")
            print(f"ID: {task_id}")
            print(f"状态: {status}")
            print(f"消息: {message}")
            print(f"单图URL: {result_url}")
            print(f"多图JSON: {result_urls_json}")
            
            # 尝试解析result_urls JSON
            if result_urls_json:
                try:
                    result_urls = json.loads(result_urls_json)
                    print(f"多图URLs: {result_urls} (共{len(result_urls)}张)")
                except json.JSONDecodeError as e:
                    print(f"JSON解析错误: {e}")
            else:
                print("多图URLs: None")
            
            print(f"创建时间: {created_at}")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"数据库错误: {e}")
    except Exception as e:
        print(f"其他错误: {e}")

def test_api_response():
    """测试API响应数据"""
    import requests
    
    try:
        print("\n=== 测试API响应 ===")
        response = requests.get("http://localhost:8000/tasks")
        
        if response.status_code == 200:
            data = response.json()
            tasks = data.get("tasks", [])
            print(f"API返回 {len(tasks)} 个任务")
            
            for i, task in enumerate(tasks[:3], 1):  # 只显示前3个
                print(f"\n--- API任务 {i} ---")
                print(f"ID: {task.get('task_id', 'N/A')}")
                print(f"状态: {task.get('status', 'N/A')}")
                print(f"单图URL: {task.get('result_url', 'N/A')}")
                print(f"多图URLs: {task.get('result_urls', 'N/A')}")
                if task.get('result_urls'):
                    print(f"多图数量: {len(task['result_urls'])}")
        else:
            print(f"API请求失败: {response.status_code}")
    
    except requests.exceptions.ConnectionError:
        print("无法连接到API服务器 (localhost:8000)")
    except Exception as e:
        print(f"API测试错误: {e}")

if __name__ == "__main__":
    print("🔍 ComfyUI批量生图数据库调试工具")
    print("=" * 50)
    
    check_database()
    test_api_response()
    
    print("\n" + "=" * 50)
    print("调试完成！")
