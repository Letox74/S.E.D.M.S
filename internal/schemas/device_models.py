from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class DeviceTypes(str, Enum):
    SMART_METER = "smart_meter"  # measures and records electricity, gas or water consumption
    THERMOSTAT = "thermostat"  # detects the ambient temperature and controls heating or cooling systems to maintain a setpoint
    HUMIDITY_SENSOR = "humidity_sensor"  # measures the amount of water vapor in the air, often used in HVAC or greenhouse automation
    SOLAR_INVERTER = "solar_inverter"  # converts DC electricity from solar panels into AC electricity for home use or grid feed-in
    EV_CHARGER = "ev_charger"  # supplies electric energy for the recharging of electric vehicles
    HEAT_PUMP = "heat_pump"  # a device that transfers thermal energy from a source to a heat sink for climate control
    VIBRATION_SENSOR = "vibration_sensor"  # detects mechanical oscillations, curcial for predictive maintenance of industrial machines
    PRESSURE_GAUGE = "pressure_gauge"  # measures the force exerted by fluids or gases, used in pipes, tanks or pneumatic systems
    FLOW_METER = "flow_meter"  # quantifies the volume or mass of a liquid or gas moving through a pipe per unit of time
    ACOUSTIC_SENSOR = "acoustic_sensor"  # detects sound waves or noise levels, used for security, noise pollution monitoring, or failure detection
    CO2_MONITOR = "co2_monitor"  # measures the concentraction of carbon dioxide in the air to ensure proper indoor air quality
    MOTION_DETECTOR = "motion_detector"  # uses PIR or microwave technology to sense movement, typically for security or lightning control
    SMOKE_DETECTOR = "smoke_detector"  # senses smoke or combustion particles to provide an early warning of potential fire hazards
    PH_SENSOR = "ph_sensor"  # measures the acidity or alkalinty of a liquid, essential for water treatment and chemical precesses
    VALVE_ACTUATOR = "valve_actuator"  # a mechanical device for opening and closing a valve, allowing remote control of fluid flow

    @classmethod
    async def values(cls) -> list[str]:
        return [enum.value for enum in cls]


class DeviceStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    ERROR = "error"

    @classmethod
    async def values(cls) -> list[str]:
        return [enum.value for enum in cls]


class DeviceBase(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    name: str = Field(
        default=...,
        description="The name of the Device",
        min_length=3,
        max_length=20
    )

    type: DeviceTypes = Field(
        default=...,
        description="The type of the Device",
    )

    firmware_version: str = Field(
        default=...,
        description="The firmware version of the Device",
        min_length=5,
        max_length=32
    )

    description: Optional[str] = Field(
        default=None,
        description="The descripton of the Device. The description is optional",
        max_length=200
    )

    status: Optional[DeviceStatus] = Field(
        default="online",
        description="The current status of Device"
    )


class DeviceCreate(DeviceBase):
    is_active: Optional[bool] = Field(
        default=True,
        description="If the Device is currently active. Default is True",
        examples=[True, False]
    )

    has_battery: bool = Field(
        default=...,
        description="If the Device has a battery"
    )


class DeviceUpdate(DeviceBase):
    name: Optional[str] = Field(
        default=None,
        description="The name of the Device",
        min_length=3,
        max_length=20
    )

    type: Optional[DeviceTypes] = Field(
        default=None,
        description="The type of the Device",
    )

    firmware_version: Optional[str] = Field(
        default=None,
        description="The firmware version of the Device",
        min_length=5,
        max_length=32
    )

    description: Optional[str] = Field(
        default=None,
        description="The descripton of the Device",
        max_length=200
    )

    status: Optional[DeviceStatus] = Field(
        default=None,
        description="The current status of the Device",
    )

    is_active: Optional[bool] = Field(
        default=None,
        description="If the Device is currently active"
    )


class DeviceRead(DeviceBase):
    id: UUID = Field(
        default=...,
        description="The generated uuid ID for the Device"
    )

    is_active: bool = Field(
        default=True,
        description="If the Device is currently active"
    )

    created_at: datetime = Field(
        default=...,
        description="The time the Device was registered"
    )

    modified_at: datetime = Field(
        default=...,
        description="When the Device was last modified"
    )