import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_js_eval import get_geolocation
import os
from datetime import datetime
import streamlit.components.v1 as components

# PAGE SETTINGS
st.set_page_config(page_title="SheShield", layout="wide")

# THEME CSS
st.markdown("""
<style>
.stApp { background-color: #FFF4B8; }
h1, h2, h3, p, label, div { color: #d63384 !important; }
[data-testid="stSidebar"] { background-color: #ffe4ec; }
.stButton > button {
    background: linear-gradient(to right, #ff5c8a, #c77dff);
    color: white; border-radius: 12px; border: none; font-weight: bold;
}
[data-testid="metric-container"] {
    background-color: #fff0f6; border: 2px solid #f8bbd0;
    border-radius: 10px; padding: 10px;
}
[data-testid="stMetricValue"] {
    color: #d63384 !important;
}
</style>
""", unsafe_allow_html=True)

# LOAD ALERTS
if os.path.exists("alerts.csv"):
    df = pd.read_csv("alerts.csv")
else:
    df = pd.DataFrame(columns=["Name", "Location", "Emergency Type", "Timestamp"])

# SIDEBAR
st.sidebar.title("🌸 SheShield")
page = st.sidebar.radio(
    "Navigation",
    ["🏠 Home", "🚨 Send SOS", "📋 View Alerts", "📊 Analytics", "🏥 Nearby Help", "🛡️ Safety Tips"]
)

