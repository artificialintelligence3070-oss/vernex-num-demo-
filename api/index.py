import os
import time
import uuid
import requests
from flask import Flask, request, jsonify, redirect, url_for, session, render_template_string

app = Flask(__name__)
app.secret_key = "shayan_explorer_ultra_secure_glow_vault"

# Admin Authentication credentials
ADMIN_USER = "vernex"
ADMIN_PASS = "vernex@16vx"

# In-memory storage structures
API_KEYS = {}
REQUEST_LOGS = []

# Map of supported service modules (20 Features)
TARGET_APIS = {
    "adv": "https://ft-osint-api.duckdns.org/api/adv",
    "paytm": "https://ft-osint-api.duckdns.org/api/paytm",
    "imei": "https://ft-osint-api.duckdns.org/api/imei",
    "calltracer": "https://ft-osint-api.duckdns.org/api/calltracer",
    "upi": "https://ft-osint-api.duckdns.org/api/upi",
    "ifsc": "https://ft-osint-api.duckdns.org/api/ifsc",
    "number": "https://ft-osint-api.duckdns.org/api/number",
    "pincode": "https://ft-osint-api.duckdns.org/api/pincode",
    "ip": "https://ft-osint-api.duckdns.org/api/ip",
    "challan": "https://ft-osint-api.duckdns.org/api/challan",
    "ff": "https://ft-osint-api.duckdns.org/api/ff",
    "bgmi": "https://ft-osint-api.duckdns.org/api/bgmi",
    "snap": "https://ft-osint-api.duckdns.org/api/snap",
    "email": "https://ft-osint-api.duckdns.org/api/email",
    "vehicle": "https://ft-osint-api.duckdns.org/api/vehicle",
    "git": "https://ft-osint-api.duckdns.org/api/git",
    "insta": "https://ft-osint-api.duckdns.org/api/insta",
    "tg": "https://ft-osint-api.duckdns.org/api/tg",
    "tgidinfo": "https://ft-osint-api.duckdns.org/api/tgidinfo",
    "numleak": "https://ft-osint-api.duckdns.org/api/numleak"
}

UPSTREAM_TOKEN = "vernex-6a9dc4fdd5923c40b0aba27bf1e39e3f"

