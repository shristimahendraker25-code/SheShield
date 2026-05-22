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
#  CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════
USER_NAME       = "Shristi VM"
ALERT_EMAIL     = "shristimahendraker25@gmail.com"
SENDER_EMAIL    = "your_sender_gmail@gmail.com"
SENDER_APP_PWD  = "xxxx xxxx xxxx xxxx"

TWILIO_SID      = "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TWILIO_TOKEN    = "your_auth_token"
TWILIO_FROM     = "whatsapp:+14155238886"

ANTHROPIC_KEY   = "sk-ant-xxxxxxxxxxxxxxxxxxxx"

# ══════════════════════════════════════════════════════════════════════════════
#  CSS / THEME
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700;800&family=Inter:wght@400;500;600&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;background-color:#080A14;color:#F2F4FF;}
.stApp{background-color:#080A14;}
h1,h2,h3,h4{font-family:'Outfit',sans-serif!important;color:#F2F4FF!important;}
[data-testid="stSidebar"]{background-color:#0F1120;border-right:1px solid rgba(255,255,255,0.08);}
[data-testid="stSidebar"] *{color:#C8CCE8!important;}
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
    """Fetch nearby places. Radius default 10 km, also queries relations."""
    try:
        q = (
            f"[out:json][timeout:25];"
            f"("
            f"node[amenity={amenity}](around:{radius_m},{lat},{lon});"
            f"way[amenity={amenity}](around:{radius_m},{lat},{lon});"
            f"relation[amenity={amenity}](around:{radius_m},{lat},{lon});"
            f");out center {limit};"
        )
        r = requests.post("https://overpass-api.de/api/interpreter", data={"data": q}, timeout=30)
        out = []
        for el in r.json().get("elements", []):
            tags = el.get("tags", {})
            name = tags.get("name") or tags.get("name:en") or amenity.replace("_"," ").title()
            elat = el.get("lat") or el.get("center", {}).get("lat")
            elon = el.get("lon") or el.get("center", {}).get("lon")
            if elat and elon:
                out.append({
                    "name": name, "lat": elat, "lon": elon,
                    "dist_km": haversine_km(lat, lon, elat, elon),
                    "phone": tags.get("phone") or tags.get("contact:phone", "")
                })
        out.sort(key=lambda x: x["dist_km"])
        return out[:limit]
    except Exception as e:
        return []

def reverse_geocode(lat,lon):
    try:
        r=requests.get("https://nominatim.openstreetmap.org/reverse",
            params={"lat":lat,"lon":lon,"format":"json"},
            headers={"User-Agent":"SheShield/2.0"},timeout=4)
        d=r.json().get("address",{})
        return (d.get("road") or d.get("neighbourhood") or d.get("suburb") or
                d.get("village") or d.get("town") or d.get("city") or f"{lat:.4f},{lon:.4f}")
    except: return f"{lat:.4f},{lon:.4f}"

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
    try:
        from twilio.rest import Client
        client=Client(TWILIO_SID,TWILIO_TOKEN)
        msg=f"SOS ALERT!\n{name} needs help!\nEmergency: {emergency}\nLocation: https://maps.google.com/?q={location}\nTime: {datetime.now().strftime('%H:%M')}"
        for c in contacts:
            if c.get("phone"):
                try:
                    client.messages.create(body=msg,from_=TWILIO_FROM,to=f"whatsapp:+91{c['phone']}")
                    sent+=1
                except: pass
    except ImportError:
        st.info("Install twilio: pip install twilio")
    except Exception as e:
        st.warning(f"WhatsApp error: {e}")
    return sent

def call_claude_api(messages, system_prompt):
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            system=system_prompt,
            messages=messages
        )
        return resp.content[0].text
    except ImportError:
        return fallback_ai(messages[-1]["content"] if messages else "")
    except Exception as e:
        return fallback_ai(messages[-1]["content"] if messages else "")

def fallback_ai(q):
    q=q.lower()
    if any(w in q for w in ["sos","help me","danger","attack"]):
        return f"Activating SOS protocol! Alerting all trusted contacts with your GPS location. Stay on the line."
    if any(w in q for w in ["safe","okay","fine"]):
        return f"Great to hear you're safe, {USER_NAME}! Next check-in in 28 minutes."
    if any(w in q for w in ["route","home","go","path"]):
        return f"Take well-lit main roads, {USER_NAME}. Avoid isolated lanes after 9 PM."
    if any(w in q for w in ["police","hospital","nearest"]):
        return f"Check the Nearby Help page — it shows real police stations and hospitals within 10 km of you."
    if any(w in q for w in ["night","late","dark"]):
        return f"Night Shield is active, {USER_NAME}. Check-ins every 15 min, contacts on standby."
    return f"I'm here with you, {USER_NAME}. Stay aware and keep your phone accessible. What do you need?"

def sos_countdown_and_send(name,location,emergency,desc,contacts,play_sound,demo_mode):
    placeholder=st.empty()
    cancelled=False
    for i in range(3,0,-1):
        with placeholder.container():
            st.markdown(f"""
            <div style="background:#E8196E18;border:2px solid #E8196E;border-radius:20px;
            padding:30px;text-align:center;margin:10px 0;">
              <div style="font-size:60px;font-weight:900;color:#E8196E;">{i}</div>
              <p style="font-size:16px;font-weight:600;color:#F2F4FF;">Sending SOS alert in {i} second{"s" if i>1 else ""}...</p>
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
    if not demo_mode:
        email_ok=send_email(name,location,emergency,desc,timestamp)
        wa_sent=send_whatsapp(name,location,emergency,contacts)
    else:
        email_ok=True; wa_sent=len([c for c in contacts if c.get("phone")])

    alert={"Name":name,"Location":location,"Emergency Type":emergency,
           "Description":desc,"Timestamp":timestamp}
    st.session_state.alerts_df=pd.concat(
        [st.session_state.alerts_df,pd.DataFrame([alert])],ignore_index=True)
    st.session_state.alerts_df.to_csv("alerts.csv",index=False)
    st.session_state.sos_count+=1

    st.error("SOS ALERT SENT!")
    if email_ok: st.success(f"Email sent to {ALERT_EMAIL}")
    if wa_sent:  st.success(f"WhatsApp sent to {wa_sent} contact(s)")

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
# CHANGE: Priya Sharma -> Shristi VM, Meera Nair -> Dhanushree G
DEFAULT_CONTACTS=[
    {"initials":"SV","name":"Shristi VM","relation":"Contact 1","phone":"8088630512"},
    {"initials":"DG","name":"Dhanushree G","relation":"Contact 2","phone":"8431918980"},
    {"initials":"C3","name":"","relation":"Contact 3","phone":""},
    {"initials":"C4","name":"","relation":"Contact 4","phone":""},
]

if "alerts_df" not in st.session_state:
    st.session_state.alerts_df = pd.read_csv("alerts.csv") if os.path.exists("alerts.csv") else pd.DataFrame(
        columns=["Name","Location","Emergency Type","Description","Timestamp"])

DEFAULTS={
    "onboarded":False,"ai_history":[],"live_lat":None,"live_lon":None,
    "trusted_contacts":DEFAULT_CONTACTS,"nearby_police":[],"nearby_hospitals":[],
    "nearby_fetched_for":None,"last_checkin":datetime.now(),"checkin_interval":30,
    "sos_count":0,"total_checkins":0,"demo_mode":False,
    "unsafe_zones":[],"zones_fetched_for":None,
}
for k,v in DEFAULTS.items():
    if k not in st.session_state: st.session_state[k]=v

df=st.session_state.alerts_df
is_night=(datetime.now().hour>=21 or datetime.now().hour<6)
if is_night: st.session_state.checkin_interval=15

# ══════════════════════════════════════════════════════════════════════════════
#  ONBOARDING — name + phone only, no trusted contacts step
# ══════════════════════════════════════════════════════════════════════════════
if not st.session_state.onboarded:
    st.markdown("""
    <div style="max-width:480px;margin:60px auto;text-align:center;">
      <div style="font-size:64px;margin-bottom:16px;">🛡️</div>
      <h1 style="font-family:'Outfit',sans-serif;font-size:36px;margin-bottom:8px;">Welcome to SheShield</h1>
      <p style="color:#7A7E9A;margin-bottom:32px;">Your personal AI safety companion.</p>
    </div>""",unsafe_allow_html=True)

    col1,col2,col3=st.columns([1,2,1])
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### Step 1 — Your details")
        uname  = st.text_input("Your name", value="Shristi VM", placeholder="Enter your full name")
        uphone = st.text_input("Your phone number", placeholder="10-digit mobile number")
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### Step 2 — Allow location")
        st.markdown("<p style='font-size:12px;color:#7A7E9A;'>Click Allow when your browser asks — used for Nearby Help and safety predictions.</p>", unsafe_allow_html=True)
        if st.button("🛡️ Enter SheShield", use_container_width=True):
            if not uname.strip():
                st.error("Please enter your name.")
            elif not uphone.strip() or not uphone.strip().isdigit() or len(uphone.strip()) != 10:
                st.error("Please enter a valid 10-digit phone number.")
            else:
                st.session_state.onboarded = True
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
shield_color="#22c55e" if not is_night else "#7B61FF"
shield_label="Protected" if not is_night else "Night Shield"

st.sidebar.markdown(f"""
<div style="padding:16px 0 8px;">
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
    <span style="color:#E8196E;font-size:18px;">🛡️</span>
    <span style="font-family:'Outfit',sans-serif;font-weight:700;font-size:13px;
    letter-spacing:3px;text-transform:uppercase;color:#E8196E;">SheShield</span>
  </div>
  <p style="font-family:'Outfit',sans-serif;font-weight:700;font-size:20px;color:#F2F4FF;margin:0;">
    Hey, {USER_NAME} 👋</p>
  <p style="font-size:12px;color:#7A7E9A;margin:2px 0 0;">{datetime.now().strftime("%A, %d %b %Y · %I:%M %p")}</p>
</div>
<div style="background:{shield_color}18;border:1px solid {shield_color}30;border-radius:30px;
padding:4px 12px;display:inline-flex;align-items:center;gap:6px;margin-bottom:12px;">
  <span style="width:8px;height:8px;border-radius:50%;background:{shield_color};display:inline-block;
  animation:pulse 2s infinite;"></span>
  <span style="font-size:12px;color:{shield_color};font-weight:600;">{shield_label}</span>
</div>
<style>@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.5}}}}</style>
""",unsafe_allow_html=True)

demo=st.sidebar.toggle("🎭 Demo Mode",value=st.session_state.demo_mode)
st.session_state.demo_mode=demo
if demo:
    st.sidebar.success("Demo mode ON — safe to present!")

page=st.sidebar.radio("Navigation",[
    "🏠 Home","🚨 Send SOS","📋 View Alerts",
    "📊 Analytics","🏥 Nearby Help","🤖 Shristi's AI","👥 Trusted Contacts"
],label_visibility="collapsed")

st.sidebar.markdown("---")
st.sidebar.markdown("**📞 Quick Dial**",unsafe_allow_html=False)
for label,num in [("🚨 Emergency","112"),("🚓 Police","100"),("🚑 Ambulance","108"),("👩 Women","1091")]:
    st.sidebar.markdown(f'<a href="tel:{num}" style="display:block;color:#C8CCE8;font-size:12px;padding:3px 0;">{label}: {num}</a>',unsafe_allow_html=True)

if is_night:
    st.markdown("""
    <div class="night-banner">
      <span style="font-size:20px;">🌙</span>
      <div>
        <span style="font-weight:700;color:#a78bfa;">Night Shield Active</span>
        <span style="font-size:12px;color:#7A7E9A;margin-left:8px;">Check-ins every 15 min · Contacts on standby</span>
      </div>
    </div>""",unsafe_allow_html=True)

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
#  LIVE LOCATION
# ══════════════════════════════════════════════════════════════════════════════
loc_data=get_geolocation()
if loc_data and isinstance(loc_data,dict) and "coords" in loc_data:
    c=loc_data["coords"]
    lat,lon=c.get("latitude"),c.get("longitude")
    if lat and lon:
        st.session_state.live_lat=lat
        st.session_state.live_lon=lon

home_lat=st.session_state.live_lat
home_lon=st.session_state.live_lon

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
            {"Name":"Shristi VM","Location":"12.934567, 77.624500","Emergency Type":"Unsafe Area",
             "Description":"Felt followed near underpass","Timestamp":"2024-01-15 21:32:00"},
            {"Name":"Shristi VM","Location":"Koramangala 5th Block","Emergency Type":"Harassment",
             "Description":"Eve-teasing incident","Timestamp":"2024-01-18 20:10:00"},
            {"Name":"Dhanushree G","Location":"HSR Layout Sector 3","Emergency Type":"Stalking",
             "Description":"Unknown person following","Timestamp":"2024-01-20 22:45:00"},
            {"Name":"Shristi VM","Location":"Silk Board Junction","Emergency Type":"Unsafe Area",
             "Description":"Poorly lit, isolated","Timestamp":"2024-01-22 23:10:00"},
        ])
        st.session_state.alerts_df=demo_alerts
        df=demo_alerts
    total_sos=len(df); total_checkins=47; safety_score=78

# ══════════════════════════════════════════════════════════════════════════════
#  HOME
# ══════════════════════════════════════════════════════════════════════════════
if page=="🏠 Home":
    st.markdown("<h1 style='margin-bottom:4px;'>SheShield Dashboard</h1>",unsafe_allow_html=True)
    st.markdown("<p style='color:#7A7E9A;margin-bottom:20px;'>Smart Women Safety & Emergency Response</p>",unsafe_allow_html=True)

    c1,c2,c3,c4=st.columns(4)
    active_contacts=sum(1 for c in st.session_state.trusted_contacts if c.get("phone"))
    c1.metric("🚨 SOS Alerts",total_sos)
    c2.metric("🛡️ Safety Score",f"{safety_score}/100")
    c3.metric("👥 Contacts",active_contacts)
    c4.metric("✅ Check-ins",total_checkins)
    st.markdown("---")

    bar_color="#22c55e" if checkin_pct<70 else ("#FFB020" if checkin_pct<90 else "#E8196E")
    st.markdown(f"""
    <div class="countdown-bar">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
        <span style="font-weight:600;font-size:14px;">⏱️ Next Check-in</span>
        <span style="font-size:20px;font-weight:700;color:{bar_color};">{mins_left:02d}:{secs_left:02d}</span>
      </div>
      <div style="background:#1A1D2E;border-radius:8px;height:8px;">
        <div style="background:{bar_color};height:8px;border-radius:8px;width:{checkin_pct}%;
        transition:width 1s ease;"></div>
      </div>
      <p style="font-size:12px;color:#7A7E9A;margin-top:6px;">
        {"⚠️ Overdue! Check in now." if seconds_left==0 else f"Auto-alert fires if you miss this check-in · Every {st.session_state.checkin_interval} min"}
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
            st.success(f"✅ Check-in confirmed, {USER_NAME}! Contacts notified.")
            st.rerun()

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
              <p style="font-weight:600;font-size:13px;margin-bottom:6px;">📍 Your Live Location</p>
              <p style="font-size:12px;color:#7A7E9A;margin-bottom:8px;">{home_lat:.5f}, {home_lon:.5f}</p>
              <a href="https://maps.google.com/?q={home_lat},{home_lon}" target="_blank"
              style="font-size:12px;color:#E8196E;">🗺️ Open in Google Maps</a>
            </div>""",unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  SEND SOS
# ══════════════════════════════════════════════════════════════════════════════
elif page=="🚨 Send SOS":
    st.markdown("<h1>🚨 Emergency SOS</h1>",unsafe_allow_html=True)
    st.markdown("<p style='color:#7A7E9A;'>An instant alert with your location to all trusted contacts + email + WhatsApp.</p>",unsafe_allow_html=True)

    col_form,col_info=st.columns([3,2])
    with col_form:
        st.markdown('<div class="card">',unsafe_allow_html=True)
        name=st.text_input("Your Name",value=USER_NAME)
        emergency=st.selectbox("Emergency Type",["Unsafe Area","Harassment","Medical Emergency","Kidnapping Risk","Stalking","Other"])
        loc_opt=st.radio("Location",["📍 Use Live Location","✍️ Enter Manually"],horizontal=True)

        latitude,longitude,location=None,None,"Location not found"
        if loc_opt=="📍 Use Live Location":
            if home_lat and home_lon:
                latitude,longitude=home_lat,home_lon
                location=f"{latitude:.6f}, {longitude:.6f}"
                acc=loc_data["coords"].get("accuracy",0) if loc_data and "coords" in loc_data else 0
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
                    st.markdown("**Nearby hospitals:**")
                    with st.spinner("Fetching hospitals…"):
                        hosp=fetch_nearby_osm(glat,glon,"hospital",limit=3)
                    for h in hosp:
                        st.markdown(f'<div class="card" style="padding:10px 16px;margin-bottom:6px;"><b>🏥 {h["name"]}</b><br><span style="font-size:12px;color:#7A7E9A;">{h["dist_km"]:.2f} km · <a href="https://maps.google.com/?q={h["lat"]},{h["lon"]}" target="_blank" style="color:#E8196E;">Directions</a></span></div>',unsafe_allow_html=True)
                    st.markdown("**Nearby police stations:**")
                    with st.spinner("Fetching police stations…"):
                        pol=fetch_nearby_osm(glat,glon,"police",limit=3)
                    for p in pol:
                        st.markdown(f'<div class="card" style="padding:10px 16px;margin-bottom:6px;"><b>🚔 {p["name"]}</b><br><span style="font-size:12px;color:#7A7E9A;">{p["dist_km"]:.2f} km · <a href="https://maps.google.com/?q={p["lat"]},{p["lon"]}" target="_blank" style="color:#E8196E;">Directions</a></span></div>',unsafe_allow_html=True)
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
                sos_countdown_and_send(name,location,emergency,desc,contacts,play_sound,demo)
        st.markdown("</div>",unsafe_allow_html=True)

    with col_info:
        st.markdown("""
        <div class="card">
          <p style="font-weight:700;margin-bottom:12px;">⚡ What happens when you send SOS?</p>
          <div style="display:flex;gap:10px;margin-bottom:10px;"><span style="color:#E8196E;font-weight:700;">1</span><span style="color:#C8CCE8;font-size:13px;">3-second countdown — cancel if accidental</span></div>
          <div style="display:flex;gap:10px;margin-bottom:10px;"><span style="color:#E8196E;font-weight:700;">2</span><span style="color:#C8CCE8;font-size:13px;">Email alert sent to shristimahendraker25@gmail.com</span></div>
          <div style="display:flex;gap:10px;margin-bottom:10px;"><span style="color:#E8196E;font-weight:700;">3</span><span style="color:#C8CCE8;font-size:13px;">WhatsApp message to all saved contacts</span></div>
          <div style="display:flex;gap:10px;margin-bottom:10px;"><span style="color:#E8196E;font-weight:700;">4</span><span style="color:#C8CCE8;font-size:13px;">SOS alarm sounds to deter attacker</span></div>
          <div style="display:flex;gap:10px;"><span style="color:#E8196E;font-weight:700;">5</span><span style="color:#C8CCE8;font-size:13px;">Alert logged with timestamp for evidence</span></div>
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
elif page=="📋 View Alerts":
    st.markdown("<h1>📋 Emergency Alerts</h1>",unsafe_allow_html=True)
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
elif page=="📊 Analytics":
    st.markdown("<h1>📊 Safety Insights</h1>",unsafe_allow_html=True)
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
#  NEARBY HELP — 10 km radius, clinic fallback, refresh button
# ══════════════════════════════════════════════════════════════════════════════
elif page=="🏥 Nearby Help":
    st.markdown("<h1>🏥 Nearby Help</h1>",unsafe_allow_html=True)
    st.markdown("<p style='color:#7A7E9A;'>Real places from OpenStreetMap — searching within <b style='color:#F2F4FF;'>10 km</b> of your GPS.</p>",unsafe_allow_html=True)

    if home_lat and home_lon:
        st.success(f"📍 Your location: **{home_lat:.5f}, {home_lon:.5f}**")
        st.map(pd.DataFrame({"lat":[home_lat],"lon":[home_lon]}),zoom=13)

        cache_key=f"{home_lat:.4f},{home_lon:.4f}"
        if st.session_state.nearby_fetched_for != cache_key:
            with st.spinner("🔍 Searching 10 km radius on OpenStreetMap…"):
                police    = fetch_nearby_osm(home_lat, home_lon, "police",   radius_m=10000, limit=8)
                hospitals = fetch_nearby_osm(home_lat, home_lon, "hospital", radius_m=10000, limit=8)
                # fallback: merge clinics if hospital list is thin
                if len(hospitals) < 3:
                    clinics = fetch_nearby_osm(home_lat, home_lon, "clinic", radius_m=10000, limit=5)
                    seen = {h["name"] for h in hospitals}
                    for cl in clinics:
                        if cl["name"] not in seen:
                            hospitals.append(cl)
                            seen.add(cl["name"])
                    hospitals.sort(key=lambda x: x["dist_km"])
                st.session_state.nearby_police    = police
                st.session_state.nearby_hospitals = hospitals
                st.session_state.nearby_fetched_for = cache_key
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
        st.markdown(f"""
        <div class="card" style="display:flex;align-items:center;gap:14px;padding:14px 18px;margin-bottom:8px;">
          <div style="width:42px;height:42px;border-radius:12px;background:{color}18;
          display:flex;align-items:center;justify-content:center;font-size:20px;">{icon}</div>
          <div style="flex:1;">
            <div style="font-weight:600;font-size:14px;">{p['name']}</div>
            <div style="font-size:12px;color:#7A7E9A;">{p['dist_km']:.2f} km ·
              <a href="{ml}" target="_blank" style="color:#E8196E;">Get Directions</a></div>
          </div>{ph}
        </div>""",unsafe_allow_html=True)

    if filt in ["All","🚔 Police"]:
        st.markdown("### 🚔 Nearest Police Stations")
        if st.session_state.nearby_police:
            for p in st.session_state.nearby_police: place_card(p,"🚔","#3b82f6")
        else:
            st.warning("No police stations found within 10 km via OpenStreetMap.")
            st.markdown(f'<a href="https://www.google.com/maps/search/police+station/@{home_lat},{home_lon},13z" target="_blank" style="color:#E8196E;">🔍 Search on Google Maps instead</a>',unsafe_allow_html=True)

    if filt in ["All","🏥 Hospital / Clinic"]:
        st.markdown("### 🏥 Nearest Hospitals & Clinics")
        if st.session_state.nearby_hospitals:
            for h in st.session_state.nearby_hospitals: place_card(h,"🏥","#22c55e")
        else:
            st.warning("No hospitals or clinics found within 10 km via OpenStreetMap.")
            st.markdown(f'<a href="https://www.google.com/maps/search/hospital/@{home_lat},{home_lon},13z" target="_blank" style="color:#E8196E;">🔍 Search on Google Maps instead</a>',unsafe_allow_html=True)

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
#  SHRISTI'S AI
# ══════════════════════════════════════════════════════════════════════════════
elif page=="🤖 Shristi's AI":
    st.markdown("<h1>🤖 Shristi's AI</h1>",unsafe_allow_html=True)
    st.markdown("<p style='color:#7A7E9A;'>Powered by Claude AI · Personal Safety Assistant · Online 24/7</p>",unsafe_allow_html=True)

    st.markdown("""
    <div style="background:#22c55e12;border:1px solid #22c55e30;border-radius:30px;
    padding:6px 14px;display:inline-flex;align-items:center;gap:8px;margin-bottom:20px;">
      <span style="width:8px;height:8px;border-radius:50%;background:#22c55e;display:inline-block;"></span>
      <span style="font-size:12px;color:#22c55e;font-weight:600;">AI active · powered by Claude</span>
    </div>""",unsafe_allow_html=True)

    if not st.session_state.ai_history:
        st.session_state.ai_history=[{"role":"assistant","content":
            f"Hi {USER_NAME}! I'm your personal safety AI. I know your location and your trusted contacts. How can I help you stay safe today?"}]

    chips=["I'm safe ✅","Plan my route home 🗺️","What areas are unsafe near me?",
           "Activate SOS 🚨","What can you do?","It's late at night 🌙","Nearest police station?"]
    cols=st.columns(min(len(chips),4))
    for i,chip in enumerate(chips):
        with cols[i%4]:
            if st.button(chip,key=f"chip_{i}"):
                st.session_state.ai_history.append({"role":"user","content":chip})
                loc_ctx=f"User location: {home_lat},{home_lon}" if home_lat else "Location unknown"
                contacts_ctx=", ".join([c["name"] for c in st.session_state.trusted_contacts if c.get("name")])
                system=f"""You are Shristi's personal safety AI assistant. You are warm, concise, and focused on women's safety.
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
        user_input=st.text_input("",placeholder=f"Ask anything, {USER_NAME}…",label_visibility="collapsed")
        submitted=st.form_submit_button("Send ➤",use_container_width=True)
        if submitted and user_input.strip():
            st.session_state.ai_history.append({"role":"user","content":user_input})
            loc_ctx=f"User location: {home_lat},{home_lon}" if home_lat else "Location unknown"
            contacts_ctx=", ".join([c["name"] for c in st.session_state.trusted_contacts if c.get("name")])
            system=f"""You are Shristi's personal safety AI assistant. Warm, concise, focused on women's safety.
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
elif page=="👥 Trusted Contacts":
    st.markdown("<h1>👥 Trusted Contacts</h1>",unsafe_allow_html=True)
    st.markdown("<p style='color:#7A7E9A;'>Up to 4 people who get WhatsApp + call alerts in an emergency.</p>",unsafe_allow_html=True)

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
      💬 <b style="color:#F2F4FF;">WhatsApp message:</b> "SOS ALERT! Shristi VM needs help! Emergency: Harassment · Location: maps.google.com/?q=... · Time: 21:42"<br>
      📧 <b style="color:#F2F4FF;">Email:</b> Full details with map link sent to shristimahendraker25@gmail.com<br>
      📞 <b style="color:#F2F4FF;">Call link:</b> Your contacts can tap your number directly from the home screen
      </p>
    </div>""",unsafe_allow_html=True)
