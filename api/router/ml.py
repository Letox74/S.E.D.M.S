from datetime import datetime, date
from typing import Optional, Literal, Never
from uuid import UUID

from fastapi import APIRouter, status, Depends, Query, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse

from api.dependencies import (
    get_db_session,
    validate_device_exists,
    validate_device_has_telemetry,
    validate_daterange,
    validate_device_has_analytics,
    validate_predictions_exists,
    validate_enough_analytics
)
from core.config import PREDICTION_HORIZONS
from database.connection import DatabaseManager
from internal.schemas.prediction_models import PredictionRead
from internal.service import ml_service
from .utils import to_csv

ml_router = APIRouter(
    prefix="/ml",
    tags=["ML"]
)


@ml_router.get(
    path="/predict",
    description="Get a prediction in a horizon",
    response_model=PredictionRead,
    status_code=status.HTTP_200_OK
)
async def get_prediction(
        device_id: Optional[UUID] = Query(default=None, description="Optional Device ID"),
        horizon_minutes: int = Query(default=..., description="The prediction horizon in minutes", ge=0, le=PREDICTION_HORIZONS[-1]),
        db: DatabaseManager = Depends(get_db_session)
) -> PredictionRead:
    if not await ml_service.check_if_models_are_loaded():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No model loaded"
        )

    if device_id:
        device_id = str(device_id)
        await validate_device_exists(device_id, db)
        await validate_device_has_analytics(device_id, db)

    return await ml_service.get_prediction(device_id, horizon_minutes, db)


@ml_router.post(
    path="/retrain",
    description="Retrains the models on the current data",
    status_code=status.HTTP_202_ACCEPTED
)
async def retrain_models(
        bg_task: BackgroundTasks,
        optimize: bool = Query(default=True, description="If the Models should be optimized"),
        db: DatabaseManager = Depends(get_db_session)
) -> dict[str, str | bool]:
    await validate_enough_analytics(db)
    bg_task.add_task(ml_service.retrain_models, optimize, db)

    return {"info": "retraining started", "optimize": optimize}


@ml_router.get(
    path="/metadata",
    description="Get the model metadata history",
    status_code=status.HTTP_200_OK
)
async def get_model_metadata(
        after: Optional[date] = Query(default=None, description="A date after what date the data should be returned"),
        version: Optional[str] = Query(default=None, description="Get a specific version")
) -> dict[str, dict[str, str | list[dict[str, str | dict[str, float | int]]]]] | None:
    return await ml_service.get_model_metadata(after, version)


@ml_router.delete(
    path="/metadata/clear",
    description="clear the metadata after a date",
    status_code=status.HTTP_200_OK
)
async def clear_metadata_history(
        before: date = Query(default=..., description="Before which date")
) -> None:
    await ml_service.clear_model_metadata(before)


@ml_router.get(
    path="/predictions/latest",
    description="Get the lastest Prediction data",
    response_model=PredictionRead,
    status_code=status.HTTP_200_OK
)
async def get_latest_prediction(
        device_id: Optional[UUID] = Query(default=None, description="The Device ID"),
        db: DatabaseManager = Depends(get_db_session)
) -> PredictionRead | None:
    await validate_predictions_exists(db)

    device_id = str(device_id) if device_id else None

    if device_id:
        await validate_device_exists(device_id, db)
        await validate_device_has_telemetry(device_id, db)

    return await ml_service.db_get_latest_prediction(device_id, db)


@ml_router.get(
    path="/predictions/history",
    description="Gets the Predictions History with optional arguments like dates and limits",
    response_model=list[PredictionRead],
    status_code=status.HTTP_200_OK
)
async def get_prediction_history(
        device_id: Optional[UUID] = Query(default=None, description="The Device ID"),
        start_datetime: Optional[datetime] = Query(default=None, description="The start datetime"),
        end_datetime: Optional[datetime] = Query(default=None, description="The end datetime"),
        limit: Optional[int] = Query(default=20, ge=0, description="A optional limit"),
        db: DatabaseManager = Depends(get_db_session)
) -> list[PredictionRead] | list[Never]:
    await validate_predictions_exists(db)

    device_id = str(device_id) if device_id else None

    if device_id:
        await validate_device_exists(device_id, db)
        await validate_device_has_telemetry(device_id, db)
    daterange = await validate_daterange(start_datetime, end_datetime)

    return await ml_service.db_get_predictions_history(device_id, daterange, limit, db)


