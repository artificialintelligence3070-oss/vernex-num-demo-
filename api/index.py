import os
import json
import uuid
import requests
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, redirect, url_for, session, render_template_string

app = Flask(__name__)
app.secret_key = "shayan_explorer_matrix_gateway_secret_session_core"

# Administrative Security Verification Credentials
ADMIN_USER = "vernex"
ADMIN_PASS = "vernex@16vx"

# Target Upstream Base Core API
TARGET_BASE_API = "https://ft-osint-api.duckdns.org/api"

# Ephemeral Persistent Local Storage Matrix Path for Vercel Serverless Workspaces
DB_FILE_PATH = "/tmp/matrix_gateway_db.json"

# Supported Global Tool Routing Array Modules
SUPPORTED_TOOLS = [
    "adv", "paytm", "imei", "calltracer", "upi", "ifsc", 
    "number", "pincode", "ip", "challan", "ff", "bgmi", 
    "snap", "email", "vehicle", "git", "insta", "tg", "tgidinfo", "numleak"
]

def load_system_database():
    """Extracts authorization credentials and logs directly from local cached JSON storage."""
    if not os.path.exists(DB_FILE_PATH):
        initial_structure = {"keys": {}, "logs": []}
        with open(DB_FILE_PATH, 'w') as file:
            json.dump(initial_structure, file)
        return initial_structure
    try:
        with open(DB_FILE_PATH, 'r') as file:
            return json.load(file)
    except Exception:
        return {"keys": {}, "logs": []}

def save_system_database(data_matrix):
    """Commits state transitions, transaction parameters, and metrics safely to runtime disk space."""
    try:
        with open(DB_FILE_PATH, 'w') as file:
            json.dump(data_matrix, file, indent=4)
    except Exception:
        pass

def synchronize_key_states():
    """Loops through historical array objects and changes text labels to expired if deadlines cross."""
    db = load_system_database()
    changed = False
    current_time = datetime.now()
    
    for key, data in db["keys"].items():
        if data["status"] == "active":
            expiry_dt = datetime.strptime(data["expiry"], "%Y-%m-%dT%H:%M")
            if current_time > expiry_dt:
                db["keys"][key]["status"] = "expired"
                changed = True
                
    if changed:
        save_system_database(db)

