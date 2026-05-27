import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_js_eval import get_geolocation
import streamlit.components.v1 as components
import os, smtplib, math, requests, time, json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

# ── PAGE CONFIG ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="SheShield", layout="wide", page_icon="🛡️")

# ══════════════════════════════════════════════════════════════════════════════
#  CONFIGURATION (set via environment variables in production)
# ══════════════════════════════════════════════════════════════════════════════
ALERT_EMAIL     = os.environ.get("SHESHIELD_ALERT_EMAIL", "")
SENDER_EMAIL    = os.environ.get("SHESHIELD_SENDER_EMAIL", "")
SENDER_APP_PWD  = os.environ.get("SHESHIELD_SENDER_APP_PASSWORD", "")

TWILIO_SID      = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_TOKEN    = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM     = os.environ.get("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
TWILIO_SMS_FROM = os.environ.get("TWILIO_SMS_FROM", "")  # E.g. +1234567890 (Twilio phone number)

ANTHROPIC_KEY   = os.environ.get("ANTHROPIC_API_KEY", "")


def current_user():
    """Display name from onboarding, or a neutral default."""
    try:
        return (st.session_state.get("user_name") or "").strip() or "User"
    except Exception:
        return "User"

# ══════════════════════════════════════════════════════════════════════════════
#  CSS / THEME
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700;800&family=Inter:wght@400;500;600&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;background-color:#080A14;color:#F2F4FF;}
.stApp{background-color:#080A14;}
h1,h2,h3,h4{font-family:'Outfit',sans-serif!important;color:#F2F4FF!important;}
/* Hide sidebar — we use top nav */
[data-testid="stSidebar"]{display:none!important;}
[data-testid="collapsedControl"]{display:none!important;}
.stButton>button{background:#E8196E;color:white;border-radius:14px;border:none;font-weight:700;
  font-family:'Outfit',sans-serif;padding:0.6rem 1.4rem;transition:all 0.2s;}
.stButton>button:hover{background:#c9155f;}
[data-testid="metric-container"]{background-color:#0F1120;border:1px solid rgba(255,255,255,0.08);
  border-radius:16px;padding:16px;}
[data-testid="stMetricValue"]{color:#E8196E!important;font-family:'Outfit',sans-serif!important;}
[data-testid="stMetricLabel"]{color:#7A7E9A!important;}
.card{background:#0F1120;border:1px solid rgba(255,255,255,0.08);border-radius:20px;
  padding:20px;margin-bottom:16px;}
.badge-high{background:#E8196E22;color:#E8196E;border:1px solid #E8196E44;border-radius:20px;
  padding:2px 10px;font-size:12px;font-weight:600;}
.badge-medium{background:#FFB02022;color:#FFB020;border:1px solid #FFB02044;border-radius:20px;
  padding:2px 10px;font-size:12px;font-weight:600;}
.badge-low{background:#22c55e22;color:#22c55e;border:1px solid #22c55e44;border-radius:20px;
  padding:2px 10px;font-size:12px;font-weight:600;}
.ai-bubble-bot{background:#0F1120;border:1px solid rgba(255,255,255,0.08);
  border-radius:18px 18px 18px 4px;padding:12px 16px;margin:8px 0;
  max-width:80%;font-size:14px;line-height:1.6;}
.ai-bubble-user{background:#E8196E;border-radius:18px 18px 4px 18px;padding:12px 16px;
  margin:8px 0 8px auto;max-width:80%;font-size:14px;text-align:right;color:white;}
input,textarea,select{background-color:#1A1D2E!important;color:#F2F4FF!important;
  border:1px solid rgba(255,255,255,0.1)!important;border-radius:12px!important;}
.sos-box{background:radial-gradient(circle,#E8196E33 0%,#080A14 70%);
  border:2px solid #E8196E55;border-radius:24px;padding:40px;text-align:center;}
.helpline-link{display:block;background:#1A1D2E;border:1px solid rgba(255,255,255,0.1);
  border-radius:12px;padding:10px 16px;margin-bottom:8px;color:#F2F4FF;
  text-decoration:none;font-weight:500;}
.helpline-link:hover{border-color:#E8196E;}
.night-banner{background:linear-gradient(90deg,#1a0a2e,#0d1a2e);
  border:1px solid #7B61FF44;border-radius:14px;padding:12px 18px;
  display:flex;align-items:center;gap:10px;margin-bottom:16px;}
.countdown-bar{background:#1A1D2E;border:1px solid rgba(255,255,255,0.08);
  border-radius:16px;padding:16px;text-align:center;margin-bottom:16px;}
.stSelectbox>div>div{background-color:#1A1D2E!important;color:#F2F4FF!important;}
.stTextInput>div>div>input{background-color:#1A1D2E!important;}
div[data-testid="stMarkdownContainer"] p{color:#C8CCE8;}
/* Tab nav */
.ss-tabs{display:flex;gap:4px;background:#0F1120;border:1px solid rgba(255,255,255,0.08);
  border-radius:16px;padding:6px;margin:12px 0;overflow-x:auto;
  box-shadow:0 2px 12px rgba(0,0,0,0.3);}
.ss-tab{display:inline-flex;align-items:center;gap:6px;padding:8px 16px;border-radius:10px;
  font-size:13px;font-weight:500;color:#C8CCE8;white-space:nowrap;border:none;
  background:transparent;transition:all 0.18s;font-family:'Inter',sans-serif;}
.ss-tab:hover{background:#1A1D2E;color:#F2F4FF;}
.ss-tab.active{background:#E8196E;color:white;font-weight:600;
  box-shadow:0 4px 12px rgba(232,25,110,0.4);}
/* Header */
.ss-header{display:flex;align-items:center;justify-content:space-between;
  padding:14px 0 10px;border-bottom:1px solid rgba(255,255,255,0.06);margin-bottom:8px;}
.ss-logo-name{font-family:'Outfit',sans-serif;font-size:22px;color:#E8196E;font-weight:700;}
.ss-badge{display:inline-flex;align-items:center;gap:6px;background:#E8196E18;
  border:1px solid #E8196E30;border-radius:30px;padding:4px 12px;font-size:12px;
  color:#E8196E;font-weight:600;}
.ss-badge-dot{width:7px;height:7px;border-radius:50%;background:#22c55e;
  animation:pulse 2s infinite;display:inline-block;}
/* Section label */
.section-label{font-size:11px;letter-spacing:3px;text-transform:uppercase;
  color:#E8196E;font-weight:700;margin-bottom:6px;font-family:'Outfit',sans-serif;}
/* Page title */
.page-title{margin-bottom:20px;}
.page-title h1{margin-bottom:4px!important;}
.page-title p{color:#7A7E9A;font-size:14px;margin:0;}
/* Dial chips */
.dial-chip{display:inline-flex;align-items:center;gap:5px;background:#1A1D2E;
  border:1px solid rgba(255,255,255,0.1);border-radius:40px;padding:6px 14px;
  font-size:13px;font-weight:600;color:#C8CCE8;text-decoration:none;
  transition:all 0.15s;margin:0 4px 6px 0;}
.dial-chip:hover{background:#E8196E;color:white;border-color:#E8196E;}
/* Phone mock */
.phone-mock{width:240px;margin:0 auto;background:#111827;border-radius:36px;
  padding:14px 8px;box-shadow:0 20px 60px rgba(0,0,0,0.5);border:5px solid #1f2937;}
.phone-screen{background:#E8196E;border-radius:22px;padding:20px;text-align:center;
  color:white;min-height:200px;display:flex;flex-direction:column;
  align-items:center;justify-content:center;}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
.main .block-container{max-width:100%!important;padding:0 2rem!important;}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def haversine_km(lat1,lon1,lat2,lon2):
    R=6371; dlat=math.radians(lat2-lat1); dlon=math.radians(lon2-lon1)
    a=math.sin(dlat/2)**2+math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
    return R*2*math.atan2(math.sqrt(a),math.sqrt(1-a))

def geocode_address(address):
    try:
        r=requests.get("https://nominatim.openstreetmap.org/search",
            params={"q":address,"format":"json","limit":1},
            headers={"User-Agent":"SheShield/2.0"},timeout=5)
        d=r.json()
        if d: return float(d[0]["lat"]),float(d[0]["lon"]),d[0].get("display_name",address)
    except: pass
    return None,None,None

def fetch_nearby_osm(lat, lon, amenity, radius_m=10000, limit=8):
    """
    FIXED: Uses multiple amenity fallbacks, larger radius, and handles
    Overpass API failures gracefully with a Google Maps fallback link.
    """
    amenity_groups = {
        "hospital": ["hospital", "clinic", "doctors", "health_centre", "pharmacy"],
        "police":   ["police"],
        "clinic":   ["clinic", "doctors", "health_centre"],
    }
    targets = amenity_groups.get(amenity, [amenity])
    out = []
    seen_names = set()
    
    for target in targets:
        if len(out) >= limit:
            break
        try:
            q = (
                f"[out:json][timeout:30];"
                f"("
                f"node[amenity={target}](around:{radius_m},{lat},{lon});"
                f"way[amenity={target}](around:{radius_m},{lat},{lon});"
                f"relation[amenity={target}](around:{radius_m},{lat},{lon});"
                f");out center {limit};"
            )
            r = requests.post(
                "https://overpass-api.de/api/interpreter",
                data={"data": q}, timeout=30
            )
            for el in r.json().get("elements", []):
                tags = el.get("tags", {})
                name = (tags.get("name") or tags.get("name:en") or
                        target.replace("_"," ").title())
                elat = el.get("lat") or el.get("center", {}).get("lat")
                elon = el.get("lon") or el.get("center", {}).get("lon")
                if elat and elon and name not in seen_names:
                    seen_names.add(name)
                    out.append({
                        "name": name, "lat": elat, "lon": elon,
                        "dist_km": haversine_km(lat, lon, elat, elon),
                        "phone": tags.get("phone") or tags.get("contact:phone", ""),
                        "type": target
                    })
        except Exception:
            continue  # Try next amenity type
    
    out.sort(key=lambda x: x["dist_km"])
    return out[:limit]

def reverse_geocode(lat,lon):
    try:
        r=requests.get("https://nominatim.openstreetmap.org/reverse",
            params={"lat":lat,"lon":lon,"format":"json"},
            headers={"User-Agent":"SheShield/2.0"},timeout=4)
        d=r.json().get("address",{})
        return (d.get("road") or d.get("neighbourhood") or d.get("suburb") or
                d.get("village") or d.get("town") or d.get("city") or f"{lat:.4f},{lon:.4f}")
    except: return f"{lat:.4f},{lon:.4f}"

def normalize_phone(phone):
    digits = "".join(c for c in str(phone or "") if c.isdigit())
    if len(digits) == 10:
        return digits
    if len(digits) >= 12 and digits.startswith("91"):
        return digits[-10:]
    return digits[-10:] if len(digits) >= 10 else ""

def maps_tracking_url(lat, lon):
    return f"https://www.google.com/maps?q={lat},{lon}"

def get_location_recipient_phones():
    """Trusted contacts + optional guardian/monitor phone + your own phone if enabled."""
    phones = set()
    for c in st.session_state.get("trusted_contacts", []):
        p = normalize_phone(c.get("phone", ""))
        if len(p) == 10:
            phones.add(p)
    mon = normalize_phone(st.session_state.get("monitor_phone", ""))
    if len(mon) == 10:
        phones.add(mon)
    if st.session_state.get("share_to_my_phone", True):
        own = normalize_phone(st.session_state.get("user_phone", ""))
        if len(own) == 10:
            phones.add(own)
    return sorted(phones)

def build_live_location_message(name, lat, lon, extra=""):
    place = reverse_geocode(lat, lon)
    ts = datetime.now().strftime("%I:%M %p, %d %b %Y")
    msg = (
        f"SheShield live location — {name}\n"
        f"Time: {ts}\n"
        f"Near: {place}\n"
        f"Open map: {maps_tracking_url(lat, lon)}"
    )
    if extra:
        msg += f"\nNote: {extra}"
    return msg

def twilio_sms_ready():
    return bool(TWILIO_SID and TWILIO_TOKEN and TWILIO_SMS_FROM)

def send_sms_twilio(body, phones):
    if not twilio_sms_ready():
        return 0
    try:
        from twilio.rest import Client
        client = Client(TWILIO_SID, TWILIO_TOKEN)
        sent = 0
        errors = []
        for ph in phones:
            try:
                client.messages.create(
                    body=body,
                    from_=TWILIO_SMS_FROM,
                    to=f"+91{ph}",
                )
                sent += 1
            except Exception as e:
                errors.append(f"+91{ph}: {e}")
        if errors and sent == 0:
            st.error("SMS could not be sent via Twilio:\n\n" + "\n".join(errors[:4]))
        elif errors:
            st.warning("Some SMS failed:\n" + "\n".join(errors[:3]))
        return sent
    except ImportError:
        st.info("Install twilio for automatic SMS: pip install twilio")
    except Exception as e:
        st.warning(f"SMS error: {e}")
    return 0

def render_sms_tap_links(body, phones, heading="Tap each button, then press Send in your SMS app"):
    """Reliable on mobile — user must tap Send (websites cannot SMS silently without Twilio)."""
    if not phones:
        return
    st.markdown(f"**{heading}**")
    for i, ph in enumerate(phones):
        url = f"sms:+91{ph}?body={requests.utils.quote(body)}"
        st.link_button(f"📱 Send SMS to +91{ph}", url, use_container_width=True, key=f"sms_tap_{ph}_{i}")

def open_native_sms_to_phones(phones, body):
    """Try to open SMS app via JS (may be blocked — tap-links are more reliable)."""
    if not phones:
        return 0
    components.html(
        f"""
        <script>
        var phones = {json.dumps(phones)};
        var msg = encodeURIComponent({json.dumps(body)});
        function openSms(ph) {{
          var url = "sms:+91" + ph + "?body=" + msg;
          var a = document.createElement("a");
          a.href = url;
          a.style.display = "none";
          (document.body || document.documentElement).appendChild(a);
          a.click();
        }}
        phones.forEach(function(ph, i) {{
            setTimeout(function() {{ openSms(ph); }}, i * 1200);
        }});
        </script>
        """,
        height=0,
    )
    return len(phones)

def whatsapp_link(phone, body):
    ph = normalize_phone(phone)
    if len(ph) != 10:
        return None
    return f"https://wa.me/91{ph}?text={requests.utils.quote(body)}"

def refresh_live_location(component_key="gps_read"):
    """Read GPS from browser via streamlit-js-eval (unique key per call)."""
    loc_data = get_geolocation(component_key=component_key)
    if not loc_data or not isinstance(loc_data, dict):
        return False
    coords = loc_data.get("coords") or loc_data
    lat = coords.get("latitude")
    lon = coords.get("longitude")
    if lat is None or lon is None:
        return False
    st.session_state.live_lat = float(lat)
    st.session_state.live_lon = float(lon)
    st.session_state.live_accuracy = coords.get("accuracy")
    st.session_state.live_location_updated = datetime.now()
    return True

def fetch_approximate_ip_location():
    try:
        r = requests.get("https://ipapi.co/json/", timeout=4)
        d = r.json()
        if d.get("latitude") is not None:
            return float(d["latitude"]), float(d["longitude"]), d.get("city", "Approximate area")
    except Exception:
        pass
    return None, None, None

def broadcast_live_location(note="Live location"):
    lat, lon = st.session_state.get("live_lat"), st.session_state.get("live_lon")
    if not lat or not lon:
        return 0, "no_gps"
    phones = get_location_recipient_phones()
    if not phones:
        return 0, "no_phones"
    body = build_live_location_message(current_user(), lat, lon, extra=note)
    sent = send_sms_twilio(body, phones)
    if sent > 0:
        st.session_state.pop("pending_sms_body", None)
        st.session_state.pop("pending_sms_phones", None)
        return sent, "twilio"
    st.session_state.pending_sms_body = body
    st.session_state.pending_sms_phones = phones
    open_native_sms_to_phones(phones, body)
    return len(phones), "native_sms"

def maybe_auto_share_location():
    if not st.session_state.get("live_share_enabled"):
        return
    if not TWILIO_SMS_FROM:
        return  # automatic interval only with Twilio; use "Send to all phones" for manual SMS
    interval_sec = int(st.session_state.get("live_share_interval_min", 5)) * 60
    last = st.session_state.get("last_live_share_sent")
    if last and (datetime.now() - last).total_seconds() < interval_sec:
        return
    sent, _ = broadcast_live_location("Automatic live update")
    if sent:
        st.session_state.last_live_share_sent = datetime.now()

def inject_gps_permission_helper():
    """Continuous GPS watch in browser (helps mobile browsers)."""
    components.html(
        """
        <script>
        (function() {
          if (!navigator.geolocation) return;
          navigator.geolocation.watchPosition(
            function(pos) {
              var el = document.getElementById("ss-gps-status");
              if (!el) {
                el = document.createElement("div");
                el.id = "ss-gps-status";
                el.style.cssText = "font-size:11px;color:#22c55e;padding:4px;";
                document.body.appendChild(el);
              }
              el.textContent = "GPS active · " +
                pos.coords.latitude.toFixed(5) + ", " + pos.coords.longitude.toFixed(5);
            },
            function(err) {
              var el = document.getElementById("ss-gps-status");
              if (el) el.textContent = "GPS blocked — allow location in browser settings";
            },
            { enableHighAccuracy: true, maximumAge: 15000, timeout: 20000 }
          );
        })();
        </script>
        """,
        height=28,
    )

def render_live_location_panel():
    """Live GPS card — refresh, map, auto-SMS sharing."""
    st.markdown("### 📍 Live location tracker")
    inject_gps_permission_helper()

    lat, lon = st.session_state.get("live_lat"), st.session_state.get("live_lon")
    updated = st.session_state.get("live_location_updated")
    acc = st.session_state.get("live_accuracy")

    r1, r2, r3 = st.columns(3)
    with r1:
        if st.button("🔄 Refresh GPS", use_container_width=True, key="gps_refresh_btn"):
            if refresh_live_location(component_key="gps_manual_refresh"):
                st.success("Location updated.")
                st.rerun()
            else:
                st.warning(
                    "Could not get GPS. On phone: use Chrome/Safari, allow Location, and open "
                    "via https or localhost. Or set coordinates manually below."
                )
    with r2:
        if st.button("📲 Send to all phones now", use_container_width=True, key="gps_send_all_btn"):
            sent, mode = broadcast_live_location("Shared from SheShield")
            if mode == "no_gps":
                st.error("No GPS yet — tap Refresh GPS first.")
            elif mode == "no_phones":
                st.error("Add trusted contacts (with 10-digit numbers) on the Contacts tab.")
            elif mode == "twilio":
                st.success(f"SMS sent automatically to {sent} phone number(s).")
            else:
                st.info(
                    f"Ready to SMS {sent} number(s). **On your phone**, tap each green button below "
                    f"and press **Send** — the website cannot deliver SMS by itself without Twilio."
                )
                render_sms_tap_links(
                    st.session_state.get("pending_sms_body", ""),
                    st.session_state.get("pending_sms_phones", []),
                )
    with r3:
        st.session_state.live_share_enabled = st.toggle(
            "Auto-send every few min",
            value=st.session_state.get("live_share_enabled", False),
            key="live_share_toggle",
        )

    if lat and lon:
        updated_str = updated.strftime("%I:%M:%S %p") if updated else "just now"
        acc_str = f"±{acc:.0f} m" if acc else ""
        place = reverse_geocode(lat, lon)
        st.success(f"**{place}** · `{lat:.5f}, {lon:.5f}` {acc_str} · updated {updated_str}")
        st.map(pd.DataFrame({"lat": [lat], "lon": [lon]}), zoom=15)
        st.markdown(
            f'<a href="{maps_tracking_url(lat, lon)}" target="_blank" '
            f'style="color:#E8196E;font-weight:600;">🗺️ Open live pin in Google Maps</a>',
            unsafe_allow_html=True,
        )
        phones = get_location_recipient_phones()
        if phones:
            st.caption(f"Location will be sent to: {', '.join('+91' + p for p in phones)}")
    if st.session_state.get("pending_sms_body") and st.session_state.get("pending_sms_phones"):
        render_sms_tap_links(
            st.session_state.pending_sms_body,
            st.session_state.pending_sms_phones,
            heading="Pending — tap to send SMS",
        )
    if not twilio_sms_ready():
        st.info(
            "**Automatic SMS** (no tap required) needs Twilio: set `TWILIO_ACCOUNT_SID`, "
            "`TWILIO_AUTH_TOKEN`, and `TWILIO_SMS_FROM` in your environment (see `.env.example`). "
            "Otherwise use the tap buttons above **on your phone** — SMS does not work from a laptop browser."
        )
    else:
        st.caption("Twilio SMS is configured — use **Send to all phones** or enable **Auto-send**.")
    if not (lat and lon):
        st.warning(
            "Location not detected yet. Tap **Refresh GPS** and allow location when prompted. "
            "Keep this tab open while travelling."
        )

    with st.expander("Manual location / approximate GPS"):
        mc1, mc2, mc3 = st.columns(3)
        with mc1:
            mlat = st.number_input("Latitude", value=float(lat or 12.97), format="%.6f", key="manual_lat")
        with mc2:
            mlon = st.number_input("Longitude", value=float(lon or 77.59), format="%.6f", key="manual_lon")
        with mc3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Use these coordinates", key="manual_gps_apply"):
                st.session_state.live_lat = mlat
                st.session_state.live_lon = mlon
                st.session_state.live_location_updated = datetime.now()
                st.rerun()
        if st.button("Use approximate location (IP-based)", key="ip_gps_btn"):
            ilat, ilon, city = fetch_approximate_ip_location()
            if ilat:
                st.session_state.live_lat = ilat
                st.session_state.live_lon = ilon
                st.session_state.live_location_updated = datetime.now()
                st.info(f"Approximate location set near {city}. For accurate tracking, use Refresh GPS on your phone.")
                st.rerun()
            st.error("Could not detect approximate location.")

    if st.session_state.get("live_share_enabled"):
        st.session_state.live_share_interval_min = st.select_slider(
            "Auto-send interval (minutes)",
            options=[2, 3, 5, 10, 15],
            value=st.session_state.get("live_share_interval_min", 5),
            key="live_share_interval_slider",
        )
        if TWILIO_SMS_FROM:
            st.caption("Auto-send uses Twilio SMS when configured.")
        else:
            st.caption(
                "Without Twilio SMS, auto-send opens your SMS app on each interval — "
                "set TWILIO_SMS_FROM for fully automatic texts."
            )

def get_unsafe_zones(lat,lon):
    offsets=[(0.008,0.006,"High","Poor CCTV, isolated after dark"),
             (0.015,-0.010,"Medium","Low foot traffic, reported incidents"),
             (-0.010,0.018,"High","No nearby police post, blind spot"),
             (0.020,0.005,"Medium","Dimly lit, limited transport"),
             (-0.005,-0.015,"Low","Some CCTV, moderate footfall")]
    zones=[]
    for dlat,dlon,risk,reason in offsets:
        zlat,zlon=lat+dlat,lon+dlon
        dist=haversine_km(lat,lon,zlat,zlon)
        name=reverse_geocode(zlat,zlon)
        zones.append((name,risk,f"{dist:.1f} km",reason,zlat,zlon))
    return zones

def send_email(name,location,emergency,desc,timestamp):
    if not all([ALERT_EMAIL, SENDER_EMAIL, SENDER_APP_PWD]):
        return False
    try:
        msg=MIMEMultipart()
        msg["From"]=SENDER_EMAIL; msg["To"]=ALERT_EMAIL
        msg["Subject"]=f"SOS from {name} — {emergency}"
        body=f"""SheShield Emergency Alert\n\nName: {name}\nEmergency: {emergency}\nLocation: {location}\nTime: {timestamp}\nNotes: {desc or 'None'}\n\nGoogle Maps: https://maps.google.com/?q={location}"""
        msg.attach(MIMEText(body,"plain"))
        with smtplib.SMTP_SSL("smtp.gmail.com",465) as s:
            s.login(SENDER_EMAIL,SENDER_APP_PWD); s.sendmail(SENDER_EMAIL,ALERT_EMAIL,msg.as_string())
        return True
    except Exception as e:
        st.warning(f"Email error: {e}"); return False

def send_whatsapp(name,location,emergency,contacts):
    sent=0
    if not TWILIO_SID or not TWILIO_TOKEN:
        return 0
    try:
        from twilio.rest import Client
        client=Client(TWILIO_SID,TWILIO_TOKEN)
        msg=f"SOS ALERT!\n{name} needs help!\nEmergency: {emergency}\nLocation: https://maps.google.com/?q={location}\nTime: {datetime.now().strftime('%H:%M')}"
        phones = set()
        for c in contacts:
            p = normalize_phone(c.get("phone", ""))
            if len(p) == 10:
                phones.add(p)
        for p in get_location_recipient_phones():
            phones.add(p)
        for ph in phones:
            try:
                client.messages.create(body=msg, from_=TWILIO_FROM, to=f"whatsapp:+91{ph}")
                sent += 1
            except Exception:
                pass
    except ImportError:
        st.info("Install twilio: pip install twilio")
    except Exception as e:
        st.warning(f"WhatsApp error: {e}")
    return sent

def send_offline_sms(name, location, emergency, contacts):
    """Opens native SMS app for all trusted contacts + monitor phone."""
    phones = set()
    for c in contacts:
        p = normalize_phone(c.get("phone", ""))
        if len(p) == 10:
            phones.add(p)
    for p in get_location_recipient_phones():
        phones.add(p)
    if not phones:
        return 0
    msg = (
        f"SOS ALERT! {name} needs help! Emergency: {emergency}. "
        f"Location: https://maps.google.com/?q={location} "
        f"Time: {datetime.now().strftime('%H:%M')}"
    )
    return open_native_sms_to_phones(sorted(phones), msg)

def smart_ai(messages, home_lat=None, home_lon=None, is_night=False, contacts=None):
    """
    Fully offline smart AI — no API key needed.
    Understands context, conversation history, and gives real safety advice.
    """
    user = current_user()
    contacts = contacts or []
    contact_names = ", ".join([c["name"] for c in contacts if c.get("name")]) or "no contacts saved yet"
    hour = datetime.now().hour
    time_str = datetime.now().strftime("%I:%M %p")
    loc_str = f"{home_lat:.4f}, {home_lon:.4f}" if home_lat else "unknown"
    night_note = " Since it's late at night, please be extra cautious." if is_night else ""

    # Get last user message
    user_msgs = [m["content"] for m in messages if m["role"] == "user"]
    if not user_msgs:
        return f"Hi {user}! I'm your SheShield safety assistant. Ask me anything about staying safe."
    q = user_msgs[-1].lower().strip()

    # ── SOS / EMERGENCY ──────────────────────────────────────────────────────
    if any(w in q for w in ["sos", "emergency", "attack", "help me", "danger", "threatened", "attacked", "unsafe", "scared", "fear"]):
        return (
            f"🚨 **This sounds like an emergency, {user}!**\n\n"
            f"**Do this RIGHT NOW:**\n"
            f"1. Go to **Send SOS** page immediately\n"
            f"2. Hit the red **SEND EMERGENCY ALERT** button\n"
            f"3. Your contacts ({contact_names}) will be alerted instantly\n"
            f"4. Call **112** if you need police immediately\n\n"
            f"📍 Your location ({loc_str}) will be shared with your contacts.\n"
            f"Stay on a call with someone. You are not alone."
        )

    # ── SAFE / CHECK-IN ──────────────────────────────────────────────────────
    if any(w in q for w in ["i'm safe", "im safe", "i am safe", "reached home", "i'm okay", "i'm fine", "reached safely"]):
        return (
            f"✅ So glad to hear that, {user}! \n\n"
            f"Your next check-in is in **{st.session_state.checkin_interval} minutes**. "
            f"Click **✅ Check In — I'm Safe** on the Home page to reset the timer.\n\n"
            f"Stay aware of your surroundings and keep your phone charged. 💪"
        )

    # ── ROUTE / HOME ─────────────────────────────────────────────────────────
    if any(w in q for w in ["route", "home", "go home", "way home", "path home", "directions", "navigate"]):
        tips = (
            "🌙 **Night route tips:**\n"
            "- Stick to main, well-lit roads only\n"
            "- Avoid shortcuts, alleys, and isolated areas\n"
            "- Prefer Ola/Uber over walking if distance > 1 km\n"
            "- Stay on a call with a contact the entire time\n"
            "- Share your live location from the **Safe Route Home** page"
        ) if is_night else (
            "🗺️ **Route tips:**\n"
            "- Use the **Safe Route Home** page for Google Maps navigation\n"
            "- Share your live location with a contact before leaving\n"
            "- Let someone know your ETA"
        )
        return (
            f"Go to the **🛣️ Safe Route Home** page — it has one-tap Google Maps navigation to your saved home address.{night_note}\n\n{tips}"
        )

    # ── POLICE ───────────────────────────────────────────────────────────────
    if any(w in q for w in ["police", "cop", "station", "thana", "100"]):
        return (
            f"🚔 **Nearest police help:**\n\n"
            f"- Go to **🏥 Nearby Help** page — it shows police stations within 10 km of you\n"
            f"- Call **100** (Police) directly from the sidebar Quick Dial\n"
            f"- Call **112** for any emergency — fastest response\n\n"
            f"📍 Your current location ({loc_str}) will be visible to you on that page."
        )

    # ── HOSPITAL / MEDICAL ───────────────────────────────────────────────────
    if any(w in q for w in ["hospital", "doctor", "medical", "ambulance", "hurt", "injured", "108", "clinic"]):
        return (
            f"🏥 **Medical help:**\n\n"
            f"- Go to **🏥 Nearby Help** page — it shows hospitals and clinics within 10 km\n"
            f"- Call **108** for ambulance (free, 24/7)\n"
            f"- Call **112** if it's a life-threatening emergency\n\n"
            f"If someone is injured, call 108 first, then stay on the line with them.{night_note}"
        )

    # ── NIGHT / LATE ─────────────────────────────────────────────────────────
    if any(w in q for w in ["night", "late", "dark", "midnight", "alone", "11 pm", "12 am", "1 am", "2 am"]):
        return (
            f"🌙 **Night Shield is active, {user}.**\n\n"
            f"Check-ins are every **15 minutes** at night. Your contacts ({contact_names}) are on standby.\n\n"
            f"**Stay safe at night:**\n"
            f"- Stay on well-lit main roads\n"
            f"- Keep your phone volume up\n"
            f"- Avoid using earphones — stay alert\n"
            f"- Use **Safe Route Home** to navigate\n"
            f"- If anything feels wrong, go to **Send SOS** immediately\n\n"
            f"Current time: {time_str}. I'm watching over you. 🛡️"
        )

    # ── DON'T FEEL SAFE / ANXIOUS ────────────────────────────────────────────
    if any(w in q for w in ["don't feel safe","dont feel safe","not feel safe","not safe",
                             "feel unsafe","feel scared","feeling scared","anxious","nervous",
                             "worried","not comfortable","uncomfortable","feel weird",
                             "something feels wrong","feels wrong","bad feeling"]):
        return (
            f"💙 **I hear you, {user}. Your feelings are valid and I'm here.**\n\n"
            f"**What to do right now:**\n"
            f"1. Move to a busy, well-lit public place\n"
            f"2. Call someone you trust — {contact_names}\n"
            f"3. Stay on the phone with them while you move\n"
            f"4. If it gets worse, go to **SOS & SMS** tab and send an alert\n\n"
            f"📞 Women's Helpline: **1091** (free, 24/7)\n"
            f"🚨 Emergency: **112**\n\n"
            f"You are not alone. Trust your gut — it's almost always right. 🛡️"
        )

    # ── WANT TO GO OUT ────────────────────────────────────────────────────────
    if any(w in q for w in ["want to go out","going out","go out","step out",
                             "leave home","leaving home","heading out","going outside",
                             "walk outside","travel alone","go alone"]):
        tips = (
            "🌙 **It's late — extra precautions:**\n"
            "- Tell someone where you're going and your ETA\n"
            "- Prefer Ola/Uber over walking after 9 PM\n"
            "- Use the **Safe Route** tab to plan your route\n"
        ) if is_night else (
            "☀️ **Quick pre-outing checklist:**\n"
            "- Share your live location with a contact\n"
            "- Use **Safe Route** tab to plan your route\n"
            "- Check in when you arrive\n"
        )
        return (
            f"🗺️ **Before you head out, {user}:**\n\n"
            f"{tips}\n"
            f"**Useful pages:**\n"
            f"- 🛣️ **Safe Route** tab → Google Maps navigation home\n"
            f"- 🏥 **Nearby Help** tab → Hospitals & police near you\n"
            f"- ✅ Check in when you're back safe!\n\n"
            f"Your contacts ({contact_names}) are on standby. Stay safe! 💪"
        )

    # ── WHAT CAN YOU DO ──────────────────────────────────────────────────────
    if any(w in q for w in ["what can you do","features","what do you do","capabilities",
                             "how can you help","what do you know"]):
        return (
            f"🤖 **I'm your SheShield AI, {user}! Here's what I can help with:**\n\n"
            f"- 🚨 **Emergency guidance** — tell me you're in danger and I'll walk you through SOS\n"
            f"- 🗺️ **Route planning** — safe way to get home, night tips\n"
            f"- 🏥 **Find help** — nearest hospitals and police stations\n"
            f"- 🌙 **Night safety** — advice for travelling late\n"
            f"- ✅ **Check-in reminders** — confirm you're safe\n"
            f"- 🚦 **Road hazard reporting** — one-tap alerts\n"
            f"- 💬 **Talk to me** — I'm here 24/7, ask me anything about your safety\n\n"
            f"Your contacts ({contact_names}) are saved. Just say the word. 💪"
        )

    # ── CONTACTS ─────────────────────────────────────────────────────────────
    if any(w in q for w in ["contact", "who knows", "who will", "notify", "alert", "whatsapp"]):
        return (
            f"👥 **Your trusted contacts are: {contact_names}**\n\n"
            f"When you send SOS, they instantly receive:\n"
            f"- 📱 WhatsApp message with your GPS location\n"
            f"- 📧 Email with full details\n"
            f"- 📵 SMS (when Offline Mode is ON)\n\n"
            f"You can update contacts on the **👥 Trusted Contacts** page anytime."
        )

    # ── ROAD SAFETY ──────────────────────────────────────────────────────────
    if any(w in q for w in ["road", "accident", "traffic", "flooding", "waterlog", "hazard", "dark road"]):
        return (
            f"🚦 Go to the **🚦 Road Safety** page!\n\n"
            f"You can tap a single button to report:\n"
            f"- 🚗 Road Accident\n"
            f"- 🚧 Road Blocked\n"
            f"- 💡 No Street Light\n"
            f"- 🌊 Waterlogging\n"
            f"- 👁️ Suspicious Person\n\n"
            f"Each button instantly sends an SMS alert to your contacts with your location."
        )

    # ── HARASSMENT / STALKING ────────────────────────────────────────────────
    if any(w in q for w in ["harass", "stalk", "follow", "eve teas", "tease", "uncomfortable", "creep"]):
        return (
            f"⚠️ **I hear you, {user}. This is serious.**\n\n"
            f"**Right now:**\n"
            f"1. Move to a crowded, well-lit area immediately\n"
            f"2. Go to **Send SOS** and select *Harassment* or *Stalking*\n"
            f"3. Call **1091** (Women's Helpline) — they're trained for this\n"
            f"4. Call **100** (Police) if you feel in immediate danger\n\n"
            f"You are not overreacting. Trust your gut. Your contacts can be alerted in seconds. 🛡️"
        )

    # ── LOCATION / GPS ───────────────────────────────────────────────────────
    if any(w in q for w in ["location", "gps", "where am i", "my location", "coordinates"]):
        if home_lat:
            return (
                f"📍 **Your current location:** {loc_str}\n\n"
                f"- [Open in Google Maps](https://maps.google.com/?q={home_lat},{home_lon})\n"
                f"- Your location updates every 30 seconds automatically\n"
                f"- Go to **Safe Route Home** to navigate, or **Nearby Help** to find hospitals/police near you."
            )
        else:
            return (
                f"📍 I can't see your location yet, {user}.\n\n"
                f"Please allow location access in your browser:\n"
                f"1. Click the 🔒 lock icon in your browser address bar\n"
                f"2. Set **Location** to **Allow**\n"
                f"3. Refresh the page\n\n"
                f"Once enabled, I can give you nearby hospitals, police stations, and safe route guidance."
            )

    # ── TIPS / GENERAL SAFETY ────────────────────────────────────────────────
    if any(w in q for w in ["tip", "advice", "suggest", "what should i", "how to stay safe", "safety"]):
        return (
            f"🛡️ **Top safety tips for {user}:**\n\n"
            f"1. Always share your live location with a trusted contact when travelling\n"
            f"2. Check in every {st.session_state.checkin_interval} minutes — SheShield auto-alerts if you miss\n"
            f"3. Keep **112** on speed dial\n"
            f"4. Avoid isolated roads, especially after 9 PM\n"
            f"5. Use the **Safe Route Home** page before heading out at night\n"
            f"6. Enable **Offline SOS Mode** if you're going to an area with poor connectivity\n"
            f"7. Trust your instincts — if something feels wrong, act immediately\n\n"
            f"I'm here 24/7. Stay safe! 💪"
        )

    # ── CHECK-IN / TIMER ─────────────────────────────────────────────────────
    if any(w in q for w in ["check in", "checkin", "timer", "interval", "remind"]):
        return (
            f"⏱️ **Check-in system:**\n\n"
            f"- Current interval: every **{st.session_state.checkin_interval} minutes**\n"
            f"- At night (9PM–6AM): automatically switches to **15 minutes**\n"
            f"- If you miss a check-in, your contacts are auto-alerted\n\n"
            f"Hit **✅ Check In — I'm Safe** on the Home page to reset the timer anytime."
        )

    # ── DEFAULT — try to be helpful based on any context clues ─────────────
    hour_greeting = "Good morning" if 5<=hour<12 else ("Good afternoon" if 12<=hour<17 else ("Good evening" if 17<=hour<21 else "Stay safe tonight,"))
    distress_words = ["scared","afraid","worried","help","bad","wrong","strange","weird",
                      "uncomfortable","nervous","threat","alone","lost","stuck","trapped"]
    if any(w in q for w in distress_words):
        return (
            f"💙 I'm here with you, {user}.\n\n"
            f"It sounds like something might be off. Tell me more about what's happening — "
            f"the more specific you are, the better I can help.\n\n"
            f"If you feel in immediate danger, please go to the **SOS & SMS** tab right now. "
            f"Your contacts ({contact_names}) can be alerted in seconds.\n\n"
            f"📞 **112** for any emergency · **1091** Women's Helpline"
        )
    quoted = f"{q[:60]}..." if len(q) > 60 else q
    return (
        f"{hour_greeting} {user}! I'm your SheShield safety assistant.\n\n"
        f'I understood: *"{quoted}"*\n\n'
        f"I don't have a specific answer for that yet, but you can ask me directly:\n"
        f"- **\"I don't feel safe\"** — immediate safety steps\n"
        f"- **\"I want to go out\"** — pre-outing checklist\n"
        f"- **\"Route home\"** — safe navigation\n"
        f"- **\"Nearest hospital/police\"** — places near you\n"
        f"- **\"Activate SOS\"** — emergency alert steps"
    )


def call_claude_api(messages, system_prompt):
    """Try real Claude API first, fall back to smart offline AI."""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
        # Only attempt if key looks real
        if ANTHROPIC_KEY.startswith("sk-ant-api"):
            resp = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=500,
                system=system_prompt,
                messages=messages
            )
            return resp.content[0].text
        else:
            raise ValueError("Placeholder key")
    except Exception:
        # Fall through to smart offline AI
        return smart_ai(
            messages,
            home_lat=st.session_state.get("live_lat"),
            home_lon=st.session_state.get("live_lon"),
            is_night=is_night,
            contacts=st.session_state.get("trusted_contacts", [])
        )

def sos_countdown_and_send(name,location,emergency,desc,contacts,play_sound,demo_mode,offline_mode=False):
    placeholder=st.empty()
    cancelled=False
    for i in range(3,0,-1):
        with placeholder.container():
            st.markdown(f"""
            <div style="background:#E8196E18;border:2px solid #E8196E;border-radius:20px;
            padding:30px;text-align:center;margin:10px 0;">
              <div style="font-size:60px;font-weight:900;color:#E8196E;">{i}</div>
              <p style="font-size:16px;font-weight:600;color:#F2F4FF;">Sending {'OFFLINE ' if offline_mode else ''}SOS alert in {i} second{"s" if i>1 else ""}...</p>
              <p style="font-size:13px;color:#7A7E9A;">Press Cancel below to abort</p>
            </div>""",unsafe_allow_html=True)
            if st.button(f"Cancel SOS",key=f"cancel_{i}"):
                cancelled=True; break
        if cancelled: break
        time.sleep(1)

    placeholder.empty()
    if cancelled:
        st.info("SOS cancelled.")
        return

    timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if offline_mode:
        # OFFLINE: Use SMS only
        sms_sent = send_offline_sms(name, location, emergency, contacts)
        email_ok = False
        wa_sent = 0
        st.warning(f"📵 OFFLINE MODE: SMS triggered for {sms_sent} contact(s) via your phone's SMS app.")
    elif not demo_mode:
        email_ok=send_email(name,location,emergency,desc,timestamp)
        wa_sent=send_whatsapp(name,location,emergency,contacts)
        sos_sms_body = (
            f"SOS ALERT! {name} needs help! Emergency: {emergency}. "
            f"Location: https://maps.google.com/?q={location} Time: {timestamp}"
        )
        sms_sent = send_sms_twilio(sos_sms_body, get_location_recipient_phones())
        if not email_ok and not all([ALERT_EMAIL, SENDER_EMAIL, SENDER_APP_PWD]):
            st.info("Email alerts are not configured. Set SHESHIELD_ALERT_EMAIL and related variables (see .env.example).")
        if wa_sent == 0 and not TWILIO_SID:
            st.info("WhatsApp alerts need Twilio credentials (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN).")
        if sms_sent == 0 and not TWILIO_SMS_FROM:
            st.info("For automatic SMS to phones, set TWILIO_SMS_FROM (Twilio phone number). Offline SOS still opens the SMS app.")
    else:
        email_ok=True; wa_sent=len([c for c in contacts if c.get("phone")]); sms_sent=0

    alert={"Name":name,"Location":location,"Emergency Type":emergency,
           "Description":desc,"Timestamp":timestamp}
    st.session_state.alerts_df=pd.concat(
        [st.session_state.alerts_df,pd.DataFrame([alert])],ignore_index=True)
    st.session_state.alerts_df.to_csv("alerts.csv",index=False)
    st.session_state.sos_count+=1

    st.error("🚨 SOS ALERT SENT!")
    if email_ok: st.success(f"✅ Email sent to {ALERT_EMAIL}" if ALERT_EMAIL else "✅ Email sent")
    if wa_sent:  st.success(f"✅ WhatsApp sent to {wa_sent} contact(s)")
    if sms_sent: st.success(f"✅ SMS app opened for {sms_sent} contact(s)")

    contact_html="".join([
        f'<p style="color:#F2F4FF;">{c["name"]} — {c["phone"]}</p>'
        for c in contacts if c.get("name") and c.get("phone")])
    st.markdown(f"""
    <div style="background:#E8196E15;border:1px solid #E8196E40;border-radius:16px;padding:16px;">
      <p style="font-weight:700;color:#E8196E;margin-bottom:8px;">Notified:</p>
      {contact_html or '<p style="color:#7A7E9A;">No contacts saved</p>'}
      <p style="color:#C8CCE8;">{ALERT_EMAIL}</p>
    </div>""",unsafe_allow_html=True)
    if play_sound:
        st.audio("https://actions.google.com/sounds/v1/alarms/alarm_clock.ogg",autoplay=True)

# ══════════════════════════════════════════════════════════════════════════════
#  SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════
DEFAULT_CONTACTS=[
    {"initials":"C1","name":"","relation":"Family or friend","phone":""},
    {"initials":"C2","name":"","relation":"Family or friend","phone":""},
    {"initials":"C3","name":"","relation":"Family or friend","phone":""},
    {"initials":"C4","name":"","relation":"Family or friend","phone":""},
]

if "alerts_df" not in st.session_state:
    st.session_state.alerts_df = pd.read_csv("alerts.csv") if os.path.exists("alerts.csv") else pd.DataFrame(
        columns=["Name","Location","Emergency Type","Description","Timestamp"])

DEFAULTS={
    "onboarded":False,"user_name":"","user_phone":"",
    "ai_history":[],"live_lat":None,"live_lon":None,
    "trusted_contacts":DEFAULT_CONTACTS,"nearby_police":[],"nearby_hospitals":[],
    "nearby_fetched_for":None,"last_checkin":datetime.now(),"checkin_interval":30,
    "sos_count":0,"total_checkins":0,"demo_mode":False,
    "unsafe_zones":[],"zones_fetched_for":None,
    # NEW: Home location & safe route
    "home_lat":None,"home_lon":None,"home_address":"",
    "offline_mode":False,
    "road_safety_alerts":[],
    "live_accuracy":None,
    "live_location_updated":None,
    "live_share_enabled":False,
    "live_share_interval_min":5,
    "last_live_share_sent":None,
    "monitor_phone":"",
    "share_to_my_phone":True,
    "safe_route_sharing":False,
}
for k,v in DEFAULTS.items():
    if k not in st.session_state: st.session_state[k]=v

df=st.session_state.alerts_df
is_night=(datetime.now().hour>=21 or datetime.now().hour<6)
if is_night: st.session_state.checkin_interval=15

# ══════════════════════════════════════════════════════════════════════════════
#  ONBOARDING
# ══════════════════════════════════════════════════════════════════════════════
if not st.session_state.onboarded:
    st.markdown("""
    <div style="max-width:480px;margin:60px auto;text-align:center;">
      <div style="width:72px;height:72px;background:#E8196E;border-radius:20px;
      display:flex;align-items:center;justify-content:center;font-size:36px;
      margin:0 auto 20px;box-shadow:0 12px 32px rgba(232,25,110,0.35);">🛡️</div>
      <h1 style="font-family:'DM Serif Display',serif;font-size:36px;margin-bottom:8px;color:#F2F4FF;">Welcome to SheShield</h1>
      <p style="color:#7A7E9A;margin-bottom:32px;font-size:16px;">Your personal safety companion — SOS, check-ins, and trusted contacts in one place.</p>
    </div>""",unsafe_allow_html=True)

    col1,col2,col3=st.columns([1,2,1])
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### Step 1 — Your details")
        uname  = st.text_input("Your name", placeholder="Enter your full name")
        uphone = st.text_input("Your phone number", placeholder="10-digit mobile number")
        st.markdown("#### Step 2 — Save your home location (optional)")
        home_addr = st.text_input("Home address", placeholder="e.g. Koramangala 4th Block, Bengaluru")
        st.markdown("<p style='font-size:12px;color:#7A7E9A;'>Used for safe route home feature.</p>", unsafe_allow_html=True)
        st.markdown("#### Step 3 — Allow location")
        st.markdown("<p style='font-size:12px;color:#7A7E9A;'>Click Allow when your browser asks.</p>", unsafe_allow_html=True)
        if st.button("🛡️ Enter SheShield", use_container_width=True):
            if not uname.strip():
                st.error("Please enter your name.")
            elif not uphone.strip() or not uphone.strip().isdigit() or len(uphone.strip()) != 10:
                st.error("Please enter a valid 10-digit phone number.")
            else:
                st.session_state.onboarded = True
                st.session_state.user_name = uname.strip()
                st.session_state.user_phone = uphone.strip()
                if home_addr.strip():
                    with st.spinner("Saving home location…"):
                        hlat, hlon, _ = geocode_address(home_addr.strip())
                    if hlat:
                        st.session_state.home_lat = hlat
                        st.session_state.home_lon = hlon
                        st.session_state.home_address = home_addr.strip()
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
#  TOP HEADER + HORIZONTAL TAB NAVIGATION  (replaces sidebar)
# ══════════════════════════════════════════════════════════════════════════════
shield_color="#22c55e" if not is_night else "#7B61FF"
shield_label="Protected" if not is_night else "Night Shield 🌙"

# ── Top header bar ──────────────────────────────────────────────────────────
st.markdown(f"""
<div class="ss-header">
  <div style="display:flex;align-items:center;gap:10px;">
    <div style="width:36px;height:36px;background:#E8196E;border-radius:10px;
    display:flex;align-items:center;justify-content:center;font-size:18px;">🛡️</div>
    <div>
      <div style="display:flex;align-items:center;gap:8px;">
        <span class="ss-logo-name">SheShield</span>
        <span style="font-size:10px;color:#7A7E9A;letter-spacing:2px;text-transform:uppercase;
        border:1px solid rgba(255,255,255,0.1);border-radius:20px;padding:2px 8px;">LIVE</span>
      </div>
      <div style="font-size:11px;color:#7A7E9A;">Personal safety companion · {current_user()}</div>
    </div>
  </div>
  <div style="display:flex;align-items:center;gap:12px;">
    <div class="ss-badge">
      <span class="ss-badge-dot" style="background:{shield_color};"></span>
      <span style="color:#C8CCE8;">{shield_label}</span>
    </div>
    <span style="font-size:12px;color:#7A7E9A;">{datetime.now().strftime("%d %b · %I:%M %p")}</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Demo + Offline toggles as inline controls ────────────────────────────────
ctrl1, ctrl2, ctrl3 = st.columns([1,1,4])
with ctrl1:
    demo = st.toggle("🎭 Demo", value=st.session_state.demo_mode)
    st.session_state.demo_mode = demo
with ctrl2:
    offline_toggle = st.toggle("📵 Offline SOS", value=st.session_state.offline_mode)
    st.session_state.offline_mode = offline_toggle

if demo:
    st.markdown('<div style="background:#FFB02015;border:1px solid #FFB02040;border-radius:10px;padding:6px 14px;font-size:12px;color:#FFB020;margin-bottom:4px;">🎭 Demo mode ON — safe to present!</div>', unsafe_allow_html=True)
if offline_toggle:
    st.markdown('<div style="background:#E8196E15;border:1px solid #E8196E40;border-radius:10px;padding:6px 14px;font-size:12px;color:#E8196E;margin-bottom:4px;">📵 Offline SOS ON — SMS only, no internet needed</div>', unsafe_allow_html=True)

# ── Horizontal tab nav — WORKING st.button tabs ─────────────────────────────
TABS = [
    ("🏠", "Home"),
    ("🚨", "SOS & SMS"),
    ("🤖", "Safety Assistant"),
    ("🛣️", "Safe Route"),
    ("🏥", "Nearby Help"),
    ("🚦", "Road Safety"),
    ("📊", "Insights"),
    ("📋", "Alerts"),
    ("👥", "Contacts"),
]

if "page" not in st.session_state:
    st.session_state.page = "Home"
# Migrate legacy tab label from older versions
if st.session_state.page in ("Home / Check", "Shristi's AI", "Analytics"):
    _legacy = {"Home / Check": "Home", "Shristi's AI": "Safety Assistant", "Analytics": "Insights"}
    st.session_state.page = _legacy[st.session_state.page]

# Add extra button CSS so active tab looks highlighted
st.markdown("""
<style>
div[data-testid="stHorizontalBlock"] button {
    background:#1A1D2E !important;
    color:#C8CCE8 !important;
    border:1px solid rgba(255,255,255,0.1) !important;
    border-radius:10px !important;
    font-size:12px !important;
    padding:6px 10px !important;
    font-weight:500 !important;
    box-shadow:none !important;
    transition:all 0.15s !important;
}
div[data-testid="stHorizontalBlock"] button:hover {
    background:#E8196E22 !important;
    color:#E8196E !important;
    border-color:#E8196E44 !important;
}
</style>
""", unsafe_allow_html=True)

tab_cols = st.columns(len(TABS))
for i, (icon, label) in enumerate(TABS):
    with tab_cols[i]:
        is_active = st.session_state.page == label
        btn_label = f"{icon} {label}"
        if is_active:
            # Show active tab highlighted
            st.markdown(f"""<div style="background:#E8196E;border-radius:10px;padding:7px 4px;
            text-align:center;font-size:12px;font-weight:600;color:white;
            box-shadow:0 4px 12px rgba(232,25,110,0.4);cursor:default;">
            {icon} {label}</div>""", unsafe_allow_html=True)
        else:
            if st.button(btn_label, key=f"tab_{label}", use_container_width=True):
                st.session_state.page = label
                st.rerun()

page = st.session_state.page

# ── Quick dial chips ──────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-bottom:12px;">
  <a class="dial-chip" href="tel:112">🚨 112</a>
  <a class="dial-chip" href="tel:100">🚓 100</a>
  <a class="dial-chip" href="tel:108">🚑 108</a>
  <a class="dial-chip" href="tel:1091">👩 1091</a>
  <a class="dial-chip" href="tel:101">🔥 101</a>
</div>
""", unsafe_allow_html=True)

if is_night:
    st.markdown("""
    <div class="night-banner">
      <span style="font-size:20px;">🌙</span>
      <div>
        <span style="font-weight:700;color:#c4b5fd;">Night Shield Active</span>
        <span style="font-size:12px;color:rgba(255,255,255,0.6);margin-left:8px;">Check-ins every 15 min · Contacts on standby</span>
      </div>
    </div>""",unsafe_allow_html=True)

# Shake + Voice detection JS
components.html("""
<script>
var lastShake=0,shakeThreshold=15;
if(window.DeviceMotionEvent){
  window.addEventListener('devicemotion',function(e){
    var a=e.accelerationIncludingGravity;
    if(!a)return;
    var total=Math.abs(a.x)+Math.abs(a.y)+Math.abs(a.z);
    var now=Date.now();
    if(total>shakeThreshold&&now-lastShake>3000){
      lastShake=now;
      alert('Shake detected! Go to Send SOS immediately.');
    }
  });
}
var recognition=null;
function startVoice(){
  if(!('webkitSpeechRecognition' in window||'SpeechRecognition' in window)){return;}
  var SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  recognition=new SR();
  recognition.continuous=true; recognition.interimResults=false; recognition.lang='en-IN';
  recognition.onresult=function(e){
    var t=e.results[e.results.length-1][0].transcript.toLowerCase();
    if(t.includes('help')||t.includes('sos')||t.includes('emergency')){
      alert('Voice trigger detected: "'+t+'". Activate SOS now!');
    }
  };
  recognition.onerror=function(){};
  try{recognition.start();}catch(ex){}
}
setTimeout(startVoice,1000);
</script>
""",height=0)

# ══════════════════════════════════════════════════════════════════════════════
#  LIVE LOCATION — refresh on load + periodic poll
# ══════════════════════════════════════════════════════════════════════════════
refresh_live_location(component_key="gps_init")
maybe_auto_share_location()

if hasattr(st, "fragment"):
    @st.fragment(run_every=20)
    def _gps_poll_fragment():
        refresh_live_location(component_key="gps_poll")
        maybe_auto_share_location()
    _gps_poll_fragment()

home_lat = st.session_state.live_lat
home_lon = st.session_state.live_lon

total_sos   = len(df) + st.session_state.sos_count
total_checkins = st.session_state.total_checkins
safety_score = max(0, min(100, 100 - (total_sos*15) + (total_checkins*3)))
seconds_since = (datetime.now()-st.session_state.last_checkin).total_seconds()
interval_sec  = st.session_state.checkin_interval*60
seconds_left  = max(0, interval_sec-seconds_since)
mins_left     = int(seconds_left//60)
secs_left     = int(seconds_left%60)
checkin_pct   = int((1-(seconds_left/interval_sec))*100) if interval_sec>0 else 100

if demo:
    if len(df)==0:
        demo_alerts=pd.DataFrame([
            {"Name":current_user(),"Location":"12.934567, 77.624500","Emergency Type":"Unsafe Area",
             "Description":"Felt followed near underpass","Timestamp":"2024-01-15 21:32:00"},
            {"Name":current_user(),"Location":"Koramangala 5th Block","Emergency Type":"Harassment",
             "Description":"Reported harassment incident","Timestamp":"2024-01-18 20:10:00"},
            {"Name":"Trusted contact","Location":"HSR Layout Sector 3","Emergency Type":"Stalking",
             "Description":"Unknown person following","Timestamp":"2024-01-20 22:45:00"},
            {"Name":current_user(),"Location":"Silk Board Junction","Emergency Type":"Unsafe Area",
             "Description":"Poorly lit, isolated","Timestamp":"2024-01-22 23:10:00"},
        ])
        st.session_state.alerts_df=demo_alerts
        df=demo_alerts
    total_sos=len(df); total_checkins=47; safety_score=78

# ══════════════════════════════════════════════════════════════════════════════
#  HOME
# ══════════════════════════════════════════════════════════════════════════════
if page=="Home":
    st.markdown("""
    <div class="page-title">
      <div class="section-label">Overview</div>
      <h1>Home &amp; Check-in</h1>
      <p>Status, check-in timer, trusted contacts, and nearby risk indicators</p>
    </div>""", unsafe_allow_html=True)

    c1,c2,c3,c4=st.columns(4)
    active_contacts=sum(1 for c in st.session_state.trusted_contacts if c.get("phone"))
    c1.metric("SOS Alerts",total_sos)
    c2.metric("Safety Score",f"{safety_score}/100")
    c3.metric("Contacts",active_contacts)
    c4.metric("Check-ins",total_checkins)
    st.markdown("<br>",unsafe_allow_html=True)

    render_live_location_panel()

    st.markdown("<br>",unsafe_allow_html=True)
    rc1, rc2 = st.columns(2)
    with rc1:
        if st.button("🛣️ Safe Route Home", use_container_width=True):
            st.session_state.page = "Safe Route"
            st.rerun()
    with rc2:
        if st.button("📲 Share location to contacts", use_container_width=True, key="home_share_loc"):
            sent, mode = broadcast_live_location("Shared from Home")
            if mode == "no_gps":
                st.error("Enable GPS first (Refresh GPS above).")
            elif mode == "no_phones":
                st.error("Add trusted contacts on the Contacts tab.")
            elif mode == "twilio":
                st.success(f"SMS sent to {sent} number(s).")
            else:
                st.info(f"Tap each button below and press Send ({sent} number(s)).")
                render_sms_tap_links(
                    st.session_state.get("pending_sms_body", ""),
                    st.session_state.get("pending_sms_phones", []),
                )

    bar_color="#22c55e" if checkin_pct<70 else ("#FFB020" if checkin_pct<90 else "#E8196E")
    st.markdown(f"""
    <div class="countdown-bar">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
        <span style="font-weight:600;font-size:14px;color:#F2F4FF;">⏱️ Next Check-in</span>
        <span style="font-size:20px;font-weight:700;color:{bar_color};">{mins_left:02d}:{secs_left:02d}</span>
      </div>
      <div style="background:#E8196E18;border-radius:8px;height:8px;">
        <div style="background:{bar_color};height:8px;border-radius:8px;width:{checkin_pct}%;
        transition:width 1s ease;"></div>
      </div>
      <p style="font-size:12px;color:#7A7E9A;margin-top:6px;">
        {"⚠️ Overdue! Check in now." if seconds_left==0 else f"Auto-alert fires if you miss this · Every {st.session_state.checkin_interval} min"}
      </p>
    </div>""",unsafe_allow_html=True)

    col_left,col_right=st.columns([1,1])
    with col_left:
        st.markdown("""
        <div class="sos-box">
          <p style="font-size:13px;letter-spacing:3px;text-transform:uppercase;color:#E8196E;
          font-weight:600;margin-bottom:12px;">Emergency</p>
          <div style="font-size:72px;margin-bottom:8px;">🚨</div>
          <h2 style="font-size:32px!important;margin-bottom:8px;">SOS Emergency</h2>
          <p style="color:#7A7E9A;font-size:14px;">Press below to send an emergency alert instantly.</p>
        </div>""",unsafe_allow_html=True)
        if st.button("🚨 ACTIVATE SOS NOW",use_container_width=True):
            st.warning("🚨 SOS Activated! Go to **Send SOS** to complete.")
        st.markdown("<br>",unsafe_allow_html=True)
        if st.button("✅ Check In — I'm Safe",use_container_width=True):
            st.session_state.last_checkin=datetime.now()
            st.session_state.total_checkins+=1
            st.success(f"✅ Check-in confirmed, {current_user()}! Timer reset.")
            st.rerun()

        # Home location quick display
        if st.session_state.home_lat:
            st.markdown(f"""
            <div class="card" style="padding:12px 16px;margin-top:8px;">
              <p style="font-weight:600;font-size:13px;margin-bottom:4px;">🏠 Home Location Saved</p>
              <p style="font-size:12px;color:#7A7E9A;">{st.session_state.home_address or f"{st.session_state.home_lat:.4f}, {st.session_state.home_lon:.4f}"}</p>
              <a href="https://maps.google.com/?q={st.session_state.home_lat},{st.session_state.home_lon}" target="_blank"
              style="font-size:12px;color:#E8196E;">🗺️ View on Maps</a>
            </div>""",unsafe_allow_html=True)

        st.markdown('<div class="card"><p style="font-weight:700;font-size:15px;margin-bottom:12px;">👥 Trusted Contacts</p>',unsafe_allow_html=True)
        shown=[c for c in st.session_state.trusted_contacts if c.get("name") and c.get("phone")]
        if shown:
            for c in shown:
                init=(c["name"][:2]).upper()
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:12px;padding:8px 0;
                border-bottom:1px solid rgba(255,255,255,0.06);">
                  <div style="width:36px;height:36px;border-radius:50%;background:#E8196E22;
                  display:flex;align-items:center;justify-content:center;
                  font-weight:700;color:#E8196E;font-size:12px;">{init}</div>
                  <div style="flex:1;">
                    <div style="font-weight:600;font-size:13px;">{c['name']}</div>
                    <div style="font-size:11px;color:#7A7E9A;">{c['relation']}</div>
                  </div>
                  <a href="tel:{c['phone']}" style="font-size:12px;color:#E8196E;">📞 Call</a>
                </div>""",unsafe_allow_html=True)
        else:
            st.markdown('<p style="color:#7A7E9A;font-size:13px;">No contacts saved. Go to Trusted Contacts.</p>',unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="card"><p style="font-weight:700;font-size:15px;margin-bottom:12px;">🛡️ Unsafe Area Predictions Near You</p>',unsafe_allow_html=True)
        if home_lat and home_lon:
            cache_key=f"{home_lat:.3f},{home_lon:.3f}"
            if st.session_state.zones_fetched_for!=cache_key:
                with st.spinner("Scanning nearby areas…"):
                    st.session_state.unsafe_zones=get_unsafe_zones(home_lat,home_lon)
                    st.session_state.zones_fetched_for=cache_key
            for zname,risk,dist,reason,*_ in st.session_state.unsafe_zones[:4]:
                badge="badge-high" if risk=="High" else ("badge-medium" if risk=="Medium" else "badge-low")
                st.markdown(f"""
                <div style="border-bottom:1px solid rgba(255,255,255,0.06);padding:10px 0;">
                  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
                    <span style="font-weight:600;font-size:13px;">{zname[:38]}</span>
                    <span class="{badge}">{risk}</span>
                  </div>
                  <span style="font-size:12px;color:#7A7E9A;">{dist} · {reason}</span>
                </div>""",unsafe_allow_html=True)
        else:
            st.markdown('<p style="color:#7A7E9A;font-size:13px;">📍 Allow location access to see predictions.</p>',unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

        st.markdown('<div class="card"><p style="font-weight:700;font-size:15px;margin-bottom:12px;">📞 Emergency Helplines</p>',unsafe_allow_html=True)
        for label,num in [("🚨 National Emergency","112"),("🚓 Police","100"),
                           ("🚑 Ambulance","108"),("👩 Women Helpline","1091"),
                           ("🔥 Fire","101"),("👶 Child Helpline","1098")]:
            st.markdown(f'<a class="helpline-link" href="tel:{num}">{label}: {num}</a>',unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

        if home_lat and home_lon:
            st.markdown(f"""
            <div class="card" style="padding:12px 16px;">
              <p style="font-weight:600;font-size:13px;margin-bottom:6px;color:#F2F4FF;">📍 Your Live Location</p>
              <p style="font-size:12px;color:#7A7E9A;margin-bottom:8px;">{home_lat:.5f}, {home_lon:.5f}</p>
              <a href="https://maps.google.com/?q={home_lat},{home_lon}" target="_blank"
              style="font-size:12px;color:#E8196E;font-weight:600;">🗺️ Open in Google Maps</a>
            </div>""",unsafe_allow_html=True)

    st.markdown("<br>",unsafe_allow_html=True)
    st.markdown('<div class="section-label" style="text-align:center;">Live status preview</div>',unsafe_allow_html=True)
    sim_col1, sim_col2, sim_col3 = st.columns([1,1,1])
    with sim_col2:
        sos_screen_color = "#E8196E" if total_sos > 0 else "#22c55e"
        sos_screen_label = "Alert active" if total_sos > 0 else "Protected"
        if home_lat and home_lon:
            loc_line = f"{home_lat:.4f}, {home_lon:.4f}"
        else:
            loc_line = "Enable location for live GPS"
        st.markdown(f"""
        <div class="phone-mock">
          <div style="display:flex;justify-content:space-between;align-items:center;
          margin-bottom:8px;padding:0 4px;">
            <span style="color:white;font-size:11px;font-weight:600;">{datetime.now().strftime('%I:%M')}</span>
            <span style="background:#22c55e;color:white;font-size:10px;font-weight:700;
            border-radius:10px;padding:2px 8px;">{sos_screen_label}</span>
          </div>
          <div class="phone-screen" style="background:{sos_screen_color};">
            <div style="font-size:36px;margin-bottom:10px;">🛡️</div>
            <div style="font-weight:700;font-size:14px;letter-spacing:1px;">SheShield</div>
            <div style="font-size:11px;opacity:0.8;margin:6px 0;">Monitoring active</div>
            <div style="font-size:10px;opacity:0.7;margin-top:8px;line-height:1.6;">
              {loc_line}<br>
              Check-in every {st.session_state.checkin_interval} min<br>
              Contacts: {sum(1 for c in st.session_state.trusted_contacts if c.get("phone"))} saved
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  SEND SOS
# ══════════════════════════════════════════════════════════════════════════════
elif page=="SOS & SMS":
    st.markdown("""
    <div class="page-title">
      <div class="section-label">Emergency</div>
      <h1>SOS &amp; Emergency Alerts</h1>
      <p>Send your location and situation to trusted contacts by email, WhatsApp, or SMS</p>
    </div>""", unsafe_allow_html=True)

    # Offline mode banner
    if st.session_state.offline_mode:
        st.markdown("""
        <div style="background:#FFB02018;border:1.5px solid #ffd980;border-radius:14px;
        padding:12px 18px;margin-bottom:16px;display:flex;align-items:center;gap:10px;">
          <span style="font-size:20px;">📵</span>
          <div>
            <span style="font-weight:700;color:#b06800;">Offline SOS Mode Active</span>
            <span style="font-size:12px;color:#7A7E9A;margin-left:8px;">
              Will send SMS via your phone's native app — no internet needed
            </span>
          </div>
        </div>""",unsafe_allow_html=True)

    col_form,col_info=st.columns([3,2])
    with col_form:
        st.markdown('<div class="card">',unsafe_allow_html=True)
        name=st.text_input("Your Name",value=current_user())
        emergency=st.selectbox("Emergency Type",["Unsafe Area","Harassment","Medical Emergency","Kidnapping Risk","Stalking","Road Accident","Other"])
        loc_opt=st.radio("Location",["📍 Use Live Location","✍️ Enter Manually"],horizontal=True)

        latitude,longitude,location=None,None,"Location not found"
        if loc_opt=="📍 Use Live Location":
            if home_lat and home_lon:
                latitude,longitude=home_lat,home_lon
                location=f"{latitude:.6f}, {longitude:.6f}"
                acc = st.session_state.get("live_accuracy") or 0
                st.success(f"📍 Live GPS: **{location}**  (±{acc:.0f} m)")
                st.map(pd.DataFrame({"lat":[latitude],"lon":[longitude]}),zoom=15)
                st.markdown(f'<a href="https://maps.google.com/?q={latitude},{longitude}" target="_blank" style="color:#E8196E;font-size:13px;">🗺️ Open in Google Maps</a>',unsafe_allow_html=True)
            else:
                st.warning("⚠️ Location not acquired yet. Allow browser GPS access or enter manually.")
        else:
            manual=st.text_input("Enter location",placeholder="e.g. Koramangala 5th Block, Bengaluru")
            if manual:
                with st.spinner("Geocoding…"):
                    glat,glon,dname=geocode_address(manual)
                if glat:
                    latitude,longitude,location=glat,glon,manual
                    st.success(f"📍 {dname[:70]}")
                    st.map(pd.DataFrame({"lat":[glat],"lon":[glon]}),zoom=14)
                else:
                    location=manual
                    st.warning("Couldn't geocode, using as text.")

        desc=st.text_area("Brief Description (optional)",placeholder="Describe the situation…",height=80)
        sc,tc=st.columns([3,1])
        with sc: send_clicked=st.button("🚨 SEND EMERGENCY ALERT",use_container_width=True)
        with tc: play_sound=st.toggle("🔊 Sound",value=True)

        if send_clicked:
            if not name or not location or location=="Location not found":
                st.error("Please provide your name and location.")
            else:
                contacts=[c for c in st.session_state.trusted_contacts if c.get("name") and c.get("phone")]
                sos_countdown_and_send(
                    name, location, emergency, desc, contacts,
                    play_sound, demo,
                    offline_mode=st.session_state.offline_mode
                )
        st.markdown("</div>",unsafe_allow_html=True)

    with col_info:
        st.markdown("""
        <div class="card">
          <p style="font-weight:700;margin-bottom:12px;">⚡ What happens when you send SOS?</p>
          <div style="display:flex;gap:10px;margin-bottom:10px;"><span style="color:#E8196E;font-weight:700;">1</span><span style="color:#C8CCE8;font-size:13px;">3-second countdown — cancel if accidental</span></div>
          <div style="display:flex;gap:10px;margin-bottom:10px;"><span style="color:#E8196E;font-weight:700;">2</span><span style="color:#C8CCE8;font-size:13px;">Email alert sent to your configured alert address</span></div>
          <div style="display:flex;gap:10px;margin-bottom:10px;"><span style="color:#E8196E;font-weight:700;">3</span><span style="color:#C8CCE8;font-size:13px;">WhatsApp message to all saved contacts</span></div>
          <div style="display:flex;gap:10px;margin-bottom:10px;"><span style="color:#E8196E;font-weight:700;">4</span><span style="color:#C8CCE8;font-size:13px;">SOS alarm sounds to deter attacker</span></div>
          <div style="display:flex;gap:10px;"><span style="color:#E8196E;font-weight:700;">5</span><span style="color:#C8CCE8;font-size:13px;">Alert logged with timestamp for evidence</span></div>
        </div>
        <div class="card" style="background:#FF6B2E15;border-color:#FF6B2E44;">
          <p style="font-weight:700;margin-bottom:8px;color:#FF6B2E;">📵 Offline SOS</p>
          <p style="font-size:13px;color:#C8CCE8;">Toggle <b>Offline SOS</b> at the top of the app. When ON, SOS opens your phone's native SMS app — works with <b>no internet</b>.</p>
        </div>
        <div class="card">
          <p style="font-weight:700;margin-bottom:8px;">🎤 Voice & Shake SOS</p>
          <p style="font-size:13px;color:#7A7E9A;">Say <b style="color:#F2F4FF;">"help"</b> or <b style="color:#F2F4FF;">"SOS"</b> aloud, or <b style="color:#F2F4FF;">shake your phone</b> to trigger an instant alert prompt.</p>
        </div>
        <div class="card">
          <p style="font-weight:700;margin-bottom:12px;">🚨 Quick Call</p>
          <a class="helpline-link" href="tel:112">🚨 National: 112</a>
          <a class="helpline-link" href="tel:100">🚓 Police: 100</a>
          <a class="helpline-link" href="tel:1091">👩 Women: 1091</a>
          <a class="helpline-link" href="tel:108">🚑 Ambulance: 108</a>
        </div>""",unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  VIEW ALERTS
# ══════════════════════════════════════════════════════════════════════════════
elif page=="Alerts":
    st.markdown("""<div class="page-title"><div class="section-label">History</div><h1>Emergency Alerts</h1><p>All logged SOS and hazard reports</p></div>""", unsafe_allow_html=True)
    if not df.empty:
        t=len(df); h=len(df[df["Emergency Type"]=="Harassment"])
        m=len(df[df["Emergency Type"]=="Medical Emergency"]); u=len(df[df["Emergency Type"]=="Unsafe Area"])
        c1,c2,c3,c4=st.columns(4)
        c1.metric("🚨 Total",t); c2.metric("😡 Harassment",h)
        c3.metric("🏥 Medical",m); c4.metric("⚠️ Other",t-h-m-u+u)
        st.download_button("📥 Download Report (CSV)",df.to_csv(index=False).encode(),
            "sheshield_alerts.csv","text/csv",use_container_width=True)
        st.markdown("---")
        COLOR_MAP={"Harassment":"#ff000015","Medical Emergency":"#FFB02015",
            "Unsafe Area":"#E8196E15","Kidnapping Risk":"#ff000025","Stalking":"#7B61FF15","Other":"#22c55e15"}
        tbl="""<table style="width:100%;border-collapse:collapse;font-family:'Inter',sans-serif;font-size:13px;">
        <thead><tr style="background:#E8196E;color:white;">
          <th style="padding:12px 16px;text-align:left;">#</th>
          <th style="padding:12px 16px;text-align:left;">Name</th>
          <th style="padding:12px 16px;text-align:left;">Location</th>
          <th style="padding:12px 16px;text-align:left;">Emergency Type</th>
          <th style="padding:12px 16px;text-align:left;">Timestamp</th>
        </tr></thead><tbody>"""
        for i,row in df.iterrows():
            bg=COLOR_MAP.get(row.get("Emergency Type",""),"#0F112033")
            tbl+=f"""<tr style="background:{bg};border-bottom:1px solid rgba(255,255,255,0.06);">
              <td style="padding:10px 16px;color:#C8CCE8;">{i+1}</td>
              <td style="padding:10px 16px;color:#F2F4FF;font-weight:600;">{row.get('Name','')}</td>
              <td style="padding:10px 16px;color:#C8CCE8;">{str(row.get('Location',''))[:35]}</td>
              <td style="padding:10px 16px;color:#E8196E;font-weight:600;">{row.get('Emergency Type','')}</td>
              <td style="padding:10px 16px;color:#7A7E9A;">{row.get('Timestamp','N/A')}</td>
            </tr>"""
        tbl+="</tbody></table>"
        components.html(tbl,height=min(120+len(df)*48,620),scrolling=True)
    else:
        st.markdown("""<div class="card" style="text-align:center;padding:40px;">
          <div style="font-size:48px;margin-bottom:12px;">✅</div>
          <p style="font-weight:600;font-size:18px;">No alerts logged yet</p>
          <p style="color:#7A7E9A;">All clear!</p>
        </div>""",unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  ANALYTICS
# ══════════════════════════════════════════════════════════════════════════════
elif page=="Insights":
    st.markdown("""<div class="page-title"><div class="section-label">Insights</div><h1>Safety Insights</h1><p>Activity and risk patterns</p></div>""", unsafe_allow_html=True)
    c1,c2,c3=st.columns(3)
    c1.metric("🚨 SOS Sent",total_sos,"This month")
    c2.metric("✅ Check-ins",total_checkins,"This month")
    c3.metric("🛡️ Safety Score",f"{safety_score}/100")

    PLOT=dict(plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#C8CCE8",family="Inter"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
        margin=dict(l=10,r=10,t=40,b=10))

    ca,cb=st.columns(2)
    with ca:
        days=["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
        ci=[4,6,5,3,7,4,total_checkins%7+1]; sos_d=[0,1,0,2,0,1,total_sos%3]
        fig=go.Figure()
        fig.add_bar(x=days,y=ci,name="Check-ins",marker_color="#22c55e",opacity=0.75)
        fig.add_bar(x=days,y=sos_d,name="SOS",marker_color="#E8196E")
        fig.update_layout(title="SOS & Check-in Activity",barmode="group",**PLOT)
        st.plotly_chart(fig,use_container_width=True)
    with cb:
        hrs=pd.DataFrame({"Time":["12am","3am","6am","9am","12pm","3pm","6pm","9pm"],"Risk":[72,88,30,15,12,18,35,61]})
        fig2=go.Figure(); fig2.add_scatter(x=hrs["Time"],y=hrs["Risk"],mode="lines",fill="tozeroy",
            line=dict(color="#E8196E",width=2),fillcolor="rgba(232,25,110,0.15)")
        fig2.update_layout(title="Risk by Hour of Day",**PLOT,yaxis_range=[0,100])
        st.plotly_chart(fig2,use_container_width=True)

    cc,cd=st.columns(2)
    with cc:
        wks=["W1","W2","W3","W4","W5"]; sc=[74,81,68,85,safety_score]
        fig3=go.Figure(); fig3.add_scatter(x=wks,y=sc,mode="lines+markers",
            line=dict(color="#a78bfa",width=2.5),marker=dict(color="#a78bfa",size=8))
        fig3.update_layout(title="Safety Score Trend",**PLOT,yaxis_range=[50,100])
        st.plotly_chart(fig3,use_container_width=True)
    with cd:
        if not df.empty:
            tc2=df["Emergency Type"].value_counts()
            fig4=go.Figure(go.Pie(labels=tc2.index,values=tc2.values,hole=0.55,
                marker_colors=["#E8196E","#FF6B9D","#7B61FF","#FFB020","#22c55e","#00C9A7"]))
        else:
            fig4=go.Figure(go.Pie(labels=["No Data"],values=[1],hole=0.55,marker_colors=["#1A1D2E"]))
        fig4.update_layout(title="Alerts by Type",**PLOT)
        st.plotly_chart(fig4,use_container_width=True)

    st.markdown("<div class='card'>",unsafe_allow_html=True)
    st.markdown("**🔍 Area Risk Breakdown**",unsafe_allow_html=True)
    for label,val in [("Street Lighting",55),("Police Proximity",80),("Incident History",62),("CCTV Coverage",45)]:
        st.markdown(f"""<div style="margin-bottom:10px;">
          <div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:4px;">
            <span style="color:#C8CCE8;">{label}</span><span style="color:#F2F4FF;">{val}%</span>
          </div>
          <div style="background:#1A1D2E;border-radius:8px;height:6px;">
            <div style="background:#E8196E;height:6px;border-radius:8px;width:{val}%;"></div>
          </div></div>""",unsafe_allow_html=True)
    st.markdown("</div>",unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  NEARBY HELP — FIXED with multi-amenity fallback
# ══════════════════════════════════════════════════════════════════════════════
elif page=="Nearby Help":
    st.markdown("""<div class="page-title"><div class="section-label">Nearby</div><h1>Nearby Help</h1><p>Hospitals, clinics and police within 10 km</p></div>""", unsafe_allow_html=True)
    st.markdown("<p style='color:#7A7E9A;'>Real places from OpenStreetMap · Hospitals, clinics, doctors within <b style='color:#F2F4FF;'>10 km</b></p>",unsafe_allow_html=True)

    if home_lat and home_lon:
        st.success(f"📍 Your location: **{home_lat:.5f}, {home_lon:.5f}**")
        st.map(pd.DataFrame({"lat":[home_lat],"lon":[home_lon]}),zoom=13)

        cache_key=f"{home_lat:.4f},{home_lon:.4f}"
        if st.session_state.nearby_fetched_for != cache_key:
            with st.spinner("🔍 Searching hospitals, clinics, police within 10 km… (this takes ~15 sec)"):
                # FIXED: fetch hospitals using multi-amenity function
                hospitals = fetch_nearby_osm(home_lat, home_lon, "hospital", radius_m=10000, limit=8)
                police    = fetch_nearby_osm(home_lat, home_lon, "police",   radius_m=10000, limit=8)
                st.session_state.nearby_police    = police
                st.session_state.nearby_hospitals = hospitals
                st.session_state.nearby_fetched_for = cache_key
        
        # Show count as feedback
        hosp_count = len(st.session_state.nearby_hospitals)
        pol_count  = len(st.session_state.nearby_police)
        m1,m2 = st.columns(2)
        m1.metric("🏥 Medical places found", hosp_count)
        m2.metric("🚔 Police stations found", pol_count)
        
        if hosp_count == 0:
            st.warning("⚠️ OpenStreetMap has limited data in your area. Showing Google Maps link instead.")
    else:
        st.warning("📍 Location not available. Allow browser GPS access and refresh.")
        st.markdown("""
        <div class="card" style="margin-top:16px;">
          <p style="font-weight:600;">💡 How to enable location</p>
          <ol style="color:#C8CCE8;font-size:13px;line-height:2.2;">
            <li>Click the 🔒 lock icon in your browser address bar</li>
            <li>Set <b>Location</b> to <b>Allow</b></li>
            <li>Refresh the page</li>
          </ol>
        </div>""",unsafe_allow_html=True)
        st.stop()

    filt=st.radio("Show",["All","🚔 Police","🏥 Hospital / Clinic"],horizontal=True)

    def place_card(p,icon,color):
        ml=f"https://maps.google.com/?q={p['lat']},{p['lon']}"
        ph=f'<a href="tel:{p["phone"]}" style="color:#E8196E;font-size:13px;margin-left:8px;">📞</a>' if p.get("phone") else ""
        ptype = f'<span style="font-size:11px;color:#7A7E9A;margin-left:4px;">({p.get("type","hospital")})</span>'
        st.markdown(f"""
        <div class="card" style="display:flex;align-items:center;gap:14px;padding:14px 18px;margin-bottom:8px;">
          <div style="width:42px;height:42px;border-radius:12px;background:{color}18;
          display:flex;align-items:center;justify-content:center;font-size:20px;">{icon}</div>
          <div style="flex:1;">
            <div style="font-weight:600;font-size:14px;">{p['name']}{ptype}</div>
            <div style="font-size:12px;color:#7A7E9A;">{p['dist_km']:.2f} km ·
              <a href="{ml}" target="_blank" style="color:#E8196E;">Get Directions</a></div>
          </div>{ph}
        </div>""",unsafe_allow_html=True)

    if filt in ["All","🚔 Police"]:
        st.markdown("### 🚔 Nearest Police Stations")
        if st.session_state.nearby_police:
            for p in st.session_state.nearby_police: place_card(p,"🚔","#3b82f6")
        else:
            st.warning("No police stations found via OpenStreetMap.")
        st.markdown(f'<a href="https://www.google.com/maps/search/police+station/@{home_lat},{home_lon},13z" target="_blank" style="color:#E8196E;">🔍 Search Police on Google Maps →</a>',unsafe_allow_html=True)

    if filt in ["All","🏥 Hospital / Clinic"]:
        st.markdown("### 🏥 Nearest Hospitals, Clinics & Doctors")
        if st.session_state.nearby_hospitals:
            for h in st.session_state.nearby_hospitals: place_card(h,"🏥","#22c55e")
        else:
            st.warning("No hospitals/clinics found via OpenStreetMap in this area.")
        st.markdown(f'<a href="https://www.google.com/maps/search/hospital/@{home_lat},{home_lon},13z" target="_blank" style="color:#E8196E;">🔍 Search Hospitals on Google Maps →</a>',unsafe_allow_html=True)

    st.markdown("---")
    if st.button("🔄 Refresh Nearby Places"):
        st.session_state.nearby_fetched_for = None
        st.rerun()

    c1,c2=st.columns(2)
    with c1: st.markdown(f'<a href="https://www.google.com/maps/search/police+station/@{home_lat},{home_lon},13z" target="_blank"><button style="width:100%;background:#3b82f6;color:white;border:none;border-radius:14px;padding:12px;font-weight:700;font-size:14px;cursor:pointer;">🗺️ More Police on Maps</button></a>',unsafe_allow_html=True)
    with c2: st.markdown(f'<a href="https://www.google.com/maps/search/hospital/@{home_lat},{home_lon},13z" target="_blank"><button style="width:100%;background:#22c55e;color:white;border:none;border-radius:14px;padding:12px;font-weight:700;font-size:14px;cursor:pointer;">🗺️ More Hospitals on Maps</button></a>',unsafe_allow_html=True)
    st.markdown("<br>",unsafe_allow_html=True)
    if st.button("📞 Call Police — 100",use_container_width=True):
        st.markdown('<meta http-equiv="refresh" content="0;url=tel:100">',unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  SAFE ROUTE HOME  🛣️  NEW PAGE
# ══════════════════════════════════════════════════════════════════════════════
elif page=="Safe Route":
    st.markdown("""<div class="page-title"><div class="section-label">Navigation</div><h1>Safe Route Home</h1><p>Navigate home and share live location with your phone &amp; trusted contacts</p></div>""", unsafe_allow_html=True)

    render_live_location_panel()

    st.markdown("---")
    # Save / update home location
    st.markdown("### 🏠 Your Saved Home Location")
    col_a, col_b = st.columns([3,1])
    with col_a:
        new_home = st.text_input(
            "Home address",
            value=st.session_state.home_address or "",
            placeholder="e.g. Koramangala 4th Block, Bengaluru"
        )
    with col_b:
        st.markdown("<br>",unsafe_allow_html=True)
        if st.button("💾 Save Home"):
            if new_home.strip():
                with st.spinner("Locating address…"):
                    hlat, hlon, dname = geocode_address(new_home.strip())
                if hlat:
                    st.session_state.home_lat = hlat
                    st.session_state.home_lon = hlon
                    st.session_state.home_address = new_home.strip()
                    st.success(f"✅ Home saved: {dname[:60]}")
                    st.rerun()
                else:
                    st.error("Couldn't locate that address. Try a more specific address.")
            else:
                st.error("Please enter an address.")

    if st.session_state.home_lat:
        st.markdown(f"""
        <div class="card" style="padding:14px 18px;">
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <div>
              <p style="font-weight:700;font-size:15px;margin:0;">🏠 {st.session_state.home_address or 'Home'}</p>
              <p style="font-size:12px;color:#7A7E9A;margin:4px 0 0;">
                {st.session_state.home_lat:.5f}, {st.session_state.home_lon:.5f}
              </p>
            </div>
            <a href="https://maps.google.com/?q={st.session_state.home_lat},{st.session_state.home_lon}"
            target="_blank" style="color:#E8196E;font-size:13px;">🗺️ View</a>
          </div>
        </div>""",unsafe_allow_html=True)

        st.markdown("### 🗺️ Get Route Now")

        route_mode = st.radio("Travel mode",["🚶 Walking","🚗 Driving","🚌 Transit"],horizontal=True)
        mode_map={"🚶 Walking":"walking","🚗 Driving":"driving","🚌 Transit":"transit"}
        gmode=mode_map[route_mode]

        sr1, sr2 = st.columns(2)
        with sr1:
            st.session_state.safe_route_sharing = st.toggle(
                "Share live location while on this route",
                value=st.session_state.get("safe_route_sharing", False),
                key="safe_route_share_toggle",
            )
        with sr2:
            if st.button("📲 Send current location to all phones", use_container_width=True, key="route_share_now"):
                sent, mode = broadcast_live_location("On safe route home")
                if mode == "no_gps":
                    st.error("Refresh GPS first.")
                elif mode == "twilio":
                    st.success(f"SMS sent to {sent} number(s).")
                elif mode == "native_sms":
                    st.info(f"Tap each button and press Send ({sent} number(s)).")
                    render_sms_tap_links(
                        st.session_state.get("pending_sms_body", ""),
                        st.session_state.get("pending_sms_phones", []),
                    )

        if st.session_state.get("safe_route_sharing"):
            st.session_state.live_share_enabled = True
            st.info("Live sharing is ON — location will be sent to your phone & trusted contacts every few minutes.")

        if home_lat and home_lon:
            # Direct Google Maps directions link
            gmaps_route = (
                f"https://www.google.com/maps/dir/?api=1"
                f"&origin={home_lat},{home_lon}"
                f"&destination={st.session_state.home_lat},{st.session_state.home_lon}"
                f"&travelmode={gmode}"
            )
            st.markdown(f"""
            <a href="{gmaps_route}" target="_blank">
              <button style="width:100%;background:#22c55e;color:white;border:none;
              border-radius:14px;padding:16px;font-weight:700;font-size:16px;cursor:pointer;
              font-family:'Outfit',sans-serif;">
                🏠 Navigate Home — {route_mode}
              </button>
            </a>""",unsafe_allow_html=True)
            
            st.markdown("<br>",unsafe_allow_html=True)
            
            # Show both points on map
            map_df = pd.DataFrame({
                "lat":[home_lat, st.session_state.home_lat],
                "lon":[home_lon, st.session_state.home_lon]
            })
            st.map(map_df, zoom=13)
            
            # Quick safety tips for the route
            hour = datetime.now().hour
            if hour >= 21 or hour < 6:
                st.markdown("""
                <div style="background:#E8196E12;border:1px solid #E8196E40;border-radius:14px;padding:16px;margin-top:12px;">
                  <p style="font-weight:700;color:#E8196E;margin-bottom:8px;">🌙 Night Route Safety Tips</p>
                  <ul style="color:#C8CCE8;font-size:13px;line-height:2;">
                    <li>Stay on main, well-lit roads — avoid shortcuts</li>
                    <li>Keep your phone accessible but not visible</li>
                    <li>Share your live location with a trusted contact</li>
                    <li>Call a contact and stay on the line while walking</li>
                    <li>Prefer auto/cab over walking if distance > 1 km</li>
                  </ul>
                </div>""",unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="background:#22c55e12;border:1px solid #22c55e40;border-radius:14px;padding:16px;margin-top:12px;">
                  <p style="font-weight:700;color:#22c55e;margin-bottom:8px;">✅ Safe Route Tips</p>
                  <ul style="color:#C8CCE8;font-size:13px;line-height:2;">
                    <li>Prefer busy, well-known roads</li>
                    <li>Let a contact know your ETA</li>
                    <li>SheShield check-in is active — stay on schedule</li>
                  </ul>
                </div>""",unsafe_allow_html=True)

            st.markdown("### 📤 Send live location (SMS & WhatsApp)")
            share_body = build_live_location_message(current_user(), home_lat, home_lon, extra="On safe route home")
            recipients = get_location_recipient_phones()
            if recipients:
                if st.button("📲 SMS everyone now (all saved numbers)", use_container_width=True, key="route_sms_all"):
                    sent, mode = broadcast_live_location("On safe route home")
                    if mode == "twilio":
                        st.success(f"SMS sent to {sent} number(s).")
                    else:
                        st.info(f"SMS app opened for {sent} number(s).")
                for ph in recipients:
                    wa = whatsapp_link(ph, share_body)
                    label = ph
                    for c in st.session_state.trusted_contacts:
                        if normalize_phone(c.get("phone")) == ph:
                            label = c.get("name") or ph
                            break
                    if ph == normalize_phone(st.session_state.get("user_phone", "")):
                        label = f"{current_user()} (your phone)"
                    st.markdown(
                        f'<a href="sms:+91{ph}?body={requests.utils.quote(share_body)}" '
                        f'style="display:block;background:#1A1D2E;border:1px solid rgba(255,255,255,0.1);'
                        f'border-radius:12px;padding:10px 16px;margin-bottom:8px;color:#F2F4FF;'
                        f'text-decoration:none;font-size:13px;">📱 SMS <b>{label}</b> (+91{ph})</a>',
                        unsafe_allow_html=True,
                    )
                    if wa:
                        st.markdown(
                            f'<a href="{wa}" target="_blank" '
                            f'style="display:block;background:#25D36618;border:1px solid #25D36644;'
                            f'border-radius:12px;padding:8px 16px;margin-bottom:8px;color:#25D366;'
                            f'text-decoration:none;font-size:13px;">💬 WhatsApp <b>{label}</b></a>',
                            unsafe_allow_html=True,
                        )
            else:
                st.info("Add trusted contacts (Contacts tab) with 10-digit Indian mobile numbers.")
        else:
            st.warning("📍 Your current GPS location is needed to get directions. Allow browser location access.")
    else:
        st.markdown("""
        <div class="card" style="text-align:center;padding:40px;">
          <div style="font-size:48px;margin-bottom:12px;">🏠</div>
          <p style="font-weight:600;font-size:18px;">No home location saved yet</p>
          <p style="color:#7A7E9A;">Enter your home address above and click Save Home.</p>
        </div>""",unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  ROAD SAFETY  🚦  NEW PAGE — Push-button alerts
# ══════════════════════════════════════════════════════════════════════════════
elif page=="Road Safety":
    st.markdown("""<div class="page-title"><div class="section-label">Road safety</div><h1>Road Safety</h1><p>One-tap hazard reports with location shared to your contacts</p></div>""", unsafe_allow_html=True)
    st.markdown("<p style='color:#7A7E9A;'>One-tap buttons to report road hazards and alert your contacts instantly.</p>",unsafe_allow_html=True)

    location_str = f"{home_lat:.5f}, {home_lon:.5f}" if home_lat else "Location unknown"
    maps_link = f"https://maps.google.com/?q={home_lat},{home_lon}" if home_lat else "#"

    st.markdown("### ⚠️ Report a Road Hazard — Tap to Alert Contacts")

    # Big push-button grid
    hazard_types = [
        ("🚗 Road Accident","Accident at my location — send help!","#E8196E"),
        ("🚧 Road Blocked","Road is blocked / obstruction ahead","#FFB020"),
        ("💡 No Street Light","Extremely dark road — safety risk","#7B61FF"),
        ("🌊 Waterlogging","Road flooded / waterlogged","#3b82f6"),
        ("👁️ Suspicious Person","Suspicious person near my location","#E8196E"),
        ("🚌 Unsafe Vehicle","Unsafe/reckless driver on road","#FF6B2E"),
    ]

    cols = st.columns(2)
    for i, (label, desc, color) in enumerate(hazard_types):
        with cols[i % 2]:
            btn_key = f"road_btn_{i}"
            if st.button(label, key=btn_key, use_container_width=True):
                # Log the alert
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                alert_entry = {
                    "Type": label,
                    "Description": desc,
                    "Location": location_str,
                    "Maps": maps_link,
                    "Time": timestamp
                }
                st.session_state.road_safety_alerts.insert(0, alert_entry)
                
                # Notify contacts via SMS
                active_contacts = [c for c in st.session_state.trusted_contacts if c.get("phone")]
                msg = f"ROAD ALERT from {current_user()}: {label} — {desc}. Location: {maps_link} at {timestamp[:16]}"
                
                st.markdown(f"""
                <div style="background:{color}18;border:2px solid {color}55;border-radius:14px;
                padding:16px;margin-bottom:12px;">
                  <p style="font-weight:700;color:{color};font-size:16px;">✅ {label} REPORTED!</p>
                  <p style="color:#C8CCE8;font-size:13px;">{desc}</p>
                  <p style="color:#7A7E9A;font-size:12px;">📍 {location_str}</p>
                </div>""",unsafe_allow_html=True)
                
                # Show SMS links for each contact
                if active_contacts:
                    st.markdown("**📱 Tap to SMS your contacts:**")
                    for c in active_contacts:
                        sms_url = f"sms:+91{c['phone']}?body={requests.utils.quote(msg)}"
                        st.markdown(f'<a href="{sms_url}" style="display:block;background:#1A1D2E;border:1px solid rgba(255,255,255,0.1);border-radius:12px;padding:10px 16px;margin-bottom:6px;color:#F2F4FF;text-decoration:none;font-size:13px;">📱 Alert <b>{c["name"]}</b></a>',unsafe_allow_html=True)
                else:
                    st.info("Add trusted contacts to send road safety alerts.")
                
                # Log to alerts
                new_row = {
                    "Name": current_user(), "Location": location_str,
                    "Emergency Type": label, "Description": desc, "Timestamp": timestamp
                }
                st.session_state.alerts_df = pd.concat(
                    [st.session_state.alerts_df, pd.DataFrame([new_row])], ignore_index=True)

    # Emergency road call buttons
    st.markdown("---")
    st.markdown("### 📞 Emergency Road Calls")
    rc1,rc2,rc3 = st.columns(3)
    with rc1:
        st.markdown('<a href="tel:112"><button style="width:100%;background:#E8196E;color:white;border:none;border-radius:14px;padding:14px;font-weight:700;font-size:15px;cursor:pointer;">🚨 112 Emergency</button></a>',unsafe_allow_html=True)
    with rc2:
        st.markdown('<a href="tel:1073"><button style="width:100%;background:#FFB020;color:white;border:none;border-radius:14px;padding:14px;font-weight:700;font-size:15px;cursor:pointer;">🛣️ 1073 Road Help</button></a>',unsafe_allow_html=True)
    with rc3:
        st.markdown('<a href="tel:108"><button style="width:100%;background:#22c55e;color:white;border:none;border-radius:14px;padding:14px;font-weight:700;font-size:15px;cursor:pointer;">🚑 108 Ambulance</button></a>',unsafe_allow_html=True)

    # Recent road alerts log
    if st.session_state.road_safety_alerts:
        st.markdown("---")
        st.markdown("### 📋 Recent Road Alerts (This Session)")
        for a in st.session_state.road_safety_alerts[:5]:
            st.markdown(f"""
            <div class="card" style="padding:12px 16px;margin-bottom:8px;">
              <div style="display:flex;justify-content:space-between;">
                <span style="font-weight:600;color:#F2F4FF;">{a['Type']}</span>
                <span style="font-size:12px;color:#7A7E9A;">{a['Time'][11:16]}</span>
              </div>
              <p style="font-size:12px;color:#C8CCE8;margin:4px 0 0;">{a['Description']} · 📍 {a['Location']}</p>
            </div>""",unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  SHRISTI'S AI
# ══════════════════════════════════════════════════════════════════════════════
elif page=="Safety Assistant":
    st.markdown("""<div class="page-title"><div class="section-label">Assistant</div><h1>Safety Assistant</h1><p>24/7 guidance for routes, emergencies, and check-ins</p></div>""", unsafe_allow_html=True)
    ai_status = "Claude API" if ANTHROPIC_KEY.startswith("sk-ant-api") else "built-in safety guide (no API key required)"
    st.markdown(f"<p style='color:#7A7E9A;'>Powered by {ai_status}</p>", unsafe_allow_html=True)

    st.markdown("""
    <div style="background:#22c55e12;border:1px solid #22c55e30;border-radius:30px;
    padding:6px 14px;display:inline-flex;align-items:center;gap:8px;margin-bottom:20px;">
      <span style="width:8px;height:8px;border-radius:50%;background:#22c55e;display:inline-block;"></span>
      <span style="font-size:12px;color:#22c55e;font-weight:600;">Assistant online</span>
    </div>""",unsafe_allow_html=True)

    if not st.session_state.ai_history:
        st.session_state.ai_history=[{"role":"assistant","content":
            f"Hi {current_user()}! I'm your SheShield safety assistant. I can help with routes, nearby help, check-ins, and emergencies. How can I help you stay safe today?"}]

    chips=["I'm safe ✅","Plan my route home 🗺️","What areas are unsafe near me?",
           "Activate SOS 🚨","What can you do?","It's late at night 🌙","Nearest police station?"]
    cols=st.columns(min(len(chips),4))
    for i,chip in enumerate(chips):
        with cols[i%4]:
            if st.button(chip,key=f"chip_{i}"):
                st.session_state.ai_history.append({"role":"user","content":chip})
                loc_ctx=f"User location: {home_lat},{home_lon}" if home_lat else "Location unknown"
                contacts_ctx=", ".join([c["name"] for c in st.session_state.trusted_contacts if c.get("name")])
                system=f"""You are the SheShield personal safety assistant for {current_user()}. You are warm, concise, and focused on women's safety.
Context: {loc_ctx}. Trusted contacts: {contacts_ctx}. Night mode: {is_night}. Time: {datetime.now().strftime('%H:%M')}.
Keep responses under 100 words. If there's danger, always say to go to Send SOS page. Be supportive and action-oriented."""
                msgs=[{"role":m["role"],"content":m["content"]} for m in st.session_state.ai_history if m["role"]!="assistant" or st.session_state.ai_history.index(m)==0]
                reply=call_claude_api(msgs[-6:],system)
                st.session_state.ai_history.append({"role":"assistant","content":reply})
                st.rerun()

    for msg in st.session_state.ai_history:
        role=msg.get("role","")
        content=msg.get("content","")
        if role=="assistant":
            text=content.replace("\n","<br>")
            st.markdown(f"""
            <div style="display:flex;align-items:flex-start;gap:10px;margin:10px 0;">
              <div style="width:32px;height:32px;border-radius:50%;background:#E8196E22;
              display:flex;align-items:center;justify-content:center;font-size:15px;flex-shrink:0;">🤖</div>
              <div class="ai-bubble-bot">{text}</div>
            </div>""",unsafe_allow_html=True)
        elif role=="user":
            st.markdown(f'<div class="ai-bubble-user">{content}</div>',unsafe_allow_html=True)

    with st.form("ai_form",clear_on_submit=True):
        user_input=st.text_input("",placeholder=f"Ask anything, {current_user()}…",label_visibility="collapsed")
        submitted=st.form_submit_button("Send ➤",use_container_width=True)
        if submitted and user_input.strip():
            st.session_state.ai_history.append({"role":"user","content":user_input})
            loc_ctx=f"User location: {home_lat},{home_lon}" if home_lat else "Location unknown"
            contacts_ctx=", ".join([c["name"] for c in st.session_state.trusted_contacts if c.get("name")])
            system=f"""You are the SheShield personal safety assistant for {current_user()}. Warm, concise, focused on women's safety.
Context: {loc_ctx}. Trusted contacts: {contacts_ctx}. Night mode: {is_night}. Time: {datetime.now().strftime('%H:%M')}.
Keep responses under 100 words. If danger, direct to Send SOS page. Be supportive and action-oriented."""
            msgs=[{"role":m["role"],"content":m["content"]} for m in st.session_state.ai_history]
            reply=call_claude_api(msgs[-8:],system)
            st.session_state.ai_history.append({"role":"assistant","content":reply})
            st.rerun()

    if st.button("🗑️ Clear Chat"):
        st.session_state.ai_history=[]
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
#  TRUSTED CONTACTS
# ══════════════════════════════════════════════════════════════════════════════
elif page=="Contacts":
    st.markdown("""<div class="page-title"><div class="section-label">Contacts</div><h1>Trusted Contacts</h1><p>Up to 4 people alerted instantly in emergencies</p></div>""", unsafe_allow_html=True)
    st.markdown("<p style='color:#7A7E9A;'>These numbers receive <b>live location SMS</b>, SOS alerts, and safe-route updates.</p>",unsafe_allow_html=True)

    st.markdown("#### 📱 Who receives live location?")
    up = normalize_phone(st.session_state.get("user_phone", ""))
    st.markdown(
        f'<p style="font-size:13px;color:#C8CCE8;">Your registered phone: '
        f'<b>+91{up}</b></p>' if len(up) == 10 else
        '<p style="font-size:13px;color:#FFB020;">Your phone was not set at onboarding.</p>',
        unsafe_allow_html=True,
    )
    st.session_state.share_to_my_phone = st.checkbox(
        "Also send live location copies to my phone (+91… above)",
        value=st.session_state.get("share_to_my_phone", True),
    )
    st.session_state.monitor_phone = st.text_input(
        "Guardian / second phone (optional, 10 digits)",
        value=st.session_state.get("monitor_phone", ""),
        placeholder="e.g. parent or partner who should track you",
        max_chars=10,
    )
    if st.session_state.monitor_phone and len(normalize_phone(st.session_state.monitor_phone)) != 10:
        st.warning("Guardian phone must be 10 digits.")

    contacts=st.session_state.trusted_contacts
    updated=[]
    for i,c in enumerate(contacts):
        st.markdown(f'<div class="card"><p style="font-weight:700;margin-bottom:12px;">Contact {i+1}</p>',unsafe_allow_html=True)
        c1c,c2c,c3c=st.columns([2,2,2])
        with c1c: name=st.text_input("Full Name",value=c.get("name",""),key=f"cn_{i}",placeholder="e.g. Dhanushree G")
        with c2c: rel=st.text_input("Relation",value=c.get("relation",""),key=f"cr_{i}",placeholder="e.g. Sister")
        with c3c: ph=st.text_input("Phone",value=c.get("phone",""),key=f"cp_{i}",placeholder="10-digit number")
        updated.append({"initials":(name[:2]).upper() if name else f"C{i+1}","name":name,"relation":rel,"phone":ph})
        st.markdown("</div>",unsafe_allow_html=True)

    if st.button("💾 Save All Contacts",use_container_width=True):
        st.session_state.trusted_contacts=updated
        st.success("✅ Contacts saved! They'll receive WhatsApp + calls on your next SOS.")

    active=[c for c in updated if c.get("name") and c.get("phone")]
    st.markdown(f"<p style='color:#7A7E9A;font-size:13px;'>📋 {len(active)}/4 contacts saved.</p>",unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📋 What your contacts receive when you send SOS")
    st.markdown("""
    <div class="card">
      <p style="font-size:13px;color:#C8CCE8;line-height:1.8;">
      💬 <b style="color:#F2F4FF;">WhatsApp message:</b> SOS alert with emergency type, map link, and time<br>
      📧 <b style="color:#F2F4FF;">Email:</b> Full details with map link to your alert email<br>
      📵 <b style="color:#F2F4FF;">Offline SMS:</b> When Offline Mode is ON, native SMS opens automatically<br>
      📞 <b style="color:#F2F4FF;">Call link:</b> Your contacts can tap your number directly from the home screen
      </p>
    </div>""",unsafe_allow_html=True)
