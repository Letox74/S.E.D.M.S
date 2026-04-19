from datetime import datetime

from pydantic import BaseModel, Field


class AnalyticsRead(BaseModel):
    id: int = Field(
        default=...,
        description="The generated id of the data",
        ge=0
    )

    device_id: str = Field(
        default=...,
        description="The generated uuid id for the device or sensor, where the analytic data is from",
        min_length=36,
        max_length=36
    )

    avg_power: float = Field(
        default=...,
        description="The average power of the device or sensor, measured in Watts (W)",
        ge=0
    )

    peak_power: float = Field(
        default=...,
        description="The highest power of the device or sensor, measured in Watts (W)",
        ge=0
    )

    min_power: float = Field(
        default=...,
        description="The lowest power of the device or sensor, measured in Watts (W)",
        ge=0
    )

    variance_power: float = Field(
        default=...,
        description="The variance power of the device or sensor, measured in Watts (W)",
        ge=0
    )

    operation_hours: float = Field(
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

    energy_consumption: float = Field(
        default=...,
        description="The energy consumption of the device or sensor, measured in kilowatt-hours (kWh)"
    )

    last_reset: datetime = Field(
        default=...,
        description="The time when the device or sensor was last resetet"
    )
