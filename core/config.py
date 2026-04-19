import os
from pathlib import Path

from dotenv import load_dotenv

ENV_PATH = Path(__file__).parent.parent.resolve() / ".env"

load_dotenv(dotenv_path=ENV_PATH)

# general
VERSION: str = "0.1.0"

# path to the db
DB_PATH: Path = Path(__file__).parent.parent.resolve() / "database" / "storage.db"

# api key
API_KEY: str = os.getenv("API_KEY")

# api stuff
DOCS_URL: str | None = "/sedms/api/docs"
REDOC_URL: str | None = "/sedms/api/redoc"
OPENAPI_URL: str | None = "/sedms/api/openapi.json"

# rate limits
DEFAULT_RATE_LIMIT: str = "35/minute"
DEFAULT_TELEMETRY_RATE_LIMIT: str = "60/minute"
ACTIVATE_RATE_LIMITS: bool = True
