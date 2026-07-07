import os
import json
import uuid
import requests
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, redirect, url_for, session, render_template_string

app = Flask(__name__)
app.secret_key = "shayan_explorer_premium_secure_vault_token"

# System Administrative Access Profiles
ADMIN_USER = "vernex"
ADMIN_PASS = "vernex@16vx"

# Master Downstream Vendor Target Configurations
TARGET_BASE_API = "https://ft-osint-api.duckdns.org/api"
MASTER_VENDOR_KEY = "vx-osint"

# Supported Application Gateway Routing Modules Matrix
SUPPORTED_TOOLS = {
    "adv": "num", "paytm": "num", "imei": "imei", "calltracer": "num",
    "upi": "upi", "ifsc": "ifsc", "number": "num", "pincode": "pin",
    "ip": "ip", "challan": "vehicle", "ff": "uid", "bgmi": "uid",
    "snap": "username", "email": "email", "vehicle": "vehicle", "git": "username",
    "insta": "username", "tg": "info", "tgidinfo": "id", "numleak": "num",
    "pk": "num", "name": "name", "aadhar": "num", "numtoupi": "num",
    "pan": "pan", "veh2num": "vehicle", "adharfamily": "num", "bomber": "number"
}

# -------------------------------------------------------------
# ZERO-GLITCH STATE STORAGE CONTROLLER
# -------------------------------------------------------------
# To keep keys from being deleted when Vercel serverless containers reset, 
# this memory matrix falls back gracefully. To preserve keys indefinitely across
# Vercel container recycles, set an Environment Variable named 'PERSISTENT_STATE'.
# -------------------------------------------------------------
LOCAL_MEMORY_CACHE = {
    "keys": {},
    "logs": []
}

def sync_load_state():
    env_state = os.environ.get("PERSISTENT_STATE")
    if env_state:
        try:
            return json.loads(env_state)
        except Exception:
            pass
    return LOCAL_MEMORY_CACHE

def sync_save_state(state_matrix):
    global LOCAL_MEMORY_CACHE
    LOCAL_MEMORY_CACHE = state_matrix
    # Hook point: To auto-save to an external cluster, transmit state payload here.

def evaluate_and_clean_keys():
    state = sync_load_state()
    modified = False
    now = datetime.now()
    
    for key_token, meta in list(state["keys"].items()):
        if meta["status"] == "active":
            expiry_time = datetime.strptime(meta["expiry"], "%Y-%m-%dT%H:%M")
            if now > expiry_time:
                state["keys"][key_token]["status"] = "expired"
                modified = True
                
    if modified:
        sync_save_state(state)

