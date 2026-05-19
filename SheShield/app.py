import streamlit as st
import mysql.connector
import pandas as pd
import plotly.express as px
from streamlit_js_eval import get_geolocation

# DATABASE CONNECTION
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root1234",
    database="sheshield"
)

cursor = db.cursor()

# PAGE SETTINGS
st.set_page_config(
    page_title="SheShield",
    layout="wide"
)

# CUSTOM CSS
st.markdown("""
<style>
.main {
    background-color: #0e1117;
    color: white;
}

.stButton>button {
    background-color: #ff4b6e;
    color: white;
    border-radius: 10px;
    height: 3em;
    width: 100%;
    font-size: 18px;
}

.metric-card {
    background-color: #1c2333;
    padding: 20px;
    border-radius: 15px;
    text-align: center;
    box-shadow: 0px 0px 15px rgba(255,75,110,0.3);
}
</style>
""", unsafe_allow_html=True)

# SIDEBAR
st.sidebar.title("🌸 SheShield")

page = st.sidebar.radio(
    "Navigation",
    ["🏠 Home", "🚨 Send SOS", "📋 View Alerts", "📊 Analytics"]
)

# HOME PAGE
if page == "🏠 Home":

    st.title("🌸 SheShield")
    st.subheader("Smart Women Safety & Emergency Response System")

    st.write("## Features")
    st.write("• Emergency SOS Alerts")
    st.write("• Women Safety Dashboard")
    st.write("• Alert Monitoring")
    st.write("• Smart Emergency Management")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class='metric-card'>
            <h1>🚨</h1>
            <h1>24/7</h1>
            <h3>Emergency Support</h3>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class='metric-card'>
            <h1>🛡️</h1>
            <h1>100%</h1>
            <h3>Women Safety Focus</h3>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class='metric-card'>
            <h1>⚡</h1>
            <h1>Instant</h1>
            <h3>Alert Response</h3>
        </div>
        """, unsafe_allow_html=True)

# SEND SOS PAGE
elif page == "🚨 Send SOS":

    st.title("🚨 Emergency SOS")

    name = st.text_input("Enter Your Name")

    # LIVE GPS LOCATION
    loc = get_geolocation()

    if loc:
        latitude = loc["coords"]["latitude"]
        longitude = loc["coords"]["longitude"]
        location = f"{latitude}, {longitude}"
        st.success(f"📍 Live Location: {location}")
    else:
        location = "Location not found"
        st.warning("Please allow browser location access")

    emergency = st.selectbox(
        "Emergency Type",
        [
            "Unsafe Area",
            "Harassment",
            "Medical Emergency",
            "Kidnapping Risk",
            "Other"
        ]
    )

    if st.button("🚨 SEND EMERGENCY ALERT"):

        query = """
        INSERT INTO emergency_alerts
        (name, location, emergency_type)
        VALUES (%s, %s, %s)
        """

        values = (name, location, emergency)

        cursor.execute(query, values)
        db.commit()

        st.success("Emergency Alert Sent Successfully!")

# VIEW ALERTS PAGE
elif page == "📋 View Alerts":

    st.title("📋 Emergency Alerts")

    query = "SELECT * FROM emergency_alerts"

    df = pd.read_sql(query, db)

    st.dataframe(df)

# ANALYTICS PAGE
elif page == "📊 Analytics":

    st.title("📊 Emergency Analytics Dashboard")

    query = "SELECT * FROM emergency_alerts"

    df = pd.read_sql(query, db)

    if not df.empty:

        st.subheader("🚨 Total Alerts")
        st.metric("Total Emergency Alerts", len(df))

        # Emergency Type Analytics
        st.subheader("📌 Emergency Types")

        type_count = df["emergency_type"].value_counts()

        fig = px.bar(
            x=type_count.index,
            y=type_count.values,
            labels={
                'x': 'Emergency Type',
                'y': 'Count'
            },
            title="Emergency Alerts by Type"
        )

        st.plotly_chart(fig)

        # Location Analytics
        st.subheader("📍 Alerts by Location")

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
