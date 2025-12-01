import requests
import sys

API_URL = "http://localhost:8088"
API_KEY = "sk-admin-123456"

def test_login():
    print(f"正在测试连接 {API_URL} ...")
    
    # 1. 测试健康检查
    try:
        resp = requests.get(f"{API_URL}/health", timeout=5)
        print(f"健康检查: {resp.status_code}")
    except Exception as e:
        print(f"❌ 无法连接服务器: {e}")
        return

    # 2. 测试登录 (/me)
    print(f"正在验证 Key: {API_KEY}")
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    try:
        resp = requests.get(f"{API_URL}/me", headers=headers)
        print(f"登录响应: {resp.status_code}")
        print(f"响应内容: {resp.text}")
        
        if resp.status_code == 200:
            print("✅ 验证成功！后端工作正常。")
        elif resp.status_code == 401:
            print("❌ 验证失败：Key 无效。")
        else:
            print("❌ 未知错误。")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")

if __name__ == "__main__":
    test_login()

