from abc import ABC, abstractmethod

class StorageAdapter(ABC):
    @abstractmethod
    async def upload(self, file_data: bytes, filename: str, content_type: str = "image/png") -> str:
        """上传文件并返回访问URL"""
        pass

