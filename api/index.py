import os
import json
import time
import uuid
import requests
from flask import Flask, request, jsonify, render_template_string, redirect, session, url_for

app = Flask(__name__)
app.secret_key = "vx_secret_glow_core_2026"

# Absolute persistence path inside writable /tmp or local fallback
DB_FILE = "/tmp/vx_osint_database.json" if os.path.exists("/tmp") else "vx_osint_database.json"

def load_db():
    if not os.path.exists(DB_FILE):
        default_data = {
            "keys": {},
            "logs": []
        }
        with open(DB_FILE, "w") as f:
            json.dump(default_data, f)
        return default_data
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {"keys": {}, "logs": []}

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Native Master Target Endpoint Rules
TARGET_API_BASE = "https://ft-osint-api.duckdns.org/api"
UPSTREAM_KEY = "vx-osint"

API_ENDPOINTS = {
    "adv": "adv?key={key}&num={num}",
    "paytm": "paytm?key={key}&num={num}",
    "imei": "imei?key={key}&imei={imei}",
    "calltracer": "calltracer?key={key}&num={num}",
    "upi": "upi?key={key}&upi={upi}",
    "ifsc": "ifsc?key={key}&ifsc={ifsc}",
    "number": "number?key={key}&num={num}",
    "pincode": "pincode?key={key}&pin={pin}",
    "ip": "ip?key={key}&ip={ip}",
    "challan": "challan?key={key}&vehicle={vehicle}",
    "ff": "ff?key={key}&uid={uid}",
    "bgmi": "bgmi?key={key}&uid={uid}",
    "snap": "snap?key={key}&username={username}",
    "email": "email?key={key}&email={email}",
    "vehicle": "vehicle?key={key}&vehicle={vehicle}",
    "git": "git?key={key}&username={username}",
    "insta": "insta?key={key}&username={username}",
    "tg": "tg?key={key}&info={info}",
    "tgidinfo": "tgidinfo?key={key}&id={id}",
    "numleak": "numleak?key={key}&num={num}"
}

# ================= CORE API ROUTE PROXY =================
@app.route("/api/<endpoint_name>", methods=["GET"])
def proxy_api(endpoint_name):
    if endpoint_name not in API_ENDPOINTS:
        return jsonify({"status": "error", "message": "Unknown endpoint target."}), 404
        
    user_key = request.args.get("key")
    if not user_key:
        return jsonify({"status": "error", "message": "Authentication Key is missing. Purchase key from SHAYAN_EXPLORER."}), 401

    db = load_db()
    if user_key not in db["keys"]:
        return jsonify({"status": "error", "message": "The key is invalid. Please buy a new key."}), 401

    key_info = db["keys"][user_key]

    # Check Suspension Status
    if key_info.get("suspended", False):
        return jsonify({"status": "error", "message": "The key is suspended by admin."}), 403

    # Check Scope Permissions
    allowed_tools = key_info.get("allowed_tools", "all")
    if allowed_tools != "all" and endpoint_name not in allowed_tools:
        return jsonify({"status": "error", "message": f"This key does not have access to [{endpoint_name}]. Upgrade your plan."}), 403

    # Check Temporal Expiry
    expiry_type = key_info.get("expiry_type", "lifetime")
    if expiry_type == "date":
        expire_timestamp = key_info.get("expiry_timestamp", 0)
        if time.time() > expire_timestamp:
            return jsonify({"status": "error", "message": "The key is expired. Please buy a new key."}), 401

    # Check Request Usage Limits
    max_limit = int(key_info.get("limit", 0))
    current_usage = int(key_info.get("usage", 0))
    if max_limit > 0 and current_usage >= max_limit:
        return jsonify({"status": "error", "message": "Key request limit reached. Rate limit exceeded."}), 429

    # Update state usage metric safely
    db["keys"][user_key]["usage"] = current_usage + 1
    
    # Track diagnostic logs safely
    search_query = json.dumps({k: v for k, v in request.args.items() if k != 'key'})
    db["logs"].append({
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "key_name": key_info.get("name", "Unknown"),
        "key": user_key,
        "endpoint": endpoint_name,
        "query": search_query
    })
    save_db(db)

    # Build backend target upstream URL dynamically
    param_template = API_ENDPOINTS[endpoint_name]
    query_params = {k: v for k, v in request.args.items() if k != 'key'}
    query_params['key'] = UPSTREAM_KEY

    try:
        target_url = f"{TARGET_API_BASE}/{param_template.format(**query_params)}"
    except KeyError as e:
        return jsonify({"status": "error", "message": f"Missing query parameter: {str(e)}"}), 400

    try:
        resp = requests.get(target_url, timeout=12)
        return (resp.text, resp.status_code, {"Content-Type": "application/json"})
    except Exception as e:
        return jsonify({"status": "error", "message": "Internal gateway routing lookup error.", "details": str(e)}), 500


