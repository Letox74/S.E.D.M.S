from datetime import datetime

from pydantic import BaseModel, Field


class TelemetryBase(BaseModel):
    device_id: str = Field(
        default=...,
        description="The generated uuid id for the Device, where the telemetry data is from",
        examples=["57f087ae-4b24-473d-bb52-9efeb1d36ba6"]
    )

    voltage: float = Field(
        default=...,
        description="The current voltage of the Device, measured in Volts",
        examples=[230.5, 400.0],
        ge=0.0,
        le=500.0
    )

    current: float = Field(
        default=...,
        description="The electric current, measured in Ampere",
        examples=[12.4],
        ge=0.0,
        le=100.0
    )

    signal_strength: float = Field(
        default=...,
        description="Received signal strength indicator in dBm. Values closer to 0 indicate a stronger signal",
        examples=[-65.5],
        ge=-140.0,
        le=0.0
    )

    frequency: float = Field(
        default=...,
        description="Grid frequency in Hertz",
        examples=[50.0],
        ge=45.0,
        le=65.0
    )

    temperature: float = Field(
        default=...,
        description="The temperature of the Device, measured in Celcius",
        examples=[30.0, 23.4],
        ge=-20.0,
        le=100.0
    )

    current_battery_percentage: float = Field(
        default=-1.0,  # if the Device does not have a battery
        description="The current battery percentage of the Device",
        examples=[43.2, 76.9],
        ge=0.0,
        le=100.0
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
