from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import requests
from datetime import datetime
import secrets

app = Flask(__name__)
CORS(app)

# Upstream engine destination configurations
UPSTREAM_BASE_URL = "https://ft-osint-api.duckdns.org/api"
MASTER_KEY = "explorer16"

# Stateful tracking dictionaries (In-Memory Sandbox Storage)
API_KEYS_DB = {
    "vx-osint": {
        "owner": "Master Deployment",
        "key": "vx-osint",
        "daily_limit": 5000,
        "used_count": 0,
        "is_lifetime": True,
        "expiry_date": "",
        "status": "Active",
        "scopes": ["ALL"]
    }
}
PIPELINE_LOGS = []

# Embedded UI Assets Panel (SHAYAN_EXPLORER HUB Theme Layout)
HTML_DASHBOARD = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SHAYAN_EXPLORER HUB</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {
            background-color: #0b0a0f;
            color: #e2e1e9;
            font-family: 'Courier New', Courier, monospace;
        }
        .glow-border {
            border: 1px solid #2d1b4e;
            box-shadow: 0 0 10px rgba(147, 51, 234, 0.1);
        }
        .accent-purple { color: #bf5af2; }
        .bg-purple-accent { background-color: #9d4edd; }
        .bg-purple-accent:hover { background-color: #7b2cbf; }
    </style>
</head>
<body class="p-4 md:p-8">

    <!-- AUTHENTICATION GATEWAY CONTROLLER -->
    <div id="login-screen" class="max-w-md mx-auto my-20 p-6 bg-[#12111a] rounded-lg glow-border">
        <h2 class="text-xl font-bold tracking-widest text-center mb-6 accent-purple">SHAYAN_EXPLORER HUB</h2>
        <div class="mb-4">
            <label class="block text-xs uppercase mb-1 text-gray-400">System Operator Identity</label>
            <input type="text" id="username" class="w-full bg-[#1b1926] border border-[#2d1b4e] p-2 rounded text-sm focus:outline-none focus:border-purple-500 text-white" value="vernex">
        </div>
        <div class="mb-6">
            <label class="block text-xs uppercase mb-1 text-gray-400">Security Credentials</label>
            <input type="password" id="password" class="w-full bg-[#1b1926] border border-[#2d1b4e] p-2 rounded text-sm focus:outline-none focus:border-purple-500 text-white" value="vernex@16vx">
        </div>
        <button onclick="handleLogin()" class="w-full bg-purple-accent text-white text-xs py-3 font-bold tracking-widest rounded transition-all">ESTABLISH CONNECTION</button>
        <p id="login-err" class="text-red-500 text-xs mt-3 text-center hidden">Access credentials invalid.</p>
    </div>

    <!-- MAIN INTERACTIVE HUB INTERFACE -->
    <div id="dashboard-screen" class="max-w-6xl mx-auto hidden">
        
        <header class="flex justify-between items-center mb-8 border-b border-[#2d1b4e] pb-4">
            <div>
                <h1 class="text-xl font-bold tracking-widest text-white uppercase">SHAYAN_EXPLORER HUB</h1>
                <p class="text-[10px] text-gray-500">SYSTEM ARCHITECTURE: DEV SHAYAN_EXPLORER // INFRASTRUCTURE SECURE</p>
            </div>
            <div class="flex items-center gap-4">
                <span class="text-xs border border-[#2d1b4e] px-3 py-1 rounded text-gray-400 uppercase tracking-wider text-[10px]">VIEW_SYSTEM_APIS</span>
                <button onclick="handleLogout()" class="text-xs text-red-400 hover:underline text-[10px] uppercase">LOGOUT</button>
            </div>
        </header>

        <!-- SUB PANEL 01: KEY STRATEGY CREATION GENERATOR -->
        <section class="bg-[#12111a] p-6 rounded-lg glow-border mb-8">
            <h2 class="text-xs font-bold tracking-widest accent-purple uppercase mb-4 flex items-center gap-2">
                <span>●</span> PROPOSE SYSTEM COMMUNICATIONS KEY
            </h2>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                <div>
                    <label class="block text-[10px] uppercase text-gray-400 mb-1">Target Owner Name</label>
                    <input type="text" id="new-owner" placeholder="e.g. Client Profile" class="w-full bg-[#1b1926] border border-[#2d1b4e] p-2 rounded text-xs text-white">
                </div>
                <div>
                    <label class="block text-[10px] uppercase text-gray-400 mb-1">Custom Assignment String</label>
                    <input type="text" id="new-token" placeholder="Random token string if left empty" class="w-full bg-[#1b1926] border border-[#2d1b4e] p-2 rounded text-xs text-white">
                </div>
                <div>
                    <label class="block text-[10px] uppercase text-gray-400 mb-1">Daily Call Limit Volume</label>
                    <input type="number" id="new-limit" value="2500" class="w-full bg-[#1b1926] border border-[#2d1b4e] p-2 rounded text-xs text-white">
                </div>
                <div>
                    <label class="block text-[10px] uppercase text-gray-400 mb-1">Life Strategy</label>
                    <label class="flex items-center gap-2 mt-3 cursor-pointer text-xs text-gray-300">
                        <input type="checkbox" id="new-lifetime" onchange="toggleDateDisable(this)" class="accent-purple"> 
                        LIFETIME ACCESS TIER
                    </label>
                </div>
                <div class="md:col-span-2">
                    <label class="block text-[10px] uppercase text-gray-400 mb-1">Target Expiration Lifecycle</label>
                    <input type="datetime-local" id="new-expiry" class="w-full bg-[#1b1926] border border-[#2d1b4e] p-2 rounded text-xs text-gray-400">
                </div>
            </div>

            <!-- PRIVILEGED SUB-ROUTE SECURITY SCOPES SELECTION INTERFACE -->
            <div class="mb-6">
                <div class="flex justify-between items-center mb-2">
                    <label class="block text-[10px] uppercase text-gray-400">Route Authorization Privileges Scope</label>
                    <button onclick="selectAllScopes()" class="text-[10px] text-purple-400 hover:underline">Select All Available Sub-Tools</button>
                </div>
                <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 bg-[#1b1926] p-4 rounded border border-[#2d1b4e]" id="scopes-box">
                    <label class="flex items-center gap-2 text-xs text-gray-300"><input type="checkbox" value="ADV" class="scope-item accent-purple"> ADV</label>
                    <label class="flex items-center gap-2 text-xs text-gray-300"><input type="checkbox" value="PAYTM" class="scope-item accent-purple"> PAYTM</label>
                    <label class="flex items-center gap-2 text-xs text-gray-300"><input type="checkbox" value="IMEI" class="scope-item accent-purple"> IMEI</label>
                    <label class="flex items-center gap-2 text-xs text-gray-300"><input type="checkbox" value="CALLTRACER" class="scope-item accent-purple"> CALLTRACER</label>
                    <label class="flex items-center gap-2 text-xs text-gray-300"><input type="checkbox" value="UPI" class="scope-item accent-purple"> UPI</label>
                    <label class="flex items-center gap-2 text-xs text-gray-300"><input type="checkbox" value="IFSC" class="scope-item accent-purple"> IFSC</label>
                    <label class="flex items-center gap-2 text-xs text-gray-300"><input type="checkbox" value="PINCODE" class="scope-item accent-purple"> PINCODE</label>
                    <label class="flex items-center gap-2 text-xs text-gray-300"><input type="checkbox" value="IP" class="scope-item accent-purple"> IP</label>
                    <label class="flex items-center gap-2 text-xs text-gray-300"><input type="checkbox" value="CHALLAN" class="scope-item accent-purple"> CHALLAN</label>
                    <label class="flex items-center gap-2 text-xs text-gray-300"><input type="checkbox" value="FF" class="scope-item accent-purple"> FF</label>
                    <label class="flex items-center gap-2 text-xs text-gray-300"><input type="checkbox" value="BGMI" class="scope-item accent-purple"> BGMI</label>
                    <label class="flex items-center gap-2 text-xs text-gray-300"><input type="checkbox" value="SNAP" class="scope-item accent-purple"> SNAP</label>
                    <label class="flex items-center gap-2 text-xs text-gray-300"><input type="checkbox" value="NUMBER" class="scope-item accent-purple"> NUMBER</label>
                    <label class="flex items-center gap-2 text-xs text-gray-300"><input type="checkbox" value="EMAIL" class="scope-item accent-purple"> EMAIL</label>
                    <label class="flex items-center gap-2 text-xs text-gray-300"><input type="checkbox" value="VEHICLE" class="scope-item accent-purple"> VEHICLE</label>
                    <label class="flex items-center gap-2 text-xs text-gray-300"><input type="checkbox" value="GIT" class="scope-item accent-purple"> GIT</label>
                    <label class="flex items-center gap-2 text-xs text-gray-300"><input type="checkbox" value="INSTA" class="scope-item accent-purple"> INSTA</label>
                    <label class="flex items-center gap-2 text-xs text-gray-300"><input type="checkbox" value="TG" class="scope-item accent-purple"> TG</label>
                    <label class="flex items-center gap-2 text-xs text-gray-300"><input type="checkbox" value="TGIDINFO" class="scope-item accent-purple"> TGIDINFO</label>
                    <label class="flex items-center gap-2 text-xs text-gray-300"><input type="checkbox" value="NUMLEAK" class="scope-item accent-purple"> NUMLEAK</label>
                    <!-- Expanded API Catalog Implementations -->
                    <label class="flex items-center gap-2 text-xs text-gray-300"><input type="checkbox" value="PK" class="scope-item accent-purple"> PK</label>
                    <label class="flex items-center gap-2 text-xs text-gray-300"><input type="checkbox" value="NAME" class="scope-item accent-purple"> NAME</label>
                    <label class="flex items-center gap-2 text-xs text-gray-300"><input type="checkbox" value="AADHAR" class="scope-item accent-purple"> AADHAR</label>
                    <label class="flex items-center gap-2 text-xs text-gray-300"><input type="checkbox" value="NUMTOUPI" class="scope-item accent-purple"> NUMTOUPI</label>
                    <label class="flex items-center gap-2 text-xs text-gray-300"><input type="checkbox" value="PAN" class="scope-item accent-purple"> PAN</label>
                    <label class="flex items-center gap-2 text-xs text-gray-300"><input type="checkbox" value="VEH2NUM" class="scope-item accent-purple"> VEH2NUM</label>
                    <label class="flex items-center gap-2 text-xs text-gray-300"><input type="checkbox" value="ADHARFAMILY" class="scope-item accent-purple"> ADHARFAMILY</label>
                    <label class="flex items-center gap-2 text-xs text-gray-300"><input type="checkbox" value="BOMBER" class="scope-item accent-purple"> BOMBER</label>
                </div>
            </div>

            <div class="flex justify-end">
                <button onclick="provisionKey()" class="bg-[#bf5af2] hover:bg-[#a846db] text-white text-[10px] font-bold tracking-widest px-6 py-2.5 rounded uppercase">PROVISION_KEY</button>
            </div>
        </section>

        <!-- SUB PANEL 02: AUTHORIZATION KEY TRACKING MATRIX -->
        <section class="bg-[#12111a] p-6 rounded-lg glow-border mb-8">
            <h2 class="text-xs font-bold tracking-widest accent-purple uppercase mb-4 flex items-center gap-2">
                <span>●</span> KEY REGISTRY MATRIX
            </h2>
            <div class="overflow-x-auto">
                <table class="w-full text-left text-xs border-collapse">
                    <thead>
                        <tr class="border-b border-[#2d1b4e] text-gray-400 text-[10px] tracking-wider uppercase">
                            <th class="pb-3 font-normal">Owner Identity</th>
                            <th class="pb-3 font-normal">Authorization Token Key</th>
                            <th class="pb-3 font-normal">Dynamic Expiry Status Counter</th>
                            <th class="pb-3 font-normal">Usage Velocity</th>
                            <th class="pb-3 font-normal">Status</th>
                            <th class="pb-3 font-normal">Route Scope Privileges</th>
                            <th class="pb-3 font-normal text-right">System Configuration Interventions</th>
                        </tr>
                    </thead>
                    <tbody id="matrix-tbody" class="text-gray-300 font-mono text-[11px]"></tbody>
                </table>
            </div>
        </section>

        <!-- SUB PANEL 03: LIVE REQUEST INTERCEPTION PIPE LOGS -->
        <section class="bg-[#12111a] p-6 rounded-lg glow-border">
            <h2 class="text-xs font-bold tracking-widest text-amber-500 uppercase mb-4 flex items-center gap-2">
                <span>●</span> INTERCEPTED REQUEST STREAMS PIPELINE LOGS
            </h2>
            <div class="overflow-x-auto">
                <table class="w-full text-left text-xs border-collapse">
                    <thead>
                        <tr class="border-b border-[#2d1b4e] text-gray-400 text-[10px] tracking-wider uppercase">
                            <th class="pb-3 font-normal">Time Intercepted</th>
                            <th class="pb-3 font-normal">Executing Key Token ID</th>
                            <th class="pb-3 font-normal">Endpoint Route Call</th>
                            <th class="pb-3 font-normal">Query Data Parameters Passed</th>
                        </tr>
                    </thead>
                    <tbody id="logs-tbody" class="text-gray-400 font-mono text-[11px]"></tbody>
                </table>
                <div id="no-logs" class="text-center text-gray-600 py-6 text-xs uppercase tracking-widest hidden">
                    No active request stream metrics tracking currently.
                </div>
            </div>
        </section>
    </div>

    <!-- PIPELINE CLIENT DRIVER INTERACTION CONTROL LOGIC -->
    <script>
        if (localStorage.getItem("admin_authenticated") === "true") { showDashboard(); }

        function handleLogin() {
            const u = document.getElementById("username").value;
            const p = document.getElementById("password").value;
            fetch('/api/admin/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: u, password: p })
            })
            .then(res => {
                if (res.status === 200) {
                    localStorage.setItem("admin_authenticated", "true");
                    showDashboard();
                } else {
                    document.getElementById("login-err").classList.remove("hidden");
                }
            }).catch(() => document.getElementById("login-err").classList.remove("hidden"));
        }

        function handleLogout() {
            localStorage.removeItem("admin_authenticated");
            window.location.reload();
        }

        function showDashboard() {
            document.getElementById("login-screen").classList.add("hidden");
            document.getElementById("dashboard-screen").classList.remove("hidden");
            refreshDataPipeline();
            setInterval(refreshDataPipeline, 4000);
        }

        function toggleDateDisable(cb) { document.getElementById("new-expiry").disabled = cb.checked; }
        function selectAllScopes() { document.querySelectorAll('.scope-item').forEach(checkbox => checkbox.checked = true); }

        function provisionKey() {
            const owner = document.getElementById("new-owner").value || "Client Profile";
            const custom_token = document.getElementById("new-token").value;
            const daily_limit = document.getElementById("new-limit").value || 2500;
            const is_lifetime = document.getElementById("new-lifetime").checked;
            const expiry_date = document.getElementById("new-expiry").value;
            let scopes = [];
            document.querySelectorAll('.scope-item:checked').forEach(cb => scopes.push(cb.value));

            fetch('/api/admin/keys', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ owner, custom_token, daily_limit, is_lifetime, expiry_date, scopes })
            }).then(() => {
                document.getElementById("new-owner").value = "";
                document.getElementById("new-token").value = "";
                document.getElementById("new-lifetime").checked = false;
                document.getElementById("new-expiry").value = "";
                document.getElementById("new-expiry").disabled = false;
                document.querySelectorAll('.scope-item').forEach(cb => cb.checked = false);
                refreshDataPipeline();
            });
        }

        function fireKeyAction(key, action) {
            fetch('/api/admin/keys/action', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ key, action })
            }).then(() => refreshDataPipeline());
        }

        function refreshDataPipeline() {
            fetch('/api/admin/keys')
            .then(res => res.json())
            .then(data => {
                const tbody = document.getElementById("matrix-tbody");
                tbody.innerHTML = "";
                data.forEach(item => {
                    const statusColor = item.status === "Active" ? "text-emerald-400" : "text-rose-500";
                    const expiryDisplay = item.is_lifetime ? "LIFETIME ACCESS" : (item.expiry_date ? item.expiry_date.replace("T", " ") : "NOT SET");
                    const scopeDisplay = item.scopes.join(", ");
                    tbody.innerHTML += `
                        <tr class="border-b border-[#1b1926] hover:bg-[#161522]">
                            <td class="py-3 text-white font-semibold">\${item.owner}</td>
                            <td class="py-3 text-fuchsia-400 font-mono">\${item.key}</td>
                            <td class="py-3 text-purple-300 font-bold text-[10px] uppercase">\${expiryDisplay}</td>
                            <td class="py-3 text-gray-400">\${item.used_count} / <span class="text-gray-500">\${item.daily_limit}</span></td>
                            <td class="py-3 \${statusColor} font-bold text-[10px] uppercase">\${item.status}</td>
                            <td class="py-3 max-w-xs truncate text-gray-400 text-[10px]">\text{\${scopeDisplay}}</td>
                            <td class="py-3 text-right">
                                <div class="inline-flex gap-1 text-[10px] font-bold">
                                    <button onclick="fireKeyAction('\${item.key}', 'RESET')" class="px-2 py-0.5 rounded bg-blue-600/20 text-blue-400 border border-blue-600/30 hover:bg-blue-600/40">RESET</button>
                                    <button onclick="fireKeyAction('\${item.key}', 'TOGGLE')" class="px-2 py-0.5 rounded bg-orange-600/20 text-orange-400 border border-orange-600/30 hover:bg-orange-600/40">TOGGLE</button>
                                    <button onclick="fireKeyAction('\${item.key}', 'DEL')" class="px-2 py-0.5 rounded bg-rose-600/20 text-rose-400 border border-rose-600/30 hover:bg-rose-600/40">DEL</button>
                                </div>
                            </td>
                        </tr>`;
                });
            });

            fetch('/api/admin/logs')
            .then(res => res.json())
            .then(data => {
                const tbody = document.getElementById("logs-tbody");
                const emptyMsg = document.getElementById("no-logs");
                tbody.innerHTML = "";
                if (data.length === 0) { emptyMsg.classList.remove("hidden"); } 
                else {
                    emptyMsg.classList.add("hidden");
                    data.forEach(log => {
                        tbody.innerHTML += `
                            <tr class="border-b border-[#1b1926]">
                                <td class="py-2 text-gray-500">\${log.timestamp}</td>
                                <td class="py-2 text-fuchsia-400 font-mono">\${log.key_token}</td>
                                <td class="py-2 text-sky-400 font-bold uppercase">/api/v1/\${log.route}</td>
                                <td class="py-2 text-gray-300 break-all font-mono text-[10px]">\${log.parameters}</td>
                            </tr>`;
                    });
                }
            });
        }
    </script>
