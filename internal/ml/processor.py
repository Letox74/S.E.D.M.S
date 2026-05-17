from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd

from database.connection import DatabaseManager
from .handler import get_raw_data


def _apply_sin_cos(df: pd.DataFrame, target_time) -> pd.DataFrame:
    # use sin and cos, so that the model understands that 23:00 is almost the same as 1:00
    df["hour_sin"] = np.sin(2 * np.pi * (target_time.hour / 24))
    df["hour_cos"] = np.cos(2 * np.pi * (target_time.hour / 24))

    df["day_sin"] = np.sin(2 * np.pi * (target_time.weekday / 7))
    df["day_cos"] = np.cos(2 * np.pi * (target_time.weekday / 7))

    df["month_sin"] = np.sin(2 * np.pi * (target_time.month - 1) / 12)
    df["month_cos"] = np.cos(2 * np.pi * (target_time.month - 1) / 12)

    return df


def _apply_lags_and_rolling(df: pd.DataFrame) -> pd.DataFrame:
    group = df.groupby("device_id")

    # power related
    df["avg_power_lag1"] = group["avg_power"].shift(1)  # 15min
    df["avg_power_lag2"] = group["avg_power"].shift(4)  # 1h
    df["avg_power_rolling"] = group["avg_power"].transform(lambda x: x.rolling(4).mean())  # 1h
    df["std_power_lag1"] = group["std_power"].shift(1)

    # voltage
    df["avg_voltage_lag1"] = group["avg_voltage"].shift(1)
    df["avg_voltage_rolling"] = group["avg_voltage"].transform(lambda x: x.rolling(8).std())  # 2h

    # temperature
    df["avg_temperature_lag1"] = group["avg_temperature"].shift(1)
    df["avg_temperature_rolling"] = group["avg_temperature"].transform(lambda x: x.rolling(12).mean())  # 3h

    # efficiency score
    df["efficiency_score_rolling"] = group["efficiency_score"].transform(lambda x: x.rolling(96).mean())  # 24h

    # energy consumption
    df["energy_consumption_lag1"] = group["energy_consumption"].shift(1)
    df["energy_consumption_lag2"] = group["energy_consumption"].shift(4)

    # is active
    df["is_active_lag1"] = group["is_active"].shift(1)

    # battery percentage
    df["current_battery_percentage_lag1"] = group["current_battery_percentage"].shift(2)

    return df.ffill().bfill()


async def create_data(device_id: Optional[str], after: Optional[datetime], horizon_minutes: int, db: DatabaseManager) -> \
        tuple[pd.DataFrame, pd.Series]:
    df = await get_raw_data(device_id, after, db)

    # extract the hour, day and month
    df["hour"] = df.index.hour
    df["day"] = df.index.weekday
    df["month"] = df.index.month

    # apply sine and cosine
    target_time = df.index + pd.Timedelta(minutes=horizon_minutes)
    df = _apply_sin_cos(df, target_time)

    # apply lags
    df = _apply_lags_and_rolling(df)

    # convert type into a cat feature
    df["type"] = df["type"].astype("category")

    # unnessecary columns
    df.drop(columns=["hour", "day", "month", "device_id"], inplace=True)
    df.reset_index(drop=True, inplace=True)

    # shift the target, depends on the horzion
    shift_steps = -(horizon_minutes // 15)
    df["energy_consumption"] = df["energy_consumption"].shift(shift_steps)

    df.dropna(inplace=True)

    return df.drop(columns=["energy_consumption"]), df["energy_consumption"]
