from fastapi import HTTPException, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from starlette.status import HTTP_401_UNAUTHORIZED
from backend.src.database.db import get_user_by_key

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

async def get_current_user(api_key_header: str = Security(api_key_header)):
    """
    验证 API Key 并返回当前用户对象
    """
    if not api_key_header:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="缺少认证凭证 (Authorization Header)",
        )
    
    # 处理 "Bearer " 前缀
    api_key = api_key_header.replace("Bearer ", "").strip()
    
    user = get_user_by_key(api_key)
    
    if not user:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="无效的 API Key",
        )
    
    return user
