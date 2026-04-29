import asyncio
import logging
import time
from uuid import uuid4

import lightgbm as lgbm
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder

from core.config import PREDICTION_HORIZONS
from database.connection import DatabaseManager
from .evaluator import evaluate_model
from .handler import save_model, save_model_metadata
from .optimizer import optimize_regression_model
from .processor import create_data

app_logger = logging.getLogger("App")


async def train_models(optimize: bool, analytics_count: int, db: DatabaseManager) -> None | str:
    await asyncio.gather(
        train_regression(optimize, analytics_count, db),
        train_isolation_forest(analytics_count, db)
    )



def _get_regression_parameters(analytics_count: int) -> dict[str, float | int | list[str]]:
    return {
        "n_estimators": 180 if analytics_count < 10_000 else 350,
        "max_depth": 4 if analytics_count < 10_000 else 5,
        "learning_rate": 0.1 if analytics_count < 10_000 else 0.04,
        "num_leaves": 20 if analytics_count < 10_000 else 35,
        "min_data_in_leaf": 15 if analytics_count < 10_000 else 28,
        "feature_fraction": 0.85 if analytics_count < 10_000 else 0.7,
        "min_gain_to_split": 0.5 if analytics_count < 10_000 else 0.6,
        "verbosity": -1,
        "cat_features": ["type"],
        "n_jobs": -1,
        "random_state": 42
    }


def _get_train_test_split(X, y):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train, y_train, test_size=0.2, random_state=42
    )

    return X_train, X_val, X_test, y_train, y_val, y_test


async def _train_regression_model(X, y, name, optimize: bool, analytics_count: int) -> None:
    X_train, X_val, X_test, y_train, y_val, y_test = _get_train_test_split(X, y) # get the prepared data
    best_params = None

    if not optimize:
        lgbm_model = lgbm.LGBMRegressor(**_get_regression_parameters(analytics_count))
        lgbm_model.fit(X_train, y_train, eval_set=[(X_val, y_val)],
                            callbacks=[lgbm.callback.early_stopping(25, verbose=False)])

        preds = lgbm_model.predict(X_test)

    else:
        lgbm_model, best_params = await optimize_regression_model(analytics_count, X_train, X_val, X_test, y_train, y_val, y_test)
        preds = lgbm_model.predict(X_test)

    metrics = await evaluate_model(preds, y_test)
    save_model(lgbm_model, name)
    save_model_metadata(lgbm_model, name, metrics, best_params)


async def train_regression(optimize: bool, analytics_count: int, db: DatabaseManager) -> None:
    id = str(uuid4())
    start_time = time.perf_counter()

    app_logger.info(f"ID: {id}\t Model training started (Optimize: {optimize})")

    model_data = await asyncio.gather(*[create_data(db, minutes) for minutes in PREDICTION_HORIZONS])
    await asyncio.gather(*[_train_regression_model(data[i][0], data[i][1], name, optimize, analytics_count)
                                    for name, i, data in zip(["15min", "1h", "6h"], enumerate(model_data))])

    app_logger.info(f"ID: {id}\t Model training ended, took {((time.perf_counter() - start_time) / 60):.2f} minutes")


def _get_iso_forest_parameters(analytics_count: int) -> dict[str, float | str | int]:
    return {
        "n_estimators": 100 if analytics_count < 50_000 else 200,
        "max_features": 0.8 if analytics_count < 30_000 else 0.6,
        "max_samples": "auto",
        "contamination": "auto",
        "verbose": 0,
        "n_jobs": -1,
        "random_state": 42
    }


async def train_isolation_forest(analytics_count: int, db: DatabaseManager) -> None:
    training_data = await create_data(db, 15)
    training_data = training_data[0]

    # define the column transformer for the status column
    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1), ["status"])
        ],
        remainder="passthrough"
    )

    # create the pipeline for the isolaion forest
    iso_forest_pipe = Pipeline([
        ("preprocessor", preprocessor),
        ("iso_forest", IsolationForest(**_get_iso_forest_parameters(analytics_count)))
    ])
    iso_forest_pipe.fit(training_data)

    save_model(iso_forest_pipe, None)