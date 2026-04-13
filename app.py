from flask import Flask, jsonify, request, Response, session, redirect, url_for
from flask_cors import CORS
import sqlite3
import random
import string
import hashlib
import time
from datetime import datetime, timedelta
import json
import os
import secrets
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))
CORS(app, origins=["*"])  # Allow all origins including Vercel

DB_PATH = "chainvista.db"

# DATABASE SETUP


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.executescript("""
        CREATE TABLE IF NOT EXISTS shipments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shipment_no TEXT UNIQUE,
            product TEXT,
            origin TEXT,
            destination TEXT,
            current_location TEXT,
            status TEXT,
            temperature REAL,
            humidity REAL,
            lat REAL,
            lng REAL,
            carrier TEXT,
            eta TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT,
            title TEXT,
            message TEXT,
            shipment_ref TEXT,
            resolved INTEGER DEFAULT 0,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS blockchain_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT,
            tx_hash TEXT,
            status TEXT,
            gas_used INTEGER,
            block_number INTEGER,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS passports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            passport_id TEXT UNIQUE,
            product_name TEXT,
            origin TEXT,
            destination TEXT,
            manufacturer TEXT,
            batch_no TEXT,
            verified INTEGER DEFAULT 0,
            nft_minted INTEGER DEFAULT 0,
            nft_token_id TEXT,
            data_hash TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS iot_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT,
            device_type TEXT,
            temperature REAL,
            humidity REAL,
            pressure REAL,
            battery REAL,
            timestamp TEXT
        );

        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT UNIQUE,
            device_type TEXT,
            location TEXT,
            status TEXT,
            last_seen TEXT
        );

        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT,
            provider TEXT DEFAULT 'local',
            provider_id TEXT,
            role TEXT DEFAULT 'user',
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS otp_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            otp TEXT NOT NULL,
            purpose TEXT DEFAULT 'login',
            expires_at TEXT NOT NULL,
            used INTEGER DEFAULT 0,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS marketplace_listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seller_name TEXT,
            seller_email TEXT,
            title TEXT NOT NULL,
            description TEXT,
            category TEXT,
            price REAL NOT NULL,
            unit TEXT DEFAULT 'unit',
            stock INTEGER DEFAULT 1,
            location TEXT,
            image_emoji TEXT DEFAULT '📦',
            tags TEXT,
            rating REAL DEFAULT 0,
            review_count INTEGER DEFAULT 0,
            verified INTEGER DEFAULT 0,
            active INTEGER DEFAULT 1,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS marketplace_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            buyer_email TEXT NOT NULL,
            listing_id INTEGER NOT NULL,
            quantity INTEGER DEFAULT 1,
            total_price REAL,
            status TEXT DEFAULT 'Pending',
            note TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS marketplace_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            listing_id INTEGER NOT NULL,
            reviewer_email TEXT,
            reviewer_name TEXT,
            rating INTEGER NOT NULL,
            comment TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS marketplace_cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            buyer_email TEXT NOT NULL,
            listing_id INTEGER NOT NULL,
            quantity INTEGER DEFAULT 1,
            added_at TEXT
        );
    """)

    # Seed shipments
    c.execute("SELECT COUNT(*) FROM shipments")
    if c.fetchone()[0] == 0:
        shipments = [
            ("SHP-1023", "Pharmaceutical Batch A", "Chennai", "Delhi", "Agra",
             "In Transit", 4.2, 57.5, 27.1767, 78.0081, "FastCargo India", "2026-03-21", datetime.now().isoformat()),
            ("SHP-1024", "Electronic Components", "Pune", "Mumbai", "Thane",
             "Delayed", 28.2, 62.1, 19.2183, 72.9781, "BlueDart", "2026-03-23", datetime.now().isoformat()),
            ("SHP-1025", "Organic Produce", "Bangalore", "Hyderabad", "Hyderabad",
             "Delivered", 8.0, 75.0, 17.3850, 78.4867, "Delhivery", "2026-03-20", (datetime.now()-timedelta(days=1)).isoformat()),
            ("SHP-1026", "Auto Parts", "Kolkata", "Nagpur", "Raipur",
             "In Transit", 25.1, 50.2, 21.2514, 81.6296, "DTDC", "2026-03-22", datetime.now().isoformat()),
            ("SHP-1027", "Luxury Textiles", "Surat", "Jaipur", "Ahmedabad",
             "Processing", 22.5, 45.0, 23.0225, 72.5714, "Ekart", "2026-03-24", datetime.now().isoformat()),
            ("SHP-1028", "Cold Chain Vaccines", "Mumbai", "Patna", "Bhopal",
             "In Transit", 2.8, 68.0, 23.2599, 77.4126, "ColdEx Logistics", "2026-03-22", datetime.now().isoformat()),
            ("SHP-1029", "Industrial Machinery", "Delhi", "Bangalore", "Nagpur",
             "In Transit", 31.4, 43.0, 21.1458, 79.0882, "VRL Logistics", "2026-03-25", datetime.now().isoformat()),
            ("SHP-1030", "Fresh Seafood", "Kochi", "Chennai", "Coimbatore",
             "Delayed", 1.5, 82.0, 11.0168, 76.9558, "Snowman Logistics", "2026-03-21", datetime.now().isoformat()),
            ("SHP-1031", "Defence Equipment", "Hyderabad", "Chandigarh", "Indore",
             "In Transit", 26.0, 38.5, 22.7196, 75.8577, "SafeFreight", "2026-03-26", datetime.now().isoformat()),
            ("SHP-1032", "IT Hardware", "Bangalore", "Kolkata", "Visakhapatnam",
             "Processing", 24.5, 52.0, 17.6868, 83.2185, "DHL India", "2026-03-27", datetime.now().isoformat()),
            ("SHP-1033", "Chemical Reagents", "Vadodara", "Chennai", "Hyderabad",
             "In Transit", 18.3, 55.0, 17.3850, 78.4867, "Gati KWE", "2026-03-24", datetime.now().isoformat()),
            ("SHP-1034", "Frozen Goods", "Amritsar", "Delhi", "Ludhiana",
             "Delivered", -3.2, 90.0, 30.9010, 75.8573, "Refrigerated Lines", "2026-03-19", datetime.now().isoformat()),
        ]
        c.executemany("""INSERT INTO shipments
            (shipment_no,product,origin,destination,current_location,status,temperature,
             humidity,lat,lng,carrier,eta,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""", shipments)

    # Seed alerts
    c.execute("SELECT COUNT(*) FROM alerts")
    if c.fetchone()[0] == 0:
        alerts = [
            ("High Alert", "Temperature Breach", "Temperature exceeded threshold in Warehouse A.", "SHP-1023", 0, datetime.now().isoformat()),
            ("Warning", "Humidity Fluctuation", "Humidity fluctuation detected in Shipment #1023.", "SHP-1023", 0, datetime.now().isoformat()),
            ("Warning", "Shipment Delay", "Shipment #1024 delayed due to customs hold.", "SHP-1024", 0, (datetime.now()-timedelta(hours=2)).isoformat()),
            ("Info", "New Device Connected", "IoT-Node-047 registered and transmitting data.", None, 0, (datetime.now()-timedelta(hours=4)).isoformat()),
            ("Info", "Passport Verified", "Blockchain verification successful for SHP-1025.", "SHP-1025", 1, (datetime.now()-timedelta(hours=6)).isoformat()),
        ]
        c.executemany("INSERT INTO alerts (level,title,message,shipment_ref,resolved,created_at) VALUES (?,?,?,?,?,?)", alerts)

    # Seed blockchain activity
    c.execute("SELECT COUNT(*) FROM blockchain_activity")
    if c.fetchone()[0] == 0:
        activities = [
            ("Passport Issued", "0x57ab3e...e912", "Success", 21000, 19284761, datetime.now().isoformat()),
            ("Passport Updated", "0x21fa9c...bb41", "Confirmed", 18500, 19284799, datetime.now().isoformat()),
            ("NFT Minted", "0x82ff1a...1a7d", "Success", 65000, 19284812, datetime.now().isoformat()),
            ("Data Verified", "0x3ad7bc...44f1", "Success", 12000, 19284830, (datetime.now()-timedelta(hours=1)).isoformat()),
            ("Passport Issued", "0x99de12...c3a0", "Pending", 21000, 19284841, (datetime.now()-timedelta(minutes=30)).isoformat()),
        ]
        c.executemany("INSERT INTO blockchain_activity (action,tx_hash,status,gas_used,block_number,created_at) VALUES (?,?,?,?,?,?)", activities)

    # Seed IoT readings (last 7 days)
    c.execute("SELECT COUNT(*) FROM iot_readings")
    if c.fetchone()[0] == 0:
        devices = [("DEV-001","temperature"), ("DEV-002","humidity"), ("DEV-003","multi")]
        base_temps = [24.1, 25.5, 22.8, 26.0, 23.5, 25.1, 24.8]
        base_hums  = [55.0, 57.5, 60.2, 58.0, 56.8, 61.0, 59.3]
        for dev_id, dev_type in devices:
            for i in range(7):
                ts = (datetime.now() - timedelta(days=6-i)).isoformat()
                c.execute("""INSERT INTO iot_readings
                    (device_id,device_type,temperature,humidity,pressure,battery,timestamp)
                    VALUES (?,?,?,?,?,?,?)""",
                    (dev_id, dev_type,
                     round(base_temps[i] + random.uniform(-1, 1), 1),
                     round(base_hums[i] + random.uniform(-2, 2), 1),
                     round(1013 + random.uniform(-5, 5), 1),
                     round(random.uniform(60, 100), 0),
                     ts))

    # Seed devices
    c.execute("SELECT COUNT(*) FROM devices")
    if c.fetchone()[0] == 0:
        devices_list = [
            ("DEV-001", "Temperature Sensor", "Warehouse A", "Online", datetime.now().isoformat()),
            ("DEV-002", "Humidity Sensor", "Warehouse B", "Online", datetime.now().isoformat()),
            ("DEV-003", "Multi Sensor", "Transit Hub", "Online", datetime.now().isoformat()),
            ("DEV-004", "GPS Tracker", "Shipment 1023", "Online", datetime.now().isoformat()),
            ("DEV-005", "Temperature Sensor", "Cold Storage", "Offline", (datetime.now()-timedelta(hours=3)).isoformat()),
        ]
        c.executemany("INSERT INTO devices (device_id,device_type,location,status,last_seen) VALUES (?,?,?,?,?)", devices_list)

    seed_marketplace(c)
    conn.commit()
    conn.close()

