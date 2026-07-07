import os
import json
import uuid
import requests
from datetime import datetime
from flask import Flask, request, jsonify, redirect, url_for, session, render_template_string

app = Flask(__name__)
app.secret_key = "shayan_explorer_matrix_gateway_core_secure_vault"

# Administrative Access Configuration
ADMIN_USER = "vernex"
ADMIN_PASS = "vernex@16vx"

# Downstream Endpoint Targets
TARGET_BASE_API = "https://ft-osint-api.duckdns.org/api"
MASTER_VENDOR_KEY = "vx-osint"

# Supported Routing Registry Map
SUPPORTED_TOOLS = {
    "adv": "num", "paytm": "num", "imei": "imei", "calltracer": "num",
    "upi": "upi", "ifsc": "ifsc", "number": "num", "pincode": "pin",
    "ip": "ip", "challan": "vehicle", "ff": "uid", "bgmi": "uid",
    "snap": "username", "email": "email", "vehicle": "vehicle", "git": "username",
    "insta": "username", "tg": "info", "tgidinfo": "id", "numleak": "num",
    "pk": "num", "name": "name", "aadhar": "num", "numtoupi": "num",
    "pan": "pan", "veh2num": "vehicle", "adharfamily": "num", "bomber": "number"
}

# -----------------------------------------------------------------------------
# PERSISTENCE INTERFACE LAYER
# To ensure keys remain valid across serverless instances, implement a database connection.
# For testing purposes, this fallback layer uses an environment variable variable map.
# -----------------------------------------------------------------------------
CORE_STATE_CACHE = {
    "keys": {},
    "logs": []
}

def fetch_active_state():
    """Reads state variables from the environment layer or fallback memory cache."""
    env_data = os.environ.get("GATEWAY_DATABASE_STATE")
    if env_data:
        try:
            return json.loads(env_data)
        except Exception:
            pass
    return CORE_STATE_CACHE

def commit_state_changes(state_payload):
    """Saves updated data states back to the persistence cache layer."""
    global CORE_STATE_CACHE
    CORE_STATE_CACHE = state_payload
    # Integration point: Add code here to write back to your external database provider API.

def evaluate_key_expiration():
    """Checks active keys and marks them as expired if they pass their deadline."""
    state = fetch_active_state()
    updated = False
    now = datetime.now()
    
    for key, metadata in list(state["keys"].items()):
        if metadata["status"] == "active" and not metadata.get("is_lifetime", False):
            expiry_dt = datetime.strptime(metadata["expiry"], "%Y-%m-%dT%H:%M")
            if now > expiry_dt:
                state["keys"][key]["status"] = "expired"
                updated = True
                
    if updated:
        commit_state_changes(state)

