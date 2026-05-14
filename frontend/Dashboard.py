import sys
from pathlib import Path

# append path to allow imports from other folders
current_dir = str(Path(__file__).resolve().parent.parent)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from datetime import datetime, timezone, date, time, timedelta
from typing import Any

import numpy as np
import streamlit as st

from utils import check_for_password_verification, display_prediction_card, get_api_client
from core.config import IGNORE_WARNINGS
from api.client.api_client import APIResponse

from streamlit_javascript import st_javascript
import pytz

if IGNORE_WARNINGS:
    import warnings

    warnings.filterwarnings("ignore")

st.set_page_config(layout="wide")

TTL_CACHE_TIME = 60 * 30  # 30 minutes

# api client
api_client = get_api_client()


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
def get_last_prediction() -> APIResponse:
    return api_client.request("GET", "/ml/predictions/latest")


# header for the page
st.header("Dashboard")
st.divider()

check_for_password_verification(main_page=True)

# get the users timezone
tz_res = st_javascript("Intl.DateTimeFormat().resolvedOptions().timeZone")  # get the users browser timezone
user_tz = pytz.timezone(tz_res) if tz_res else pytz.utc

# fetching data
with st.status("Fetching data...", expanded=True) as status:
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

    status.update(label="Fetching data complete", expanded=False, state="complete")

# metrics at the top
st.subheader("Overview")

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
        st.dataframe(
            battery_alerts,
            column_config={
                "current_battery_percentage": st.column_config.ProgressColumn("Battery", format="%d%%"),
                "device_name": st.column_config.TextColumn("Device"),
                "device_location": st.column_config.TextColumn("Location"),
                "timestamp": st.column_config.DatetimeColumn("Timestamp", format="DD.MM.YYYY HH:mm", timezone="utc"),
                "id": None,
                "devie_id": None,
                "voltage": None,
                "current": None,
                "signal_strength": None,
                "frequency": None,
                "temperature": None
            },
            hide_index=True,
            use_container_width=True
        )

    else:
        st.success("All batteries are within normal range")

with tab_temp:
    st.metric("Total Devices", len(temp_alerts), border=True, help="How many Devices have high temperature")

    if temp_alerts:
        st.dataframe(
            temp_alerts,
            column_config={
                "temperature": st.column_config.NumberColumn("Temperature", format="%d%°C"),
                "device_name": st.column_config.TextColumn("Device"),
                "device_location": st.column_config.TextColumn("Location"),
                "timestamp": st.column_config.DatetimeColumn("Timestamp", format="DD.MM.YYYY HH:mm", timezone="utc"),
                "id": None,
                "devie_id": None,
                "voltage": None,
                "current": None,
                "signal_strength": None,
                "frequency": None,
                "current_battery_percentage": None,
            },
            hide_index=True,
            use_container_width=True
        )

    else:
        st.success("No temperature anomalies detected")

# ml area
st.space("medium")
st.subheader("ML")
st.divider()

st.write(f"**Models: {"loaded" if loaded else "not loaded"}**")
st.space("xsmall")

if not metadata["15min"]["history"]:
    st.warning("No model metadata yet")

else:
    cols = st.columns(4)

    model_names = ["15min", "1h", "6h", "24h"]
    for i, m_name in enumerate(model_names):
        with cols[i]:
            with st.container(border=True):
                m_data = metadata.get(m_name, {})
                current_ver = m_data.get("current_version", "N/A")
                st.markdown(f"**Model: {m_name}**")
                st.code(f"Version: {current_ver if current_ver else "N/A"}")  # could be an empty string

                # Nur die aktuellsten Metriken zeigen
                if m_data.get("history"):
                    metrics = m_data["history"][0].get("metrics", {})
                    for metric_name, value in metrics.items():
                        if metric_name in ("mae", "r2"):
                            st.metric(label=metric_name.upper(), value=f"{value}")
                else:
                    st.caption("No metrics available")

st.space("xsmall")
ml_container = st.container()

# footer (needs to be here, else it would not be shown if st.stop() is used)
st.divider()
st.caption("S.E.D.M.S - Open Source IoT Management System | [GitHub](https://github.com/Letox74/S.E.D.M.S)")

# prediction part
st.space("xsmall")
if not last_prediction.is_success:
    with ml_container:
        st.warning("No Prediction found")
        st.stop()

last_prediction.data["timestamp"] = datetime.fromisoformat(last_prediction.data["timestamp"]).replace( tzinfo=timezone.utc)

# check if the prediction is already expired
if (last_prediction.data["timestamp"] + timedelta(minutes=last_prediction.data["prediction_horizon_minutes"])
        < datetime.now(timezone.utc)):
    with ml_container:
        st.warning("Last Prediction already expired")
        st.stop()

with ml_container:
    st.divider()
    display_prediction_card(last_prediction.data, user_tz)
