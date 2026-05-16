from datetime import datetime, timezone, timedelta
from typing import Optional, Any

import pandas as pd
import pytz
import streamlit as st

from api.client.api_client import APIClient
from api.client.provider import create_api_instance
from core.config import settings


@st.cache_resource
def get_api_client() -> APIClient:
    return create_api_instance()

api_client = get_api_client()


def check_for_password_verification(main_page: bool = False) -> None:
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        place_holder = st.empty()

        if main_page:
            if password := place_holder.text_input("Enter the password", type="password", placeholder="password..."):
                if password == settings.frontend.password:
                    st.session_state.authenticated = True
                    place_holder.empty()
                    st.rerun()

                else:
                    st.error("Wrong password")
                    st.stop()

            st.stop()


        else:
            st.error("Not verified yet. Please go to the Dashboard to verify")
            st.stop()


def _calc_delta(prediction, actual_avg) -> float:
    if actual_avg == 0: return 0.0
    return ((prediction - actual_avg) / actual_avg) * 100


def _get_historical_avg_for_timeslot(device_id: Optional[str], horizon_minutes: int) -> float:
    now = datetime.now(timezone.utc)
    start_time = now.time()
    end_time = (now + timedelta(minutes=horizon_minutes)).time()
    seven_days_ago = now - timedelta(days=7)

    response = api_client.sync_request("GET", "/analytics/history",
                                       params={"device_id": device_id, "start_datetime": seven_days_ago})

    if not response.is_success or not response.data:
        return 0.0

    df_hist = pd.DataFrame(response.data)
    df_hist["timestamp"] = pd.to_datetime(df_hist["timestamp"], errors="coerce", yearfirst=True)

    mask = (df_hist["timestamp"].dt.time >= start_time) & (df_hist["timestamp"].dt.time <= end_time)
    data = df_hist.loc[mask]

    return data["energy_consumption"].mean()


def display_prediction_card(data: Any, users_tz) -> None:
    prediction_value = data["predicted_load"]
    confidence = data["confidence"]
    avg_value = _get_historical_avg_for_timeslot(data["device_id"], data["prediction_horizon_minutes"])

    dt_object = datetime.fromisoformat(data["timestamp"]) if not isinstance(data["timestamp"], datetime) else data[
        "timestamp"]

    if dt_object.tzinfo is None:
        dt_object = pytz.utc.localize(dt_object)

    start_time = dt_object.astimezone(users_tz)
    end_time = start_time + timedelta(minutes=data["prediction_horizon_minutes"])

    if data["prediction_horizon_minutes"] / 60 > 1:
        horizon_value = data["prediction_horizon_minutes"] / 60
        horizon_metric = "hours"

    else:
        horizon_value = data["prediction_horizon_minutes"]
        horizon_metric = "minutes"

    delta = _calc_delta(data["predicted_load"], avg_value)

    st.metric(
        label=f"Predicted Load",
        value=f"{prediction_value:.2f} Wh",
        delta=f"{delta:.1f}% vs. last 7 days",
        delta_color="inverse"
    )
    st.caption(f"Target: {horizon_value} {horizon_metric} was selected")
    st.caption(
        f"Prediction started at {start_time.strftime("%Y-%m-%d %H:%M")} and forecasts till {end_time.strftime("%Y-%m-%d %H:%M")}")

    conf_color = "green" if confidence > 80 else "orange" if confidence > 50 else "red"
    st.markdown(f"**Confidence Score:** :{conf_color}[{confidence:.0f}%]")
    st.progress(confidence / 100)
