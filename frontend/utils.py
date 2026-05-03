from dataclasses import dataclass
from typing import Optional, Any

import httpx
from starlette import status

from core.config import BASE_URL, PORT, PREFIX, API_KEY

URL = BASE_URL + str(PORT) + PREFIX


@dataclass(kw_only=True)
class APIResponse:
    status_code: int
    data: Optional[Any] = None
    error_detail: Optional[str] = None

    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 300


class APIClient:
    def __init__(self, base_url: str, api_key: str) -> None:
        self.base_url = base_url
        self._headers = {"API-KEY": api_key}

    async def request(self, method: str, path: str, **kwargs) -> APIResponse:
        with httpx.Client(base_url=self.base_url, headers=self._headers) as client:
            try:
                response = client.request(method, path, **kwargs)
                return APIResponse(
                    status_code=response.status_code,
                    data=response.json() if response.status_code != status.HTTP_204_NO_CONTENT else None
                )

            except Exception as e:
                return APIResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, error_detail=str(e))

    # for the CSV Download
    async def get_stream(self, path: str, **kwargs) -> bytes:
        return httpx.get(f"{self.base_url}{path}", headers=self._headers, **kwargs).content


api_client = APIClient(URL, API_KEY)