@ml_router.get(
    path="/predictions/range",
    description="Get the Prediction data in a daterange",
    response_model=list[PredictionRead],
    status_code=status.HTTP_200_OK
)
async def get_predictions_range(
        device_id: Optional[UUID] = Query(default=None, description="The Device ID"),
        start_datetime: datetime = Query(default=..., description="The start datetime"),
        end_datetime: datetime = Query(default=..., description="The end datetime"),
        db: DatabaseManager = Depends(get_db_session)
) -> list[PredictionRead] | list[Never]:
    await validate_predictions_exists(db)

    device_id = str(device_id) if device_id else None

    if device_id:
        await validate_device_exists(device_id, db)
        await validate_device_has_telemetry(device_id, db)
    daterange = await validate_daterange(start_datetime, end_datetime)

    return await ml_service.db_get_predictions_range(device_id, daterange, db)


@ml_router.delete(
    path="/predictions/clear",
    description="Clears the Prediction data",
    status_code=status.HTTP_200_OK
)
async def clear_predictions(
        device_id: Optional[UUID] = Query(default=None, description="The Device ID"),
        before: Optional[datetime] = Query(default=None, description="Only clear before this datetime"),
        limit: Optional[int] = Query(default=50, ge=0, description="A optional limit"),
        db: DatabaseManager = Depends(get_db_session)
) -> dict[str, str | int]:
    await validate_predictions_exists(db)

    device_id = str(device_id) if device_id else None

    if device_id:
        await validate_device_exists(device_id, db)
        await validate_device_has_telemetry(device_id, db)
    deleted_rows = await ml_service.db_delete_predictions(device_id, before, limit, db)

    return {"deleted_rows": deleted_rows}


@ml_router.get(
    path="/predictions/count",
    description="Cont how many entries there are",
    status_code=status.HTTP_200_OK
)
async def get_predictions_count(
        device_id: Optional[UUID] = Query(default=None, description="The Device ID"),
        db: DatabaseManager = Depends(get_db_session)
) -> dict[str, str | int]:
    await validate_predictions_exists(db)

    device_id = str(device_id) if device_id else None

    if device_id:
        await validate_device_exists(device_id, db)
        await validate_device_has_telemetry(device_id, db)
    count = await ml_service.db_predictions_count(device_id, db)

    return {"count": count}


@ml_router.get(
    path="/info/status",
    description="Check if the models are loaded",
    status_code=status.HTTP_200_OK
)
async def get_ml_status() -> dict[str, bool]:
    result = await ml_service.check_if_models_are_loaded()
    return {"loaded": result}


@ml_router.get(
    path="/export/all",
    description="Export all prediction data",
    response_model=None,
    status_code=status.HTTP_200_OK
)
async def export_all_predictions(
        file_format: Literal["json", "csv"] = Query(default="json", description="The format of the returned data"),
        start_datetime: Optional[datetime] = Query(default=None, description="The start datetime"),
        end_datetime: Optional[datetime] = Query(default=None, description="The end datetime"),
        limit: Optional[int] = Query(default=None, ge=0, description="A limit"),
        db: DatabaseManager = Depends(get_db_session)
) -> list[PredictionRead] | list[Never] | StreamingResponse:
    await validate_predictions_exists(db)

    daterange = await validate_daterange(start_datetime, end_datetime)
    data = await ml_service.db_get_predictions_history(None, daterange, limit, db)

    if not data:
        return []

    if file_format == "csv":
        return to_csv(data)

    return data
