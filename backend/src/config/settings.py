# ... existing imports ...
import os
from pathlib import Path

# ComfyUI 配置 (原生/本地)
COMFYUI_SERVER = os.getenv("COMFYUI_SERVER", "http://106.75.213.77:8188")
COMFYUI_WS = os.getenv("COMFYUI_WS", "ws://106.75.213.77:8188/ws")

# ComfyUI Deploy 配置 (云端)
# ⚠️ 调试模式：强制开启，并使用硬编码的 Key 和 ID
USE_COMFY_DEPLOY = True
COMFY_DEPLOY_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidXNlcl8zNjM5UllsMW03cFROS1o3REdVVTNRWmlpVFciLCJpYXQiOjE3NjQyMzE4NDIsIm9yZ19pZCI6Im9yZ18zNjM5VkZXYTNQNU56RnNIMTZuZmJaS294cUUifQ.BoKEoHBuVBFKMrMqwRmakFBO9KOA3yOSd-x0k9cmkm4"
COMFY_DEPLOY_DEPLOYMENT_ID = "f6cd9d42-eee8-4aa8-86cb-fa7ece757cfd"
COMFY_DEPLOY_HOST = "https://api.comfydeploy.com"

print(f"🔍 配置检查: USE_COMFY_DEPLOY={USE_COMFY_DEPLOY}")
print(f"🔍 配置检查: DEPLOYMENT_ID={COMFY_DEPLOY_DEPLOYMENT_ID}")

# 存储配置
# ... existing code ...
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "./generated_images"))
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploaded_images"))
DB_PATH = os.getenv("DB_PATH", "./tasks.db")

# 存储类型: local, s3, oss
STORAGE_TYPE = os.getenv("STORAGE_TYPE", "local")

# S3/OSS 配置
S3_ENDPOINT = os.getenv("S3_ENDPOINT", "")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "")
S3_REGION = os.getenv("S3_REGION", "")
S3_PUBLIC_URL = os.getenv("S3_PUBLIC_URL", "") # CDN URL prefix

# 创建必要目录
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
UPLOAD_DIR.mkdir(exist_ok=True, parents=True)
