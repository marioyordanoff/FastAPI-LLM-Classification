from fastapi import HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from config import Settings

settings = Settings()
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def authenticate_api_key(api_key: str = Security(api_key_header)):
    if api_key != settings.api_key:
        raise HTTPException(status_code=403, detail="Could not validate API key")
    return api_key
