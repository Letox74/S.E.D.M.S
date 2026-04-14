import uuid
from datetime import datetime

from pydantic import BaseModel, Field

type Number = int | float


class AnalyticsRead(BaseModel):
    id: int = Field(
        default=...,
        description="The generated id of the data",
        examples=[3, 8, 24, 81],
        ge=0
    )

    device_id: uuid.UUID | str = Field(
        default=...,
        description="The generated uuid id for the device or sensor, where the analytic data is from",
        min_length=36,
        max_length=36
    )

    avg_power: Number = Field(
        default=...,
        description="The average power of the device or sensor, measured in Watts (W)",
        ge=0
    )

    peak_power: Number = Field(
        default=...,
        description="The highest power of the device or sensor, measured in Watts (W)",
        ge=0
    )

    min_power: Number = Field(
        default=...,
        description="The lowest power of the device or sensor, measured in Watts (W)",
        ge=0
    )

    variance_power: Number = Field(
        default=...,
        description="The variance power of the device or sensor, measured in Watts (W)",
        ge=0
    )

    operation_hours: Number = Field(
        default=...,
        description="The operating time of the sensor or device in hours",
        ge=0
    )

    efficiency_score: float = Field(
        default=...,
        description="How efficient the device or sensor is in percentage",
        ge=0,
        le=1
    )

    energy_consumption: Number = Field(
        default=...,
        description="The energy consumption of the device or sensor, measured in kilowatt-hours (kWh)"
    )

    last_reset: datetime = Field(
        default=...,
        description="The time when the device or sensor was last resetet"
    )
