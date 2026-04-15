from slowapi import Limiter
from slowapi.util import get_remote_address

from core.config import DEFAULT_RATE_LIMIT  # can be set in .env (standard is 35/minute)

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[DEFAULT_RATE_LIMIT]
)  # define limiter