# ================= DASHBOARD CONTROLLER ROUTING =================
ADMIN_USER = "vernex"
ADMIN_PASS = "vernex@16vx"

@app.route("/", methods=["GET", "POST"])
def login_dashboard():
    if session.get("logged_in"):
        return redirect(url_for("admin_panel"))
        
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == ADMIN_USER and password == ADMIN_PASS:
            session["logged_in"] = True
            return redirect(url_for("admin_panel"))
        else:
            error = "Invalid matrix administrative credentials."
            
    return render_template_string(LOGIN_HTML, error=error)

@app.route("/dashboard")
def admin_panel():
    if not session.get("logged_in"):
        return redirect(url_for("login_dashboard"))
    db = load_db()
    return render_template_string(DASHBOARD_HTML, db=db, endpoints=API_ENDPOINTS.keys())

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_dashboard"))

@app.route("/action/generate", methods=["POST"])
def action_generate():
    if not session.get("logged_in"): return jsonify({"status": "unauthorized"}), 401
    
    name = request.form.get("name", "Unnamed Key")
    limit = int(request.form.get("limit", 0))
    expiry_type = request.form.get("expiry_type", "lifetime")
    days = float(request.form.get("expiry_days", 0)) if expiry_type == "date" else 0
    tools_scope = request.form.getlist("tools")
    
    generated_key = "VX-" + str(uuid.uuid4()).replace("-", "").upper()[:16]
    expiry_timestamp = time.time() + (days * 86400) if expiry_type == "date" else 0
    
    db = load_db()
    db["keys"][generated_key] = {
        "name": name,
        "limit": limit,
        "usage": 0,
        "expiry_type": expiry_type,
        "expiry_timestamp": expiry_timestamp,
        "allowed_tools": "all" if "all" in tools_scope or not tools_scope else tools_scope,
        "suspended": False
    }
    save_db(db)
    return redirect(url_for("admin_panel"))

@app.route("/action/modify/<key>", methods=["POST"])
def action_modify(key):
    if not session.get("logged_in"): return jsonify({"status": "unauthorized"}), 401
    db = load_db()
    if key in db["keys"]:
        op = request.form.get("op")
        if op == "suspend":
            db["keys"][key]["suspended"] = True
        elif op == "unsuspend":
            db["keys"][key]["suspended"] = False
        elif op == "delete":
            del db["keys"][key]
        elif op == "update":
            db["keys"][key]["name"] = request.form.get("name")
            db["keys"][key]["limit"] = int(request.form.get("limit", 0))
            expiry_type = request.form.get("expiry_type")
            db["keys"][key]["expiry_type"] = expiry_type
            if expiry_type == "date":
                days = float(request.form.get("expiry_days", 0))
                db["keys"][key]["expiry_timestamp"] = time.time() + (days * 86400)
            tools_scope = request.form.getlist("tools")
            db["keys"][key]["allowed_tools"] = "all" if "all" in tools_scope or not tools_scope else tools_scope
        save_db(db)
    return redirect(url_for("admin_panel"))