# -----------------------------------------------------------------------------
# PITCH BLACK HIGH-PERFORMANCE RESPONSIVE USER INTERFACE
# -----------------------------------------------------------------------------
UI_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>SHAYAN_EXPLORER // Control Core</title>
    <style>
        :root {
            --bg-solid: #000000;
            --card-bg: #07090e;
            --input-bg: #020305;
            --cyan-neon: #00f0ff;
            --cyan-dark: #004a52;
            --text-pure: #ffffff;
            --text-dim: #64748b;
            --status-green: #00ff66;
            --status-red: #ff2a4b;
            --status-orange: #ff9f00;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif; }
        body { background-color: var(--bg-solid); color: var(--text-pure); padding: 12px; min-height: 100vh; }

        .container { max-width: 1340px; margin: 0 auto; }

        header {
            background: var(--card-bg); border: 1px solid #111827; padding: 20px;
            border-radius: 12px; display: flex; flex-direction: column; gap: 15px; margin-bottom: 20px;
            box-shadow: 0 0 30px rgba(0, 240, 255, 0.02);
        }

        .header-main h1 { font-size: 1.5rem; font-weight: 800; letter-spacing: -0.5px; }
        .header-main p { color: var(--text-dim); font-size: 0.8rem; margin-top: 2px; }
        .dev-tag { color: var(--cyan-neon); font-weight: 700; }

        /* Portal Security Interface */
        .login-frame { max-width: 400px; margin: 100px auto; padding: 30px; background: var(--card-bg); border: 1px solid #111827; border-radius: 16px; }
        .login-header { text-align: center; margin-bottom: 25px; }
        .login-header h2 { color: var(--cyan-neon); font-size: 1.4rem; font-weight: 800; }

        .input-group { margin-bottom: 16px; }
        .input-group label { display: block; margin-bottom: 6px; font-size: 0.75rem; font-weight: 700; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.5px; }
        
        input[type="text"], input[type="password"], input[type="number"], input[type="datetime-local"], select {
            width: 100%; padding: 14px; background: var(--input-bg); border: 1px solid #1e293b;
            color: #fff; border-radius: 8px; outline: none; font-size: 0.95rem; transition: all 0.2s ease;
        }
        input:focus, select:focus { border-color: var(--cyan-neon); box-shadow: 0 0 10px rgba(0, 240, 255, 0.15); }

        .toggle-row { display: flex; align-items: center; gap: 10px; margin-top: 10px; }
        .toggle-row input[type="checkbox"] { width: 18px; height: 18px; accent-color: var(--cyan-neon); }

        /* Button Component Matrix */
        .btn {
            display: inline-flex; align-items: center; justify-content: center; padding: 12px 20px;
            background: #0d1527; border: 1px solid var(--cyan-neon); color: var(--cyan-neon);
            font-size: 0.85rem; font-weight: 700; border-radius: 8px; cursor: pointer; transition: all 0.2s ease; text-decoration: none;
        }
        .btn:hover { background: var(--cyan-neon); color: var(--bg-solid); box-shadow: 0 0 15px rgba(0, 240, 255, 0.4); }
        .btn-danger { border-color: var(--status-red); color: var(--status-red); background: transparent; }
        .btn-danger:hover { background: var(--status-red); color: #fff; box-shadow: 0 0 15px rgba(255, 42, 75, 0.4); }

        /* Responsive Layout Matrix Grid */
        .layout-grid { display: grid; grid-template-columns: 1fr; gap: 20px; margin-bottom: 20px; }
        
        /* Device-Specific Adaptations for Desktop viewports */
        @media(min-width: 1024px) {
            body { padding: 24px; }
            header { flex-direction: row; justify-content: space-between; align-items: center; padding: 24px; }
            .layout-grid { grid-template-columns: 1.10fr 0.90fr; gap: 24px; }
            .header-main h1 { font-size: 1.75rem; }
        }

        .card { background: var(--card-bg); border: 1px solid #111827; padding: 22px; border-radius: 14px; }
        .card-title { font-size: 1rem; font-weight: 700; padding-bottom: 12px; margin-bottom: 18px; border-bottom: 1px solid #1e293b; display: flex; justify-content: space-between; align-items: center; }

        .selector-box { max-height: 140px; overflow-y: auto; background: var(--input-bg); border: 1px solid #1e293b; padding: 10px; border-radius: 8px; }
        .selector-item { display: flex; align-items: center; margin-bottom: 8px; font-size: 0.85rem; color: #cbd5e1; }
        .selector-item input { margin-right: 10px; width: 15px; height: 15px; accent-color: var(--cyan-neon); }

        /* Interactive Route Endpoint Rows */
        .viewport-scroll { max-height: 400px; overflow-y: auto; padding-right: 4px; }
        .route-strip { background: var(--input-bg); border-radius: 8px; padding: 12px; margin-bottom: 10px; border-left: 3px solid var(--cyan-neon); display: flex; justify-content: space-between; align-items: center; gap: 10px; }
        .route-details { overflow: hidden; width: 75%; }
        .route-header { font-size: 0.8rem; font-weight: 700; color: var(--cyan-neon); text-transform: uppercase; }
        .route-link { font-size: 0.75rem; color: var(--text-dim); white-space: nowrap; overflow-x: auto; margin-top: 2px; font-family: monospace; }

        /* Responsive Data Registry Layouts */
        .table-wrap { width: 100%; overflow-x: auto; border-radius: 8px; background: var(--input-bg); }
        table { width: 100%; border-collapse: collapse; text-align: left; }
        th { padding: 14px; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; color: var(--text-dim); border-bottom: 1px solid #1e293b; }
        td { padding: 14px; font-size: 0.85rem; border-bottom: 1px solid #0f172a; white-space: nowrap; }
        tr:hover td { background: rgba(0, 240, 255, 0.01); }

        .pill { padding: 3px 8px; font-size: 0.7rem; font-weight: 700; border-radius: 4px; text-transform: uppercase; }
        .pill-active { background: rgba(0, 255, 102, 0.1); color: var(--status-green); }
        .pill-suspended { background: rgba(255, 42, 75, 0.1); color: var(--status-red); }
        .pill-expired { background: rgba(255, 159, 0, 0.1); color: var(--status-orange); }

        ::-webkit-scrollbar { width: 4px; height: 4px; }
        ::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--cyan-neon); }
    </style>
</head>
<body>
<div class="container">

    {% if view == 'login' %}
    <div class="login-frame">
        <div class="login-header">
            <h2>SYSTEM REGISTRY</h2>
            <p style="color: var(--text-dim); font-size: 0.75rem; margin-top: 4px;">VERIFY OPERATOR IDENTIFICATION</p>
        </div>
        {% if error %}<p style="color: var(--status-red); text-align: center; font-size: 0.8rem; margin-bottom: 12px; font-weight: 600;">{{ error }}</p>{% endif %}
        <form action="/login" method="POST">
            <div class="input-group">
                <label>Operator ID</label>
                <input type="text" name="username" required autocomplete="off">
            </div>
            <div class="input-group">
                <label>Security Keyphrase</label>
                <input type="password" name="password" required>
            </div>
            <button type="submit" class="btn" style="width: 100%; margin-top: 4px;">INITIALIZE CORE</button>
        </form>
    </div>

    {% elif view == 'main' %}
    <header>
        <div class="header-main">
            <h1>CENTRAL SECURITY RUNTIME</h1>
            <p>GATEWAY STATUS: ONLINE // DEVELOPER: <span class="dev-tag">SHAYAN_EXPLORER</span></p>
        </div>
        <a href="/logout" class="btn btn-danger">TERMINATE INSTANCE</a>
    </header>

    <div class="layout-grid">
        <div class="card">
            <div class="card-title">MINT GATEWAY ACCESS CREDENTIAL</div>
            <form action="/admin/key/generate" method="POST">
                <div class="input-group">
                    <label>Client Reference Description</label>
                    <input type="text" name="name" placeholder="Subscriber Token Identity" required autocomplete="off">
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                    <div class="input-group">
                        <label>Request Volume Limit</label>
                        <input type="number" name="limit" value="1000" required min="1">
                    </div>
                    <div class="input-group" id="expiry_date_block">
                        <label>Timeline Expiration Date</label>
                        <input type="datetime-local" name="expiry" id="expiry_field">
                    </div>
                </div>
                <div class="input-group">
                    <div class="toggle-row">
                        <input type="checkbox" name="is_lifetime" id="is_lifetime" onchange="toggleLifetimeContext(this)">
                        <label style="margin-bottom:0; cursor:pointer;" for="is_lifetime">Grant Lifetime Validity Matrix (No Expiration)</label>
                    </div>
                </div>
                <div class="input-group">
                    <label>Restrict Scopes (Leave unchecked for All Module Privileges)</label>
                    <div class="selector-box">
                        {% for tool in tools %}
                        <label class="selector-item" for="t-{{ tool }}">
                            <input type="checkbox" name="tools" value="{{ tool }}" id="t-{{ tool }}">
                            <span>{{ tool | upper }} Verification Path</span>
                        </label>
                        {% endfor %}
                    </div>
                </div>
                <button type="submit" class="btn" style="width: 100%;">DEPLOY KEY ROUTE ACCESS</button>
            </form>
        </div>

        <div class="card">
            <div class="card-title">ROUTING GRAPH MODULES</div>
            <div class="viewport-scroll">
                {% for tool, fallback_param in tools.items() %}
                <div class="route-strip">
                    <div class="route-details">
                        <div class="route-header">{{ tool }}</div>
                        <div class="route-link" id="url-{{ tool }}">/api/{{ tool }}?key={KEY_STRING}&{{ fallback_param }}={VALUE}</div>
                    </div>
                    <button class="btn" style="padding: 6px 10px; font-size: 0.7rem;" onclick="copySystemRoute('url-{{ tool }}')">COPY</button>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>

    <div class="card" style="margin-bottom: 20px;">
        <div class="card-title">CREDENTIAL SYSTEM LEDGER</div>
        <div class="table-wrap">
            <table>
                <thead>
                    <tr>
                        <th>Access Token Key</th>
                        <th>Client Tag</th>
                        <th>Usage Vol</th>
                        <th>Target Expiration Timeline</th>
                        <th>Allowed Scope Access</th>
                        <th>State</th>
                        <th>Operations</th>
                    </tr>
                </thead>
                <tbody>
                    {% for key, info in keys.items() %}
                    <tr>
                        <td style="color: var(--cyan-neon); font-weight: 700;"><code>{{ key }}</code></td>
                        <td>{{ info.name }}</td>
                        <td>{{ info.usages }} / {{ info.limit }}</td>
                        <td style="font-size: 0.8rem; color: var(--text-dim);">
                            {% if info.is_lifetime %}LIFETIME VALIDITY{% else %}{{ info.expiry.replace('T', ' ') }}{% endif %}
                        </td>
                        <td style="max-width: 140px; overflow: hidden; text-overflow: ellipsis;">{{ info.allowed_tools | join(', ') }}</td>
                        <td><span class="pill pill-{{ info.status }}">{{ info.status }}</span></td>
                        <td>
                            {% if info.status == 'active' %}
                            <a href="/admin/key/action/{{ key }}/suspend" class="btn" style="padding: 4px 8px; font-size: 0.7rem; border-color: var(--status-orange); color: var(--status-orange);">SUSPEND</a>
                            {% else %}
                            <a href="/admin/key/action/{{ key }}/unsuspend" class="btn" style="padding: 4px 8px; font-size: 0.7rem;">REVIVE</a>
                            {% endif %}
                            <a href="/admin/key/action/{{ key }}/delete" class="btn btn-danger" style="padding: 4px 8px; font-size: 0.7rem;" onclick="return confirm('Purge access profile metadata?')">PURGE</a>
                        </td>
                    </tr>
                    {% else %}
                    <tr><td colspan="7" style="text-align: center; color: var(--text-dim); padding: 25px;">No active access tokens configured inside operational persistence layer memory blocks.</td></tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

    <div class="card">
        <div class="card-title">REALTIME ACCESS TRAFFIC LOGS</div>
        <div class="table-wrap" style="max-height: 240px;">
            <table>
                <thead>
                    <tr>
                        <th>Timestamp Frame</th>
                        <th>Execution Key String</th>
                        <th>Client Tag</th>
                        <th>Module Path</th>
                        <th>Query Metadata String</th>
                    </tr>
                </thead>
                <tbody>
                    {% for log in logs | reverse %}
                    <tr>
                        <td style="color: var(--text-dim); font-size: 0.8rem;">{{ log.timestamp }}</td>
                        <td><code>{{ log.key }}</code></td>
                        <td>{{ log.name }}</td>
                        <td style="color: var(--cyan-neon); font-weight: 600;">{{ log.tool | upper }}</td>
                        <td><span style="color: #fff; background: rgba(0, 240, 255, 0.03); padding: 4px 8px; border-radius: 4px; font-size: 0.8rem; border: 1px solid rgba(0,240,255,0.05);">{{ log.query }}</span></td>
                    </tr>
                    {% else %}
                    <tr><td colspan="5" style="text-align: center; color: var(--text-dim); padding: 25px;">Awaiting operational gateway traffic request logs...</td></tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    {% endif %}

</div>

<script>
if(document.getElementById('expiry_field')) {
    var futureTarget = new Date();
    futureTarget.setHours(futureTarget.getHours() + 48);
    document.getElementById('expiry_field').value = futureTarget.toISOString().slice(0, 16);
}

function toggleLifetimeContext(checkboxElement) {
    var inputBlock = document.getElementById('expiry_date_block');
    var targetField = document.getElementById('expiry_field');
    if(checkboxElement.checked) {
        inputBlock.style.opacity = '0.3';
        targetField.required = false;
        targetField.disabled = true;
    } else {
        inputBlock.style.opacity = '1';
        targetField.required = true;
        targetField.disabled = false;
    }
}

function copySystemRoute(targetRef) {
    var pathStr = document.getElementById(targetRef).innerText;
    var remoteDomain = window.location.origin;
    var completeBuffer = remoteDomain + pathStr;
    
    navigator.clipboard.writeText(completeBuffer).then(function() {
        alert("Gateway Route URL Map Buffer Successfully Copied to Device Clipboard.");
    }).catch(function(err) {
        console.error('Incompatible runtime environment permissions architecture: ', err);
    });
}
</script>
</body>
</html>
"""

@app.route('/')
def home():
    evaluate_key_expiration()
    if not session.get('logged_in'):
        return render_template_string(UI_TEMPLATE, view='login')
    return redirect(url_for('admin_dashboard'))

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if username == ADMIN_USER and password == ADMIN_PASS:
        session['logged_in'] = True
        return redirect(url_for('admin_dashboard'))
    return render_template_string(UI_TEMPLATE, view='login', error="Authorization Mismatch: Invalid Control Credentials.")

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('home'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('home'))
    evaluate_key_expiration()
    state_matrix = fetch_active_state()
    return render_template_string(
        UI_TEMPLATE, 
        view='main', 
        keys=state_matrix["keys"], 
        logs=state_matrix["logs"], 
        tools=SUPPORTED_TOOLS
    )

@app.route('/admin/key/generate', methods=['POST'])
def generate_key():
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized Node Access"}), 403
        
    name = request.form.get('name', 'External Core Node')
    limit = int(request.form.get('limit', 1000))
    expiry = request.form.get('expiry')
    is_lifetime = request.form.get('is_lifetime') is not None
    selected_tools = request.form.getlist('tools')
    
    if not expiry and not is_lifetime:
        return redirect(url_for('admin_dashboard'))
        
    generated_token = f"SHAYAN_{uuid.uuid4().hex[:10].upper()}"
    state_matrix = fetch_active_state()
    
    state_matrix["keys"][generated_token] = {
        "name": name,
        "limit": limit,
        "usages": 0,
        "expiry": expiry if not is_lifetime else "9999-12-31T23:59",
        "is_lifetime": is_lifetime,
        "allowed_tools": selected_tools if selected_tools else ["all"],
        "status": "active"
    }
    commit_state_changes(state_matrix)
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/key/action/<key_id>/<action>')
def key_action(key_id, action):
    if not session.get('logged_in'):
        return redirect(url_for('home'))
        
    state_matrix = fetch_active_state()
    if key_id in state_matrix["keys"]:
        if action == "suspend":
            state_matrix["keys"][key_id]["status"] = "suspended"
        elif action == "unsuspend":
            state_matrix["keys"][key_id]["status"] = "active"
        elif action == "delete":
            del state_matrix["keys"][key_id]
            
    commit_state_changes(state_matrix)
    return redirect(url_for('admin_dashboard'))

# Dynamic Proxy Engine Gateway Route
@app.route('/api/<tool_name>', methods=['GET'])
def endpoint_proxy_link(tool_name):
    if tool_name not in SUPPORTED_TOOLS:
        return jsonify({"error": f"Endpoint signature mapping target '{tool_name}' unknown."}), 404
        
    client_key = request.args.get('key')
    state_matrix = fetch_active_state()
    
    if not client_key or client_key not in state_matrix["keys"]:
        return jsonify({"error": "The key is invalid. Please buy a new key.", "status": "invalid"}), 401
        
    key_info = state_matrix["keys"][client_key]
    
    if key_info["status"] == "suspended":
        return jsonify({"error": "The key is suspended by admin.", "status": "suspended"}), 403
        
    if not key_info.get("is_lifetime", False):
        expiry_deadline = datetime.strptime(key_info["expiry"], "%Y-%m-%dT%H:%M")
        if datetime.now() > expiry_deadline:
            state_matrix["keys"][client_key]["status"] = "expired"
            commit_state_changes(state_matrix)
            return jsonify({"error": "The key is expired. Please buy a new key.", "status": "expired"}), 401
        
    if key_info["usages"] >= key_info["limit"]:
        return jsonify({"error": "Allocated volumetric data limits reached for key context.", "status": "limited"}), 429
        
    if "all" not in key_info["allowed_tools"] and tool_name not in key_info["allowed_tools"]:
        return jsonify({"error": f"This key does not have access to the '{tool_name}' endpoint.", "status": "unauthorized"}), 403
        
    # Query Analysis Auditing System
    raw_query_params = request.args.to_dict()
    mapped_query_key = SUPPORTED_TOOLS[tool_name]
    extracted_query_value = raw_query_params.get(mapped_query_key, "N/A")
    
    state_matrix["logs"].append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "key": client_key,
        "name": key_info["name"],
        "tool": tool_name,
        "query": f"{mapped_query_key}={extracted_query_value}"
    })
    
    state_matrix["keys"][client_key]["usages"] += 1
    commit_state_changes(state_matrix)
    
    # Restructure outgoing parameters for downstream authentication translation
    forwarded_params = raw_query_params.copy()
    forwarded_params['key'] = MASTER_VENDOR_KEY
    
    try:
        upstream_response = requests.get(f"{TARGET_BASE_API}/{tool_name}", params=forwarded_params, timeout=12)
        return (upstream_response.content, upstream_response.status_code, upstream_response.headers.items())
    except requests.exceptions.RequestException:
        return jsonify({"error": "Data stream connectivity error from base network layer."}), 502

if __name__ == '__main__':
    app.run(debug=True)



