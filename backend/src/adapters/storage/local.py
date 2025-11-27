from pathlib import Path
import logging
from .base import StorageAdapter
from backend.src.config.settings import OUTPUT_DIR

logger = logging.getLogger(__name__)

class LocalStorageAdapter(StorageAdapter):
    async def upload(self, file_data: bytes, filename: str, content_type: str = "image/png") -> str:
        path = OUTPUT_DIR / filename
        with open(path, 'wb') as f:
            f.write(file_data)
        logger.info(f"已保存本地文件: {path}")
        return f"/images/{filename}"

