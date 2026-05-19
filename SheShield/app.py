import streamlit as st
import mysql.connector
import pandas as pd
import plotly.express as px
from streamlit_js_eval import get_geolocation

# DATABASE CONNECTION
try:
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root1234",
        database="sheshield"
    )
except:
    db = None

if db:
    cursor = db.cursor()
else:
    cursor = None

# PAGE SETTINGS
st.set_page_config(
    page_title="SheShield",
    layout="wide"
)

st.title("🚨 SheShield - Women Safety Emergency App")

# LIVE LOCATION
location = get_geolocation()

if location:
    latitude = location["coords"]["latitude"]
    longitude = location["coords"]["longitude"]

    st.success(f"Live Location Captured ✅")
    st.write("Latitude:", latitude)
    st.write("Longitude:", longitude)

    maps_df = pd.DataFrame({
        'lat': [latitude],
        'lon': [longitude]
    })

    st.map(maps_df)

else:
    st.warning("Location not available. Please allow location access.")

# SOS BUTTON
if st.button("🚨 SEND SOS ALERT"):
    if db and cursor and location:
        alert_type = "SOS"
        message = "Emergency! Immediate help needed."
        location_text = f"{latitude}, {longitude}"

        query = """
        INSERT INTO emergency_alerts (alert_type, message, location)
        VALUES (%s, %s, %s)
        """
        values = (alert_type, message, location_text)

        cursor.execute(query, values)
        db.commit()

        st.error("SOS ALERT SENT SUCCESSFULLY 🚨")

    else:
        st.error("Database not connected or location unavailable.")

# DASHBOARD
st.header("📊 Emergency Alerts Dashboard")

query = "SELECT * FROM emergency_alerts"

if db:
    df = pd.read_sql(query, db)
else:
    df = pd.DataFrame()

if not df.empty:

    # Alert Type Chart
    st.subheader("Alert Type Distribution")
    alert_count = df["alert_type"].value_counts()

    fig = px.bar(
        x=alert_count.index,
        y=alert_count.values,
        labels={"x": "Alert Type", "y": "Count"},
        title="Emergency Alert Types"
    )

    st.plotly_chart(fig)

    # Location Chart
    st.subheader("Alerts by Location")

    location_count = df["location"].value_counts()

    pie = px.pie(
        values=location_count.values,
        names=location_count.index,
        title="Alerts by Location"
    )

    st.plotly_chart(pie)

    # Full Data
    st.subheader("📋 Full Emergency Data")
    st.dataframe(df)

else:
    st.warning("No emergency alerts found.")
