from datetime import datetime, timezone, date, time, timedelta
from typing import Any

import numpy as np
import streamlit as st

from utils import check_for_password_verification, api_client

st.set_page_config(layout="wide")

TTL_CACHE_TIME = 60 * 30  # 30 minutes


# helper functions for the api calls
@st.cache_data(ttl=TTL_CACHE_TIME)
def get_active_device_count() -> int:
    return len(api_client.request("GET", "/devices/active").data)


@st.cache_data(ttl=TTL_CACHE_TIME)
def get_total_kwh_today() -> float:
    today = datetime.combine(date.today(), time.min, tzinfo=timezone.utc)
    data = api_client.request("GET", "/analytics/history", params={"start_datetime": today}).data
    return round(sum([analytic["energy_consumption"] for analytic in data]) / 1_000, 2) if data else 0.00


@st.cache_data(ttl=TTL_CACHE_TIME)
def get_avg_efficiency_score_today() -> float:
    today = datetime.combine(date.today(), time.min, tzinfo=timezone.utc)
    data = api_client.request("GET", "/analytics/history", params={"start_datetime": today}).data
    return round(np.mean([analytic["efficiency_score"] for analytic in data]), 2) if data else 0.00


@st.cache_data(ttl=TTL_CACHE_TIME)
def get_battery_alerts() -> list[Any]:
    after = datetime.now(timezone.utc) - timedelta(minutes=5)
    return api_client.request("GET", "/telemetry/alerts/battery", params={"after": after}).data


@st.cache_data(ttl=TTL_CACHE_TIME)
def get_temperature_alerts() -> list[Any]:
    after = datetime.now(timezone.utc) - timedelta(minutes=5)
    return api_client.request("GET", "/telemetry/alerts/temperature", params={"after": after}).data


@st.cache_data(ttl=TTL_CACHE_TIME)
def get_model_loaded_and_version() -> tuple[bool, dict[Any]]:
    loaded = api_client.request("GET", "/ml/info/status").data["loaded"]
    models = api_client.request("GET", "/ml/metadata").data

    return loaded, models


@st.cache_data(ttl=TTL_CACHE_TIME)
def get_last_prediction() -> Any:
    return api_client.request("GET", "/ml/predictions/latest")


# header for the page
st.header("Dashboard")
st.divider()

check_for_password_verification(main_page=True)

# metrics at the top
st.subheader("Overview")

empty_status = st.empty()
with empty_status.status("Fetching Overview data...", expanded=True):
    st.write("Getting the active Device count...")
    device_count = get_active_device_count()

    st.write("Getting the average efficiency score today...")
    avg_efficiency_score = get_avg_efficiency_score_today()

    st.write("Getting the total kWh today...")
    total_kwh = get_total_kwh_today()

    st.write("Getting the Battery alerts...")
    battery_alerts = get_battery_alerts()

    st.write("Getting the temperature alerts...")
    temp_alerts = get_temperature_alerts()

    st.write("Fetiching the status and metadata...")
    loaded, metadata = get_model_loaded_and_version()

    st.write("Fetiching last prediction")
    last_prediction = get_last_prediction()

empty_status.empty()

# columns
overview_col1, overview_col2, overview_col3 = st.columns([3, 4, 5])

with overview_col1:
    st.metric("Active Devices", device_count, border=True, help="All current active Devices")

with overview_col2:
    st.metric("Efficiency Score", f"{avg_efficiency_score:.2f}", border=True,
              help="The average efficiency score today")

with overview_col3:
    st.metric("Consumption", f"{total_kwh:.2f} kWh", border=True, help="Todays Energy consumption")

# alert area
st.space("medium")
st.subheader("Alerts")
st.divider()

tab_batt, tab_temp = st.tabs(["Battery Alerts", "Temperature Alerts"])

with tab_batt:
    st.metric("Total Devices", len(battery_alerts), border=True, help="How many Devices have low Battery")

    if battery_alerts:
        st.dataframe(battery_alerts, column_config={
            "current_battery_percentage": st.column_config.ProgressColumn("Battery", format="%d%%"),
            "device_name": "Device",
            "device_location": "Location"
        }, hide_index=True, use_container_width=True)

    else:
        st.success("All batteries are within normal range")

with tab_temp:
    st.metric("Total Devices", len(temp_alerts), border=True, help="How many Devices have high temperature")

    if temp_alerts:
        st.dataframe(temp_alerts, column_config={
            "temperature": st.column_config.NumberColumn("Temperature", format="%d%°C"),
            "device_name": "Device",
            "device_location": "Location"
        }, hide_index=True, use_container_width=True)

    else:
        st.success("No temperature anomalies detected")

# ml area
st.space("medium")
st.subheader("ML")
st.divider()

st.write(f"**Models: {"loaded" if loaded else "not loaded"}**")
st.space("xsmall")

if not metadata["15min"]["history"]:
    st.info("No model metadata yet")

else:
    for model_name, data in metadata.items():
        st.write(f"**Model: {model_name}**")
        st.write(f"Current version: {data["current_version"]}")

        with st.expander("Metadata"):
            st.write(f"- training date: {data["history"][0]["date"]}")

            for dict_key, value in data["history"][0].items():
                if isinstance(value, dict):
                    st.write(f"- {dict_key}:")

                    for key, val in value.items():
                        st.write(f"\t- {key}: {val}")

        st.space("xsmall")

st.space("xsmall")
if not last_prediction.is_success:
    st.info("No Prediction found")
    st.stop()

last_prediction["timestamp"] = datetime.fromisoformat(last_prediction["timestamp"]).replace(tzinfo=timezone.utc)

# check if the prediction is already expired
if (last_prediction["timestamp"] + timedelta(minutes=last_prediction["prediction_horizon_minutes"])
        < datetime.now(timezone.utc)):
    st.write("Last Prediction already expired")
    st.stop()

# prepare the time values
start_dt = last_prediction["timestamp"].strftime("%H:%M:%S")
end_dt = (start_dt + timedelta(minutes=last_prediction["prediction_horizon_minutes"])).strftime("%H:%M:%S")
prediction_value = last_prediction["predicted_load"]

ml_col1, ml_col2, ml_col3 = st.columns(3)

with ml_col1:
    st.metric("Start time", start_dt, border=True, help="The time the when the prediction was made")

with ml_col2:
    st.metric("End time", end_dt, border=True, help="The time by which it was predicted")

with ml_col3:
    st.metric("Period", f"{last_prediction["prediction_horizon_minutes"]} Min.", border=True,
              help="The prediction period")

st.metric("Predicted value", f"{last_prediction["predicted_load"]} Wh", border=True)


# footer
st.divider()
st.caption("S.E.D.M.S - Open Source IoT Management System | [GitHub](https://github.com/Letox74/S.E.D.M.S)")