def gen_tx_hash():
    return "0x" + ''.join(random.choices(string.hexdigits.lower(), k=8)) + "..." + ''.join(random.choices(string.hexdigits.lower(), k=4))

# ─────────────────────────────────────────
# AUTH HELPERS
# ─────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user"):
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated

def get_user_by_email(email):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    conn.close()
    return dict(row) if row else None

def create_user(name, email, password_hash, provider="local", provider_id=None):
    conn = get_db()
    conn.execute(
        "INSERT INTO users (name,email,password_hash,provider,provider_id,created_at) VALUES (?,?,?,?,?,?)",
        (name, email, password_hash, provider, provider_id, datetime.now().isoformat())
    )
    conn.commit()
    user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    conn.close()
    return dict(user)


# ─────────────────────────────────────────
# AUTH API ROUTES
# ─────────────────────────────────────────

@app.route("/api/auth/register", methods=["POST"])
def auth_register():
    d = request.json or {}
    name     = (d.get("name") or "").strip()
    email    = (d.get("email") or "").strip().lower()
    password = d.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters."}), 400
    if get_user_by_email(email):
        return jsonify({"error": "An account with this email already exists."}), 409

    pw_hash = generate_password_hash(password)
    user = create_user(name or email.split("@")[0], email, pw_hash)
    session["user"] = {"id": user["id"], "name": user["name"], "email": user["email"], "provider": "local"}
    return jsonify({"success": True, "user": session["user"]}), 201


@app.route("/api/auth/login", methods=["POST"])
def auth_login():
    d = request.json or {}
    email    = (d.get("email") or "").strip().lower()
    password = d.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    user = get_user_by_email(email)
    if not user or not user.get("password_hash"):
        return jsonify({"error": "Invalid email or password."}), 401
    if not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid email or password."}), 401

    session["user"] = {"id": user["id"], "name": user["name"], "email": user["email"], "provider": "local"}
    return jsonify({"success": True, "user": session["user"]})


@app.route("/api/auth/demo", methods=["POST"])
def auth_demo():
    """Instant demo session — no credentials needed."""
    session["user"] = {
        "id": 0,
        "name": "Demo User",
        "email": "demo@chainvista.app",
        "provider": "demo"
    }
    return jsonify({"success": True, "user": session["user"]})


@app.route("/api/auth/logout", methods=["POST"])
@app.route("/logout")
def auth_logout():
    session.clear()
    return redirect("/login")


@app.route("/api/auth/me")
def auth_me():
    user = session.get("user")
    if not user:
        return jsonify({"authenticated": False}), 401
    return jsonify({"authenticated": True, "user": user})


# ─────────────────────────────────────────
# OTP SYSTEM
# ─────────────────────────────────────────

import smtplib
import random as _random
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

SMTP_HOST   = os.environ.get("SMTP_HOST",   "smtp.gmail.com")
SMTP_PORT   = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER   = os.environ.get("SMTP_USER",   "")   # your Gmail address
SMTP_PASS   = os.environ.get("SMTP_PASS",   "")   # Gmail App Password
OTP_TTL_MIN = int(os.environ.get("OTP_TTL_MIN", "10"))


def _generate_otp(length=6):
    return str(_random.randint(10**(length-1), 10**length - 1))


