import secrets

from dotenv import load_dotenv, set_key
from fastapi import HTTPException, status

from core.config import settings, ENV_PATH


def verify_api_key(provided_api_key: str) -> None:
    if not settings.api.key == provided_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The provided API-Key does not match with the saved one"
        )

def generate_new_api_key(nbytes: int = 32, override_in_env: bool = True):
    new_key = secrets.token_hex(nbytes)

    if override_in_env:
        set_key(ENV_PATH, "API_KEY", new_key)
        load_dotenv(override=True, dotenv_path=ENV_PATH)

    return new_key