from dotenv import load_dotenv
from pathlib import Path
import os

ENV_PATH = Path().cwd() / ".env"
load_dotenv(dotenv_path=ENV_PATH)

DB_PATH = os.getenv("DB_PATH")
API_KEY = os.getenv("API_KEY")