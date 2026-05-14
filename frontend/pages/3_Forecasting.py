from typing import Any

import pytz
import streamlit as st
from streamlit_javascript import st_javascript

from database.ml.status_manager import get_current_status
from frontend.utils import check_for_password_verification, get_api_client, display_prediction_card

st.set_page_config(layout="wide")

TTL_CACHE_TIME = 60 * 30  # 30 minutes

# api client
api_client = get_api_client()

# api call functions
@st.cache_data(ttl=TTL_CACHE_TIME)
def fetch_device_fleet() -> Any:
    return api_client.request("GET", "/devices/").data


@st.cache_data(ttl=TTL_CACHE_TIME)
def fetch_ml_metadata() -> Any:
    return api_client.request("GET", "/ml/metadata", params={"version": "latest"}).data


# title
st.header("Forecasting")
st.divider()

check_for_password_verification()

# get the users timezone
tz_res = st_javascript("Intl.DateTimeFormat().resolvedOptions().timeZone")  # get the users browser timezone
user_tz = pytz.timezone(tz_res) if tz_res else pytz.utc

# status
with st.status("Fetching necessary data...", expanded=True) as status:
    st.write("Fetching all Devices...")
    devices = fetch_device_fleet()

    st.write("Fetching model metadata...")
    model_metadata = fetch_ml_metadata()

    status.update(label="Fechting complete", expanded=False, state="complete")

# active models and theire metadata
st.subheader("Active Models")
cols = st.columns(4)

model_names = ["15min", "1h", "6h", "24h"]
for i, m_name in enumerate(model_names):
    with cols[i]:
        with st.container(border=True):
            m_data = model_metadata.get(m_name, {})
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

st.divider()


# retraining
@st.fragment(run_every="10s")
def retraining_section() -> None:
    st.subheader("Model Retraining")
    st.info("Retraining uses Optuna for hyperparameter optimization. This can take up to 30 minutes.")

    # get retraining status
    is_retraining = get_current_status()

    # set session state variables
    if "was_retraining" not in st.session_state:
        st.session_state.was_retraining = False

    if "retraining_sucess" not in st.session_state:
        st.session_state.retraining_sucess = True

    # notify user
    if st.session_state.was_retraining and not is_retraining:
        st.toast("Retraining complete. New models are now active")
        st.session_state.was_retraining = False

    if is_retraining:
        st.session_state.was_retraining = True

    # retraining
    col_opt, col_btn = st.columns([3, 1])

    with col_opt:
        optimize = st.checkbox("Enable Hyperparameter Optimization", value=True,
                               help="If disabled, models train with default params (faster)")

    with col_btn:
        if is_retraining:
            st.button("Training in Progress...", disabled=True, use_container_width=True)

        else:
            if st.button("Start Retraining", type="primary", use_container_width=True):
                response = api_client.request("POST", "/ml/retrain", params={"optimize": optimize})

                if response.is_success:
                    st.toast("Retraining started")
                    st.rerun(scope="fragment")  # rerun to get into the retraining state

                else:
                    st.session_state.retraining_sucess = False
                    st.session_state.api_ml_error_detail = response.data["detail"]
                    st.rerun(scope="fragment")

    if is_retraining:
        st.info("Optuna is searching for best parameters...") if optimize else st.info("Models are getting retrained")
        st.session_state.was_retraining = True

    if not st.session_state.retraining_sucess:
        st.warning(st.session_state.get("api_ml_error_detail"))


# prediction
st.subheader("Load Prediction")
with st.container(border=True):
    with st.form("predict_load", border=False):
        p_col1, p_col2 = st.columns([2, 1])

        with p_col1:
            dev_options = {"All Devices": None}
            for d in devices:
                dev_options[f"{d["name"]} ({d["location"]})"] = d["id"]

            selected_dev = st.selectbox("Target Device (Optional)", options=list(dev_options.keys()))
            horizon = st.number_input("Prediction Horizon (Minutes)",
                                      min_value=15, max_value=1440, value=60, step=15)

        with p_col2:
            st.write("##")  # alignment
            predict = st.form_submit_button("Predict Load", type="primary", use_container_width=True)

    if predict:
        with st.spinner("Calculating..."):
            params = {k: v for k, v in zip(["horizon_minutes", "device_id"], [horizon, dev_options[selected_dev]]) if v}
            result = api_client.request("GET", "/ml/predict", params=params)

            if result.is_success:
                display_prediction_card(result.data, user_tz)

            else:
                st.info(result.data["detail"])

st.divider()
st.space("xsmall")
retraining_section()

# footer
st.divider()
st.caption("S.E.D.M.S - Open Source IoT Management System | [GitHub](https://github.com/Letox74/S.E.D.M.S)")
