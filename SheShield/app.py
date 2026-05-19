import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_js_eval import get_geolocation
import os
import smtplib
from email.mime.text import MIMEText

def send_email_alert(name, location, emergency):

    sender_email = st.secrets["EMAIL"]
    app_password = st.secrets["APP_PASSWORD"]
    receiver_email = st.secrets["EMAIL"]

    subject = "🚨 SheShield SOS ALERT"

    body = f"""
Emergency Alert Received!

Name: {name}
Location: {location}
Emergency Type: {emergency}

Trusted Contacts:
8088630512
8431918980
"""

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver_email

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        st.success("📧 Alert sent to Gmail successfully!")

    except Exception:
        st.error("Email sending failed")

# LOAD ALERTS
if os.path.exists("alerts.csv"):
    df = pd.read_csv("alerts.csv")
else:
    df = pd.DataFrame(columns=["Name", "Location", "Emergency Type"])

# PAGE SETTINGS
st.set_page_config(page_title="SheShield", layout="wide")

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
    ["🏠 Home", "🚨 Send SOS", "📋 View Alerts", "📊 Analytics", "🛡️ Safety Tips"]
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

    st.subheader("📞 24/7 Emergency Helpline")

    st.markdown("""
<a href="tel:100">🚓 Police: 100</a><br>
<a href="tel:108">🚑 Ambulance: 108</a><br>
<a href="tel:101">🔥 Fire: 101</a><br>
<a href="tel:1091">👩 Women Helpline: 1091</a><br>
<a href="tel:112">🚨 National Emergency: 112</a><br>
<a href="tel:1098">👶 Child Helpline: 1098</a>
""", unsafe_allow_html=True)

    st.subheader("👨‍👩‍👧 Trusted Contacts")

    st.markdown("""
<a href="tel:8088630512">📞 Trusted Contact 1: 8088630512</a><br>
<a href="tel:8431918980">📞 Trusted Contact 2: 8431918980</a>
""", unsafe_allow_html=True)

# SEND SOS PAGE
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
        send_email_alert(name, location, emergency)

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
