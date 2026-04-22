from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PredictionBase(BaseModel):
    device_id: UUID = Field(
        default=...,
        description="The generated uuid for the Device, where the prediction data is from"
    )

    predicted_load: float = Field(
        default=...,
        description="The predicted power consumption in Watts over the next X hours",
        ge=0.0
    )

    actual_load: Optional[float] = Field(
        default=None,
        description="The actual power consumption in Watts",
        ge=0.0
    )

    prediction_error: Optional[float] = Field(  # calculated by actual_load - predicted_load
        default=None,
        description="How wrong the model was"
    )

    anomaly_score: float = Field(
        default=...,
        description="How confident the model is with the prediction (0 very confident, 1 complete anomaly)",
        ge=0.0,
        le=1.0
    )

    is_anomaly: bool = Field(
        default=...,
        description="If it the prediction is anomaly, by a Threshold",
    )

    feature_importance: str = Field(
        default=...,
        description="The most important features according to the model (JSON String)"
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


class PredictionCreate(PredictionBase):
    pass


class PredictionRead(PredictionBase):
    id: int = Field(
        default=...,
        description="The generated id of the data",
        ge=0
    )

    timestamp: datetime = Field(
        default=...,
        description="The time when the prediction was made"
    )
