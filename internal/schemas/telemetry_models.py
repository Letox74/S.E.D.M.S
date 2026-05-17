from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TelemetryBase(BaseModel):
    device_id: str = Field(
        default=...,
        description="The generated uuid id for the Device, where the telemetry data is from",
        examples=["57f087ae-4b24-473d-bb52-9efeb1d36ba6"]
    )

    voltage: float | int = Field(
        default=...,
        description="The current voltage of the Device, measured in Volts",
        examples=[230.5, 400.0],
        ge=0,
        le=500
    )

    current: float | int = Field(
        default=...,
        description="The electric current, measured in Ampere",
        examples=[12.4],
        ge=0,
        le=100
    )

    signal_strength: float | int = Field(
        default=...,
        description="Received signal strength indicator in dBm. Values closer to 0 indicate a stronger signal",
        examples=[-65.5],
        ge=-140,
        le=0
    )

    frequency: float | int = Field(
        default=...,
        description="Grid frequency in Hertz",
        examples=[50.0],
        ge=45,
        le=65
    )

    temperature: float | int = Field(
        default=...,
        description="The temperature of the Device, measured in Celcius",
        examples=[30.0, 23.4],
        ge=-20,
        le=100
    )

    current_battery_percentage: float | int = Field(
        default=-1.0,  # if the Device does not have a battery
        description="The current battery percentage of the Device",
        examples=[43.2, 76.9],
        ge=-1,
        le=100
    )


class TelemetryCreate(TelemetryBase):
    pass


class TelemetryRead(TelemetryBase):
    id: int = Field(
        default=...,
        description="The generated ID of the data",
        ge=0
    )

    timestamp: datetime = Field(
        default=...,
        description="The time when the data was inserted in the database"
    )

    device_name: Optional[str] = Field(
        default=None,
        description="The name of the Device",
        min_length=3,
        max_length=20
    )

    device_location: Optional[str] = Field(
        default=None,
        description="Where the Device is located",
        max_length=50
    )
