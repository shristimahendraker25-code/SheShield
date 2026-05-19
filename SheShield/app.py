import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_js_eval import get_geolocation

# PAGE SETTINGS
st.set_page_config(
    page_title="SheShield",
    layout="wide"
)

st.title("🚨 SheShield - Women Safety Emergency App")

# SAMPLE DATA (instead of MySQL)
alerts = []

# LIVE LOCATION
location = get_geolocation()

if location:
    lat = location["coords"]["latitude"]
    lon = location["coords"]["longitude"]

    st.map(pd.DataFrame({
        'lat': [lat],
        'lon': [lon]
    }))

else:
    lat, lon = None, None
    st.warning("Allow location access to continue")

# SOS BUTTON
if st.button("🚨 SEND SOS ALERT"):
    alert = {
        "alert_id": len(alerts) + 1,
        "latitude": lat,
        "longitude": lon,
        "status": "Emergency"
    }
    alerts.append(alert)
    st.success("SOS Alert Sent Successfully!")

# DASHBOARD
st.header("📊 Emergency Alerts Dashboard")

if alerts:
    df = pd.DataFrame(alerts)

    st.dataframe(df)

    status_count = df["status"].value_counts().reset_index()
    status_count.columns = ["Status", "Count"]

    fig = px.pie(
        status_count,
        names="Status",
        values="Count",
        title="Alert Status Distribution"
    )

    st.plotly_chart(fig)

else:
    st.info("No alerts yet. Press SOS to generate one.")
