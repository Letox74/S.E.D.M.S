import os
from pathlib import Path
from typing import Never, Optional

from dotenv import load_dotenv

ENV_PATH = Path(__file__).parent.parent.resolve() / ".env"

load_dotenv(dotenv_path=ENV_PATH)

# general
VERSION: str = "0.1.0"

# path to the db
DB_PATH: Path = Path(__file__).parent.parent.resolve() / "database" / "storage.db"

# api stuff
# api key
API_KEY: str = os.getenv("API_KEY")

# Docs Urls
DOCS_URL: Optional[str] = "/sedms/api/docs"
REDOC_URL: Optional[str] = "/sedms/api/redoc"
OPENAPI_URL: Optional[str] = "/sedms/api/openapi.json"

# CORS
USE_CORS: bool = False
ALLOW_CREDENTIALS: bool = True
ALLOWED_ORIGINS: list[str] | list[Never] = ["*"]
ALLOWED_METHODS: list[str] | list[Never] = ["*"]
ALLOWED_HEADERS: list[str] | list[Never] = ["*"]

# rate limits
DEFAULT_RATE_LIMIT: str = "35/minute"
ACTIVATE_RATE_LIMITS: bool = True


# ml stuff (soon, just examples)
IS_RETRAINING: bool = False
RETRAIN_SCHEDULER: Optional[str] = None