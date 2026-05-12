import asyncio

from sklearn.metrics import (
    mean_squared_error,
    root_mean_squared_error,
    mean_absolute_error,
    r2_score
)


async def _get_mse(y_preds, y_true) -> float:
    return mean_squared_error(y_true, y_preds)


async def _get_rmse(y_preds, y_true) -> float:
    return root_mean_squared_error(y_true, y_preds)


async def _get_mae(y_preds, y_true) -> float:
    return mean_absolute_error(y_true, y_preds)


async def _get_r2(y_preds, y_true) -> float:
    return r2_score(y_true, y_preds)


async def evaluate_model(y_preds, y_true) -> dict[str, float]:
    results = await asyncio.gather(
        _get_mse(y_preds, y_true),
        _get_rmse(y_preds, y_true),
        _get_mae(y_preds, y_true),
        _get_r2(y_preds, y_true)
    )

    return {
        "mse": round(results[0], 2),
        "rmse": round(results[1], 2),
        "mae": round(results[2], 2),
        "r2": round(results[3], 2)
    }