# Embedded Responsive 3D Cyber Dashboard UI
DASHBOARD_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SHAYAN_EXPLORER | Command Core</title>
    <style>
        :root {
            --bg-base: #06060e;
            --bg-surface: #0b0f19;
            --neon-glow: #00d2ff;
            --neon-dim: rgba(0, 210, 255, 0.15);
            --border-color: #1e293b;
            --text-main: #f1f5f9;
        }
        body {
            background-color: var(--bg-base);
            color: var(--text-main);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding: 0;
        }
        header {
            background: var(--bg-surface);
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid var(--neon-glow);
            box-shadow: 0 0 15px var(--neon-dim);
        }
        header h1 {
            margin: 0;
            font-size: 1.4rem;
            letter-spacing: 2px;
            color: var(--neon-glow);
            text-shadow: 0 0 8px var(--neon-glow);
        }
        .logout-btn {
            padding: 0.5rem 1rem;
            background: transparent;
            border: 1px solid #ef4444;
            color: #ef4444;
            border-radius: 4px;
            text-decoration: none;
            font-weight: bold;
            transition: 0.3s;
        }
        .logout-btn:hover {
            background: #ef4444;
            color: #fff;
            box-shadow: 0 0 10px rgba(239, 68, 68, 0.4);
        }
        .container {
            max-width: 1400px;
            margin: 2rem auto;
            padding: 0 1rem;
            display: grid;
            grid-template-columns: 1fr;
            gap: 2rem;
        }
        @media(min-width: 992px) {
            .container { grid-template-columns: 1fr 2fr; }
        }
        .panel-card {
            background: var(--bg-surface);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1.5rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.7);
            transform: perspective(800px) rotateX(1deg);
            transition: transform 0.4s, border-color 0.4s, box-shadow 0.4s;
        }
        .panel-card:hover {
            transform: perspective(800px) rotateX(0deg) scale(1.01);
            border-color: var(--neon-glow);
            box-shadow: 0 0 20px var(--neon-dim);
        }
        h2 {
            margin-top: 0;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 0.5rem;
            color: var(--neon-glow);
            font-size: 1.15rem;
            text-shadow: 0 0 5px var(--neon-dim);
        }
        label {
            display: block;
            margin: 0.8rem 0 0.3rem 0;
            font-size: 0.85rem;
            opacity: 0.85;
        }
        input[type="text"], input[type="number"], select {
            width: 100%;
            padding: 10px;
            background: #090d16;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            color: #fff;
            box-sizing: border-box;
        }
        input:focus, select:focus {
            outline: none;
            border-color: var(--neon-glow);
        }
        .checkbox-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
            gap: 0.5rem;
            margin-top: 0.5rem;
            max-height: 140px;
            overflow-y: auto;
            padding: 0.5rem;
            background: #090d16;
            border: 1px solid var(--border-color);
            border-radius: 4px;
        }
        .checkbox-item { display: flex; align-items: center; font-size: 0.8rem; }
        .checkbox-item input { margin-right: 5px; }
        .action-submit {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #00d2ff, #0066cc);
            border: none;
            color: white;
            font-weight: bold;
            border-radius: 4px;
            cursor: pointer;
            margin-top: 1rem;
            transition: 0.3s;
        }
        .action-submit:hover {
            filter: brightness(1.2);
            box-shadow: 0 0 12px var(--neon-glow);
        }
        .quick-copy-area {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
            gap: 0.6rem;
            margin-bottom: 1.5rem;
        }
        .copy-pill {
            background: #090d16;
            border: 1px dashed var(--neon-glow);
            padding: 8px 12px;
            border-radius: 4px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.8rem;
            cursor: pointer;
            transition: 0.2s;
        }
        .copy-pill:hover {
            background: var(--neon-dim);
            transform: translateY(-1px);
        }
        .table-wrapper {
            overflow-x: auto;
            margin-top: 1rem;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            text-align: left;
            font-size: 0.85rem;
        }
        th, td {
            padding: 12px;
            border-bottom: 1px solid var(--border-color);
        }
        th { background: #090d16; color: var(--neon-glow); }
        .badge {
            padding: 3px 6px;
            border-radius: 3px;
            font-size: 0.75rem;
            font-weight: bold;
        }
        .badge-active { background: rgba(34, 197, 94, 0.15); color: #22c55e; border: 1px solid #22c55e; }
        .badge-suspended { background: rgba(239, 68, 68, 0.15); color: #ef4444; border: 1px solid #ef4444; }
        .mini-form { display: inline-block; margin: 0 2px; }
        .btn-mini {
            padding: 4px 8px;
            font-size: 0.75rem;
            border-radius: 3px;
            cursor: pointer;
            border: 1px solid var(--border-color);
            background: #0f172a;
            color: #fff;
            transition: 0.2s;
        }
        .btn-mini:hover { border-color: var(--neon-glow); color: var(--neon-glow); }
        .log-terminal {
            background: #040408;
            border: 1px solid #1e293b;
            font-family: monospace;
            padding: 1rem;
            border-radius: 6px;
            max-height: 250px;
            overflow-y: auto;
            font-size: 0.8rem;
            color: #38bdf8;
        }
        .log-line { margin-bottom: 0.4rem; border-left: 2px solid var(--neon-glow); padding-left: 6px; }
    </style>
</head>
<body>

<header>
    <h1>SHAYAN_EXPLORER OSINT CORE v3</h1>
    <a href="/logout" class="logout-btn">DISCONNECT Engine</a>
</header>

<div class="container">
    <div style="display: flex; flex-direction: column; gap: 2rem;">
        <div class="panel-card">
            <h2>Generate Allocation Token</h2>
            <form action="/api/v1/generate-key" method="POST">
                <label>User Identifier / Description</label>
                <input type="text" name="name" placeholder="Client Tracking Label" required autocomplete="off">
                
                <label>Total Global Requests Counter Limit</label>
                <input type="number" name="limit" value="1000" required>
                
                <label>Lifespan Span Interval</label>
                <select name="duration_days" id="gen_duration">
                    <option value="lifetime">Unlimited Lifetime Route</option>
                    <option value="1">24 Hours (1 Day)</option>
                    <option value="2">48 Hours (2 Days)</option>
                    <option value="7">1 Week</option>
                    <option value="30">30 Days</option>
                </select>
                
                <label>Allowed Features Assignment Scope</label>
                <select name="scope_type" id="gen_scope" onchange="toggleScopeGrid()">
                    <option value="all">Grant All 20 Active Tools</option>
                    <option value="custom">Custom Specified Tool Scope Selection</option>
                </select>
                
                <div class="checkbox-grid" id="gen_apis_grid" style="display:none;">
                    {% for feat in features %}
                    <div class="checkbox-item">
                        <input type="checkbox" name="apis" value="{{ feat }}" id="gen_feat_{{ feat }}">
                        <label style="display:inline; margin:0;" for="gen_feat_{{ feat }}">{{ feat }}</label>
                    </div>
                    {% endfor %}
                </div>
                
                <button type="submit" class="action-submit">Forge Access Token</button>
            </form>
        </div>
        
        <div class="panel-card">
            <h2>Live Request System Logs</h2>
            <div class="log-terminal">
                {% if logs %}
                    {% for log in logs %}
                    <div class="log-line">
                        [{{ log.timestamp }}] {{ log.name }} -> {{ log.endpoint }} | {{ log.query }}
                    </div>
                    {% endfor %}
                {% else %}
                    <div style="color:#64748b;">No active query streams hitting the application layer...</div>
                {% endif %}
            </div>
        </div>
    </div>

    <div style="display: flex; flex-direction: column; gap: 2rem;">
        <div class="panel-card">
            <h2>1-Click Endpoint Route Copy Toolkit (Without Key Element Base)</h2>
            <div class="quick-copy-area">
                {% for feat in features %}
                <div class="copy-pill" onclick="copyEndpointRoute('{{ feat }}')">
                    <span>/api/{{ feat }}</span>
                    <span style="font-size:0.7rem; color:var(--neon-glow);">[COPY]</span>
                </div>
                {% endfor %}
            </div>
        </div>

        <div class="panel-card">
            <h2>Active Keys Registry State Management Matrix</h2>
            <div class="table-wrapper">
                <table>
                    <thead>
                        <tr>
                            <th>User Target</th>
                            <th>Active Token Pattern</th>
                            <th>Usage Progress</th>
                            <th>Lifespan Deadline Status</th>
                            <th>Operational State</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% if keys %}
                            {% for token, details in keys.items() %}
                            <tr>
                                <td><strong>{{ details.name }}</strong></td>
                                <td style="color:var(--neon-glow); font-family:monospace;">{{ token }}</td>
                                <td>{{ details.req_count }} / {{ details.limit }}</td>
                                <td>
                                    {% if details.lifetime %}
                                        <span style="color:#a855f7;">LIFETIME</span>
                                    {% else %}
                                        <span class="time-countdown" data-expire="{{ details.expires_at }}">Calculating</span>
                                    {% endif %}
                                </td>
                                <td>
                                    {% if details.status == 'active' %}
                                        <span class="badge badge-active">ONLINE</span>
                                    {% else %}
                                        <span class="badge badge-suspended">SUSPENDED</span>
                                    {% endif %}
                                </td>
                                <td>
                                    <form action="/api/v1/action-key" method="POST" class="mini-form">
                                        <input type="hidden" name="token" value="{{ token }}">
                                        {% if details.status == 'active' %}
                                        <input type="hidden" name="operation" value="suspend">
                                        <button type="submit" class="btn-mini" style="color:#f97316;">Suspend</button>
                                        {% else %}
                                        <input type="hidden" name="operation" value="unsuspend">
                                        <button type="submit" class="btn-mini" style="color:#22c55e;">Activate</button>
                                        {% endif %}
                                    </form>
                                    <form action="/api/v1/action-key" method="POST" class="mini-form" onsubmit="return confirm('Confirm token deletion workflow?');">
                                        <input type="hidden" name="token" value="{{ token }}">
                                        <input type="hidden" name="operation" value="delete">
                                        <button type="submit" class="btn-mini" style="color:#ef4444;">Delete</button>
                                    </form>
                                </td>
                            </tr>
                            {% endfor %}
                        {% else %}
                            <tr>
                                <td colspan="6" style="text-align:center; color:#64748b; padding:2rem;">No active generation tracking patterns instantiated within application pool.</td>
                            </tr>
                        {% endif %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>

<script>
    function toggleScopeGrid() {
        const val = document.getElementById('gen_scope').value;
        const grid = document.getElementById('gen_apis_grid');
        grid.style.display = (val === 'custom') ? 'grid' : 'none';
    }

    function copyEndpointRoute(endpoint) {
        const host = window.location.origin;
        const fullUrl = `${host}/api/${endpoint}?key=YOUR_KEY&num=`;
        navigator.clipboard.writeText(fullUrl).then(() => {
            alert(`Copied layout design context: /api/${endpoint}`);
        });
    }

    function updateCountdowns() {
        const now = Math.floor(Date.now() / 1000);
        document.querySelectorAll('.time-countdown').forEach(el => {
            const expireEpoch = parseInt(el.getAttribute('data-expire'));
            if (!isNaN(expireEpoch)) {
                const diff = expireEpoch - now;
                if (diff <= 0) {
                    el.textContent = "EXPIRED";
                    el.style.color = "#ef4444";
                } else {
                    const hrs = Math.floor(diff / 3600);
                    const mins = Math.floor((diff % 3600) / 60);
                    el.textContent = `${hrs}h ${mins}m left`;
                    el.style.color = "#22c55e";
                }
            }
        });
    }
    setInterval(updateCountdowns, 1000);
    updateCountdowns();
</script>
</body>
</html>
"""

def evaluate_key_status(key_string):
    if key_string not in API_KEYS:
        return {"valid": False, "reason": "The key is invalid. Please buy a new key."}
    
    key_data = API_KEYS[key_string]
    if key_data.get("status") == "suspended":
        return {"valid": False, "reason": "The key is suspended by admin."}
        
    if not key_data.get("lifetime", False):
        if time.time() > key_data.get("expires_at", 0):
            return {"valid": False, "reason": "The key is expired. Please buy a new key."}
            
    if key_data.get("req_count", 0) >= key_data.get("limit", 0):
        return {"valid": False, "reason": "Request limit reached for this key token."}
        
    return {"valid": True, "data": key_data}

@app.route('/')
def home_redirect():
    if session.get('logged_in'):
        return redirect(url_for('dashboard_panel'))
    return redirect(url_for('login_panel'))

@app.route('/login', methods=['GET', 'POST'])
def login_panel():
    msg = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USER and password == ADMIN_PASS:
            session['logged_in'] = True
            return redirect(url_for('dashboard_panel'))
        else:
            msg = "Invalid authorization credentials."
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SHAYAN_EXPLORER | Secure Login</title>
        <style>
            body {{ background: #080810; color: #e2e8f0; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
            .login-card {{ background: rgba(15, 23, 42, 0.9); border: 1px solid #00d2ff; box-shadow: 0 0 20px rgba(0, 210, 255, 0.2); padding: 2.5rem; border-radius: 12px; width: 100%; max-width: 380px; text-align: center; }}
            h2 {{ color: #00d2ff; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 1.5rem; }}
            input[type="text"], input[type="password"] {{ width: 100%; padding: 12px; margin: 10px 0; background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; color: #fff; box-sizing: border-box; }}
            button {{ width: 100%; padding: 12px; background: linear-gradient(135deg, #00d2ff, #0066cc); border: none; border-radius: 6px; color: white; font-weight: bold; cursor: pointer; margin-top: 15px; }}
            .error {{ color: #ef4444; margin-top: 10px; font-size: 0.9rem; }}
        </style>
    </head>
    <body>
        <div class="login-card">
            <h2>System Access</h2>
            <form method="POST">
                <input type="text" name="username" placeholder="Username" required autocomplete="off">
                <input type="password" name="password" placeholder="Password" required>
                <button type="submit">Initialize Engine</button>
            </form>
            {"<p class='error'>" + msg + "</p>" if msg else ""}
        </div>
    </body>
    </html>
    '''

@app.route('/logout')
def logout_action():
    session.pop('logged_in', None)
    return redirect(url_for('login_panel'))

@app.route('/dashboard')
def dashboard_panel():
    if not session.get('logged_in'):
        return redirect(url_for('login_panel'))
    return render_template_string(DASHBOARD_HTML_TEMPLATE, keys=API_KEYS, logs=REQUEST_LOGS, features=TARGET_APIS)

@app.route('/api/v1/generate-key', methods=['POST'])
def generate_key_endpoint():
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
        
    name = request.form.get('name', 'Default_User')
    limit = int(request.form.get('limit', 100))
    duration_days = request.form.get('duration_days')
    scope_option = request.form.get('scope_type')
    selected_apis = request.form.getlist('apis')
    
    lifetime_mode = True
    expires_at = 0
    if duration_days and duration_days != "lifetime":
        lifetime_mode = False
        expires_at = time.time() + (float(duration_days) * 86400)
        
    allowed_endpoints = list(TARGET_APIS.keys()) if scope_option == "all" else selected_apis
    new_token = "SHAYAN-" + str(uuid.uuid4()).upper().replace("-", "")[:16]
    
    API_KEYS[new_token] = {
        "name": name,
        "limit": limit,
        "req_count": 0,
        "lifetime": lifetime_mode,
        "expires_at": expires_at,
        "scope": allowed_endpoints,
        "status": "active"
    }
    return redirect(url_for('dashboard_panel'))

@app.route('/api/v1/action-key', methods=['POST'])
def action_key_endpoint():
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
        
    target_token = request.form.get('token')
    operation = request.form.get('operation')
    
    if target_token in API_KEYS:
        if operation == "suspend":
            API_KEYS[target_token]["status"] = "suspended"
        elif operation == "unsuspend":
            API_KEYS[target_token]["status"] = "active"
        elif operation == "delete":
            del API_KEYS[target_token]
            
    return redirect(url_for('dashboard_panel'))

@app.route('/api/<endpoint>')
def gateway_proxy(endpoint):
    user_key = request.args.get('key')
    evaluation = evaluate_key_status(user_key)
    
    if not evaluation["valid"]:
        return jsonify({"status": "failed", "error": evaluation["reason"]}), 403
        
    key_config = evaluation["data"]
    if endpoint not in TARGET_APIS or endpoint not in key_config["scope"]:
        return jsonify({"status": "failed", "error": "Endpoint access route restriction triggered."}), 403

    query_params = request.args.to_dict()
    query_params['key'] = UPSTREAM_TOKEN 
    
    log_payload = {
        "timestamp": time.strftime('%H:%M:%S'),
        "key": user_key,
        "name": key_config["name"],
        "endpoint": endpoint,
        "query": str({k: v for k, v in query_params.items() if k != 'key'})
    }
    REQUEST_LOGS.insert(0, log_payload)
    if len(REQUEST_LOGS) > 100:
        REQUEST_LOGS.pop()

    API_KEYS[user_key]["req_count"] += 1

    try:
        resp = requests.get(TARGET_APIS[endpoint], params=query_params, timeout=10)
        output_data = resp.json()
        if isinstance(output_data, dict):
            output_data.pop('@ftgamer2', None)
            output_data.pop('@bornex Ultra', None)
            output_data.pop('channel', None)
            output_data['developer'] = "SHAYAN_EXPLORER"
        return jsonify(output_data), resp.status_code
    except Exception as e:
        return jsonify({"status": "failed", "error": "Upstream processing timeout"}), 500