# ================= DESIGN UI FRAMEWORKS (2026 NEO-GLOW AESTHETIC) =================
LOGIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SHAYAN_EXPLORER | Secure Terminal Auth</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Roboto, sans-serif; }
        body { background: radial-gradient(circle at center, #0f0c1b 0%, #05020a 100%); color: #fff; min-height: 100vh; display: flex; align-items: center; justify-content: center; overflow: hidden; padding: 20px; }
        .login-card { background: rgba(15, 10, 30, 0.65); border: 1px solid rgba(255, 0, 128, 0.3); border-radius: 16px; width: 100%; max-width: 420px; padding: 40px 30px; backdrop-filter: blur(20px); box-shadow: 0 0 40px rgba(255, 0, 128, 0.15), inset 0 0 20px rgba(0, 242, 254, 0.05); text-align: center; }
        h1 { font-size: 1.8rem; letter-spacing: 2px; margin-bottom: 10px; background: linear-gradient(45deg, #ff007f, #00f2fe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800; }
        p { color: #8a829e; font-size: 0.9rem; margin-bottom: 30px; }
        .form-group { text-align: left; margin-bottom: 20px; }
        label { display: block; color: #00f2fe; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; font-weight: 600; }
        input { width: 100%; background: rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.1); padding: 12px 16px; border-radius: 8px; color: #fff; font-size: 1rem; transition: all 0.3s ease; }
        input:focus { border-color: #ff007f; box-shadow: 0 0 15px rgba(255,0,128,0.4); outline: none; }
        .btn { width: 100%; background: linear-gradient(45deg, #ff007f, #7928ca); border: none; color: white; padding: 14px; font-size: 1rem; font-weight: bold; border-radius: 8px; cursor: pointer; text-transform: uppercase; letter-spacing: 1px; box-shadow: 0 4px 15px rgba(255, 0, 128, 0.4); transition: all 0.3s; }
        .btn:hover { filter: brightness(1.2); transform: translateY(-2px); box-shadow: 0 6px 20px rgba(255, 0, 128, 0.6); }
        .err { background: rgba(255,0,0,0.15); border: 1px solid #ff0033; color: #ff3366; padding: 12px; border-radius: 8px; font-size: 0.85rem; margin-bottom: 20px; text-align: left; }
    </style>
</head>
<body>
    <div class="login-card">
        <h1>SHAYAN_EXPLORER</h1>
        <p>COSMIC CORE OSINT MANAGEMENT ENGINE</p>
        {% if error %}<div class="err">{{ error }}</div>{% endif %}
        <form method="POST">
            <div class="form-group"><label>Terminal User</label><input type="text" name="username" required autocomplete="off"></div>
            <div class="form-group"><label>Access Token Secret</label><input type="password" name="password" required></div>
            <button type="submit" class="btn">Authenticate Engine</button>
        </form>
    </div>
</body>
</html>
"""

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SHAYAN_EXPLORER | Command Center</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', sans-serif; }
        body { background: #07040f; color: #e2dbf0; min-height: 100vh; padding: 20px; }
        header { max-width: 1200px; margin: 0 auto 30px auto; display: flex; justify-content: space-between; align-items: center; background: rgba(20,15,35,0.7); padding: 20px 30px; border-radius: 12px; border: 1px solid rgba(0, 242, 254, 0.2); backdrop-filter: blur(10px); }
        header h1 { font-size: 1.6rem; font-weight: 800; background: linear-gradient(45deg, #ff007f, #00f2fe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .logout-lnk { color: #ff007f; text-decoration: none; font-weight: bold; border: 1px solid #ff007f; padding: 6px 14px; border-radius: 6px; font-size: 0.85rem; transition: 0.3s; }
        .logout-lnk:hover { background: #ff007f; color: #fff; box-shadow: 0 0 15px rgba(255,0,128,0.5); }
        .wrapper { max-width: 1200px; margin: 0 auto; display: grid; grid-template-columns: 1fr; gap: 30px; }
        @media(min-width: 900px) { .wrapper { grid-template-columns: 380px 1fr; } }
        .card { background: rgba(18, 12, 32, 0.8); border: 1px solid rgba(255,255,255,0.05); border-radius: 12px; padding: 25px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); position: relative; }
        .card::before { content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 3px; background: linear-gradient(90deg, #ff007f, #00f2fe); border-radius: 12px 12px 0 0; }
        h2 { font-size: 1.2rem; color: #00f2fe; margin-bottom: 20px; text-transform: uppercase; letter-spacing: 1px; display: flex; justify-content: space-between; align-items: center; }
        .form-control { margin-bottom: 16px; }
        label { display: block; font-size: 0.8rem; color: #aaa5b9; margin-bottom: 6px; text-transform: uppercase; font-weight: 600; }
        input[type="text"], input[type="number"], select { width: 100%; background: #0c0817; border: 1px solid rgba(255,255,255,0.1); padding: 10px 14px; border-radius: 6px; color: #fff; }
        input:focus, select:focus { border-color: #00f2fe; outline: none; }
        .tools-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; max-height: 150px; overflow-y: auto; background: #080510; padding: 10px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.05); }
        .tools-grid label { display: flex; align-items: center; gap: 8px; font-size: 0.8rem; color: #eee; cursor: pointer; text-transform: none; margin: 0; }
        .btn-action { width: 100%; background: linear-gradient(45deg, #00f2fe, #7928ca); border: none; color: #fff; padding: 12px; font-weight: bold; border-radius: 6px; cursor: pointer; text-transform: uppercase; transition: 0.3s; margin-top: 10px; }
        .btn-action:hover { filter: brightness(1.2); box-shadow: 0 0 15px rgba(0,242,254,0.4); }
        
        /* Key Rows Card layout */
        .key-box { background: #0d091a; border: 1px solid rgba(255,255,255,0.04); border-radius: 8px; padding: 16px; margin-bottom: 15px; border-left: 4px solid #00f2fe; transition: 0.2s; }
        .key-box.suspended { border-left-color: #ff0055; opacity: 0.6; }
        .key-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
        .key-title { font-weight: bold; font-size: 1.05rem; color: #fff; }
        .key-string { font-family: monospace; background: #18122b; padding: 4px 8px; border-radius: 4px; color: #ff007f; font-size: 0.9rem; word-break: break-all; display: inline-block; margin: 5px 0; }
        .badge { font-size: 0.7rem; padding: 3px 8px; border-radius: 20px; font-weight: bold; text-transform: uppercase; }
        .badge-active { background: rgba(0,242,254,0.15); color: #00f2fe; }
        .badge-suspended { background: rgba(255,0,127,0.15); color: #ff007f; }
        .meta-line { font-size: 0.8rem; color: #a19bb0; margin-bottom: 4px; }
        .ops-panel { display: flex; gap: 8px; margin-top: 12px; flex-wrap: wrap; }
        .btn-op { padding: 5px 12px; font-size: 0.75rem; border-radius: 4px; cursor: pointer; font-weight: bold; border: none; color: #fff; }
        .btn-suspend { background: #d48208; }
        .btn-unsuspend { background: #00a896; }
        .btn-delete { background: #b30000; }
        .btn-edit { background: #3b2073; }
        
        /* Endpoints section button copy elements */
        .endpoints-showcase { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 25px; background: #110b22; padding: 15px; border-radius: 8px; border: 1px dashed rgba(255,0,128,0.3); }
        .endpoint-btn { background: #1b1333; border: 1px solid rgba(255,255,255,0.1); color: #00f2fe; padding: 8px 12px; border-radius: 6px; font-size: 0.8rem; cursor: pointer; font-family: monospace; transition: 0.2s; }
        .endpoint-btn:hover { background: #ff007f; color: #fff; box-shadow: 0 0 10px rgba(255,0,128,0.4); border-color: transparent; }
        
        /* Logs display matrix */
        .log-table-wrapper { overflow-x: auto; max-height: 300px; background: #090514; border-radius: 6px; border: 1px solid rgba(255,255,255,0.05); }
        table { width: 100%; border-collapse: collapse; font-size: 0.8rem; text-align: left; }
        th, td { padding: 10px 14px; border-bottom: 1px solid rgba(255,255,255,0.05); }
        th { background: #130d26; color: #00f2fe; font-weight: 600; text-transform: uppercase; font-size: 0.75rem; }
        tr:hover { background: rgba(255,255,255,0.02); }
        
        /* Modal Config */
        .modal { display:none; position: fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.8); backdrop-filter:blur(5px); justify-content:center; align-items:center; z-index:999; padding: 20px; }
        .modal-content { background:#16102b; border: 1px solid #ff007f; width:100%; max-width:450px; padding:25px; border-radius:12px; position:relative; }
        .close-modal { position:absolute; top:12px; right:16px; color:#fff; font-size:1.4rem; cursor:pointer; }
    </style>
</head>
<body>

    <header>
        <div>
            <h1>SHAYAN_EXPLORER COMMAND INTERFACE</h1>
            <div style="font-size:0.75rem; color:#888; margin-top:2px;">Engine Developer: SHAYAN_EXPLORER | Version 2026 Production Standard</div>
        </div>
        <a href="/logout" class="logout-lnk">Disconnect Session</a>
    </header>

    <div class="wrapper">
        <div class="card">
            <h2>Generate Secure Key</h2>
            <form action="/action/generate" method="POST">
                <div class="form-control">
                    <label>Client Name / Label</label>
                    <input type="text" name="name" placeholder="Example: VIP Premium Client" required>
                </div>
                <div class="form-control">
                    <label>Total Request Allowance Limit (0 = Unlimited)</label>
                    <input type="number" name="limit" value="0" min="0" required>
                </div>
                <div class="form-control">
                    <label>Validation Model</label>
                    <select name="expiry_type" id="gen_exp_type" onchange="toggleDays('gen')">
                        <option value="lifetime">Lifetime Allocation</option>
                        <option value="date">Relative Time Expire Horizon</option>
                    </select>
                </div>
                <div class="form-control" id="gen_days_wrapper" style="display:none;">
                    <label>Valid Time Windows (In Days, e.g. 2 or 0.5)</label>
                    <input type="number" name="expiry_days" value="2" step="0.01" min="0">
                </div>
                <div class="form-control">
                    <label>Allowed Microservices Sandbox Scope</label>
                    <div class="tools-grid">
                        <label><input type="checkbox" name="tools" value="all" checked> [ALL CAPABILITIES]</label>
                        {% for endpoint in endpoints %}
                        <label><input type="checkbox" name="tools" value="{{ endpoint }}"> {{ endpoint }}</label>
                        {% endfor %}
                    </div>
                </div>
                <button type="submit" class="btn-action">Deploy New Key</button>
            </form>
        </div>

        <div style="display: flex; flex-direction: column; gap: 30px;">
            
            <div class="card">
                <h2>Fast Core Endpoints Registry (One-Click Snippet Copy)</h2>
                <div class="endpoints-showcase">
                    {% for endpoint in endpoints %}
                    <button class="endpoint-btn" onclick="copyApiUrl('{{ endpoint }}')">/api/{{ endpoint }}</button>
                    {% endfor %}
                </div>
                <p style="font-size: 0.75rem; color: #8a829e;">* Clicking on any service pill automatically extracts your dynamic endpoint path directly onto your clipboard structure.</p>
            </div>

            <div class="card">
                <h2>Active Subscribed Key Ecosystem Matrix ({{ db.keys|length }})</h2>
                <div style="max-height: 600px; overflow-y: auto; padding-right:5px;">
                    {% if not db.keys %}
                    <p style="color:#666; font-style:italic;">No cryptographic keys currently active inside database.</p>
                    {% endif %}
                    {% for key, info in db.keys.items() %}
                    <div class="key-box {% if info.suspended %}suspended{% endif %}">
                        <div class="key-header">
                            <span class="key-title">{{ info.name }}</span>
                            {% if info.suspended %}
                            <span class="badge badge-suspended">Suspended</span>
                            {% else %}
                            <span class="badge badge-active">Online</span>
                            {% endif %}
                        </div>
                        <div><span class="key-string" id="str-{{key}}">{{ key }}</span></div>
                        <div class="meta-line"><strong>Quota Request Met:</strong> {{ info.usage }} / {% if info.limit == 0 %}∞{% else %}{{ info.limit }}{% endif %} requests</div>
                        <div class="meta-line"><strong>Scope Permissions:</strong> {{ info.allowed_tools }}</div>
                        <div class="meta-line">
                            <strong>Validation Model Window:</strong> 
                            {% if info.expiry_type == 'lifetime' %}
                            <span style="color:#00f2fe;">Lifetime</span>
                            {% else %}
                            <span class="expiry-timer" data-time="{{ info.expiry_timestamp }}">Calculating remaining horizon...</span>
                            {% endif %}
                        </div>
                        
                        <div class="ops-panel">
                            <form action="/action/modify//{{key}}" method="POST" style="display:inline;">
                                {% if info.suspended %}
                                <input type="hidden" name="op" value="unsuspend">
                                <button type="submit" class="btn-op btn-unsuspend">Unsuspend</button>
                                {% else %}
                                <input type="hidden" name="op" value="suspend">
                                <button type="submit" class="btn-op btn-suspend">Suspend</button>
                                {% endif %}
                            </form>
                            <form action="/action/modify/{{key}}" method="POST" style="display:inline;">
                                <input type="hidden" name="op" value="delete">
                                <button type="submit" class="btn-op btn-delete" onclick="return confirm('Confirm complete immediate key drop configuration?')">Remove</button>
                            </form>
                            <button class="btn-op btn-edit" onclick="openEditModal('{{key}}', '{{info.name}}', '{{info.limit}}', '{{info.expiry_type}}')">Edit Configuration</button>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <div class="card">
                <h2>Realtime Core Infrastructure Audit Logs (Last 50 Records)</h2>
                <div class="log-table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th>Timestamp</th>
                                <th>Client Target</th>
                                <th>Route</th>
                                <th>Query Inspected</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for log in db.logs[-50:]|reverse %}
                            <tr>
                                <td style="white-space:nowrap; color:#00f2fe;">{{ log.timestamp }}</td>
                                <td><span style="font-family:monospace; color:#ff007f;">{{ log.key_name }}</span></td>
                                <td><span class="badge badge-active">/{{ log.endpoint }}</span></td>
                                <td style="font-family:monospace; color:#ccc; max-width:300px; overflow:hidden; text-overflow:ellipsis;">{{ log.query }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <div class="modal" id="editModal">
        <div class="modal-content">
            <span class="close-modal" onclick="closeEditModal()">&times;</span>
            <h2 style="margin-bottom:15px; font-size:1.1rem;">Modify Active Runtime Parameters</h2>
            <form id="editForm" method="POST" action="">
                <input type="hidden" name="op" value="update">
                <div class="form-control">
                    <label>Client Name / Label</label>
                    <input type="text" name="name" id="edit_name" required>
                </div>
                <div class="form-control">
                    <label>Total Limit (0 = Unlimited)</label>
                    <input type="number" name="limit" id="edit_limit" required>
                </div>
                <div class="form-control">
                    <label>Validation Model</label>
                    <select name="expiry_type" id="edit_exp_type" onchange="toggleDays('edit')">
                        <option value="lifetime">Lifetime Allocation</option>
                        <option value="date">Relative Time Expire Horizon</option>
                    </select>
                </div>
                <div class="form-control" id="edit_days_wrapper" style="display:none;">
                    <label>Reset Additional Lifespan (In Days, e.g. 2)</label>
                    <input type="number" name="expiry_days" id="edit_days" value="2" step="0.01">
                </div>
                <div class="form-control">
                    <label>Allowed Sandbox Scope</label>
                    <div class="tools-grid">
                        <label><input type="checkbox" name="tools" value="all" checked> [ALL CAPABILITIES]</label>
                        {% for endpoint in endpoints %}
                        <label><input type="checkbox" name="tools" value="{{ endpoint }}"> {{ endpoint }}</label>
                        {% endfor %}
                    </div>
                </div>
                <button type="submit" class="btn-action">Commit Structural Mod Changes</button>
            </form>
        </div>
    </div>

    <script>
        function toggleDays(prefix) {
            var type = document.getElementById(prefix + '_exp_type').value;
            document.getElementById(prefix + '_days_wrapper').style.display = (type === 'date') ? 'block' : 'none';
        }
        function openEditModal(key, name, limit, expType) {
            var form = document.getElementById('editForm');
            form.action = '/action/modify/' + key;
            document.getElementById('edit_name').value = name;
            document.getElementById('edit_limit').value = limit;
            document.getElementById('edit_exp_type').value = expType;
            toggleDays('edit');
            document.getElementById('editModal').style.display = 'flex';
        }
        function closeEditModal() {
            document.getElementById('editModal').style.display = 'none';
        }
        function copyApiUrl(endpoint) {
            var host = window.location.origin;
            var fullUrl = host + "/api/" + endpoint + "?key={YOUR_GENERATED_KEY}&num=9876543210";
            navigator.clipboard.writeText(fullUrl).then(function() {
                alert("Copied Endpoint Architecture Template:\\n" + fullUrl);
            });
        }
        function updateTimers() {
            var now = Math.floor(Date.now() / 1000);
            var elements = document.getElementsByClassName('expiry-timer');
            for(var i=0; i<elements.length; i++) {
                var ts = parseFloat(elements[i].getAttribute('data-time'));
                var diff = ts - now;
                if (diff <= 0) {
                    elements[i].innerHTML = "<span style='color:#ff0055; font-weight:bold;'>EXPIRED (Buy new key)</span>";
                } else {
                    var days = Math.floor(diff / 86400);
                    var hours = Math.floor((diff % 86400) / 3600);
                    var mins = Math.floor((diff % 3600) / 60);
                    var secs = Math.floor(diff % 60);
                    elements[i].innerHTML = days + "d " + hours + "h " + mins + "m " + secs + "s remaining";
                }
            }
        }
        setInterval(updateTimers, 1000);
        updateTimers();
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(debug=True, port=5000)




