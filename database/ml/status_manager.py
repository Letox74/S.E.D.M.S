import json
from pathlib import Path

JSON_PATH = Path(__file__).parent.resolve() / "retraining_status.json"


def set_retraining_status(status: bool) -> None:
    with open(JSON_PATH, "w", encoding="utf-8") as file:
        json.dump({"is_retraining": status}, file, indent=4, ensure_ascii=True)


def get_current_status() -> bool:
    with open(JSON_PATH, "r", encoding="utf-8") as file:
        return json.load(file)["is_retraining"]