def _save_otp(email, otp, purpose="login"):
    """Store OTP in DB; invalidate any previous unused OTPs for same email+purpose."""
    expires = (datetime.now() + timedelta(minutes=OTP_TTL_MIN)).isoformat()
    conn = get_db()
    conn.execute(
        "UPDATE otp_tokens SET used=1 WHERE email=? AND purpose=? AND used=0",
        (email, purpose)
    )
    conn.execute(
        "INSERT INTO otp_tokens (email, otp, purpose, expires_at, used, created_at) VALUES (?,?,?,?,0,?)",
        (email, otp, purpose, expires, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def _verify_otp_db(email, otp, purpose="login"):
    """Returns True and marks used if OTP is valid, unexpired, unused."""
    conn = get_db()
    row = conn.execute(
        """SELECT id, expires_at FROM otp_tokens
           WHERE email=? AND otp=? AND purpose=? AND used=0
           ORDER BY id DESC LIMIT 1""",
        (email, otp, purpose)
    ).fetchone()
    if not row:
        conn.close()
        return False, "Invalid OTP."
    if datetime.fromisoformat(row["expires_at"]) < datetime.now():
        conn.close()
        return False, "OTP has expired. Please request a new one."
    conn.execute("UPDATE otp_tokens SET used=1 WHERE id=?", (row["id"],))
    conn.commit()
    conn.close()
    return True, "OK"


def _send_otp_email(to_email, otp, purpose="login"):
    """Send a beautiful HTML OTP email. Falls back gracefully if SMTP not configured."""
    if not SMTP_USER or not SMTP_PASS:
        # Dev mode: just print to console
        print(f"\n{'='*50}")
        print(f"  [DEV MODE] OTP for {to_email}")
        print(f"  Purpose : {purpose}")
        print(f"  OTP Code: {otp}")
        print(f"  Expires : {OTP_TTL_MIN} minutes")
        print(f"{'='*50}\n")
        return True, "dev"

    subject_map = {
        "login":    "Your ChainVista sign-in code",
        "register": "Verify your ChainVista account",
        "reset":    "Reset your ChainVista password",
    }
    subject = subject_map.get(purpose, "Your ChainVista OTP")

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"/></head>
<body style="margin:0;padding:0;background:#08080f;font-family:'Segoe UI',sans-serif">
<table width="100%" cellpadding="0" cellspacing="0">
  <tr><td align="center" style="padding:48px 20px">
    <table width="480" cellpadding="0" cellspacing="0"
      style="background:#12122a;border-radius:16px;border:1px solid rgba(124,58,237,.25);overflow:hidden">
      <!-- Header -->
      <tr><td style="background:linear-gradient(135deg,#7c3aed,#e91e8c);padding:32px 40px;text-align:center">
        <div style="font-size:28px;margin-bottom:8px">⛓️</div>
        <div style="font-family:'Segoe UI',sans-serif;font-size:22px;font-weight:700;color:#fff;letter-spacing:-.5px">ChainVista</div>
        <div style="font-size:12px;color:rgba(255,255,255,.7);margin-top:4px;letter-spacing:.15em;text-transform:uppercase">Supply Chain Intelligence</div>
      </td></tr>
      <!-- Body -->
      <tr><td style="padding:40px">
        <p style="color:#9090b8;font-size:14px;margin:0 0 24px">
          {"Use the code below to sign in to your account." if purpose=="login" else
           "Use the code below to verify your email address." if purpose=="register" else
           "Use the code below to reset your password."}
        </p>
        <!-- OTP Box -->
        <div style="background:#08080f;border:1px solid rgba(124,58,237,.3);border-radius:12px;padding:28px;text-align:center;margin-bottom:24px">
          <div style="font-size:11px;color:#5a5a8a;letter-spacing:.15em;text-transform:uppercase;margin-bottom:12px">Your one-time code</div>
          <div style="font-size:42px;font-weight:800;letter-spacing:.2em;
                      background:linear-gradient(135deg,#e91e8c,#9d5cf6);
                      -webkit-background-clip:text;-webkit-text-fill-color:transparent">{otp}</div>
          <div style="font-size:12px;color:#5a5a8a;margin-top:12px">Valid for {OTP_TTL_MIN} minutes · Do not share this code</div>
        </div>
        <p style="color:#5a5a8a;font-size:12px;line-height:1.6;margin:0">
          If you did not request this code, you can safely ignore this email.
          Your account will remain secure.
        </p>
      </td></tr>
      <!-- Footer -->
      <tr><td style="padding:20px 40px;border-top:1px solid rgba(124,58,237,.12);text-align:center">
        <p style="color:#3a3a5a;font-size:11px;margin:0">© ChainVista · Real-Time Supply Intelligence</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body></html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"ChainVista <{SMTP_USER}>"
    msg["To"]      = to_email
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as srv:
            srv.ehlo(); srv.starttls(); srv.ehlo()
            srv.login(SMTP_USER, SMTP_PASS)
            srv.sendmail(SMTP_USER, to_email, msg.as_string())
        return True, "sent"
    except Exception as exc:
        return False, str(exc)


# ── OTP API endpoints ─────────────────────

@app.route("/api/auth/otp/send", methods=["POST"])
def otp_send():
    """Send OTP to email. Purpose: login | register | reset."""
    d       = request.json or {}
    email   = (d.get("email") or "").strip().lower()
    purpose = d.get("purpose", "login")

    if not email:
        return jsonify({"error": "Email is required."}), 400
    if purpose not in ("login", "register", "reset"):
        return jsonify({"error": "Invalid purpose."}), 400

    # For login OTP: email must already exist
    if purpose == "login":
        if not get_user_by_email(email):
            return jsonify({"error": "No account found with this email."}), 404

    otp = _generate_otp(6)
    _save_otp(email, otp, purpose)
    ok, detail = _send_otp_email(email, otp, purpose)

    if not ok:
        return jsonify({"error": f"Failed to send email: {detail}"}), 500

    mode = "console (dev mode)" if detail == "dev" else "email"
    return jsonify({"success": True, "message": f"OTP sent via {mode}.", "dev": detail == "dev"})


@app.route("/api/auth/otp/verify", methods=["POST"])
def otp_verify():
    """Verify OTP and log the user in (or mark email as verified for register)."""
    d       = request.json or {}
    email   = (d.get("email") or "").strip().lower()
    otp     = (d.get("otp")   or "").strip()
    purpose = d.get("purpose", "login")
    name    = (d.get("name")  or "").strip()

    if not email or not otp:
        return jsonify({"error": "Email and OTP are required."}), 400

    valid, msg = _verify_otp_db(email, otp, purpose)
    if not valid:
        return jsonify({"error": msg}), 401

    # ── Purposes ──────────────────────────
    if purpose == "login":
        user = get_user_by_email(email)
        if not user:
            return jsonify({"error": "Account not found."}), 404
        session["user"] = {"id": user["id"], "name": user["name"],
                           "email": email, "provider": "otp"}
        return jsonify({"success": True, "user": session["user"]})

    elif purpose == "register":
        existing = get_user_by_email(email)
        if existing:
            # Email already registered — just sign them in
            session["user"] = {"id": existing["id"], "name": existing["name"],
                                "email": email, "provider": "otp"}
        else:
            user = create_user(name or email.split("@")[0], email,
                               None, provider="otp")
            session["user"] = {"id": user["id"], "name": user["name"],
                                "email": email, "provider": "otp"}
        return jsonify({"success": True, "user": session["user"]})

    elif purpose == "reset":
        # Return a short-lived reset token in session; frontend will POST new password
        session["pwd_reset_email"] = email
        return jsonify({"success": True, "message": "OTP verified. Proceed to set new password."})

    return jsonify({"error": "Unknown purpose."}), 400


@app.route("/api/auth/otp/reset-password", methods=["POST"])
def otp_reset_password():
    """Set a new password after OTP verification for reset flow."""
    email = session.pop("pwd_reset_email", None)
    if not email:
        return jsonify({"error": "No pending password reset. Please verify OTP first."}), 403

    d        = request.json or {}
    password = d.get("password", "")
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters."}), 400

    conn = get_db()
    conn.execute("UPDATE users SET password_hash=? WHERE email=?",
                 (generate_password_hash(password), email))
    conn.commit()
    user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    conn.close()

    if not user:
        return jsonify({"error": "Account not found."}), 404

    session["user"] = {"id": user["id"], "name": user["name"],
                       "email": email, "provider": "local"}
    return jsonify({"success": True, "message": "Password updated. Signed in.",
                    "user": session["user"]})


# ── Google OAuth ────────────────────────
GOOGLE_CLIENT_ID     = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

@app.route("/auth/google")
def auth_google():
    if not GOOGLE_CLIENT_ID:
        return """<script>alert('Google OAuth not configured.\\nSet GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET env vars on Render.');window.location='/login';</script>"""
    import urllib.parse
    params = urllib.parse.urlencode({
        "client_id":     GOOGLE_CLIENT_ID,
        "redirect_uri":  _callback_url("google"),
        "response_type": "code",
        "scope":         "openid email profile",
        "state":         secrets.token_urlsafe(16),
    })
    return redirect(f"https://accounts.google.com/o/oauth2/v2/auth?{params}")

@app.route("/auth/google/callback")
def auth_google_callback():
    import urllib.parse, urllib.request
    code = request.args.get("code")
    if not code:
        return redirect("/login")
    try:
        token_data = urllib.parse.urlencode({
            "code":          code,
            "client_id":     GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri":  _callback_url("google"),
            "grant_type":    "authorization_code",
        }).encode()
        req = urllib.request.Request("https://oauth2.googleapis.com/token",
                                     data=token_data,
                                     headers={"Content-Type": "application/x-www-form-urlencoded"})
        token_resp = json.loads(urllib.request.urlopen(req).read())
        access_token = token_resp["access_token"]

        user_req = urllib.request.Request(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        info = json.loads(urllib.request.urlopen(user_req).read())
        email = info.get("email", "").lower()
        name  = info.get("name") or email.split("@")[0]
        gid   = info.get("id")

        user = get_user_by_email(email)
        if not user:
            user = create_user(name, email, None, provider="google", provider_id=gid)
        session["user"] = {"id": user["id"], "name": user["name"], "email": email, "provider": "google"}
        return redirect("/")
    except Exception as exc:
        return redirect(f"/login?error={str(exc)}")


# ── GitHub OAuth ─────────────────────────
GITHUB_CLIENT_ID     = os.environ.get("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET", "")

@app.route("/auth/github")
def auth_github():
    if not GITHUB_CLIENT_ID:
        return """<script>alert('GitHub OAuth not configured.\\nSet GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET env vars on Render.');window.location='/login';</script>"""
    import urllib.parse
    params = urllib.parse.urlencode({
        "client_id":    GITHUB_CLIENT_ID,
        "redirect_uri": _callback_url("github"),
        "scope":        "user:email",
        "state":        secrets.token_urlsafe(16),
    })
    return redirect(f"https://github.com/login/oauth/authorize?{params}")

@app.route("/auth/github/callback")
def auth_github_callback():
    import urllib.parse, urllib.request
    code = request.args.get("code")
    if not code:
        return redirect("/login")
    try:
        token_data = urllib.parse.urlencode({
            "client_id":     GITHUB_CLIENT_ID,
            "client_secret": GITHUB_CLIENT_SECRET,
            "code":          code,
            "redirect_uri":  _callback_url("github"),
        }).encode()
        req = urllib.request.Request("https://github.com/login/oauth/access_token",
                                     data=token_data,
                                     headers={"Accept": "application/json",
                                              "Content-Type": "application/x-www-form-urlencoded"})
        token_resp = json.loads(urllib.request.urlopen(req).read())
        access_token = token_resp.get("access_token")

        user_req = urllib.request.Request(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}", "User-Agent": "ChainVista"}
        )
        info = json.loads(urllib.request.urlopen(user_req).read())

        # Get primary email if not public
        email = info.get("email")
        if not email:
            email_req = urllib.request.Request(
                "https://api.github.com/user/emails",
                headers={"Authorization": f"Bearer {access_token}", "User-Agent": "ChainVista"}
            )
            emails = json.loads(urllib.request.urlopen(email_req).read())
            primary = next((e for e in emails if e.get("primary") and e.get("verified")), None)
            email = primary["email"] if primary else f"gh_{info['id']}@github.com"

        email = email.lower()
        name  = info.get("name") or info.get("login") or email.split("@")[0]
        ghid  = str(info.get("id"))

        user = get_user_by_email(email)
        if not user:
            user = create_user(name, email, None, provider="github", provider_id=ghid)
        session["user"] = {"id": user["id"], "name": user["name"], "email": email, "provider": "github"}
        return redirect("/")
    except Exception as exc:
        return redirect(f"/login?error={str(exc)}")


def _callback_url(provider):
    base = os.environ.get("APP_URL", "http://localhost:5000")
    return f"{base}/auth/{provider}/callback"


# ─────────────────────────────────────────
# FRONTEND SERVE
# ─────────────────────────────────────────

@app.route("/login")
def login_page():
    if session.get("user"):
        return redirect("/")
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "login.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return Response(f.read(), mimetype="text/html")


@app.route("/")
@app.route("/index")
@login_required
def index():
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return Response(f.read(), mimetype="text/html")


# DASHBOARD API


@app.route("/api/dashboard")
def dashboard():
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT AVG(temperature) as temp, AVG(humidity) as hum FROM iot_readings WHERE timestamp > ?",
              ((datetime.now() - timedelta(hours=1)).isoformat(),))
    row = c.fetchone()
    temp = round(row["temp"] or 25.5, 1)
    hum  = round(row["hum"]  or 57.5, 1)

    c.execute("SELECT COUNT(*) as cnt FROM devices WHERE status='Online'")
    devices_online = c.fetchone()["cnt"]

    c.execute("SELECT COUNT(*) as cnt FROM passports WHERE verified=1")
    rep_score = c.fetchone()["cnt"]

    conn.close()
    return jsonify({
        "wallet":   "0x03b6...a720",
        "network":  "mainnet",
        "contract": "0x2486651A...",
        "temperature": temp,
        "humidity":    hum,
        "devices_online": devices_online,
        "reputation_score": rep_score,
        "block_height": random.randint(19284000, 19285000)
    })

@app.route("/api/iot/trends")
def iot_trends():
    conn = get_db()
    c = conn.cursor()
    rows = c.execute("""
        SELECT DATE(timestamp) as day, AVG(temperature) as temp, AVG(humidity) as hum
        FROM iot_readings
        GROUP BY DATE(timestamp)
        ORDER BY day DESC LIMIT 7
    """).fetchall()
    conn.close()
    labels = [r["day"] for r in reversed(rows)]
    temps  = [round(r["temp"], 1) for r in reversed(rows)]
    hums   = [round(r["hum"],  1) for r in reversed(rows)]
    return jsonify({"labels": labels, "temperature": temps, "humidity": hums})

@app.route("/api/iot/live")
def iot_live():
    """Returns a fresh simulated reading (call every few seconds)."""
    return jsonify({
        "temperature": round(random.uniform(22, 30), 1),
        "humidity":    round(random.uniform(50, 70), 1),
        "pressure":    round(random.uniform(1008, 1018), 1),
        "timestamp":   datetime.now().isoformat()
    })

@app.route("/api/sensor/distribution")
def sensor_distribution():
    conn = get_db()
    c = conn.cursor()
    rows = c.execute("SELECT device_type, COUNT(*) as cnt FROM devices GROUP BY device_type").fetchall()
    conn.close()
    return jsonify([{"type": r["device_type"], "count": r["cnt"]} for r in rows])


# SHIPMENTS API

@app.route("/api/shipments")
def get_shipments():
    conn = get_db()
    rows = conn.execute("SELECT * FROM shipments ORDER BY created_at DESC").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/shipments/<int:sid>")
def get_shipment(sid):
    conn = get_db()
    row = conn.execute("SELECT * FROM shipments WHERE id=?", (sid,)).fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Not found"}), 404
    return jsonify(dict(row))

@app.route("/api/shipments", methods=["POST"])
def create_shipment():
    d = request.json
    shipment_no = "SHP-" + str(random.randint(1100, 9999))
    conn = get_db()
    conn.execute("""INSERT INTO shipments
        (shipment_no,product,origin,destination,current_location,status,
         temperature,humidity,lat,lng,carrier,eta,created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (shipment_no, d.get("product","Unknown"),
         d.get("origin","Unknown"), d.get("destination","Unknown"),
         d.get("origin","Unknown"), "Processing",
         round(random.uniform(18, 30), 1), round(random.uniform(45, 70), 1),
         d.get("lat", 20.5937), d.get("lng", 78.9629),
         d.get("carrier","ChainFreight"), d.get("eta","TBD"),
         datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "shipment_no": shipment_no}), 201

@app.route("/api/shipments/<int:sid>/status", methods=["PUT"])
def update_shipment_status(sid):
    new_status = request.json.get("status")
    conn = get_db()
    conn.execute("UPDATE shipments SET status=? WHERE id=?", (new_status, sid))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


# TRACKING API


@app.route("/api/tracking")
def tracking():
    conn = get_db()
    rows = conn.execute(
        "SELECT shipment_no, current_location, status, lat, lng FROM shipments"
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


# ALERTS API


@app.route("/api/alerts")
def get_alerts():
    show_resolved = request.args.get("resolved", "false") == "true"
    conn = get_db()
    if show_resolved:
        rows = conn.execute("SELECT * FROM alerts ORDER BY created_at DESC").fetchall()
    else:
        rows = conn.execute("SELECT * FROM alerts WHERE resolved=0 ORDER BY created_at DESC").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/alerts/<int:aid>/resolve", methods=["PUT"])
def resolve_alert(aid):
    conn = get_db()
    conn.execute("UPDATE alerts SET resolved=1 WHERE id=?", (aid,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


# ANALYTICS API


@app.route("/api/analytics/shipment-status")
def analytics_shipment_status():
    conn = get_db()
    rows = conn.execute("SELECT status, COUNT(*) as cnt FROM shipments GROUP BY status").fetchall()
    conn.close()
    return jsonify([{"status": r["status"], "count": r["cnt"]} for r in rows])

@app.route("/api/analytics/temperature-history")
def analytics_temp_history():
    conn = get_db()
    rows = conn.execute("""
        SELECT DATE(timestamp) as day, AVG(temperature) as avg_temp, MIN(temperature) as min_t, MAX(temperature) as max_t
        FROM iot_readings GROUP BY DATE(timestamp) ORDER BY day
    """).fetchall()
    conn.close()
    return jsonify([{"day": r["day"], "avg": round(r["avg_temp"],1), "min": round(r["min_t"],1), "max": round(r["max_t"],1)} for r in rows])

@app.route("/api/analytics/throughput")
def analytics_throughput():
    conn = get_db()
    rows = conn.execute("""
        SELECT DATE(created_at) as day, COUNT(*) as cnt FROM shipments
        GROUP BY DATE(created_at) ORDER BY day
    """).fetchall()
    conn.close()
    # Pad to 7 days
    result = []
    for i in range(7):
        day = (datetime.now() - timedelta(days=6-i)).strftime("%Y-%m-%d")
        found = next((r for r in rows if r["day"] == day), None)
        result.append({"day": day, "count": found["cnt"] if found else random.randint(1, 6)})
    return jsonify(result)


# BLOCKCHAIN / PASSPORT API


@app.route("/api/blockchain/activity")
def blockchain_activity():
    conn = get_db()
    rows = conn.execute("SELECT * FROM blockchain_activity ORDER BY created_at DESC LIMIT 10").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/passport/issue", methods=["POST"])
def issue_passport():
    d = request.json or {}
    pid = "PP-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    tx  = gen_tx_hash()
    data_hash = "0x" + hashlib.sha256(json.dumps(d).encode()).hexdigest()[:16]
    conn = get_db()
    conn.execute("""INSERT INTO passports
        (passport_id,product_name,origin,destination,manufacturer,batch_no,data_hash,created_at)
        VALUES (?,?,?,?,?,?,?,?)""",
        (pid, d.get("product","Unknown"), d.get("origin","Unknown"),
         d.get("destination","Unknown"), d.get("manufacturer","Unknown"),
         d.get("batch_no","BN-001"), data_hash, datetime.now().isoformat()))
    conn.execute("INSERT INTO blockchain_activity (action,tx_hash,status,gas_used,block_number,created_at) VALUES (?,?,?,?,?,?)",
                 ("Passport Issued", tx, "Success", 21000,
                  random.randint(19284000, 19285000), datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "passport_id": pid, "tx_hash": tx, "data_hash": data_hash})

@app.route("/api/passport/update", methods=["POST"])
def update_passport():
    d = request.json or {}
    pid = d.get("passport_id")
    tx  = gen_tx_hash()
    conn = get_db()
    conn.execute("UPDATE passports SET product_name=?, destination=? WHERE passport_id=?",
                 (d.get("product"), d.get("destination"), pid))
    conn.execute("INSERT INTO blockchain_activity (action,tx_hash,status,gas_used,block_number,created_at) VALUES (?,?,?,?,?,?)",
                 ("Passport Updated", tx, "Confirmed", 18500,
                  random.randint(19284000, 19285000), datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "tx_hash": tx})

@app.route("/api/passport/view")
def view_passport():
    conn = get_db()
    rows = conn.execute("SELECT * FROM passports ORDER BY created_at DESC").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/passport/verify", methods=["POST"])
def verify_passport():
    d = request.json or {}
    pid = d.get("passport_id")
    tx  = gen_tx_hash()
    conn = get_db()
    conn.execute("UPDATE passports SET verified=1 WHERE passport_id=?", (pid,))
    conn.execute("INSERT INTO blockchain_activity (action,tx_hash,status,gas_used,block_number,created_at) VALUES (?,?,?,?,?,?)",
                 ("Data Verified", tx, "Success", 12000,
                  random.randint(19284000, 19285000), datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "verified": True, "tx_hash": tx})

@app.route("/api/passport/mint", methods=["POST"])
def mint_nft():
    d = request.json or {}
    pid = d.get("passport_id")
    token_id = "NFT-#" + str(random.randint(1000, 9999))
    tx = gen_tx_hash()
    conn = get_db()
    conn.execute("UPDATE passports SET nft_minted=1, nft_token_id=? WHERE passport_id=?", (token_id, pid))
    conn.execute("INSERT INTO blockchain_activity (action,tx_hash,status,gas_used,block_number,created_at) VALUES (?,?,?,?,?,?)",
                 ("NFT Minted", tx, "Success", 65000,
                  random.randint(19284000, 19285000), datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "token_id": token_id, "tx_hash": tx})


# LIVE SHIPMENT SIMULATION ENDPOINT


# Route waypoints for each shipment (city name + lat/lng)
ROUTE_WAYPOINTS = {
    "SHP-1023": [("Chennai",13.0827,80.2707),("Nellore",14.4426,79.9865),("Vijayawada",16.5062,80.6480),("Nagpur",21.1458,79.0882),("Bhopal",23.2599,77.4126),("Gwalior",26.2183,78.1828),("Agra",27.1767,78.0081),("Delhi",28.6139,77.2090)],
    "SHP-1024": [("Pune",18.5204,73.8567),("Lonavala",18.7537,73.4062),("Thane",19.2183,72.9781),("Mumbai",19.0760,72.8777)],
    "SHP-1026": [("Kolkata",22.5726,88.3639),("Asansol",23.6833,86.9833),("Ranchi",23.3441,85.3096),("Raipur",21.2514,81.6296),("Nagpur",21.1458,79.0882)],
    "SHP-1027": [("Surat",21.1702,72.8311),("Vadodara",22.3072,73.1812),("Ahmedabad",23.0225,72.5714),("Udaipur",24.5854,73.7125),("Jaipur",26.9124,75.7873)],
    "SHP-1028": [("Mumbai",19.0760,72.8777),("Nashik",19.9975,73.7898),("Aurangabad",19.8762,75.3433),("Bhopal",23.2599,77.4126),("Jabalpur",23.1815,79.9864),("Allahabad",25.4358,81.8463),("Patna",25.5941,85.1376)],
    "SHP-1029": [("Delhi",28.6139,77.2090),("Agra",27.1767,78.0081),("Gwalior",26.2183,78.1828),("Bhopal",23.2599,77.4126),("Nagpur",21.1458,79.0882),("Hyderabad",17.3850,78.4867),("Bangalore",12.9716,77.5946)],
    "SHP-1030": [("Kochi",9.9312,76.2673),("Palakkad",10.7867,76.6548),("Coimbatore",11.0168,76.9558),("Salem",11.6643,78.1460),("Chennai",13.0827,80.2707)],
    "SHP-1031": [("Hyderabad",17.3850,78.4867),("Nagpur",21.1458,79.0882),("Indore",22.7196,75.8577),("Bhopal",23.2599,77.4126),("Agra",27.1767,78.0081),("Delhi",28.6139,77.2090),("Chandigarh",30.7333,76.7794)],
    "SHP-1032": [("Bangalore",12.9716,77.5946),("Chennai",13.0827,80.2707),("Visakhapatnam",17.6868,83.2185),("Bhubaneswar",20.2961,85.8245),("Kolkata",22.5726,88.3639)],
    "SHP-1033": [("Vadodara",22.3072,73.1812),("Surat",21.1702,72.8311),("Mumbai",19.0760,72.8777),("Pune",18.5204,73.8567),("Hyderabad",17.3850,78.4867),("Bangalore",12.9716,77.5946),("Chennai",13.0827,80.2707)],
    "SHP-1034": [("Amritsar",31.6340,74.8723),("Ludhiana",30.9010,75.8573),("Delhi",28.6139,77.2090)],
}

# Speed: each call advances ~1 waypoint if enough time has passed (simulate movement)
import threading
_sim_lock = threading.Lock()

def get_next_waypoint(shipment_no, lat, lng):
    """Return next waypoint city/coords if found in route, else small drift."""
    route = ROUTE_WAYPOINTS.get(shipment_no, [])
    if not route:
        # Generic drift
        return None, round(lat + random.uniform(-0.08, 0.08), 4), round(lng + random.uniform(-0.08, 0.08), 4)
    # Find closest current waypoint index
    best = 0
    best_dist = float('inf')
    for i, (city, wlat, wlng) in enumerate(route):
        d = (wlat - lat)**2 + (wlng - lng)**2
        if d < best_dist:
            best_dist = d
            best = i
    # Advance to next if not at end
    if best < len(route) - 1:
        next_city, next_lat, next_lng = route[best + 1]
        # Interpolate 30% of the way towards next
        new_lat = round(lat + (next_lat - lat) * 0.30, 4)
        new_lng = round(lng + (next_lng - lng) * 0.30, 4)
        # If very close to next waypoint, snap to it
        if (next_lat - lat)**2 + (next_lng - lng)**2 < 0.01:
            return next_city, next_lat, next_lng
        return None, new_lat, new_lng
    else:
        city, wlat, wlng = route[-1]
        return city, wlat, wlng

@app.route("/api/shipments/live-update")
def shipments_live_update():
    """Tick: drift temp/humidity, advance location for in-transit shipments. Returns updated rows."""
    conn = get_db()
    c    = conn.cursor()
    rows = c.execute("SELECT * FROM shipments").fetchall()
    updates = []

    for row in rows:
        s = dict(row)
        if s["status"] not in ("In Transit", "Delayed"):
            updates.append(s)
            continue

        # Temperature drift — stays within realistic bounds per product type
        base_temp  = s["temperature"]
        temp_drift = random.uniform(-0.6, 0.6)
        # Clamp cold-chain items
        if "Pharma" in s["product"] or "Vaccine" in s["product"] or "Frozen" in s["product"] or "Seafood" in s["product"]:
            new_temp = round(max(-5.0, min(8.0, base_temp + temp_drift)), 1)
        else:
            new_temp = round(max(15.0, min(38.0, base_temp + temp_drift * 1.5)), 1)

        # Humidity drift
        new_hum  = round(max(20.0, min(95.0, s["humidity"] + random.uniform(-1.2, 1.2))), 1)

        # Location advance (only In Transit)
        new_loc   = s["current_location"]
        new_lat   = s["lat"]
        new_lng   = s["lng"]
        if s["status"] == "In Transit":
            snap_city, new_lat, new_lng = get_next_waypoint(s["shipment_no"], s["lat"], s["lng"])
            if snap_city:
                new_loc = snap_city
                # If reached final destination → mark delivered
                route = ROUTE_WAYPOINTS.get(s["shipment_no"], [])
                if route and snap_city == route[-1][0]:
                    c.execute("UPDATE shipments SET status='Delivered',current_location=?,lat=?,lng=?,temperature=?,humidity=? WHERE id=?",
                              (new_loc, new_lat, new_lng, new_temp, new_hum, s["id"]))
                    s["status"] = "Delivered"
                    s["current_location"] = new_loc
                else:
                    c.execute("UPDATE shipments SET current_location=?,lat=?,lng=?,temperature=?,humidity=? WHERE id=?",
                              (new_loc, new_lat, new_lng, new_temp, new_hum, s["id"]))
            else:
                c.execute("UPDATE shipments SET lat=?,lng=?,temperature=?,humidity=? WHERE id=?",
                          (new_lat, new_lng, new_temp, new_hum, s["id"]))
        else:
            c.execute("UPDATE shipments SET temperature=?,humidity=? WHERE id=?",
                      (new_temp, new_hum, s["id"]))

        s.update({"temperature": new_temp, "humidity": new_hum,
                  "current_location": new_loc, "lat": new_lat, "lng": new_lng})
        updates.append(s)

    conn.commit()
    conn.close()
    return jsonify(updates)




# ─────────────────────────────────────────
# MARKETPLACE SEED DATA
# ─────────────────────────────────────────

def seed_marketplace(c):
    c.execute("SELECT COUNT(*) FROM marketplace_listings")
    if c.fetchone()[0] > 0:
        return
    listings = [
        ("FastCargo India",  "logistics@fastcargo.in",  "Express Cold-Chain Logistics",        "Temperature-controlled transport for pharma & food. Real-time GPS + IoT monitoring.",           "Logistics",      4500.00,  "per shipment", 50,  "Mumbai",    "🚚", "cold-chain,pharma,express",    4.8, 24, 1, 1),
        ("SteelBridge Co",   "sales@steelbridge.in",    "Industrial Steel Components",         "High-tensile steel sheets and beams for automotive & construction. ISO certified.",             "Raw Materials",  18500.00, "per tonne",    200, "Pune",      "⚙️", "steel,industrial,certified",  4.5, 18, 1, 1),
        ("BioAgri Exports",  "info@bioagri.co.in",      "Organic Produce Bulk Supply",         "Certified organic fruits & vegetables. FSSAI approved. Cold storage available.",                "Food & Agri",    1200.00,  "per quintal",  500, "Nashik",    "🌿", "organic,food,fssai",          4.7, 31, 1, 1),
        ("ChipTech India",   "b2b@chiptech.in",         "Electronic Component Kits",           "Microcontrollers, sensors & PCB components for OEM manufacturers. Bulk discounts.",             "Electronics",    3200.00,  "per lot",      150, "Bangalore", "🔌", "electronics,oem,sensors",     4.6, 15, 1, 1),
        ("SafeFreight Ltd",  "ops@safefreight.in",      "Bonded Warehouse Storage",            "Secure, climate-controlled warehousing with blockchain-verified inventory tracking.",           "Warehousing",    8000.00,  "per month",    30,  "Delhi NCR", "🏭", "storage,climate,secure",      4.9, 42, 1, 1),
        ("MediSupply Pro",   "supply@medipro.in",       "Pharmaceutical Raw Materials",        "USP/BP grade API and excipients. GMP certified. Cold chain delivery included.",                 "Pharma",         22000.00, "per kg",       80,  "Hyderabad", "💊", "pharma,gmp,api",              4.8, 27, 1, 1),
        ("TexWave Mills",    "export@texwave.in",       "Premium Fabric Rolls — Bulk",         "Cotton, polyester & blended fabrics for garment manufacturers. Dyeing customisation.",          "Textiles",       650.00,   "per metre",    2000,"Surat",      "🧵", "fabric,cotton,export",        4.4, 9,  1, 1),
        ("AquaFreeze",       "cold@aquafreeze.in",      "Frozen Seafood — Export Grade",       "Shrimp, fish & squid, IQF frozen. HACCP & EU certified. Containerised export ready.",          "Food & Agri",    4800.00,  "per tonne",    60,  "Kochi",     "🦐", "seafood,frozen,export",       4.7, 20, 1, 1),
        ("AutoParts Hub",    "sales@autopartshub.in",   "OEM Auto Parts Catalogue",            "10,000+ SKUs for passenger & commercial vehicles. Same-day dispatch from Pune warehouse.",      "Auto Parts",     280.00,   "per part",     5000,"Pune",       "🔧", "auto,oem,wholesale",          4.5, 33, 1, 1),
        ("GreenBox Pack",    "hi@greenboxpack.in",      "Eco Packaging Solutions",             "Biodegradable corrugated boxes, mailers & void fill. Custom printing available.",               "Packaging",      12.00,    "per unit",     10000,"Chennai",   "📦", "eco,packaging,custom",        4.6, 17, 1, 1),
        ("DroneRoute",       "ops@droneroute.in",       "Last-Mile Drone Delivery",            "DGCA approved drone delivery for urgent medical & e-commerce. Coverage: 25km radius.",         "Logistics",      1800.00,  "per delivery", 100, "Bangalore", "🚁", "drone,last-mile,express",     4.3, 11, 0, 0),
        ("ChemTrade India",  "chem@chemtrade.in",       "Industrial Chemicals — Bulk",         "Solvents, acids & specialty chemicals for manufacturing. MSDS certified, safe packaging.",     "Chemicals",      9500.00,  "per drum",     200, "Vadodara",  "🧪", "chemicals,bulk,msds",         4.5, 14, 1, 1),
    ]
    c.executemany("""
        INSERT INTO marketplace_listings
        (seller_name,seller_email,title,description,category,price,unit,stock,location,image_emoji,tags,rating,review_count,verified,active,created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, [(*l, datetime.now().isoformat()) for l in listings])

    # Seed some reviews
    reviews = [
        (1,"buyer@abc.com","Priya S",5,"Excellent cold chain — vaccines arrived at 4°C exactly."),
        (1,"ops@xyz.in","Rahul M",4,"Fast and reliable. Slight delay on one shipment but resolved."),
        (2,"mfg@delta.in","Ankit K",5,"Steel quality is top notch, certified as promised."),
        (5,"wh@store.co","Neha R",5,"Best warehouse facility we've used. Blockchain logs are a huge plus."),
        (6,"pharma@rx.in","Dr. Suresh",5,"GMP certified materials, documentation complete. Will reorder."),
    ]
    c.executemany("""
        INSERT INTO marketplace_reviews (listing_id,reviewer_email,reviewer_name,rating,comment,created_at)
        VALUES (?,?,?,?,?,?)
    """, [(*r, datetime.now().isoformat()) for r in reviews])


# ─────────────────────────────────────────
# MARKETPLACE API
# ─────────────────────────────────────────

@app.route("/api/marketplace/listings")
def mp_listings():
    q        = request.args.get("q", "").lower()
    category = request.args.get("category", "")
    sort     = request.args.get("sort", "newest")   # newest | price_asc | price_desc | rating
    conn = get_db()
    rows = conn.execute("SELECT * FROM marketplace_listings WHERE active=1 ORDER BY id DESC").fetchall()
    conn.close()
    items = [dict(r) for r in rows]
    if q:
        items = [i for i in items if q in i["title"].lower() or q in (i["description"] or "").lower()
                 or q in (i["tags"] or "").lower() or q in (i["category"] or "").lower()]
    if category and category != "All":
        items = [i for i in items if i["category"] == category]
    if sort == "price_asc":  items.sort(key=lambda x: x["price"])
    elif sort == "price_desc":items.sort(key=lambda x: x["price"], reverse=True)
    elif sort == "rating":    items.sort(key=lambda x: x["rating"], reverse=True)
    return jsonify(items)


@app.route("/api/marketplace/listing/<int:lid>")
def mp_listing_detail(lid):
    conn = get_db()
    row = conn.execute("SELECT * FROM marketplace_listings WHERE id=?", (lid,)).fetchone()
    reviews = conn.execute("SELECT * FROM marketplace_reviews WHERE listing_id=? ORDER BY created_at DESC", (lid,)).fetchall()
    conn.close()
    if not row:
        return jsonify({"error": "Not found"}), 404
    data = dict(row)
    data["reviews"] = [dict(r) for r in reviews]
    return jsonify(data)


@app.route("/api/marketplace/listing", methods=["POST"])
def mp_create_listing():
    user = session.get("user")
    d = request.json or {}
    if not d.get("title") or not d.get("price"):
        return jsonify({"error": "Title and price required."}), 400
    conn = get_db()
    conn.execute("""
        INSERT INTO marketplace_listings
        (seller_name,seller_email,title,description,category,price,unit,stock,location,image_emoji,tags,verified,active,created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,0,1,?)
    """, (
        user["name"] if user else d.get("seller_name","Anonymous"),
        user["email"] if user else d.get("seller_email",""),
        d["title"], d.get("description",""), d.get("category","Other"),
        float(d["price"]), d.get("unit","unit"), int(d.get("stock",1)),
        d.get("location","India"), d.get("image_emoji","📦"), d.get("tags",""),
        datetime.now().isoformat()
    ))
    conn.commit()
    lid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return jsonify({"success": True, "id": lid}), 201


@app.route("/api/marketplace/listing/<int:lid>", methods=["DELETE"])
def mp_delete_listing(lid):
    user = session.get("user")
    conn = get_db()
    row = conn.execute("SELECT seller_email FROM marketplace_listings WHERE id=?", (lid,)).fetchone()
    if not row:
        conn.close(); return jsonify({"error": "Not found"}), 404
    if user and row["seller_email"] != user.get("email") and user.get("role") != "admin":
        conn.close(); return jsonify({"error": "Not authorised"}), 403
    conn.execute("UPDATE marketplace_listings SET active=0 WHERE id=?", (lid,))
    conn.commit(); conn.close()
    return jsonify({"success": True})


@app.route("/api/marketplace/categories")
def mp_categories():
    conn = get_db()
    rows = conn.execute(
        "SELECT category, COUNT(*) as cnt FROM marketplace_listings WHERE active=1 GROUP BY category ORDER BY cnt DESC"
    ).fetchall()
    conn.close()
    return jsonify([{"category": r["category"], "count": r["cnt"]} for r in rows])


# ── Cart ──────────────────────────────────

@app.route("/api/marketplace/cart")
def mp_cart_get():
    user = session.get("user") or {}
    email = user.get("email","demo@chainvista.app")
    conn = get_db()
    rows = conn.execute("""
        SELECT c.id, c.quantity, c.listing_id, c.added_at,
               l.title, l.price, l.unit, l.image_emoji, l.seller_name, l.stock
        FROM marketplace_cart c
        JOIN marketplace_listings l ON l.id = c.listing_id
        WHERE c.buyer_email=?
    """, (email,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/marketplace/cart", methods=["POST"])
def mp_cart_add():
    user  = session.get("user") or {}
    email = user.get("email","demo@chainvista.app")
    d     = request.json or {}
    lid   = d.get("listing_id")
    qty   = int(d.get("quantity", 1))
    if not lid:
        return jsonify({"error": "listing_id required"}), 400
    conn = get_db()
    existing = conn.execute("SELECT id, quantity FROM marketplace_cart WHERE buyer_email=? AND listing_id=?", (email, lid)).fetchone()
    if existing:
        conn.execute("UPDATE marketplace_cart SET quantity=? WHERE id=?", (existing["quantity"] + qty, existing["id"]))
    else:
        conn.execute("INSERT INTO marketplace_cart (buyer_email,listing_id,quantity,added_at) VALUES (?,?,?,?)",
                     (email, lid, qty, datetime.now().isoformat()))
    conn.commit(); conn.close()
    return jsonify({"success": True})


@app.route("/api/marketplace/cart/<int:cid>", methods=["DELETE"])
def mp_cart_remove(cid):
    conn = get_db()
    conn.execute("DELETE FROM marketplace_cart WHERE id=?", (cid,))
    conn.commit(); conn.close()
    return jsonify({"success": True})


@app.route("/api/marketplace/cart/<int:cid>", methods=["PUT"])
def mp_cart_update(cid):
    qty = int((request.json or {}).get("quantity", 1))
    conn = get_db()
    if qty <= 0:
        conn.execute("DELETE FROM marketplace_cart WHERE id=?", (cid,))
    else:
        conn.execute("UPDATE marketplace_cart SET quantity=? WHERE id=?", (qty, cid))
    conn.commit(); conn.close()
    return jsonify({"success": True})


# ── Orders ────────────────────────────────

@app.route("/api/marketplace/orders", methods=["POST"])
def mp_place_order():
    user  = session.get("user") or {}
    email = user.get("email","demo@chainvista.app")
    d     = request.json or {}
    items = d.get("items", [])  # [{listing_id, quantity}]
    if not items:
        return jsonify({"error": "No items in order"}), 400
    conn = get_db()
    order_ids = []
    for item in items:
        lid = item["listing_id"]; qty = int(item.get("quantity",1))
        row = conn.execute("SELECT price, stock, title FROM marketplace_listings WHERE id=?", (lid,)).fetchone()
        if not row:
            continue
        total = round(row["price"] * qty, 2)
        conn.execute("""
            INSERT INTO marketplace_orders (buyer_email,listing_id,quantity,total_price,status,note,created_at)
            VALUES (?,?,?,?,?,?,?)
        """, (email, lid, qty, total, "Confirmed", d.get("note",""), datetime.now().isoformat()))
        oid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        order_ids.append(oid)
        conn.execute("UPDATE marketplace_listings SET stock=MAX(0,stock-?) WHERE id=?", (qty, lid))
    # clear cart
    conn.execute("DELETE FROM marketplace_cart WHERE buyer_email=?", (email,))
    conn.commit(); conn.close()
    return jsonify({"success": True, "order_ids": order_ids}), 201


@app.route("/api/marketplace/orders")
def mp_orders_get():
    user  = session.get("user") or {}
    email = user.get("email","demo@chainvista.app")
    conn  = get_db()
    rows  = conn.execute("""
        SELECT o.*, l.title, l.image_emoji, l.seller_name, l.category
        FROM marketplace_orders o
        JOIN marketplace_listings l ON l.id = o.listing_id
        WHERE o.buyer_email=? ORDER BY o.created_at DESC
    """, (email,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


# ── Reviews ───────────────────────────────

@app.route("/api/marketplace/review", methods=["POST"])
def mp_add_review():
    user  = session.get("user") or {}
    d     = request.json or {}
    lid   = d.get("listing_id")
    rating = int(d.get("rating", 5))
    comment = d.get("comment","")
    if not lid:
        return jsonify({"error": "listing_id required"}), 400
    conn = get_db()
    conn.execute("""
        INSERT INTO marketplace_reviews (listing_id,reviewer_email,reviewer_name,rating,comment,created_at)
        VALUES (?,?,?,?,?,?)
    """, (lid, user.get("email","demo@chainvista.app"),
          user.get("name","Anonymous"), rating, comment, datetime.now().isoformat()))
    # Recalc rating
    row = conn.execute("SELECT AVG(rating) as avg, COUNT(*) as cnt FROM marketplace_reviews WHERE listing_id=?", (lid,)).fetchone()
    conn.execute("UPDATE marketplace_listings SET rating=?, review_count=? WHERE id=?",
                 (round(row["avg"],1), row["cnt"], lid))
    conn.commit(); conn.close()
    return jsonify({"success": True})


# RUN


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