# --- 2026 MODERN CRYPTO GLOWING DARK UI TEMPLATE ---
HTML_INTERFACE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SHAYAN_EXPLORER | Network Control Unit</title>
    <style>
        :root {
            --bg-main: #020204;
            --panel-bg: rgba(6, 10, 18, 0.95);
            --neon-glow: #00ffaa;
            --neon-dim: #005c3e;
            --neon-pulse: rgba(0, 255, 170, 0.4);
            --text-white: #f0f5ff;
            --text-dark: #708499;
            --crimson: #ff3355;
            --amber: #ffaa00;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Consolas', 'Courier New', monospace; }
        body { background-color: var(--bg-main); color: var(--text-white); padding: 25px; overflow-x: hidden; min-height: 100vh; }

        /* Scanning Grid Background Line Layout */
        body::before {
            content: ""; position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
            background: linear-gradient(rgba(18, 24, 38, 0) 50%, rgba(0, 0, 0, 0.25) 50%), linear-gradient(90deg, rgba(0, 255, 170, 0.03), rgba(0, 0, 0, 0));
            background-size: 100% 4px, 6px 100%; z-index: -1; pointer-events: none;
        }

        .container { max-width: 1400px; margin: 0 auto; animation: bootUp 0.6s ease-out; }
        @keyframes bootUp { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

        header {
            background: var(--panel-bg); border: 1px solid var(--neon-dim); padding: 25px;
            border-radius: 8px; display: flex; justify-content: space-between; align-items: center;
            margin-bottom: 30px; box-shadow: 0 0 25px rgba(0, 255, 170, 0.1), inset 0 0 15px rgba(0, 255, 170, 0.05);
        }
        .logo-title h1 { font-size: 1.8rem; letter-spacing: 2px; color: var(--neon-glow); text-shadow: 0 0 12px var(--neon-pulse); }
        .logo-title p { color: var(--text-dark); font-size: 0.8rem; margin-top: 4px; }

        /* Auth Portal Elements */
        .auth-container { max-width: 420px; margin: 120px auto; padding: 35px; background: var(--panel-bg); border: 1px solid var(--neon-dim); border-radius: 8px; box-shadow: 0 0 40px rgba(0,255,170,0.15); }
        .auth-header { text-align: center; margin-bottom: 25px; }
        .auth-header h2 { color: var(--neon-glow); text-shadow: 0 0 10px var(--neon-pulse); letter-spacing: 1px; }
        
        .field-group { margin-bottom: 20px; }
        .field-group label { display: block; margin-bottom: 8px; font-size: 0.85rem; color: var(--neon-glow); text-transform: uppercase; }
        input[type="text"], input[type="password"], input[type="number"], input[type="datetime-local"] {
            width: 100%; padding: 12px; background: #000; border: 1px solid var(--neon-dim); color: var(--text-white); border-radius: 4px; outline: none; transition: all 0.3s ease;
        }
        input:focus { border-color: var(--neon-glow); box-shadow: 0 0 15px rgba(0, 255, 170, 0.25); }

        .btn {
            display: inline-block; padding: 12px 24px; background: transparent; border: 1px solid var(--neon-glow);
            color: var(--neon-glow); text-transform: uppercase; font-weight: bold; font-size: 0.85rem; cursor: pointer;
            border-radius: 4px; transition: all 0.25s ease; text-align: center; text-shadow: 0 0 5px var(--neon-pulse);
            box-shadow: 0 0 10px rgba(0, 255, 170, 0.05);
        }
        .btn:hover { background: var(--neon-glow); color: var(--bg-main); box-shadow: 0 0 20px var(--neon-glow); text-shadow: none; }
        .btn-danger { border-color: var(--crimson); color: var(--crimson); text-shadow: 0 0 5px rgba(255, 51, 85, 0.4); }
        .btn-danger:hover { background: var(--crimson); color: var(--text-white); box-shadow: 0 0 20px var(--crimson); }

        /* Content Layout Framework Panels */
        .workspace-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-bottom: 30px; }
        @media (max-width: 950px) { .workspace-grid { grid-template-columns: 1fr; } }

        .panel-card { background: var(--panel-bg); border: 1px solid var(--neon-dim); padding: 25px; border-radius: 8px; box-shadow: 0 0 20px rgba(0,0,0,0.5); position: relative; }
        .panel-card::after { content: ""; position: absolute; top: 0; left: 0; width: 10px; height: 10px; border-top: 2px solid var(--neon-glow); border-left: 2px solid var(--neon-glow); }
        .panel-title { border-bottom: 1px dashed var(--neon-dim); padding-bottom: 12px; margin-bottom: 20px; color: var(--neon-glow); font-size: 1.2rem; display: flex; justify-content: space-between; align-items: center; }

        .tool-selector-block { max-height: 130px; overflow-y: auto; border: 1px solid var(--neon-dim); padding: 10px; background: #000; border-radius: 4px; }
        .tool-checkbox { display: flex; align-items: center; margin-bottom: 8px; font-size: 0.85rem; }
        .tool-checkbox input { margin-right: 10px; accent-color: var(--neon-glow); }

        /* Endpoint UI Layout */
        .endpoint-wrapper { max-height: 380px; overflow-y: auto; padding-right: 8px; }
        .endpoint-line { background: #000; padding: 12px; border-radius: 4px; border-left: 3px solid var(--neon-glow); margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; }
        .endpoint-url { font-size: 0.8rem; color: var(--text-dark); overflow-x: auto; white-space: nowrap; max-width: 80%; padding-top: 4px; }

        /* Data Matrix Tables */
        .table-scroll { overflow-x: auto; width: 100%; margin-top: 10px; }
        table { width: 100%; border-collapse: collapse; text-align: left; }
        th { background: #000; color: var(--neon-glow); font-size: 0.85rem; padding: 14px; text-transform: uppercase; border-bottom: 1px solid var(--neon-dim); }
        td { padding: 14px; border-bottom: 1px solid rgba(0, 255, 170, 0.05); font-size: 0.9rem; vertical-align: middle; }
        tr:hover td { background: rgba(0, 255, 170, 0.02); }

        .badge { padding: 4px 10px; font-size: 0.75rem; border-radius: 4px; font-weight: bold; text-transform: uppercase; display: inline-block; }
        .badge-active { background: rgba(0, 255, 170, 0.15); color: var(--neon-glow); border: 1px solid var(--neon-glow); box-shadow: 0 0 10px var(--neon-pulse); }
        .badge-suspended { background: rgba(255, 51, 85, 0.15); color: var(--crimson); border: 1px solid var(--crimson); }
        .badge-expired { background: rgba(255, 170, 0, 0.15); color: var(--amber); border: 1px solid var(--amber); }

        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: #000; }
        ::-webkit-scrollbar-thumb { background: var(--neon-dim); border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--neon-glow); }
    </style>
</head>
<body>
<div class="container">

    {% if view == 'login' %}
    <div class="auth-container">
        <div class="auth-header">
            <h2>GATEWAY CONTROL ACCESS</h2>
            <p style="color: var(--text-dark); font-size: 0.8rem; margin-top: 5px;">ENTER SIGNATURE KEYS</p>
        </div>
        {% if error %}<p style="color: var(--crimson); text-align: center; font-size: 0.85rem; margin-bottom: 15px;">{{ error }}</p>{% endif %}
        <form action="/login" method="POST">
            <div class="field-group">
                <label>Operator Root User</label>
                <input type="text" name="username" required autocomplete="off">
            </div>
            <div class="field-group">
                <label>Cipher Key Password</label>
                <input type="password" name="password" required>
            </div>
            <button type="submit" class="btn" style="width: 100%; margin-top: 10px;">VERIFY IDENTITY</button>
        </form>
    </div>

    {% elif view == 'main' %}
    <header>
        <div class="logo-title">
            <h1>SHAYAN_EXPLORER</h1>
            <p>CORE ROUTING SECURITY PLATFORM // ACTIVE STATUS ONLINE 2026</p>
        </div>
        <a href="/logout" class="btn btn-danger">DISCONNECT TERMINAL</a>
    </header>

    <div class="workspace-grid">
        <div class="panel-card">
            <div class="panel-title">MINT GATEWAY ACCESS CREDENTIAL</div>
            <form action="/admin/key/generate" method="POST">
                <div class="field-group">
                    <label>Target Client Profile Name</label>
                    <input type="text" name="name" placeholder="Ex: Premium Client Alpha" required autocomplete="off">
                </div>
                <div class="workspace-grid" style="grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 0;">
                    <div class="field-group">
                        <label>Max Volume Request Limit</label>
                        <input type="number" name="limit" value="100" required min="1">
                    </div>
                    <div class="field-group">
                        <label>Strict Validation Timeout Expiry</label>
                        <input type="datetime-local" name="expiry" id="default_expiry" required>
                    </div>
                </div>
                <div class="field-group">
                    <label>Restrict Route Execution Scopes (Empty maps to global access)</label>
                    <div class="tool-selector-block">
                        {% for tool in tools %}
                        <div class="tool-checkbox">
                            <input type="checkbox" name="tools" value="{{ tool }}" id="tool-{{ tool }}">
                            <label for="tool-{{ tool }}">{{ tool | upper }} Verification Module</label>
                        </div>
                        {% endfor %}
                    </div>
                </div>
                <button type="submit" class="btn" style="width: 100%;">GENERATE SECURE AUTHORIZED TOKEN</button>
            </form>
        </div>

        <div class="panel-card">
            <div class="panel-title">LIVE NETWORK ENDPOINT DIRECTORY</div>
            <div class="endpoint-wrapper">
                {% for tool in tools %}
                <div class="endpoint-line">
                    <div style="max-width: 80%;">
                        <span style="color: var(--neon-glow); font-size: 0.85rem; font-weight: bold;">{{ tool | upper }}</span>
                        <div class="endpoint-url" id="route-{{ tool }}">/api/{{ tool }}?key={KEY_STRING}&{% if tool in ['imei','ifsc','pincode','ip','challan','vehicle'] %}{{tool}}={VALUE}{% elif tool in ['upi','email','id','username'] %}{{tool}}={VALUE}{% else %}num={VALUE}{% endif %}</div>
                    </div>
                    <button class="btn" style="padding: 6px 12px; font-size: 0.75rem;" onclick="copySystemRoute('route-{{ tool }}')">COPY</button>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>

    <div class="panel-card" style="margin-bottom: 30px;">
        <div class="panel-title">ACTIVE RUNTIME AUTHORIZATION TARGETS REGISTRY</div>
        <div class="table-scroll">
            <table>
                <thead>
                    <tr>
                        <th>Generated Token Key</th>
                        <th>Client Reference</th>
                        <th>Usage Vol</th>
                        <th>Expirations Target</th>
                        <th>Route Bounds</th>
                        <th>State</th>
                        <th>Administrative Operations</th>
                    </tr>
                </thead>
                <tbody>
                    {% for key, data in keys.items() %}
                    <tr>
                        <td style="color: var(--neon-glow); font-weight: bold;"><code>{{ key }}</code></td>
                        <td>{{ data.name }}</td>
                        <td>{{ data.usages }} / {{ data.limit }}</td>
                        <td style="font-size: 0.8rem; color: var(--text-dark);">{{ data.expiry.replace('T', ' ') }}</td>
                        <td style="max-width: 150px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 0.8rem;">
                            {{ data.allowed_tools | join(', ') }}
                        </td>
                        <td><span class="badge badge-{{ data.status }}">{{ data.status }}</span></td>
                        <td>
                            {% if data.status == 'active' %}
                            <a href="/admin/key/action/{{ key }}/suspend" class="btn" style="padding: 4px 8px; font-size: 0.7rem; border-color: var(--amber); color: var(--amber);">SUSPEND</a>
                            {% else %}
                            <a href="/admin/key/action/{{ key }}/unsuspend" class="btn" style="padding: 4px 8px; font-size: 0.7rem;">REVIVE</a>
                            {% endif %}
                            <a href="/admin/key/action/{{ key }}/delete" class="btn btn-danger" style="padding: 4px 8px; font-size: 0.7rem;" onclick="return confirm('Purge authorization profile?')">PURGE</a>
                        </td>
                    </tr>
                    {% else %}
                    <tr><td colspan="7" style="text-align: center; color: var(--text-dark);">No access tokens found in runtime data registry.</td></tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

    <div class="panel-card">
        <div class="panel-title">GATEWAY CORE ACCESS AUDIT TELEMETRY</div>
        <div class="table-scroll" style="max-height: 280px;">
            <table>
                <thead>
                    <tr>
                        <th>Timestamp Frame</th>
                        <th>Execution Token Key</th>
                        <th>Client Name</th>
                        <th>Triggered Module</th>
                        <th>Searched Parameters</th>
                    </tr>
                </thead>
                <tbody>
                    {% for log in logs | reverse %}
                    <tr>
                        <td style="color: var(--text-dark); font-size: 0.8rem;">{{ log.timestamp }}</td>
                        <td><code>{{ log.key }}</code></td>
                        <td>{{ log.name }}</td>
                        <td><span style="color: var(--neon-glow);">{{ log.tool | upper }}</span></td>
                        <td><span style="color: #fff; background: rgba(0, 255, 170, 0.08); padding: 3px 6px; border-radius: 3px; font-size: 0.85rem;">{{ log.query }}</span></td>
                    </tr>
                    {% else %}
                    <tr><td colspan="5" style="text-align: center; color: var(--text-dark);">Awaiting network routing traffic logs events...</td></tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    {% endif %}

</div>

<script>
// Automatically set dynamic default expiry selection field 48 hours out from current timestamp
if(document.getElementById('default_expiry')) {
    var futureOffset = new Date();
    futureOffset.setHours(futureOffset.getHours() + 48);
    var formattedString = futureOffset.toISOString().slice(0, 16);
    document.getElementById('default_expiry').value = formattedString;
}

function copySystemRoute(targetElement) {
    var textValue = document.getElementById(targetElement).innerText;
    var remoteHost = window.location.origin;
    var processingBuffer = remoteHost + textValue;
    
    navigator.clipboard.writeText(processingBuffer).then(function() {
        alert("System route blueprint vector stored to clipboard matrix safely.");
    }).catch(function(err) {
        console.error('Failed copying context route stream: ', err);
    });
}
</script>
</body>
</html>
"""

@app.route('/')
def home():
    synchronize_key_states()
    if not session.get('logged_in'):
        return render_template_string(HTML_INTERFACE, view='login')
    return redirect(url_for('admin_dashboard'))

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if username == ADMIN_USER and password == ADMIN_PASS:
        session['logged_in'] = True
        return redirect(url_for('admin_dashboard'))
    return render_template_string(HTML_INTERFACE, view='login', error="Access Denied: Invalid Security Signature.")

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('home'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('home'))
    synchronize_key_states()
    db = load_system_database()
    return render_template_string(
        HTML_INTERFACE, 
        view='main', 
        keys=db["keys"], 
        logs=db["logs"], 
        tools=SUPPORTED_TOOLS
    )

@app.route('/admin/key/generate', methods=['POST'])
def generate_key():
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized Terminal Access"}), 403
        
    name = request.form.get('name', 'External Client')
    limit = int(request.form.get('limit', 100))
    expiry = request.form.get('expiry')
    selected_tools = request.form.getlist('tools')
    
    if not expiry:
        expiry = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M")
        
    new_token_key = f"SHAYAN_{uuid.uuid4().hex[:10].upper()}"
    
    db = load_system_database()
    db["keys"][new_token_key] = {
        "name": name,
        "limit": limit,
        "usages": 0,
        "expiry": expiry,
        "allowed_tools": selected_tools if selected_tools else ["all"],
        "status": "active"
    }
    save_system_database(db)
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/key/action/<key_id>/<action>')
def key_action(key_id, action):
    if not session.get('logged_in'):
        return redirect(url_for('home'))
        
    db = load_system_database()
    if key_id in db["keys"]:
        if action == "suspend":
            db["keys"][key_id]["status"] = "suspended"
        elif action == "unsuspend":
            db["keys"][key_id]["status"] = "active"
        elif action == "delete":
            del db["keys"][key_id]
            
    save_system_database(db)
    return redirect(url_for('admin_dashboard'))

# Proxy Verification API Engine Routing
@app.route('/api/<tool_name>', methods=['GET'])
def proxy_gateway(tool_name):
    if tool_name not in SUPPORTED_TOOLS:
        return jsonify({"error": f"Endpoint Module '{tool_name}' Not Available Matrix"}), 404
        
    user_key = request.args.get('key')
    db = load_system_database()
    
    # Run key status verification
    if not user_key or user_key not in db["keys"]:
        return jsonify({"error": "The key is invalid. Please buy a new key.", "status": "invalid"}), 401
        
    key_data = db["keys"][user_key]
    
    if key_data["status"] == "suspended":
        return jsonify({"error": "The key is suspended by admin.", "status": "suspended"}), 403
        
    expiry_dt = datetime.strptime(key_data["expiry"], "%Y-%m-%dT%H:%M")
    if datetime.now() > expiry_dt:
        db["keys"][user_key]["status"] = "expired"
        save_system_database(db)
        return jsonify({"error": "The key is expired. Please buy a new key.", "status": "expired"}), 401
        
    if key_data["usages"] >= key_data["limit"]:
        return jsonify({"error": "Rate limit usage boundary reached for token.", "status": "limited"}), 429
        
    if "all" not in key_data["allowed_tools"] and tool_name not in key_data["allowed_tools"]:
        return jsonify({"error": f"This key does not have access to the '{tool_name}' endpoint.", "status": "unauthorized"}), 403
        
    # Process Logging Analytics Tracker Matrix
    query_params = request.args.to_dict()
    search_query = next((v for k, v in query_params.items() if k != 'key'), "N/A")
    
    db["logs"].append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "key": user_key,
        "name": key_data["name"],
        "tool": tool_name,
        "query": search_query
    })
    
    db["keys"][user_key]["usages"] += 1
    save_system_database(db)
    
    # Map and construct request array pointing back to downstream server securely
    downstream_params = query_params.copy()
    downstream_params['key'] = "vernex-6a9dc4fdd5923c40b0aba27bf1e39e3f"
    
    try:
        response = requests.get(f"{TARGET_BASE_API}/{tool_name}", params=downstream_params, timeout=12)
        return (response.content, response.status_code, response.headers.items())
    except requests.exceptions.RequestException:
        return jsonify({"error": "Failed communicating data streams with base server matrix."}), 502

if __name__ == '__main__':
    app.run(debug=True)

