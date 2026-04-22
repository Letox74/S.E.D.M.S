from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# add only simple validation, because the model is only used for internal stuff
class AnalyticsBase(BaseModel):
    device_id: UUID = Field(
        default=...,
        description="The generated uuid for the Device, where the analytic data is from"
    )

    avg_power: float = Field(
        default=...,
        description="The average power of the Device, measured in Watts (W)",
        ge=0.0,
        le=50_000.0  # calculated by the max voltage * max current
    )

    peak_power: float = Field(
        default=...,
        description="The highest power of the Device, measured in Watts (W)",
        ge=0.0,
        le=50_000.0
    )

    min_power: float = Field(
        default=...,
        description="The lowest power of the Device, measured in Watts (W)",
        ge=0.0,
        le=50_000.0
    )

    std_power: float = Field(
        default=...,
        description="The standard devitation power of the Device, measured in Watts (W)",
        ge=0.0,
        le=50_000.0
    )

    avg_voltage: float = Field(
        default=...,
        description="The average voltage of the Device, measured in Volts (V)",
        ge=0.0,
        le=500.0
    )

    peak_voltage: float = Field(
        default=...,
        description="The highest voltage of the Device, measured in Volts (V)",
        ge=0.0,
        le=500.0
    )

    min_voltage: float = Field(
        default=...,
        description="The lowest voltage of the Device, measured in Volts (V)",
        ge=0.0,
        le=500.0
    )

    std_voltage: float = Field(
        default=...,
        description="The standard devitation voltage of the Device, measured in Volts (V)",
        ge=0.0,
        le=500.0
    )

    avg_current: float = Field(
        default=...,
        description="The average current of the Device, measured in Amperes (A)",
        ge=0.0,
        le=100.0
    )

    peak_current: float = Field(
        default=...,
        description="The highest current of the Device, measured in Amperes (A)",
        ge=0.0,
        le=100.0
    )

    min_current: float = Field(
        default=...,
        description="The lowest current of the Device, measured in Amperes (A)",
        ge=0.0,
        le=100.0
    )

    std_current: float = Field(
        default=...,
        description="The standard devitation current of the Device, measured in Amperes (A)",
        ge=0.0,
        le=100.0
    )

    avg_signal_strength: float = Field(
        default=...,
        description="The average signal strength of the Device, measured in decibel milliwatt (dBm)",
        ge=-140.0,
        le=0.0
    )

    peak_signal_strength: float = Field(
        default=...,
        description="The highest signal strength of the Device, measured in decibel milliwatt (dBm)",
        ge=-140.0,
        le=0.0
    )

    min_signal_strength: float = Field(
        default=...,
        description="The lowest signal strength of the Device, measured in decibel milliwatt (dBm)",
        ge=-140.0,
        le=0.0
    )

    std_signal_strength: float = Field(
        default=...,
        description="The standard devitation singal strength of the Device, measured in decibel milliwatt (dBm)",
        ge=-140.0,
        le=0.0
    )

    avg_temperature: float = Field(
        default=...,
        description="The average temperature of the Device, measured in Celcius (°C)",
        ge=-20.0,
        le=70.0
    )

    peak_temperature: float = Field(
        default=...,
        description="The highest temperature of the Device, measured in Celcius (C)",
        ge=-20.0,
        le=70.0
    )

    min_temperature: float = Field(
        default=...,
        description="The lowest temperature of the Device, measured in Celcius (C)",
        ge=-20.0,
        le=70.0
    )

    std_temperature: float = Field(
        default=...,
        description="The standard devitation temperature of the Device, measured in Celcius (C)",
        ge=-20.0,
        le=70.0
    )

    avg_battery_percentage: float = Field(
        default=-1.0, # if the Device does not have a battery
        description="The average battery percentage of the Device",
        ge=-1.0,
        le=100.0
    )

    min_battery_percentage: float = Field(
        default=-1.0,
        description="The lowest battery percentage of the Device",
        ge=-1.0,
        le=100.0
    )

    efficiency_score: float = Field(
        default=...,
        description="How efficient the Device in percentage",
        ge=0,
        le=1
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
