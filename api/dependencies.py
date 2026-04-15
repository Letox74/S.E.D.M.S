from fastapi import Security
from fastapi.security import APIKeyHeader

from internal.security import verify_api_key

API_KEY_HEADER = APIKeyHeader(name="API-KEY", scheme_name="API Key")


async def api_key_auth(api_key: str = Security(API_KEY_HEADER)) -> str:
    await verify_api_key(api_key)
    return api_key
