# ... existing imports ...
import os
from pathlib import Path

# ComfyUI 配置 (原生/本地)
# 根据用户截图，ComfyUI 运行在 8000 端口
COMFYUI_SERVER = os.getenv("COMFYUI_SERVER", "http://127.0.0.1:8000")
COMFYUI_WS = os.getenv("COMFYUI_WS", "ws://127.0.0.1:8000/ws")

# ComfyUI Deploy 配置 (云端) - MVP 阶段禁用
USE_COMFY_DEPLOY = False
# COMFY_DEPLOY_API_KEY = "..."
# COMFY_DEPLOY_DEPLOYMENT_ID = "..."
COMFY_DEPLOY_HOST = "https://api.comfydeploy.com"

# 配置检查日志（移除emoji以兼容Windows GBK编码）
# print(f"配置检查: USE_COMFY_DEPLOY={USE_COMFY_DEPLOY}")
# print(f"配置检查: DEPLOYMENT_ID={COMFY_DEPLOY_DEPLOYMENT_ID}")

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
