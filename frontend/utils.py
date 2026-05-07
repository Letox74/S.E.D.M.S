from dataclasses import dataclass
from typing import Optional

import httpx
import streamlit as st
from starlette import status

from core.config import BASE_URL, API_PORT, PREFIX, API_KEY, FRONTEND_PASSWORD

URL = f"{BASE_URL}:{API_PORT}{PREFIX}"


@dataclass(kw_only=True)
class APIResponse:
    status_code: int
    data: Optional[dict | list] = None
    error_detail: Optional[str] = None

    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 300


class APIClient:
    def __init__(self, base_url: str, api_key: str) -> None:
        self.base_url = base_url
        self._headers = {"API-KEY": api_key}

    def request(self, method: str, path: str, **kwargs) -> APIResponse:
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
    def get_stream(self, path: str, **kwargs) -> bytes:
        return httpx.get(f"{self.base_url}{path}", headers=self._headers, **kwargs).content


api_client = APIClient(URL, API_KEY)


def check_for_password_verification(main_page: bool = False) -> None:
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        place_holder = st.empty()

        if main_page:
            if password := place_holder.text_input("Enter the password", type="password", placeholder="password..."):
                if password == FRONTEND_PASSWORD:
                    st.session_state.authenticated = True
                    place_holder.empty()
                    st.rerun()

                else:
                    st.error("Wrong password")
                    st.stop()

            st.stop()


        else:
            st.error("Not verified yet. Please go to the Dashboard to verify")
            st.stop()
