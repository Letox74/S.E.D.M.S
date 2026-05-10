from datetime import datetime, timedelta
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pytz
import streamlit as st
from plotly.subplots import make_subplots
from streamlit_javascript import st_javascript

from frontend.utils import check_for_password_verification, api_client

st.set_page_config(layout="wide")


# api call functions
@st.cache_data(ttl=60 * 30)
def fetch_device_fleet() -> Any:
    return api_client.request("GET", "/devices/").data


@st.cache_data(ttl=60)
def get_telemetry_data(device_id, since) -> Any:
    return api_client.request("GET", f"/telemetry/history",
                              params={"device_id": device_id, "start_datetime": since}).data


@st.cache_data(ttl=60)
def get_analytics_data(device_id, since) -> Any:
    return api_client.request("GET", f"/analytics/history",
                              params={"device_id": device_id, "start_datetime": since}).data


check_for_password_verification()

# get the users timezone
tz_res = st_javascript("Intl.DateTimeFormat().resolvedOptions().timeZone") # get the users browser timezone
user_tz = pytz.timezone(tz_res) if tz_res else pytz.utc


# sidebar for filters
with st.sidebar:
    st.subheader("Filters")
    st.divider()

    device_list = fetch_device_fleet()
    device_options = {f"{device["name"]} ({device["location"]})": device["id"] for device in device_list}

    selected_label = st.selectbox("Select Device", options=list(device_options.keys()))
    selected_id = device_options[selected_label]

    # time filter
    st.subheader("Timeframe")
    time_preset = st.radio("Quick Select", ["Last Hour", "Last 24h", "Last 7 Days", "Custom"], index=1)

    if time_preset == "Custom":
        after_date = st.date_input("Start Date", value=(datetime.now(user_tz) - timedelta(days=1)).date())
        after_time = st.time_input("Start Time", value=datetime.now(user_tz).time())
        naive_datetime = datetime.combine(after_date, after_time)

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

    df_telemetry = localize_tz(df_telemetry)
    df_analytics = localize_tz(df_analytics)

    # pyhsical metrics
    st.subheader("Electrical Stats")
    fig_elec = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("Voltage (V)", "Current (A)"),
        horizontal_spacing=0.1
    )

    # voltage
    fig_elec.add_trace(
        go.Scatter(
            x=df_telemetry["timestamp"],
            y=df_telemetry["voltage"],
            name="Voltage (V)",
            line=dict(color="#00CC96")
        ),
        row=1,
        col=1
    )

    # current
    fig_elec.add_trace(
        go.Scatter(
            x=df_telemetry["timestamp"],
            y=df_telemetry["current"],
            name="Current (A)",
            line=dict(color="#636EFA")
        ),
        row=1,
        col=2
    )

    fig_elec.update_layout(
        hovermode="x unified",
        height=500,
        margin=dict(l=20, r=20, t=60, b=50),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.3,
            xanchor="center",
            x=0.5
        )
    )
    fig_elec.update_annotations(font_size=16, y=1.02)
    st.plotly_chart(fig_elec, use_container_width=True)

    # consumption and efficiency
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("Energy Consumption")
        fig_energy = px.area(
            df_analytics,
            x="timestamp",
            y="energy_consumption",
            labels={"energy_consumption": "Wh"},
            color_discrete_sequence=["#AB63FA"]
        )
        fig_energy.update_layout(margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig_energy, use_container_width=True)

    with col_right:
        st.subheader("Current Efficiency")
        # gauge chart for the current efficiency score
        current_score = df_analytics["efficiency_score"].iloc[-1] if not df_analytics.empty else 0

        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=current_score,
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
