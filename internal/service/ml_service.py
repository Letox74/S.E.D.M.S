import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta, date
from pathlib import Path
from typing import Never, Optional

import lightgbm as lgbm
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline

from core.config import PREDICTION_HORIZONS
from database.connection import DatabaseManager
from internal.ml.handler import load_active_models
from internal.ml.processor import create_data
from internal.ml.trainer import train_models
from internal.schemas.prediction_models import PredictionCreate, PredictionRead
from .utils import (
    db_insert_new_row,
    db_get_latest_row,
    db_get_range,
    db_get_history,
    db_delete,
    db_count
)

ml_logger = logging.getLogger("ML")

MODELS_DIR = Path(__file__).parent.parent.resolve() / "ml" / "models"

LGBM_PATH_15min = MODELS_DIR / "lgbm_model_15min.pkl"
LGBM_PATH_1h = MODELS_DIR / "lgbm_model_1h.pkl"
LGBM_PATH_6h = MODELS_DIR / "lgbm_model_6h.pkl"
LGBM_PATH_24h = MODELS_DIR / "lgbm_model_24h.pkl"

ISO_FOREST_PATH = MODELS_DIR / "iso_forest.pkl"

METADATA_PATH = MODELS_DIR / "metadata.json"


@dataclass
class LGBMPredictionModel:
    model: lgbm.LGBMRegressor
    horizon_minutes: int
    name: str


@dataclass
class PredicionModels:
    lgbm_models: list[LGBMPredictionModel]
    iso_forest: Pipeline


def _get_prediction_models(
        horizon_minutes: int
) -> PredicionModels:
    # get the models that fit the prediction horizon
    horizon_mapping = dict(zip(PREDICTION_HORIZONS, ["15min", "1h", "6h", "24h"]))
    lower_horizons = [horizon for horizon in horizon_mapping if horizon <= horizon_minutes]
    upper_horizons = [horizon for horizon in horizon_mapping if horizon >= horizon_minutes]

    # get the best model
    lower_model = lower_horizons[-1]
    higher_model = upper_horizons[0]

    needed_horizons = sorted(list({lower_model, higher_model}))  # set to prevent the same model

    loaded_models = []
    final_iso_forest = None

    for model in needed_horizons:
        name = horizon_mapping[model]
        lgbm_model, iso_forest = load_active_models(name)

        loaded_models.append(LGBMPredictionModel(lgbm_model, model, name))
        final_iso_forest = iso_forest

    return PredicionModels(lgbm_models=loaded_models, iso_forest=final_iso_forest)


async def _update_prediction_errors(db: DatabaseManager) -> None:
    sql = """
        WITH CalculatedPredictions AS (
            SELECT 
                T01.id,
                datetime(T01.timestamp, '+' || T01.prediction_horizon_minutes || ' minutes') AS end_timestamp,
                (
                    SELECT SUM(T02.energy_consumption)
                    FROM analytics AS T02
                    WHERE T02.timestamp >= T01.timestamp 
                      AND T02.timestamp < datetime(T01.timestamp, '+' || T01.prediction_horizon_minutes || ' minutes')
                ) AS actual_load_sum
            FROM predictions AS T01
            WHERE T01.actual_load IS NULL 
              AND T01.prediction_error IS NULL
              AND datetime(T01.timestamp, '+' || T01.prediction_horizon_minutes || ' minutes') <= (SELECT MAX(timestamp) FROM analytics)
        )
        UPDATE predictions
        SET 
            actual_load = T03.actual_load_sum,
            prediction_error = ABS(T03.actual_load_sum - predictions.predicted_load)
        FROM CalculatedPredictions AS T03
        WHERE predictions.id = T03.id;
    """
    updated_rows = await db.execute_transaction(sql)

    if updated_rows >= 1:
        ml_logger.info(f"Updated {updated_rows} rows")


def _calculate_the_prediction(
        lgbm1: lgbm.LGBMRegressor,
        lgbm1_horizon: int,
        lgbm2: lgbm.LGBMRegressor,
        lgbm2_horizon: int,
        horizon_minutes: int,
        data: pd.DataFrame
) -> float:
    prediction1 = lgbm1.predict(data)[0]
    prediction2 = lgbm2.predict(data)[0]

    # calculate distances
    dist_a = abs(horizon_minutes - lgbm1_horizon)
    dist_b = abs(lgbm2_horizon - horizon_minutes)
    total_dist = lgbm2_horizon - lgbm1_horizon

    return (prediction1 * (dist_b / total_dist)) + (prediction2 * (dist_a / total_dist))


def _calculate_confidence(iso_forest: Pipeline, data: pd.DataFrame) -> tuple[bool, float]:
    score = iso_forest.decision_function(data)[0]
    anomaly = iso_forest.predict(data)[0]

    k = 5
    x0 = -0.15
    return True if anomaly == 1 else False, (1 / (1 + np.exp(-k * (score - x0)))) * 100  # sigmoid function


