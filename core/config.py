import os
from pathlib import Path

from dotenv import load_dotenv

ENV_PATH = Path(__file__).parent.parent.resolve() / ".env"

load_dotenv(dotenv_path=ENV_PATH)

# path to the db
DB_PATH: Path = Path(__file__).parent.parent.resolve() / "database" / "storage.db"

# api key
API_KEY: str = os.getenv("API_KEY")

# rate limits
DEFAULT_RATE_LIMIT: str = "35/minute"
DEFAULT_TELEMETRY_RATE_LIMIT: str = "60/minute"
ACTIVATE_RATE_LIMITS: bool = True