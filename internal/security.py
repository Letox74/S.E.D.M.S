from fastapi import HTTPException, status

from core.config import API_KEY


async def verify_api_key(provided_api_key: str) -> None:
    if not API_KEY == provided_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The provided API-Key does not match with the saved one"
        )
