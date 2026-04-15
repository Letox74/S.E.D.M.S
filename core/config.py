import os
from pathlib import Path

from dotenv import load_dotenv

ENV_PATH = Path().cwd() / ".env"
load_dotenv(dotenv_path=ENV_PATH)

# path to the db
DB_PATH: str = os.getenv("DB_PATH")

# api key
API_KEY: str = os.getenv("API_KEY")

# rate limits
DEFAULT_RATE_LIMIT: str = "35/minute"
ACTIVATE_RATE_LIMITS: bool = True