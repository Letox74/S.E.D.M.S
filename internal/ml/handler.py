import json
import logging
import pickle
from datetime import date
from datetime import datetime
from pathlib import Path
from typing import Optional, Literal

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.pipeline import Pipeline

from database.connection import DatabaseManager

app_logger = logging.getLogger("App")

MODELS_DIR = Path(__file__).parent.resolve() / "models"

LGBM_PATH_15min = MODELS_DIR / "lgbm_model_15min.pkl"
LGBM_PATH_1h = MODELS_DIR / "lgbm_model_1h.pkl"
LGBM_PATH_6h = MODELS_DIR / "lgbm_model_6h.pkl"
LGBM_PATH_24h = MODELS_DIR / "lgbm_model_24h.pkl"

ISO_FOREST_PATH = MODELS_DIR / "iso_forest.pkl"
METADATA_PATH = MODELS_DIR / "metadata.json"


def load_active_models(model_name: Literal["15min", "1h", "6h", "24h"]) -> tuple[LGBMRegressor, Pipeline] | None:
    if not all(path.exists() for path in (LGBM_PATH_15min, LGBM_PATH_1h, LGBM_PATH_6h, LGBM_PATH_24h, ISO_FOREST_PATH)):
        return None

    with open(MODELS_DIR / f"lgbm_model_{model_name}", "rb") as lgbm_file:
        lgbm_model = pickle.load(lgbm_file)

    with open(ISO_FOREST_PATH, "rb") as iso_forest_file:
        iso_forest_model = pickle.load(iso_forest_file)

    return lgbm_model, iso_forest_model


def save_model(model: LGBMRegressor | Pipeline, model_name: Optional[Literal["15min", "1h", "6h", "24h"]]) -> None:
    if isinstance(model, LGBMRegressor):
        with open(MODELS_DIR / f"lgbm_model_{model_name}", "wb") as lgbm_file:
            pickle.dump(model, lgbm_file)

    with open(ISO_FOREST_PATH, "rb") as iso_forest_file:
        pickle.dump(model, iso_forest_file)


def _increment_version(version: str) -> str:
    if version == "":
        return "0.0.1"

    parts = [int(p) for p in version.split('.')]

    parts[2] += 1  # increase the last part by 1

    # when the last part is greater than 9, increase the second part
    if parts[2] > 9:
        parts[2] = 0
        parts[1] += 1

    # if the second part is greater than 9, increase the first part
    if parts[1] > 9:
        parts[1] = 0
        parts[0] += 1

    return f"{parts[0]}.{parts[1]}.{parts[2]}"


def save_model_metadata(
        model: LGBMRegressor,
        model_name: str,
        metrics: dict[str, float],
        best_params: Optional[dict[str, float | int]]
) -> None:
    with open(METADATA_PATH, "r", encoding="utf-8") as metadata:
        metadata_json = json.load(metadata)

    new_version = _increment_version(metadata_json["models"]["model_name"]["current_version"])
    current_date = date.today().strftime("%Y-%m-%d")

    # get features importances
    importances = model.feature_importances_
    names = model.feature_name_
    indices = np.argsort(importances)[::-1][:10]

    features = {names[i]: float(importances[i]) for i in indices}

    metadata_json["last_updated"] = current_date
    history_dict = {
        "version": new_version,
        "date": current_date,
        "metrics": metrics,
        "features": features,
        "best_params": best_params
    }

    metadata_json["models"][model_name]["current_version"] = new_version
    metadata_json["models"][model_name]["history"].insert(0, history_dict)

    with open(METADATA_PATH, "w", encoding="utf-8") as metadata:
        json.dump(metadata_json, metadata, ensure_ascii=True, indent=4)

    app_logger.info(f"Model updated to version {new_version}, RMSE: {metrics["rmse"]}")


def _get_aggregations() -> dict[str, str]:
    return {
        "avg_power": "mean",
        "std_power": "mean",
        "avg_voltage": "mean",
        "avg_temperature": "mean",
        "efficiency_score": "mean",
        "energy_consumption": "sum",
        "current_battery_percentage": "last",
        "is_active": "max",
        "type": "first",
        "has_battery": "first"
    }

async def get_raw_data(device_id: Optional[str], after: Optional[datetime], db: DatabaseManager) -> pd.DataFrame:
    params = tuple([param for param in (device_id, after) if param is not None])

    where_clause = []
    if device_id:
        where_clause.append("T01.device_id = ?")
    if after:
        where_clause.append("T01.timestamp > ?")
    where_str = f"WHRE {" AND ".join(where_clause)}" if where_clause else ""

    sql = f"""
        SELECT
            T01.avg_power,
            T01.std_power,
            T01.avg_voltage
            T01.avg_temperature,
            T01.efficiency_score,
            T01.energy_consumption,
            T01.timestamp,
            
            T02.type,
            T02.is_active,
            T02.has_battery,
            
            T03.current_battery_percentage
        
        FROM analytics AS T01
        JOIN devices AS T02 ON T01.device_id = T02.id
        JOIN telemetry AS T03 ON T01.device_id = T03.device_id
        
        {where_str}
        
        ORDER BY T01.timestamp ASC;
    """
    rows = await db.fetch_all(sql, params)

    df = pd.DataFrame([dict(row) for row in rows])
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", yearfirst=True)
    df.set_index("timestamp", inplace=True)

    df.resample(f"15min").agg(_get_aggregations())  # lowest intervall of the three models
    df.ffill(inplace=True)

    return df
