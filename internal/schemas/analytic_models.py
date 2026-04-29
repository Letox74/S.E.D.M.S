from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# add only simple validation, because the model is only used for internal stuff
class AnalyticsBase(BaseModel):
    device_id: str = Field(
        default=...,
        description="The generated uuid for the Device, where the analytic data is from"
    )

    avg_power: float = Field(
        default=...,
        description="The average power of the Device, measured in Watts (W)",
        ge=0,
        le=50_000  # calculated by the max voltage * max current
    )

    peak_power: float = Field(
        default=...,
        description="The highest power of the Device, measured in Watts (W)",
        ge=0,
        le=50_000
    )

    min_power: float = Field(
        default=...,
        description="The lowest power of the Device, measured in Watts (W)",
        ge=0,
        le=50_000
    )

    std_power: float = Field(
        default=...,
        description="The standard devitation power of the Device, measured in Watts (W)",
        ge=0,
        le=50_000
    )

    avg_voltage: float = Field(
        default=...,
        description="The average voltage of the Device, measured in Volts (V)",
        ge=0,
        le=500
    )

    peak_voltage: float = Field(
        default=...,
        description="The highest voltage of the Device, measured in Volts (V)",
        ge=0,
        le=500
    )

    min_voltage: float = Field(
        default=...,
        description="The lowest voltage of the Device, measured in Volts (V)",
        ge=0,
        le=500
    )

    std_voltage: float = Field(
        default=...,
        description="The standard devitation voltage of the Device, measured in Volts (V)",
        ge=0,
        le=500
    )

    avg_current: float = Field(
        default=...,
        description="The average current of the Device, measured in Amperes (A)",
        ge=0,
        le=100
    )

    peak_current: float = Field(
        default=...,
        description="The highest current of the Device, measured in Amperes (A)",
        ge=0,
        le=100
    )

    min_current: float = Field(
        default=...,
        description="The lowest current of the Device, measured in Amperes (A)",
        ge=0,
        le=100
    )

    std_current: float = Field(
        default=...,
        description="The standard devitation current of the Device, measured in Amperes (A)",
        ge=0,
        le=100
    )

    avg_signal_strength: float = Field(
        default=...,
        description="The average signal strength of the Device, measured in decibel milliwatt (dBm)",
        ge=-140,
        le=0
    )

    peak_signal_strength: float = Field(
        default=...,
        description="The highest signal strength of the Device, measured in decibel milliwatt (dBm)",
        ge=-140,
        le=0
    )

    min_signal_strength: float = Field(
        default=...,
        description="The lowest signal strength of the Device, measured in decibel milliwatt (dBm)",
        ge=-140,
        le=0
    )

    std_signal_strength: float = Field(
        default=...,
        description="The standard devitation singal strength of the Device, measured in decibel milliwatt (dBm)",
        ge=0,
        le=140
    )

    avg_temperature: float = Field(
        default=...,
        description="The average temperature of the Device, measured in Celcius (°C)",
        ge=-20,
        le=70
    )

    peak_temperature: float = Field(
        default=...,
        description="The highest temperature of the Device, measured in Celcius (C)",
        ge=-20,
        le=70
    )

    min_temperature: float = Field(
        default=...,
        description="The lowest temperature of the Device, measured in Celcius (C)",
        ge=-20,
        le=70
    )

    std_temperature: float = Field(
        default=...,
        description="The standard devitation temperature of the Device, measured in Celcius (C)",
        ge=-20,
        le=70
    )

    avg_battery_percentage: float = Field(
        default=-1, # if the Device does not have a battery
        description="The average battery percentage of the Device",
        ge=-1,
        le=100
    )

    min_battery_percentage: float = Field(
        default=-1,
        description="The lowest battery percentage of the Device",
        ge=-1,
        le=100
    )

    efficiency_score: float = Field(
        default=...,
        description="How efficient the Device in percentage",
        ge=0,
        le=100
    )

    energy_consumption: float = Field(
        default=...,
        description="The energy consumption of the Device, measured in kilowatt-hours (kWh)",
        ge=0
    )

    last_reset: datetime = Field(
        default=...,
        description="The time when the Device was last resetet"
    )

    operation_hours: float = Field(
        default=...,
        description="The operating time of the Device in hours",
        ge=0
    )


class AnalyticsCreate(AnalyticsBase):
    pass


class AnalyticsRead(AnalyticsBase):
    id: int = Field(
        default=...,
        description="The generated id of the data",
        ge=0
    )

    timestamp: datetime = Field(
        default=...,
        description="When the analytic data was recorded"
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
        min_length=2,
        max_length=30
    )