# -------------------------------------------------------------
# LUXURY CYAN METEOR MODERN RESPONSIVE UI
# -------------------------------------------------------------
CORE_UI_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>SHAYAN_EXPLORER | Command Core</title>
    <style>
        :root {
            --bg-deep: #03060b;
            --panel-solid: #090f19;
            --panel-glass: rgba(11, 19, 32, 0.85);
            --cyan-glow: #00e5ff;
            --cyan-dim: #005b66;
            --cyan-pulse: rgba(0, 229, 255, 0.2);
            --text-primary: #f1f5f9;
            --text-secondary: #94a3b8;
            --alert-red: #ff3b57;
            --alert-orange: #ff9100;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
        body { background-color: var(--bg-deep); color: var(--text-primary); min-height: 100vh; padding: 15px; -webkit-font-smoothing: antialiased; }

        .app-container { max-width: 1300px; margin: 0 auto; padding-bottom: 40px; }

        /* Navigation Header */
        header {
            background: var(--panel-glass); border: 1px solid var(--cyan-dim); padding: 20px;
            border-radius: 12px; display: flex; flex-direction: column; gap: 15px; margin-bottom: 25px;
            backdrop-filter: blur(10px); box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37), 0 0 15px rgba(0, 229, 255, 0.05);
        }
        @media(min-width: 768px) {
            header { flex-direction: row; justify-content: space-between; align-items: center; padding: 25px; }
        }

        .title-group h1 { font-size: 1.6rem; font-weight: 800; letter-spacing: 1px; color: #fff; text-shadow: 0 0 15px var(--cyan-pulse); }
        .title-group p { color: var(--text-secondary); font-size: 0.8rem; margin-top: 3px; font-weight: 500; }
        .developer-badge { color: var(--cyan-glow); font-weight: 700; }

        /* Portal Forms */
        .auth-panel { max-width: 440px; margin: 80px auto; padding: 30px; background: var(--panel-solid); border: 1px solid var(--cyan-dim); border-radius: 16px; box-shadow: 0 20px 50px rgba(0, 229, 255, 0.1); }
        .auth-title { text-align: center; margin-bottom: 25px; }
        .auth-title h2 { color: var(--cyan-glow); font-weight: 700; letter-spacing: 0.5px; }

        .input-stack { margin-bottom: 18px; }
        .input-stack label { display: block; margin-bottom: 8px; font-size: 0.8rem; font-weight: 600; color: var(--text-secondary); text-transform: uppercase; }
        
        input[type="text"], input[type="password"], input[type="number"], input[type="datetime-local"], select {
            width: 100%; padding: 14px; background: #05090f; border: 1px solid rgba(0, 229, 255, 0.15);
            color: #fff; border-radius: 8px; outline: none; font-size: 0.95rem; transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }
        input:focus, select:focus { border-color: var(--cyan-glow); box-shadow: 0 0 12px var(--cyan-pulse); }

        /* Action Controls */
        .btn {
            display: inline-flex; align-items: center; justify-content: center; padding: 12px 24px;
            background: linear-gradient(135deg, var(--cyan-dim), rgba(0, 229, 255, 0.3));
            border: 1px solid var(--cyan-glow); color: #fff; font-size: 0.9rem; font-weight: 600;
            border-radius: 8px; cursor: pointer; transition: all 0.2s ease; text-decoration: none; text-shadow: 0 1px 2px rgba(0,0,0,0.5);
        }
        .btn:hover { transform: translateY(-1px); box-shadow: 0 0 20px rgba(0, 229, 255, 0.4); background: var(--cyan-glow); color: var(--bg-deep); text-shadow: none; }
        .btn-danger { border-color: var(--alert-red); background: rgba(255, 59, 87, 0.1); color: var(--alert-red); text-shadow: none; }
        .btn-danger:hover { background: var(--alert-red); color: #fff; box-shadow: 0 0 20px rgba(255, 59, 87, 0.4); }

        /* Dashboard Grid layouts */
        .dashboard-grid { display: grid; grid-template-columns: 1fr; gap: 20px; margin-bottom: 25px; }
        @media(min-width: 1024px) { .dashboard-grid { grid-template-columns: 1.1fr 0.9fr; gap: 25px; } }

        .content-card { background: var(--panel-solid); border: 1px solid rgba(0, 229, 255, 0.1); padding: 22px; border-radius: 14px; box-shadow: 0 4px 20px rgba(0,0,0,0.2); }
        .card-heading { font-size: 1.1rem; font-weight: 700; color: #fff; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.05); display: flex; justify-content: space-between; align-items: center; }

        .checkbox-container { max-height: 150px; overflow-y: auto; background: #05090f; border: 1px solid rgba(0,229,255,0.1); padding: 12px; border-radius: 8px; }
        .check-row { display: flex; align-items: center; margin-bottom: 10px; font-size: 0.9rem; color: var(--text-secondary); cursor: pointer; }
        .check-row input { margin-right: 12px; width: 16px; height: 16px; accent-color: var(--cyan-glow); }

        /* Live Endpoint Item Displays */
        .scrollable-content { max-height: 410px; overflow-y: auto; padding-right: 5px; }
        .endpoint-box { background: #05090f; border-radius: 10px; padding: 14px; margin-bottom: 12px; border-left: 4px solid var(--cyan-glow); display: flex; justify-content: space-between; align-items: center; gap: 10px; }
        .endpoint-meta { overflow: hidden; width: 80%; }
        .endpoint-name { font-size: 0.85rem; font-weight: 700; color: var(--cyan-glow); text-transform: uppercase; }
        .endpoint-path { font-size: 0.8rem; color: var(--text-secondary); white-space: nowrap; overflow-x: auto; margin-top: 4px; font-family: monospace; }

        /* Core Matrix Tables */
        .table-responsive { width: 100%; overflow-x: auto; border-radius: 10px; background: #05090f; border: 1px solid rgba(255,255,255,0.03); }
        table { width: 100%; border-collapse: collapse; text-align: left; }
        th { padding: 16px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; color: var(--text-secondary); border-bottom: 2px solid rgba(255,255,255,0.05); }
        td { padding: 16px; font-size: 0.9rem; color: var(--text-primary); border-bottom: 1px solid rgba(255,255,255,0.03); white-space: nowrap; }
        tr:hover td { background: rgba(0, 229, 255, 0.01); }

        .status-pill { padding: 4px 10px; font-size: 0.75rem; font-weight: 700; border-radius: 6px; text-transform: uppercase; display: inline-block; }
        .status-active { background: rgba(0, 225, 255, 0.1); color: var(--cyan-glow); border: 1px solid rgba(0, 225, 255, 0.2); }
        .status-suspended { background: rgba(255, 59, 87, 0.1); color: var(--alert-red); border: 1px solid rgba(255, 59, 87, 0.2); }
        .status-expired { background: rgba(255, 145, 0, 0.1); color: var(--alert-orange); border: 1px solid rgba(255, 145, 0, 0.2); }

        /* Utility Web Scrollbars */
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(0, 229, 255, 0.15); border-radius: 10px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--cyan-glow); }
    </style>
</head>
<body>
<div class="app-container">

    {% if view == 'login' %}
    <div class="auth-panel">
        <div class="auth-title">
            <h2>GATEWAY AUTH</h2>
            <p style="color: var(--text-secondary); font-size: 0.8rem; margin-top: 5px;">AUTHORIZE SECURE SEED DEPLOYMENT</p>
        </div>
        {% if error %}<p style="color: var(--alert-red); text-align: center; font-size: 0.85rem; margin-bottom: 15px; font-weight: 600;">{{ error }}</p>{% endif %}
        <form action="/login" method="POST">
            <div class="input-stack">
                <label>Admin User</label>
                <input type="text" name="username" required autocomplete="off">
            </div>
            <div class="input-stack">
                <label>Cipher Core Password</label>
                <input type="password" name="password" required>
            </div>
            <button type="submit" class="btn" style="width: 100%; margin-top: 5px;">DECRYPT MATRIX</button>
        </form>
    </div>

    {% elif view == 'main' %}
    <header>
        <div class="title-group">
            <h1>SYSTEM MANAGEMENT GATEWAY</h1>
            <p>API ARCHITECTURE CONTROL UNIT // DEVELOPER: <span class="developer-badge">SHAYAN_EXPLORER</span></p>
        </div>
        <a href="/logout" class="btn btn-danger">TERMINATE SESSION</a>
    </header>

    <div class="dashboard-grid">
        <div class="content-card">
            <div class="card-heading">MINT SECURE APP CLIENT KEY</div>
            <form action="/admin/key/generate" method="POST">
                <div class="input-stack">
                    <label>Client Reference Identity Name</label>
                    <input type="text" name="name" placeholder="Ex: Premium Subscriber Token" required autocomplete="off">
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                    <div class="input-stack">
                        <label>Request Volume Volume Limit</label>
                        <input type="number" name="limit" value="1000" required min="1">
                    </div>
                    <div class="input-stack">
                        <label>Key Validation Expiration</label>
                        <input type="datetime-local" name="expiry" id="exp_picker" required>
                    </div>
                </div>
                <div class="input-stack">
                    <label>Module Resource Scope Limits (Leave unchecked for Global Access)</label>
                    <div class="checkbox-container">
                        {% for tool in tools %}
                        <label class="check-row" for="tool-{{ tool }}">
                            <input type="checkbox" name="tools" value="{{ tool }}" id="tool-{{ tool }}">
                            <span>{{ tool | upper }} Verification API</span>
                        </label>
                        {% endfor %}
                    </div>
                </div>
                <button type="submit" class="btn" style="width: 100%; margin-top: 5px;">DEPLOY NEW ACCESS CREDENTIAL</button>
            </form>
        </div>

        <div class="content-card">
            <div class="card-heading">AVAILABLE MATRIX INTERFACE ROUTING GRAPH</div>
            <div class="scrollable-content">
                {% for tool, param in tools.items() %}
                <div class="endpoint-box">
                    <div class="endpoint-meta">
                        <div class="endpoint-name">{{ tool }} module</div>
                        <div class="endpoint-path" id="p-{{ tool }}">/api/{{ tool }}?key={KEY_STRING}&{{ param }}={VALUE}</div>
                    </div>
                    <button class="btn" style="padding: 6px 12px; font-size: 0.75rem;" onclick="copyMatrixEndpoint('p-{{ tool }}')">COPY</button>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>

    <div class="content-card" style="margin-bottom: 25px;">
        <div class="card-heading">ACTIVE ROUTED ACCESS TOKENS LEDGER</div>
        <div class="table-responsive">
            <table>
                <thead>
                    <tr>
                        <th>Generated Token Key</th>
                        <th>Client Title</th>
                        <th>Usage Vol</th>
                        <th>Target Expiration</th>
                        <th>Assigned Scope Matrix</th>
                        <th>State Token</th>
                        <th>System Control Directives</th>
                    </tr>
                </thead>
                <tbody>
                    {% for key, meta in keys.items() %}
                    <tr>
                        <td style="color: var(--cyan-glow); font-weight: 700;"><code>{{ key }}</code></td>
                        <td>{{ meta.name }}</td>
                        <td>{{ meta.usages }} / {{ meta.limit }}</td>
                        <td style="font-size: 0.8rem; color: var(--text-secondary);">{{ meta.expiry.replace('T', ' ') }}</td>
                        <td style="max-width: 140px; overflow: hidden; text-overflow: ellipsis;">{{ meta.allowed_tools | join(', ') }}</td>
                        <td><span class="status-pill status-{{ meta.status }}">{{ meta.status }}</span></td>
                        <td>
                            {% if meta.status == 'active' %}
                            <a href="/admin/key/action/{{ key }}/suspend" class="btn" style="padding: 5px 10px; font-size: 0.75rem; border-color: var(--alert-orange); color: var(--alert-orange); background: transparent;">SUSPEND</a>
                            {% else %}
                            <a href="/admin/key/action/{{ key }}/unsuspend" class="btn" style="padding: 5px 10px; font-size: 0.75rem; background: transparent;">ACTIVATE</a>
                            {% endif %}
                            <a href="/admin/key/action/{{ key }}/delete" class="btn btn-danger" style="padding: 5px 10px; font-size: 0.75rem;" onclick="return confirm('Purge access credential completely from matrix?')">PURGE</a>
                        </td>
                    </tr>
                    {% else %}
                    <tr><td colspan="7" style="text-align: center; color: var(--text-secondary); padding: 30px;">No operational token maps tracked inside runtime environment memory pools.</td></tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

    <div class="content-card">
        <div class="card-heading">REAL-TIME TRAFFIC GATEWAY AUDIT STREAM</div>
        <div class="table-responsive" style="max-height: 250px;">
            <table>
                <thead>
                    <tr>
                        <th>Timestamp Frame</th>
                        <th>Validation Token</th>
                        <th>Client Mapping</th>
                        <th>Target Module Path</th>
                        <th>Query Data Vector</th>
                    </tr>
                </thead>
                <tbody>
                    {% for log in logs | reverse %}
                    <tr>
                        <td style="color: var(--text-secondary); font-size: 0.8rem;">{{ log.timestamp }}</td>
                        <td><code>{{ log.key }}</code></td>
                        <td>{{ log.name }}</td>
                        <td><span style="color: var(--cyan-glow); font-weight: 600;">{{ log.tool | upper }}</span></td>
                        <td><span style="color: #fff; background: rgba(0, 229, 255, 0.05); padding: 4px 8px; border-radius: 4px; font-size: 0.8rem; border: 1px solid rgba(0,229,255,0.05);">{{ log.query }}</span></td>
                    </tr>
                    {% else %}
                    <tr><td colspan="5" style="text-align: center; color: var(--text-secondary); padding: 30px;">Awaiting live data packets route streams traffic...</td></tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    {% endif %}

</div>

<script>
if(document.getElementById('exp_picker')) {
    var dt = new Date();
    dt.setHours(dt.getHours() + 48);
    document.getElementById('exp_picker').value = dt.toISOString().slice(0, 16);
}

function copyMatrixEndpoint(elementId) {
    var rawText = document.getElementById(elementId).innerText;
    var remoteHost = window.location.origin;
    var completeBuffer = remoteHost + rawText;
    
    navigator.clipboard.writeText(completeBuffer).then(function() {
        alert("Gateway Route URL Blueprint Map Stored To Dashboard Clipboard Successfully.");
    }).catch(function(err) {
        console.error('Incompatible execution environment context: ', err);
    });
}
</script>
</body>
</html>
"""

@app.route('/')
def home():
    evaluate_and_clean_keys()
    if not session.get('logged_in'):
        return render_template_string(CORE_UI_LAYOUT, view='login')
    return redirect(url_for('admin_dashboard'))

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if username == ADMIN_USER and password == ADMIN_PASS:
        session['logged_in'] = True
        return redirect(url_for('admin_dashboard'))
    return render_template_string(CORE_UI_LAYOUT, view='login', error="Security Failure: Signature Mismatch Verification Check.")

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('home'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('home'))
    evaluate_and_clean_keys()
    state = sync_load_state()
    return render_template_string(
        CORE_UI_LAYOUT, 
        view='main', 
        keys=state["keys"], 
        logs=state["logs"], 
        tools=SUPPORTED_TOOLS
    )

@app.route('/admin/key/generate', methods=['POST'])
def generate_key():
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized Domain Operations Security Framework"}), 403
        
    name = request.form.get('name', 'External Core Subscriber')
    limit = int(request.form.get('limit', 1000))
    expiry = request.form.get('expiry')
    selected_tools = request.form.getlist('tools')
    
    if not expiry:
        expiry = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M")
        
    new_token_key = f"SHAYAN_{uuid.uuid4().hex[:10].upper()}"
    
    state = sync_load_state()
    state["keys"][new_token_key] = {
        "name": name,
        "limit": limit,
        "usages": 0,
        "expiry": expiry,
        "allowed_tools": selected_tools if selected_tools else ["all"],
        "status": "active"
    }
    sync_save_state(state)
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/key/action/<key_id>/<action>')
def key_action(key_id, action):
    if not session.get('logged_in'):
        return redirect(url_for('home'))
        
    state = sync_load_state()
    if key_id in state["keys"]:
        if action == "suspend":
            state["keys"][key_id]["status"] = "suspended"
        elif action == "unsuspend":
            state["keys"][key_id]["status"] = "active"
        elif action == "delete":
            del state["keys"][key_id]
            
    sync_save_state(state)
    return redirect(url_for('admin_dashboard'))

# -------------------------------------------------------------
# DYNAMIC ENDPOINT VERIFICATION PROXY HOOK ENGINE
# -------------------------------------------------------------
@app.route('/api/<tool_name>', methods=['GET'])
def gateway_proxy_link(tool_name):
    if tool_name not in SUPPORTED_TOOLS:
        return jsonify({"error": f"Endpoint Module Graph Target '{tool_name}' Is Unrecognized Matrix Array"}), 404
        
    client_key = request.args.get('key')
    state = sync_load_state()
    
    if not client_key or client_key not in state["keys"]:
        return jsonify({"error": "The key is invalid. Please buy a new key.", "status": "invalid"}), 401
        
    key_metadata = state["keys"][client_key]
    
    if key_metadata["status"] == "suspended":
        return jsonify({"error": "The key is suspended by admin.", "status": "suspended"}), 403
        
    expiry_limit = datetime.strptime(key_metadata["expiry"], "%Y-%m-%dT%H:%M")
    if datetime.now() > expiry_limit:
        state["keys"][client_key]["status"] = "expired"
        sync_save_state(state)
        return jsonify({"error": "The key is expired. Please buy a new key.", "status": "expired"}), 401
        
    if key_metadata["usages"] >= key_metadata["limit"]:
        return jsonify({"error": "Rate limit capacity verification ceiling crossed.", "status": "limited"}), 429
        
    if "all" not in key_metadata["allowed_tools"] and tool_name not in key_metadata["allowed_tools"]:
        return jsonify({"error": f"This key does not have access to the '{tool_name}' endpoint.", "status": "unauthorized"}), 403
        
    # Transaction Parameter Auditing Logger Engine
    query_parameters = request.args.to_dict()
    search_query_param = SUPPORTED_TOOLS[tool_name]
    target_query_value = query_parameters.get(search_query_param, "N/A")
    
    state["logs"].append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "key": client_key,
        "name": key_metadata["name"],
        "tool": tool_name,
        "query": f"{search_query_param}={target_query_value}"
    })
    
    state["keys"][client_key]["usages"] += 1
    sync_save_state(state)
    
    # Forward Clean Payload Vectors with Updated Master Keys securely Downstream
    outbound_parameters = query_parameters.copy()
    outbound_parameters['key'] = MASTER_VENDOR_KEY
    
    try:
        upstream_response = requests.get(f"{TARGET_BASE_API}/{tool_name}", params=outbound_parameters, timeout=12)
        return (upstream_response.content, upstream_response.status_code, upstream_response.headers.items())
    except requests.exceptions.RequestException:
        return jsonify({"error": "Data relay interface timeout error connecting back with base server matrix."}), 502

if __name__ == '__main__':
    app.run(debug=True)


