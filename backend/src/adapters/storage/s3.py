import logging
from .base import StorageAdapter
from backend.src.config.settings import S3_ENDPOINT, S3_ACCESS_KEY, S3_SECRET_KEY, S3_BUCKET_NAME, S3_REGION, S3_PUBLIC_URL

logger = logging.getLogger(__name__)

class S3StorageAdapter(StorageAdapter):
    def __init__(self):
        try:
            import boto3
            self.s3 = boto3.client(
                's3',
                endpoint_url=S3_ENDPOINT if S3_ENDPOINT else None,
                aws_access_key_id=S3_ACCESS_KEY,
                aws_secret_access_key=S3_SECRET_KEY,
                region_name=S3_REGION if S3_REGION else None
            )
        except ImportError:
            logger.error("boto3未安装，无法使用S3存储")
            raise

    async def upload(self, file_data: bytes, filename: str, content_type: str = "image/png") -> str:
        # 简单的同步调用，生产环境建议使用aioboto3或run_in_executor
        try:
            self.s3.put_object(
                Bucket=S3_BUCKET_NAME,
                Key=filename,
                Body=file_data,
                ContentType=content_type,
                ACL='public-read'
            )
            
            if S3_PUBLIC_URL:
                return f"{S3_PUBLIC_URL}/{filename}"
            return f"{S3_ENDPOINT}/{S3_BUCKET_NAME}/{filename}"
        except Exception as e:
            logger.error(f"S3上传失败: {e}")
            raise