# ── HOME ─────────────────────────────────────────────────────────────────────
if page == "🏠 Home":
    st.title("🌸 SheShield")
    st.subheader("Smart Women Safety & Emergency Response System")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div style="background-color:white;padding:20px;border-radius:15px;
        text-align:center;box-shadow:0px 0px 15px rgba(255,75,110,0.3);border:2px solid #ffd700;">
            <h1>🚨</h1><h1 style='color:#c77dff;'>24/7</h1>
            <h3 style='color:#d63384;'>Emergency Support</h3>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div style="background-color:white;padding:20px;border-radius:15px;
        text-align:center;box-shadow:0px 0px 15px rgba(255,75,110,0.3);border:2px solid #ffd700;">
            <h1>🛡️</h1><h1 style='color:#c77dff;'>100%</h1>
            <h3 style='color:#d63384;'>Women Safety Focus</h3>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div style="background-color:white;padding:20px;border-radius:15px;
        text-align:center;box-shadow:0px 0px 15px rgba(255,75,110,0.3);border:2px solid #ffd700;">
            <h1>⚡</h1><h1 style='color:#c77dff;'>Instant</h1>
            <h3 style='color:#d63384;'>Alert Response</h3>
        </div>""", unsafe_allow_html=True)

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

# ── SOS ──────────────────────────────────────────────────────────────────────
elif page == "🚨 Send SOS":
    st.title("🚨 Emergency SOS")
    name = st.text_input("Enter Your Name")

    location_option = st.radio("Choose Location Option", ["📍 Live Location", "✍️ Enter Manually"])

    latitude, longitude, location = None, None, "Location not found"

    if location_option == "📍 Live Location":
        loc = get_geolocation()
        if loc:
            latitude = loc["coords"]["latitude"]
            longitude = loc["coords"]["longitude"]
            location = f"{latitude}, {longitude}"
            st.success(f"📍 Live Location: {location}")
            st.map(pd.DataFrame({"lat": [latitude], "lon": [longitude]}))
        else:
            st.warning("Allow browser location access")
    else:
        location = st.text_input("Enter your location manually")

    emergency = st.selectbox("Emergency Type", [
        "Unsafe Area", "Harassment", "Medical Emergency", "Kidnapping Risk", "Other"
    ])

    if st.button("🚨 SEND EMERGENCY ALERT"):
        alert = {
            "Name": name,
            "Location": location,
            "Emergency Type": emergency,
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        df = pd.concat([df, pd.DataFrame([alert])], ignore_index=True)
        df.to_csv("alerts.csv", index=False)
        st.success("Emergency Alert Sent Successfully!")
        st.audio("https://actions.google.com/sounds/v1/alarms/alarm_clock.ogg")
        st.warning("🚨 Trusted Contacts notified:\n\n📞 8088630512\n📞 8431918980")

# ── VIEW ALERTS ───────────────────────────────────────────────────────────────
elif page == "📋 View Alerts":
    st.title("📋 Emergency Alerts")

    if not df.empty:
        total      = len(df)
        harassment = len(df[df["Emergency Type"] == "Harassment"])
        medical    = len(df[df["Emergency Type"] == "Medical Emergency"])
        other      = total - harassment - medical

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🚨 Total Alerts",     total)
        c2.metric("😡 Harassment",        harassment)
        c3.metric("🏥 Medical Emergency", medical)
        c4.metric("⚠️ Other",             other)

        st.markdown("---")
        st.subheader("📋 All Alerts")

        COLOR_MAP = {
            "Harassment":        "#ffe0e0",
            "Medical Emergency": "#fff3cd",
            "Unsafe Area":       "#fce4ec",
            "Kidnapping Risk":   "#f8d7da",
            "Other":             "#e8f5e9",
        }

        table_html = """
        <table style="width:100%;border-collapse:collapse;border-radius:12px;
        overflow:hidden;font-family:sans-serif;">
            <thead>
                <tr style="background:#d63384;color:white;">
                    <th style="padding:12px;text-align:left;color:white;">#</th>
                    <th style="padding:12px;text-align:left;color:white;">Name</th>
                    <th style="padding:12px;text-align:left;color:white;">Location</th>
                    <th style="padding:12px;text-align:left;color:white;">Emergency Type</th>
                    <th style="padding:12px;text-align:left;color:white;">Timestamp</th>
                </tr>
            </thead>
            <tbody>
        """

        for i, row in df.iterrows():
            bg = COLOR_MAP.get(row.get("Emergency Type", ""), "#ffffff")
            ts = row.get("Timestamp", "N/A")
            table_html += f"""
                <tr style="background-color:{bg};">
                    <td style="padding:10px;color:#000000;border-bottom:1px solid #eee;">{i+1}</td>
                    <td style="padding:10px;color:#000000;border-bottom:1px solid #eee;">{row.get('Name','')}</td>
                    <td style="padding:10px;color:#000000;border-bottom:1px solid #eee;">{row.get('Location','')}</td>
                    <td style="padding:10px;color:#000000;font-weight:bold;border-bottom:1px solid #eee;">{row.get('Emergency Type','')}</td>
                    <td style="padding:10px;color:#000000;border-bottom:1px solid #eee;">{ts}</td>
                </tr>
            """

        table_html += "</tbody></table>"
        components.html(table_html, height=min(100 + len(df) * 45, 600), scrolling=True)

    else:
        st.warning("No alerts found.")

# ── ANALYTICS ─────────────────────────────────────────────────────────────────
elif page == "📊 Analytics":
    st.title("📊 Emergency Analytics Dashboard")

    if not df.empty:
        st.metric("Total Emergency Alerts", len(df))

        type_count = df["Emergency Type"].value_counts()
        fig = px.bar(
            x=type_count.index,
            y=type_count.values,
            labels={'x': 'Emergency Type', 'y': 'Count'},
            title="Emergency Alerts by Type",
            color_discrete_sequence=["#d63384"]
        )
        fig.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            font_color="#000000"
        )
        st.plotly_chart(fig)

        location_count = df["Location"].value_counts()
        pie = px.pie(
            values=location_count.values,
            names=location_count.index,
            title="Alerts by Location"
        )
        pie.update_layout(
            paper_bgcolor="white",
            font_color="#000000"
        )
        st.plotly_chart(pie)

        st.dataframe(df, use_container_width=True)
    else:
        st.warning("No emergency alerts found.")

# ── NEARBY HELP ───────────────────────────────────────────────────────────────
elif page == "🏥 Nearby Help":
    st.title("🏥 Nearby Emergency Help")
    st.write("Find real-time emergency services near your location.")

    loc = get_geolocation()

    if loc:
        latitude  = loc["coords"]["latitude"]
        longitude = loc["coords"]["longitude"]
        st.success(f"📍 Your location: {latitude:.4f}, {longitude:.4f}")

        police_url    = f"https://www.google.com/maps/search/police+station/@{latitude},{longitude},14z"
        hospital_url  = f"https://www.google.com/maps/search/hospital/@{latitude},{longitude},14z"
        ambulance_url = f"https://www.google.com/maps/search/ambulance/@{latitude},{longitude},14z"

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 🚓 Nearby Police Stations")
            st.markdown(f"""
            <div style="background:white;padding:20px;border-radius:15px;
            border:2px solid #aed6f1;margin-bottom:15px;
            box-shadow:0px 4px 10px rgba(0,0,0,0.1);">
                <h3 style="color:#1a5276;margin:0;">🔍 Find Police Stations Near You</h3>
                <p style="color:#333;margin:10px 0;">Click below to see all nearby police stations on Google Maps</p>
                <a href="{police_url}" target="_blank" style="
                    display:block;text-align:center;
                    background:linear-gradient(to right,#1a5276,#2e86c1);
                    color:white;padding:12px 20px;border-radius:10px;
                    text-decoration:none;font-weight:bold;font-size:16px;">
                    🗺️ Open Nearby Police Stations
                </a>
            </div>
            <div style="background:white;padding:20px;border-radius:15px;
            border:2px solid #aed6f1;margin-bottom:15px;
            box-shadow:0px 4px 10px rgba(0,0,0,0.1);">
                <h3 style="color:#1a5276;">📞 Police Helplines</h3>
                <p style="color:#333;font-size:16px;">🚨 National Emergency</p>
                <a href="tel:112" style="display:block;text-align:center;
                    background:#c0392b;color:white;padding:10px;
                    border-radius:8px;text-decoration:none;
                    font-weight:bold;margin-bottom:8px;">📞 Call 112</a>
                <p style="color:#333;font-size:16px;">🚓 Police</p>
                <a href="tel:100" style="display:block;text-align:center;
                    background:#1a5276;color:white;padding:10px;
                    border-radius:8px;text-decoration:none;font-weight:bold;">
                    📞 Call 100</a>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("### 🏥 Nearby Hospitals")
            st.markdown(f"""
            <div style="background:white;padding:20px;border-radius:15px;
            border:2px solid #f1948a;margin-bottom:15px;
            box-shadow:0px 4px 10px rgba(0,0,0,0.1);">
                <h3 style="color:#922b21;margin:0;">🔍 Find Hospitals Near You</h3>
                <p style="color:#333;margin:10px 0;">Click below to see all nearby hospitals on Google Maps</p>
                <a href="{hospital_url}" target="_blank" style="
                    display:block;text-align:center;
                    background:linear-gradient(to right,#922b21,#cb4335);
                    color:white;padding:12px 20px;border-radius:10px;
                    text-decoration:none;font-weight:bold;font-size:16px;margin-bottom:10px;">
                    🗺️ Open Nearby Hospitals
                </a>
                <a href="{ambulance_url}" target="_blank" style="
                    display:block;text-align:center;
                    background:linear-gradient(to right,#117a65,#148f77);
                    color:white;padding:12px 20px;border-radius:10px;
                    text-decoration:none;font-weight:bold;font-size:16px;">
                    🚑 Find Nearby Ambulance Services
                </a>
            </div>
            <div style="background:white;padding:20px;border-radius:15px;
            border:2px solid #f1948a;margin-bottom:15px;
            box-shadow:0px 4px 10px rgba(0,0,0,0.1);">
                <h3 style="color:#922b21;">📞 Medical Helplines</h3>
                <p style="color:#333;font-size:16px;">🚑 Ambulance</p>
                <a href="tel:108" style="display:block;text-align:center;
                    background:#922b21;color:white;padding:10px;
                    border-radius:8px;text-decoration:none;
                    font-weight:bold;margin-bottom:8px;">📞 Call 108</a>
                <p style="color:#333;font-size:16px;">👩 Women Helpline</p>
                <a href="tel:1091" style="display:block;text-align:center;
                    background:#c0392b;color:white;padding:10px;
                    border-radius:8px;text-decoration:none;font-weight:bold;">
                    📞 Call 1091</a>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("🗺️ Your Location on Map")
        st.map(pd.DataFrame({"lat": [latitude], "lon": [longitude]}))

    else:
        st.warning("📍 Please allow location access in your browser to find nearby help.")

# ── SAFETY TIPS ───────────────────────────────────────────────────────────────
elif page == "🛡️ Safety Tips":
    st.title("🛡️ Women Safety Tips")
    st.write("• Share live location with trusted contacts")
    st.write("• Avoid isolated areas at night")
    st.write("• Use verified transport services")
    st.write("• Keep phone charged")
    st.write("• Save emergency contacts")
    st.write("• Use SOS feature immediately")
