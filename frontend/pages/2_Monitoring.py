import streamlit as st

from frontend.utils import check_for_password_verification, api_client

st.set_page_config(layout="wide")


st.header("Monitoring")
st.divider()

check_for_password_verification()



# footer
st.divider()
st.caption("S.E.D.M.S - Open Source IoT Management System | [GitHub](https://github.com/Letox74/S.E.D.M.S)")