</body>
</html>'''

@app.route('/', methods=['GET'])
@app.route('/admin', methods=['GET'])
def index_page():
    return render_template_string(HTML_DASHBOARD)

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.json or {}
    if data.get("username") == "vernex" and data.get("password") == "vernex@16vx":
        return jsonify({"status": "success", "token": "session_authenticated_shayan"}), 200
    return jsonify({"status": "error", "message": "Invalid Credentials"}), 401

@app.route('/api/admin/keys', methods=['GET', 'POST'])
def manage_keys():
    if request.method == 'GET':
        return jsonify(list(API_KEYS_DB.values())), 200
    
    data = request.json or {}
    owner = data.get("owner", "Client Profile")
    custom_token = data.get("custom_token").strip() if data.get("custom_token") else secrets.token_hex(6)
    daily_limit = int(data.get("daily_limit", 2500))
    is_lifetime = data.get("is_lifetime", False)
    expiry_date = data.get("expiry_date", "")
    scopes = data.get("scopes", [])

    if not scopes:
        scopes = ["ALL"]

    API_KEYS_DB[custom_token] = {
        "owner": owner,
        "key": custom_token,
        "daily_limit": daily_limit,
        "used_count": 0,
        "is_lifetime": is_lifetime,
        "expiry_date": expiry_date,
        "status": "Active",
        "scopes": scopes
    }
    return jsonify({"status": "success", "data": API_KEYS_DB[custom_token]}), 200

@app.route('/api/admin/keys/action', methods=['POST'])
def key_action():
    data = request.json or {}
    target_key = data.get("key")
    action = data.get("action")
    
    if target_key not in API_KEYS_DB:
        return jsonify({"status": "error", "message": "Key not found"}), 404
        
    if action == "DEL":
        del API_KEYS_DB[target_key]
    elif action == "TOGGLE":
        current = API_KEYS_DB[target_key]["status"]
        API_KEYS_DB[target_key]["status"] = "Suspended" if current == "Active" else "Active"
    elif action == "RESET":
        API_KEYS_DB[target_key]["used_count"] = 0
    
    return jsonify({"status": "success"}), 200

@app.route('/api/admin/logs', methods=['GET'])
def get_logs():
    return jsonify(PIPELINE_LOGS), 200

# Proxy Routing Core Component & Branding Sanitizer
@app.route('/api/v1/<endpoint>', methods=['GET'])
def proxy_gateway(endpoint):
    client_key = request.args.get('key')
    
    if not client_key or client_key not in API_KEYS_DB:
        return jsonify({"error": "Unauthorized: Missing or invalid API access key"}), 401
        
    key_profile = API_KEYS_DB[client_key]
    if key_profile["status"] != "Active":
        return jsonify({"error": "Forbidden: This system key is currently suspended"}), 403

    if not key_profile["is_lifetime"] and key_profile["expiry_date"]:
        try:
            expiry_dt = datetime.strptime(key_profile["expiry_date"], "%Y-%m-%dT%H:%M")
            if datetime.now() > expiry_dt:
                key_profile["status"] = "Expired"
                return jsonify({"error": "Forbidden: This system key has expired"}), 403
        except ValueError:
            pass

    if key_profile["used_count"] >= key_profile["daily_limit"]:
        return jsonify({"error": "Too Many Requests: Daily velocity call threshold exhausted"}), 429

    normalized_scope = endpoint.upper()
    if "ALL" not in key_profile["scopes"] and normalized_scope not in [s.upper() for s in key_profile["scopes"]]:
        return jsonify({"error": f"Forbidden: Key does not hold privileges for route: {endpoint}"}), 403

    query_params = {k: v for k, v in request.args.items() if k != 'key'}
    PIPELINE_LOGS.insert(0, {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "key_token": client_key,
        "route": endpoint,
        "parameters": str(query_params)
    })
    
    key_profile["used_count"] += 1

    downstream_params = query_params.copy()
    downstream_params['key'] = MASTER_KEY
    
    try:
        response = requests.get(f"{UPSTREAM_BASE_URL}/{endpoint}", params=downstream_params, timeout=12)
        content_type = response.headers.get('Content-Type', '')
        
        # intercept and scrub branding if textual payload
        if "application/json" in content_type or "text/" in content_type:
            text_data = response.text
            
            # Dynamic text substitutions replacement map
            replacements = {
                "@ftgamer2": "@vernexzzz",
                "https://t.me/lynx_api": "https://t.me/shayan_explorer_channel",
                "@@bronex_ultra": "@vernexzzz",
                "@@bornex_ultra": "@vernexzzz",
                "@bornex_ultra": "@vernexzzz"
            }
            for old, new in replacements.items():
                text_data = text_data.replace(old, new)
                
            return (text_data, response.status_code, [('Content-Type', content_type)])
            
        return (response.content, response.status_code, response.headers.items())
    except Exception as e:
        return jsonify({"error": "Internal Server Gateway Error Connecting Downstream Core", "details": str(e)}), 502

if __name__ == '__main__':
    app.run(port=3000, debug=True)
