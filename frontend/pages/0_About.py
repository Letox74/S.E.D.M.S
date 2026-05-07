import streamlit as st

st.set_page_config(layout="wide")

st.header("About S.E.D.M.S")
st.subheader("Smart Energy & Device Management System")
st.divider()

# quick about
st.markdown("""
    Welcome to **S.E.D.M.S**, an open source solution designed to simplify how we monitor 
    and predict energy consumption in local IoT environments. 

    This project was built to give users full control over their data while providing 
    advanced analytical insights and machine learning forecasts.
    """)

st.divider()

# core features
st.subheader("Core Features")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### Device Management")
    st.write("""
    Easily register and organize your IoT hardware via a unified interface. 
    The system provides a robust local API to handle device authentication and 
    status monitoring in real time.
    """)

with col2:
    st.markdown("### Telemetry & Analytics")
    st.write("""
    The engine calculates key metrics like Peak, Min, Avg, and Std for parameters 
    such as Power, Current, Temperature etc. It also tracks total operation hours 
    and computes an efficiency score to evaluate your device performance.
    """)

with col3:
    st.markdown("### ML Forecasting")
    st.write("""
    The integrated machine learning models analyze historical patterns to predict 
    energy consumption (Wh). The system can forecast future demand for any 
    timeframe up to the next 24 hours.
    """)

st.divider()

# tech stack
st.subheader("Technology Stack")

with st.expander("See the tools used in this project"):
    st.markdown("""
    - **Frontend & Web UI:** [Streamlit](https://streamlit.io) (Hosted locally on your machine)
    - **Backend API:** FastAPI (Managing local data traffic and device communication)
    - **Data Processing:** Pandas & NumPy for statistical analysis (Peak, Avg, Std etc.)
    - **Machine Learning:** Scikit-Learn and LightGBM for Wh regression and forecasting
    - **Database:** Local storage for telemetry and analytical results (SQLite database)
    """)

# privacy and local execution
st.subheader("Privacy & Security")
st.markdown("""
    **Privacy First:** S.E.D.M.S is designed to run entirely on your local machine. 
    Your telemetry data, API logs, and database records stay in your own environment. 
    No data is uploaded to external servers.
    """)

# developer
st.subheader("About the Developer")
st.write("""
    Hi! I am currently developing S.E.D.M.S as a solo project. My goal is to create 
    a transparent and accessible tool for anyone interested in IoT and energy efficiency. 

    As this is an open source project, I am always happy to receive feedback or 
    suggestions for new features.
    """)

# footer
st.divider()
st.caption("S.E.D.M.S - Open Source IoT Management System | [GitHub](https://github.com/Letox74/S.E.D.M.S)")