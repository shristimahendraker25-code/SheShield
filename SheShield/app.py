# SEND SOS PAGE
elif page == "🚨 Send SOS":

    st.title("🚨 Emergency SOS")

    name = st.text_input("Enter Your Name")

    # LOCATION CHOICE
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
            st.warning("Please allow browser location access")

    else:
        location = st.text_input(
            "Enter your location manually",
            placeholder="Example: MG Road, Bangalore"
        )

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

        st.session_state.alerts.append(alert)

        st.success("Emergency Alert Sent Successfully!")
