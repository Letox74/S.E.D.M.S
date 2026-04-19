from datetime import datetime

from pydantic import BaseModel, Field


class TelemetryBase(BaseModel):
    voltage: float = Field(
        default=...,
        description="The current voltage of the device or sensor, measured in volts",
        examples=[230.5, 400],
        ge=0,
        le=500
    )

    current: float = Field(
        default=...,
        description="The electric current, measured in ampere",
        examples=[12.4],
        ge=0,
        le=100
    )

    frequency: float = Field(
        default=...,
        description="Grid frequency in Hertz",
        examples=[50.01],
        ge=45,
        le=65
    )

    signal_strength: float = Field(
        default=...,
        description="Received Signal Strength Indicator in dBm. Values closer to 0 indicate a stronger signal",
        examples=[-65.5],
        ge=-140,
        le=0
    )


class TelemetryCreate(TelemetryBase):
    device_id: str = Field(
        default=...,
        description="The generated uuid id for the device or sensor, where the telemetry data is from",
        min_length=36,
        max_length=36
    )


class TelemtryRead(TelemetryBase):
    id: int = Field(
        default=...,
        description="The generated id of the data",
        ge=0
    )

    timestamp: datetime = Field(
        default=...,
        description="The time when the data was in the database"
    )
