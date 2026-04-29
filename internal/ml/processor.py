import numpy as np
import pandas as pd

from database.connection import DatabaseManager
from .handler import get_raw_training_data


def _apply_sin_cos(df: pd.DataFrame, target_time) -> pd.DataFrame:
    df["hour_sin"] = np.sin(2 * np.pi * (target_time.dt.hour / 24))
    df["hour_cos"] = np.cos(2 * np.pi * (target_time.dt.hour / 24))

    df["day_sin"] = np.sin(2 * np.pi * (target_time.dt.weekday / 7))
    df["day_cos"] = np.cos(2 * np.pi * (target_time.dt.weekday / 7))

    df["month_sin"] = np.sin(2 * np.pi * (target_time.dt.month - 1) / 12)
    df["month_cos"] = np.cos(2 * np.pi * (target_time.dt.month - 1) / 12)

    return df


def _apply_lags_and_rolling(df: pd.DataFrame) -> pd.DataFrame:
    # power related
    df["avg_power_lag1"] = df["avg_power"].shift(freq="15min")
    df["avg_power_lag2"] = df["avg_power"].shift(freq="1h")
    df["avg_power_rolling"] = df["avg_power"].rolling(pd.Timedelta(hours=1)).mean()
    df["std_power_lag1"] = df["std_power"].shift(freq="15min")

    # voltage
    df["avg_voltage_lag1"] = df["avg_voltage"].shift(freq="15min")
    df["avg_voltage_rolling"] = df["avg_voltage"].rolling(pd.Timedelta(hours=2)).std()

    # temperature
    df["avg_temperature_lag1"] = df["avg_temperature"].shift(freq="15min")
    df["avg_temperature_rolling"] = df["avg_temperature"].rolling(pd.Timedelta(hours=3)).mean()

    # efficiency score
    df["efficiency_score_rolling"] = df["efficiency_score"].rolling(pd.Timedelta(hours=24)).mean()

    # energy consumption
    df["energy_consumption_lag1"] = df["energy_consumption"].shift(freq="15min")
    df["energy_consumption_lag2"] = df["energy_consumption"].shift(freq="1h")

    # is active
    df["is_active_lag1"] = df["is_active"].shift(freq="15min")

    # battery percentage
    df["current_battery_percentage_lag1"] = df["current_battery_percentage"].shift(freq="30min")

    df = df.ffill().bfill()
    return df


async def create_data(db: DatabaseManager, horizon_minutes: int) -> tuple[pd.DataFrame, pd.Series]:
    df = await get_raw_training_data(db)

    # extract the hour, day and month
    df["hour"] = df["timestamp"].dt.hour
    df["day"] = df["timestamp"].dt.weekday()
    df["month"] = df["timestamp"].dt.month

    # apply sine and cosine
    target_time = df["timestamp"] + pd.Timedelta(minutes=horizon_minutes)
    df = _apply_sin_cos(df, target_time)

    # apply lags
    df = _apply_lags_and_rolling(df)

    # convert type into a cat feature
    df["type"] = df["type"].astype("char")

    # unnessecary columns
    df.drop(columns=["timestamp", "hour", "day", "month"], inplace=True)

    # shift the target, depends on the horzion
    shift_steps = -(horizon_minutes // 15)
    df["energy_consumption"] = df["energy_consumption"].shift(shift_steps)

    df.dropna(inplace=True)

    return df.drop(columns=["energy_consumption"]), df["energy_consumption"]