def _get_model_version(name: str) -> str:
    with open(METADATA_PATH, "r", encoding="utf-8") as metadata:
        return json.load(metadata)["models"][name]["current_version"]


async def get_prediction(
        device_id: Optional[str],
        horizon_minutes: int,
        db: DatabaseManager
) -> PredictionRead:
    await _update_prediction_errors(db)

    # get the data to predict
    after = datetime.now(timezone.utc) - timedelta(hours=25)
    data = await create_data(device_id, after, horizon_minutes, db)
    prediction_data = data[0].iloc[-1:]

    models = _get_prediction_models(horizon_minutes)
    anomaly, confidence = _calculate_confidence(models.iso_forest, prediction_data)
    if len(models.lgbm_models) == 2:
        prediction = models.lgbm_models[0].model.predict(prediction_data)[0]
        version = _get_model_version(models.lgbm_models[0].name)

    else:
        prediction = _calculate_the_prediction(
            models.lgbm_models[0].model,
            models.lgbm_models[0].horizon_minutes,
            models.lgbm_models[1].model,
            models.lgbm_models[1].horizon_minutes,
            horizon_minutes,
            prediction_data
        )
        version1 = _get_model_version(models.lgbm_models[0].name)
        version2 = _get_model_version(models.lgbm_models[1].name)
        version = f"{version1} & {version2}"

    pred_create = PredictionCreate(
        device_id=device_id,
        predicted_load=prediction,
        is_anomaly=anomaly,
        confidence=confidence,
        prediction_horizon_minutes=horizon_minutes,
        model_version=version
    )
    return await db_insert_new_row(pred_create, "predictions", db)


async def retrain_models(optimize: bool, db: DatabaseManager) -> None:
    analytics_count = await db_count(None, "analytics", db)
    await train_models(optimize, analytics_count, db)


async def get_model_metadata(
        after: Optional[date],
        version: Optional[str]
) -> dict[str, dict[str, str | list[dict[str, str | dict[str, float | int]]]]] | None:
    with open(METADATA_PATH, "r", encoding="utf-8") as metadata:
        data = json.load(metadata)["models"]

    if isinstance(version, str) and version.lower() == "latest":
        return {
            name: {
                "current_version": model_info["current_version"],
                "history": [
                    history for history in model_info["history"]
                    if history["version"] == model_info["current_version"]
                ]
            }
            for name, model_info in data.items()
        }

    return {
        name: {
            "current_version": model_info["current_version"],
            "history": [
                history for history in model_info["history"]
                if (not version or history["version"] == version)
                   and (not after or datetime.strptime(history["date"], "%Y-%m-%d").date() > after)
            ]
        }
        for name, model_info in data.items()
    }


async def clear_model_metadata(before: date):
    with open(METADATA_PATH, "r+", encoding="utf-8") as metadata:
        data = json.load(metadata)
        current_date = date.today().strftime("%Y-%m-%d")
        data["last_updated"] = current_date

        for model_name in data["models"]:
            data["models"][model_name]["history"] = [
                entry for entry in data["models"][model_name]["history"]
                if datetime.strptime(entry["date"], "%Y-%m-%d").date() >= before
            ]

        metadata.seek(0)
        json.dump(data, metadata, indent=4)
        metadata.truncate()


async def db_get_latest_prediction(device_id: Optional[str], db: DatabaseManager) -> PredictionRead | None:
    return await db_get_latest_row(device_id, "predictions", db)


async def db_get_predictions_history(
        device_id: Optional[str],
        daterange: Optional[list[datetime]],
        limit: Optional[int],
        db: DatabaseManager
) -> list[PredictionRead] | list[Never]:
    return await db_get_history(device_id, daterange, limit, "predictions", db)


async def db_get_predictions_range(
        device_id: Optional[str],
        daterange: list[datetime],
        db: DatabaseManager
) -> list[PredictionRead] | list[Never]:
    return await db_get_range(device_id, daterange, "predictions", db)


async def db_delete_predictions(
        device_id: Optional[str],
        before: Optional[datetime],
        limit: Optional[int],
        db: DatabaseManager
) -> int:
    return await db_delete(device_id, before, limit, "predictions", db)


async def db_predictions_count(device_id: Optional[str], db: DatabaseManager) -> int:
    return await db_count(device_id, "predictions", db)


async def check_if_models_are_loaded() -> bool:
    if not all(path.exists() for path in (LGBM_PATH_15min, LGBM_PATH_1h, LGBM_PATH_6h, LGBM_PATH_24h, ISO_FOREST_PATH)):
        return False

    return True
