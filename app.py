from flask import Flask, jsonify, request, render_template, send_from_directory
from flask_cors import CORS
import sqlite3
import random
import string
import hashlib
import time
from datetime import datetime, timedelta
import json
import os

app = Flask(__name__)
CORS(app)

DB_PATH = os.path.join(os.environ.get("DB_DIR", "/tmp"), "chainvista.db")

# ─────────────────────────────────────────────────────────────
# DATABASE SETUP
# ─────────────────────────────────────────────────────────────

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

    conn.commit()
    conn.close()

def gen_tx_hash():
    return "0x" + ''.join(random.choices(string.hexdigits.lower(), k=8)) + "..." + ''.join(random.choices(string.hexdigits.lower(), k=4))

# ─────────────────────────────────────────────────────────────
# FRONTEND SERVE
# ─────────────────────────────────────────────────────────────


@app.route('/')
def index():
    conn = sqlite3.connect('chainvista.db')
    c = conn.cursor()
    conn.close()
    return render_template('index.html')

# ─────────────────────────────────────────────────────────────
# DASHBOARD API
# ─────────────────────────────────────────────────────────────

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

# ─────────────────────────────────────────────────────────────
# SHIPMENTS API
# ─────────────────────────────────────────────────────────────

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

# ─────────────────────────────────────────────────────────────
# TRACKING API
# ─────────────────────────────────────────────────────────────

@app.route("/api/tracking")
def tracking():
    conn = get_db()
    rows = conn.execute(
        "SELECT shipment_no, current_location, status, lat, lng FROM shipments"
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

# ─────────────────────────────────────────────────────────────
# ALERTS API
# ─────────────────────────────────────────────────────────────

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

# ─────────────────────────────────────────────────────────────
# ANALYTICS API
# ─────────────────────────────────────────────────────────────

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

# ─────────────────────────────────────────────────────────────
# BLOCKCHAIN / PASSPORT API
# ─────────────────────────────────────────────────────────────

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

# ─────────────────────────────────────────────────────────────
# LIVE SHIPMENT SIMULATION ENDPOINT
# ─────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────────────────────

# Initialize DB on startup — runs under gunicorn AND direct execution
init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
