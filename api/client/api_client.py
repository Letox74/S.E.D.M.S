from dataclasses import dataclass
from typing import Optional

import httpx
from starlette import status

from core.config import settings

API_URL = f"{settings.base_url}:{settings.api.port}{settings.api.urls.prefix}"


@dataclass(kw_only=True)
class APIResponse:
    status_code: int
    data: Optional[dict | list] = None
    error_detail: Optional[str] = None

    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 300


class APIClient:
    def __init__(self) -> None:
        self.base_url = API_URL
        self._headers = {"API-KEY": settings.api.key}

    def sync_request(self, method: str, path: str, **kwargs) -> APIResponse:
        with httpx.Client(base_url=self.base_url, headers=self._headers) as client:
            try:
                response = client.request(method, path, **kwargs)
                return APIResponse(
                    status_code=response.status_code,
                    data=response.json() if response.status_code != status.HTTP_204_NO_CONTENT else None
                )

            except Exception as e:
                return APIResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, error_detail=str(e))


    async def async_request(self, method: str, path: str, **kwargs) -> APIResponse:
        async with httpx.AsyncClient(base_url=self.base_url, headers=self._headers) as client:
            try:
                response = await client.request(method, path, **kwargs)
                return APIResponse(
                    status_code=response.status_code,
                    data=response.json() if response.status_code != status.HTTP_204_NO_CONTENT else None
                )

            except Exception as e:
                return APIResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, error_detail=str(e))