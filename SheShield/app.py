import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_js_eval import get_geolocation
import os

# LOAD ALERTS
if os.path.exists("alerts.csv"):
    df = pd.read_csv("alerts.csv")
else:
    df = pd.DataFrame(columns=["Name", "Location", "Emergency Type"])

# PAGE SETTINGS
st.set_page_config(page_title="SheShield", layout="wide")

# SIDEBAR
st.sidebar.title("🌸 SheShield")
page = st.sidebar.radio(
    "Navigation",
    ["🏠 Home", "🚨 Send SOS", "📋 View Alerts", "📊 Analytics", "🛡️ Safety Tips"]
)

# HOME PAGE
if page == "🏠 Home":

    st.title("🌸 SheShield")
    st.subheader("Smart Women Safety & Emergency Response System")

    st.subheader("📞 24/7 Emergency Helpline")

    st.markdown("""
🚓 <a href="tel:100">Police: 100</a><br>
🚑 <a href="tel:108">Ambulance: 108</a><br>
🔥 <a href="tel:101">Fire: 101</a><br>
👩 <a href="tel:1091">Women Helpline: 1091</a><br>
🚨 <a href="tel:112">National Emergency: 112</a><br>
👶 <a href="tel:1098">Child Helpline: 1098</a>
""", unsafe_allow_html=True)

    st.subheader("👨‍👩‍👧 Trusted Contacts")

    st.markdown("""
📞 <a href="tel:8088630512">Trusted Contact 1: 8088630512</a><br>
📞 <a href="tel:8431918980">Trusted Contact 2: 8431918980</a>
""", unsafe_allow_html=True)

# SEND SOS
elif page == "🚨 Send SOS":

    st.title("🚨 Emergency SOS")

    name = st.text_input("Enter Your Name")

    location_option = st.radio(
        "Choose Location Option",
        ["📍 Live Location", "✍️ Enter Manually"]
    )

    if location_option == "📍 Live Location":
        loc = get_geolocation()

        if loc:
            latitude = loc["coords"]["latitude"]
            longitude = loc["coords"]["longitude"]
            location = f"{latitude}, {longitude}"
            st.success(f"📍 Live Location: {location}")
        else:
            location = "Location not found"
            st.warning("Allow browser location access")

    else:
        location = st.text_input("Enter your location manually")

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

        alert = {
            "Name": name,
            "Location": location,
            "Emergency Type": emergency
        }

        df = pd.concat([df, pd.DataFrame([alert])], ignore_index=True)
        df.to_csv("alerts.csv", index=False)

        st.success("Emergency Alert Sent Successfully!")

        st.warning("""
🚨 Trusted Contacts:

📞 8088630512
📞 8431918980
""")

# VIEW ALERTS
elif page == "📋 View Alerts":

    st.title("📋 Emergency Alerts")

    if not df.empty:
        st.dataframe(df)
    else:
        st.warning("No alerts found.")

# ANALYTICS
elif page == "📊 Analytics":

    st.title("📊 Emergency Analytics Dashboard")

    if not df.empty:

        st.metric("Total Emergency Alerts", len(df))

        type_count = df["Emergency Type"].value_counts()

        fig = px.bar(
            x=type_count.index,
            y=type_count.values,
            labels={'x': 'Emergency Type', 'y': 'Count'},
            title="Emergency Alerts by Type"
        )
        st.plotly_chart(fig)

        location_count = df["Location"].value_counts()

        pie = px.pie(
            values=location_count.values,
            names=location_count.index,
            title="Alerts by Location"
        )
        st.plotly_chart(pie)

        st.dataframe(df)

    else:
        st.warning("No emergency alerts found.")

# SAFETY TIPS
elif page == "🛡️ Safety Tips":

    st.title("🛡️ Women Safety Tips")

    st.write("• Share live location with trusted contacts")
    st.write("• Avoid isolated areas at night")
    st.write("• Use verified transport services")
    st.write("• Keep phone charged")
    st.write("• Save emergency contacts")
    st.write("• Use SOS feature immediately")
