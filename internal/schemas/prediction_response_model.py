import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class PredictionRead(BaseModel):
    id: int = Field(
        default=...,
        description="The generated id of the data",
        examples=[3, 8, 24, 81],
        ge=0
    )

    device_id: uuid.UUID | str = Field(
        default=...,
        description="The generated uuid id for the device or sensor, where the prediction data is from",
        min_length=36,
        max_length=36
    )

    predicted_load: float = Field(
        default=...,
        description="The predicted power consumption in watts over the next X hours",
        ge=0
    )

    anomaly_score: float = Field(
        default=...,
        description="How confident the model is with the prediction (0 very confident, 1 complete anomaly)",
        ge=0,
        le=1
    )

    is_anomaly: bool = Field(
        default=...,
        description="If it the prediction is anomaly, by a Threshold",
    )

    feature_importance: str = Field(
        default=...,
        description="The most important features according to the model"
    )

    prediction_horizon_minutes: int = Field(
        default=...,
        description="How many minutes in the features this prediction is set",
        ge=0,
        le=1440  # 1 day
    )

    model_version: str = Field(
        default=...,
        description="Which model was used for the prediction"
    )

    timestamp: datetime = Field(
        default=...,
        description="The time when the prediction was made"
    )
