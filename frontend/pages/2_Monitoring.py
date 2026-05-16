from datetime import datetime, timedelta
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pytz
import streamlit as st
from streamlit_javascript import st_javascript

from frontend.utils import check_for_password_verification, api_client

st.set_page_config(layout="wide")


# api call functions
@st.cache_data(ttl=60 * 30)
def fetch_device_fleet() -> Any:
    return api_client.sync_request("GET", "/devices/").data


@st.cache_data(ttl=60)
def get_telemetry_data(device_id: str, since: datetime) -> Any:
    params = {k: v for k, v in zip(["device_id", "start_datetime"], [device_id, since]) if v}
    return api_client.sync_request("GET", f"/telemetry/history", params=params).data


@st.cache_data(ttl=60)
def get_analytics_data(device_id: str, since: datetime) -> Any:
    params = {k: v for k, v in zip(["device_id", "start_datetime"], [device_id, since]) if v}
    return api_client.sync_request("GET", f"/analytics/history", params=params).data


check_for_password_verification()

# get the users timezone
tz_res = st_javascript("Intl.DateTimeFormat().resolvedOptions().timeZone")  # get the users browser timezone
user_tz = pytz.timezone(tz_res) if tz_res else pytz.utc

# sidebar for filters
with st.sidebar:
    if "after_date" not in st.session_state:
        st.session_state.after_date = (datetime.now(user_tz) - timedelta(days=1)).date()

    if "after_time" not in st.session_state:
        st.session_state.after_time = datetime.now(user_tz).time()

    st.subheader("Filters")
    st.divider()

    device_list = fetch_device_fleet()
    device_options = {f"{device["name"]} ({device["location"]})": device["id"] for device in device_list}

    selected_label = st.selectbox("Select Device", options=["All Devices"] + list(device_options.keys()))
    selected_id = device_options[selected_label] if selected_label != "All Devices" else None

    # time filter
    st.subheader("Timeframe")
    time_preset = st.radio("Quick Select", ["Last Hour", "Last 24h", "Last 7 Days", "Custom"], index=1)

    if time_preset == "Custom":
        after_date = st.date_input("Start Date", value=st.session_state.after_date)
        after_time = st.time_input("Start Time", value=st.session_state.after_time)
        naive_datetime = datetime.combine(after_date, after_time)

        st.session_state.after_date = after_date
        st.session_state.after_time = after_time

        # convert to utc
        local_datetime = user_tz.localize(naive_datetime)
        after_datetime = local_datetime.astimezone(pytz.utc)
    else:
        offsets = {"Last Hour": 1, "Last 24h": 24, "Last 7 Days": 168}
        after_datetime = datetime.now(pytz.utc) - timedelta(hours=offsets[time_preset])

    display_time = after_datetime.astimezone(user_tz)
    st.info(f"Showing data since: \n\n**{display_time.strftime("%Y-%m-%d %H:%M")}**")


# page content
# quick func to shift all timestamps in the users tz
def localize_tz(df: pd.DataFrame) -> pd.DataFrame:
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", yearfirst=True)
    if df["timestamp"].dt.tz is None:
        df["timestamp"] = df["timestamp"].dt.tz_localize("UTC")

    df["timestamp"] = df["timestamp"].dt.tz_convert(user_tz)

    return df


# title and etc.
st.header("Monitoring")
st.caption(f"Analyzing data for: **{selected_label}**")
st.divider()

# visualization
with st.status("Fetching live streams...", expanded=True) as status:
    st.write("Fetching the Telemetry data...")
    telemetry_raw = get_telemetry_data(selected_id, after_datetime)

    st.write("Fetiching the analytics data...")
    analytics_raw = get_analytics_data(selected_id, after_datetime)

    status.update(label="Fetching live streams complete", expanded=False, state="complete")

if not telemetry_raw:
    st.warning("No telemetry data found for the selected timeframe")

elif not analytics_raw:
    st.warning("No Analytic data found for the selected timeframe")

else:
    df_telemetry = pd.DataFrame(telemetry_raw)
    df_analytics = pd.DataFrame(analytics_raw)
    print(f"{df_telemetry.shape = }")
    print(f"{df_analytics.shape = }")

    df_telemetry = localize_tz(df_telemetry)
    df_telemetry["timestamp"] = pd.to_datetime(df_telemetry["timestamp"], errors="coerce", yearfirst=True)
    df_telemetry = df_telemetry.sort_values("timestamp")

    df_analytics = localize_tz(df_analytics)
    df_analytics["timestamp"] = pd.to_datetime(df_analytics["timestamp"], errors="coerce", yearfirst=True)
    df_analytics = df_analytics.sort_values("timestamp")

    # pyhsical metrics
    st.subheader("Electrical Stats")

    # voltage
    fig_voltage = go.Figure(
        go.Scatter(
            x=df_telemetry["timestamp"],
            y=df_telemetry["voltage"],
            name="Voltage (V)",
            line=dict(color="#00CC96"),
            mode="lines",
            connectgaps=True
        )
    )
    fig_voltage.update_layout(
        title="Voltage (V)",
        xaxis_title="Time",
        yaxis_title="Volts",
        height=400,
        margin=dict(l=20, r=20, t=40, b=40),
        hovermode="x unified"
    )

    st.plotly_chart(fig_voltage, use_container_width=True)

    # current
    fig_current = go.Figure(
        go.Scatter(
            x=df_telemetry["timestamp"],
            y=df_telemetry["current"],
            name="Current (A)",
            line=dict(color="#636EFA"),
            mode="lines",
            connectgaps=True
        )
    )
    fig_current.update_layout(
        title="Current (A)",
        xaxis_title="Time",
        yaxis_title="Amperes",
        height=400,
        margin=dict(l=20, r=20, t=40, b=40),
        hovermode="x unified"
    )

    st.plotly_chart(fig_current, use_container_width=True)

    # consumption and efficiency
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("Energy Consumption")
        df_analytics["energy_consumption"] = df_analytics["energy_consumption"] / 1000  # convert to kWh

        fig_energy = px.area(
            df_analytics,
            x="timestamp",
            y="energy_consumption",
            labels={"energy_consumption": "kWh"},
            color_discrete_sequence=["#AB63FA"],
            title="Energy Consumption (kWh)"
        )
        fig_energy.update_layout(margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig_energy, use_container_width=True)

    with col_right:
        st.subheader("Current Efficiency" if selected_id else "Average efficiency score over the last 15 minutes")
        if selected_id:
            efficiency_score = df_analytics["efficiency_score"].iloc[-1] if not df_analytics.empty else 0

        else:
            last_time = df_analytics["timestamp"].max()
            mask = df_analytics["timestamp"] > last_time - pd.Timedelta(minutes=15)
            efficiency_score = df_analytics["efficiency_score"].mean()

        # gauge chart for the current efficiency score or the average if all devices are selected
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=efficiency_score,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": "Efficiency Score (%)"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#00CC96"},
                "steps": [
                    {"range": [0, 50], "color": "#FF6666"},
                    {"range": [50, 80], "color": "#FFBB00"},
                    {"range": [80, 100], "color": "#2CA02C"}
                ]
            }
        ))
        fig_gauge.update_layout(margin=dict(l=20, r=20, t=50, b=0))
        st.plotly_chart(fig_gauge, use_container_width=True)

# footer
st.divider()
st.caption("S.E.D.M.S - Open Source IoT Management System | [GitHub](https://github.com/Letox74/S.E.D.M.S)")
