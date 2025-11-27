from backend.src.config.settings import STORAGE_TYPE
from .local import LocalStorageAdapter
from .s3 import S3StorageAdapter

def get_storage_adapter():
    if STORAGE_TYPE == "s3" or STORAGE_TYPE == "oss":
        return S3StorageAdapter()
    return LocalStorageAdapter()

