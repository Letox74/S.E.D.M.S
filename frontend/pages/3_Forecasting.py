import streamlit as st

from frontend.utils import check_for_password_verification

st.set_page_config(layout="wide")


st.header("Forecasting")
st.divider()

check_for_password_verification()

