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

# URLs
BASE_URL: str = os.getenv("BASE_URL")
PORT: int = int(os.getenv("PORT"))

PREFIX: str = os.getenv("PREFIX")
DOCS_URL: Optional[str] = PREFIX + os.getenv("DOCS_URL")
REDOC_URL: Optional[str] = PREFIX + os.getenv("REDOC_URL")
OPENAPI_URL: Optional[str] = PREFIX + os.getenv("OPENAPI_URL")

# CORS
USE_CORS: bool = os.getenv("USE_CORS").lower().strip() in ("true", "1", "yes")
ALLOW_CREDENTIALS: bool = os.getenv("ALLOW_CREDENTIALS").lower().strip() in ("true", "1", "yes")
ALLOWED_ORIGINS: list[str] | list[Never] = list(os.getenv("ALLOWED_ORIGINS"))
ALLOWED_METHODS: list[str] | list[Never] = list(os.getenv("ALLOWED_METHODS"))
ALLOWED_HEADERS: list[str] | list[Never] = list(os.getenv("ALLOWED_HEADERS"))

# rate limits
DEFAULT_RATE_LIMIT: str = os.getenv("DEFAULT_RATE_LIMIT")
ACTIVATE_RATE_LIMITS: bool = os.getenv("ACTIVATE_RATE_LIMITS").lower().strip() in ("true", "1", "yes")

# Telemetry
TELEMETRY_LIMIT: int = int(os.getenv("TELEMETRY_LIMIT"))

# ml stuff (soon, just examples)
RETRAIN_SCHEDULER: Optional[str] = None

# four models in total
PREDICTION_HORIZONS: list[int] = list(map(lambda x: int(x), os.getenv("PREDICTION_HORIZONS").split(", "))) # in minutes
# can be refactored later, that the user decides the three models

# other stuff
IGNORE_WARNINGS: bool = os.getenv("IGNORE_WARNINGS").lower().strip() in ("true", "1", "yes")

# frontend
FRONTEND_PASSWORD: str = os.getenv("FRONTEND_PASSWORD")