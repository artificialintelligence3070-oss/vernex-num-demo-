import os
import time
import json
import requests
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.security import APIKeyCookie

app = FastAPI(title="SHAYAN_EXPLORER HUB API")

# --- CONFIGURATION & SECURITY ---
TARGET_BASE_API = "https://ft-osint-api.duckdns.org/api"
MASTER_KEY = "explorer16"
ADMIN_USER = "vernex"
ADMIN_PASS = "vernex@16vx"

cookie_sec = APIKeyCookie(name="session_token", auto_error=False)

# ─── 🔒 PERMANENT HARDCODED KEYS MATRIX ────────────────────────────────────────
PERMANENT_STATIC_KEYS = {
    "vx-osint": {
        "owner": "Master Deployment Default",
        "token": "vx-osint",
        "expiry": "LIFETIME ACCESS",
        "limit": 999999,
        "used": 0,
        "status": "Active",
        "scopes": ["ALL"]
    }
}

# --- APPS LIVE SYSTEM MEMORY MATRIX ---
API_KEYS_DB = {}
API_KEYS_DB.update(PERMANENT_STATIC_KEYS)
PIPELINE_LOGS = []
SESSION_LOGS = []  # Tracks authentication timelines dynamically
ROUTE_USAGE_COUNTER = {}  # Tracks metrics calculation engine for terminal bars

AVAILABLE_TOOLS = [
    "ADV", "PAYTM", "IMEI", "CALLTRACER", "UPI", "IFSC", "NUMBER", "PINCODE",
    "IP", "CHALLAN", "FF", "BGMI", "SNAP", "EMAIL", "VEHICLE", "GIT", "INSTA", 
    "TG", "TGIDINFO", "NUMLEAK", "PK", "NAME", "AADHAR", "NUMTOUPI", "PAN", 
    "VEH2NUM", "ADHARFAMILY", "BOMBER"
]

# Initialize metrics engine counters
for tool in AVAILABLE_TOOLS:
    ROUTE_USAGE_COUNTER[tool] = 0

def white_label_filter(raw_content: str) -> str:
    replacements = {
        "@ftgamer2": "@vernexzzz", "ftgamer2": "@vernexzzz", "ftgamer": "@vernexzzz",
        "https://t.me/lynx_api": "https://t.me/shayan_explorer_channel",
        "@bronex_ultra": "@vernexzzz", "@@bronex_ultra": "@vernexzzz",
        "@bornex_ultra": "@vernexzzz", "@@bornex_ultra": "@vernexzzz"
    }
    sanitized = raw_content
    for target, replacement in replacements.items():
        sanitized = sanitized.replace(target, replacement)
    return sanitized

# --- UI TEMPLATES ---
LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>SHAYAN_EXPLORER HUB - Login</title>
    <style>
        body { background-color: #000000; color: #ff3333; font-family: 'Courier New', monospace; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; overflow: hidden; }
        .login-card { background: #070101; border: 2px solid #ff0033; padding: 40px; border-radius: 4px; box-shadow: 0 0 20px #ff0033; width: 330px; animation: glowPulse 2.5s infinite alternate; }
        h2 { color: #ff0033; text-align: center; font-size: 1.3rem; margin-bottom: 30px; letter-spacing: 3px; text-shadow: 0 0 10px #ff0033; }
        .input-group { margin-bottom: 25px; }
        label { display: block; font-size: 0.75rem; color: #aa2222; margin-bottom: 6px; letter-spacing: 1px; }
        input { width: 100%; padding: 11px; background: #000000; border: 1px solid #550011; color: #ff6666; border-radius: 2px; box-sizing: border-box; font-family: monospace; }
        input:focus { border-color: #ff0033; outline: none; box-shadow: 0 0 8px #ff0033; }
        button { width: 100%; padding: 12px; background: #ff0033; border: none; color: black; font-weight: bold; cursor: pointer; border-radius: 2px; letter-spacing: 1px; transition: 0.3s; }
        button:hover { background: #ff3366; box-shadow: 0 0 15px #ff3366; color: white; }
        .error { color: #ff0000; font-size: 0.75rem; text-align: center; margin-bottom: 15px; text-shadow: 0 0 5px #ff0000; }
        @keyframes glowPulse { 0% { box-shadow: 0 0 15px rgba(255,0,51,0.4); } 100% { box-shadow: 0 0 25px rgba(255,0,51,0.8); } }
    </style>
</head>
<body>
    <div class="login-card">
        <h2>MAIN_FRAMEWORK // LOG</h2>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        <form method="POST" action="/login">
            <div class="input-group">
                <label>IDENTITY OPERATOR</label>
                <input type="text" name="username" required autocomplete="off">
            </div>
            <div class="input-group">
                <label>ENCRYPTED ACCESS STRING</label>
                <input type="password" name="password" required>
            </div>
            <button type="submit">BOOT_UP SYSTEM</button>
        </form>
    </div>
</body>
</html>
"""

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>SHAYAN_EXPLORER HUB</title>
    <style>
        body { background-color: #020203; color: #ff4d4d; font-family: 'Courier New', monospace; margin: 0; padding: 20px; }
        .navbar { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #ff0033; padding-bottom: 15px; margin-bottom: 30px; box-shadow: 0 4px 15px rgba(255,0,51,0.1); }
        .brand { color: #ff0033; font-weight: bold; font-size: 1.3rem; letter-spacing: 2px; text-shadow: 0 0 10px #ff0033; animation: blinker 3s infinite; }
        
        /* 3-Dots Dropdown Framework Matrix */
        .dots-menu-container { position: relative; display: inline-block; }
        .three-dots-btn { background: none; border: 1px solid #550011; color: #ff0033; font-size: 1.5rem; cursor: pointer; padding: 2px 14px; border-radius: 4px; transition: 0.3s; }
        .three-dots-btn:hover { background: #ff0033; color: #000; box-shadow: 0 0 10px #ff0033; }
        .dropdown-menu-content { display: none; position: absolute; right: 0; top: 35px; background: #070101; border: 2px solid #ff0033; min-width: 240px; box-shadow: 0 0 20px rgba(255,0,51,0.5); z-index: 500; border-radius: 4px; padding: 10px 0; }
        .dropdown-menu-content a, .dropdown-menu-content button { display: block; width: 100%; text-align: left; background: none; border: none; padding: 12px 20px; color: #ff4d4d; font-family: monospace; font-size: 0.8rem; text-decoration: none; box-sizing: border-box; cursor: pointer; }
        .dropdown-menu-content a:hover, .dropdown-menu-content button:hover { background: rgba(255,0,51,0.15); color: #fff; text-shadow: 0 0 5px #ff0033; }
        .menu-user-tag { padding: 8px 20px; font-size: 0.7rem; color: #881111; border-bottom: 1px solid #33000a; margin-bottom: 5px; text-transform: uppercase; letter-spacing: 1px; }

        .section-title { color: #ff0033; font-size: 0.95rem; margin-top: 40px; margin-bottom: 18px; letter-spacing: 1.5px; text-transform: uppercase; text-shadow: 0 0 8px rgba(255,0,51,0.4); }
        .card { background: #060101; border: 1px solid #33000a; padding: 25px; border-radius: 4px; margin-bottom: 25px; box-shadow: inset 0 0 10px rgba(255,0,51,0.05); }
        .grid-2 { display: grid; grid-template-columns: 1fr; gap: 20px; margin-bottom: 20px; }
        @media(min-width: 768px) { .grid-2 { grid-template-columns: 1fr 1fr; } }
        .input-box { display: flex; flex-direction: column; }
        .input-box label { font-size: 0.75rem; color: #aa2222; margin-bottom: 6px; letter-spacing: 1px; }
        .input-box input, .input-box select { background: #000000; border: 1px solid #550011; padding: 11px; color: #ff6666; border-radius: 2px; font-family: monospace; }
        .input-box input:focus { border-color: #ff0033; outline: none; box-shadow: 0 0 5px #ff0033; }
        
        .tools-header { display: flex; justify-content: space-between; font-size: 0.75rem; margin-top: 25px; margin-bottom: 12px; color: #aa2222; }
        .tools-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: 10px; }
        .tool-check { background: #000; border: 1px solid #220005; padding: 9px; border-radius: 2px; display: flex; align-items: center; font-size: 0.75rem; cursor: pointer; color: #cc3333; transition: 0.2s; }
        .tool-check:hover { border-color: #ff0033; background: #0d0103; }
        .tool-check input { margin-right: 10px; accent-color: #ff0033; }
        
        .btn-container { display: flex; justify-content: flex-end; margin-top: 25px; }
        .submit-btn { background: #ff0033; border: none; color: #000; padding: 12px 28px; font-weight: bold; border-radius: 2px; cursor: pointer; font-size: 0.8rem; font-family: monospace; transition: 0.3s; }
        .submit-btn:hover { background: #ff3366; box-shadow: 0 0 15px #ff0033; color: #fff; }
        
        /* Fixed Unified Row Styling Matrix */
        table { width: 100%; border-collapse: collapse; font-size: 0.75rem; text-align: left; }
        th { color: #aa2222; font-weight: normal; padding-bottom: 12px; border-bottom: 1px solid #33000a; letter-spacing: 1px; }
        td { padding: 14px 8px; border-bottom: 1px solid #140204; vertical-align: middle; }
        .badge-active { color: #00ff66; font-weight: bold; text-shadow: 0 0 5px rgba(0,255,102,0.4); }
        .badge-suspended { color: #ff0033; font-weight: bold; text-shadow: 0 0 5px rgba(255,0,51,0.4); }
        .badge-scope { background: #1c0205; padding: 2px 6px; border-radius: 2px; color: #ff6666; border: 1px solid #44000a; display: inline-block; margin: 2px; }
        
        /* Beautiful Single Line Button Action Framework */
        .actions-wrapper { display: flex; flex-direction: row; flex-wrap: nowrap; gap: 4px; justify-content: flex-start; align-items: center; width: max-content; }
        .btn-action { padding: 5px 10px; border-radius: 2px; font-size: 0.7rem; font-weight: bold; text-decoration: none; cursor: pointer; border: 1px solid transparent; font-family: monospace; display: inline-block; text-align: center; white-space: nowrap; transition: 0.2s; }
        .btn-edit { background: #000000; border-color: #ffcc00; color: #ffcc00; }
        .btn-edit:hover { background: #ffcc00; color: #000; box-shadow: 0 0 8px #ffcc00; }
        .btn-reset { background: #000000; border-color: #00ccff; color: #00ccff; }
        .btn-reset:hover { background: #00ccff; color: #000; box-shadow: 0 0 8px #00ccff; }
        .btn-toggle { background: #000000; border-color: #00ff66; color: #00ff66; }
        .btn-toggle:hover { background: #00ff66; color: #000; box-shadow: 0 0 8px #00ff66; }
        .btn-toggle.suspended { border-color: #ff0055; color: #ff0055; }
        .btn-toggle.suspended:hover { background: #ff0055; color: #fff; box-shadow: 0 0 8px #ff0055; }
        .btn-del { background: #ff0033; color: #000; border-color: #ff0033; }
        .btn-del:hover { background: #ff3366; color: #fff; box-shadow: 0 0 8px #ff3366; }

        /* Hacker Calculator / Analytics Matrix System Design */
        .analytics-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 15px; margin-bottom: 25px; }
        .analyzer-card { background: #040001; border: 1px solid #44000a; border-radius: 2px; padding: 15px; position: relative; overflow: hidden; }
        .analyzer-title { font-size: 0.7rem; color: #aa2222; margin-bottom: 8px; letter-spacing: 1px; }
        .analyzer-value { font-size: 1.4rem; color: #ff3333; font-weight: bold; text-shadow: 0 0 8px rgba(255,0,51,0.3); }
        .metric-bar-bg { width: 100%; height: 5px; background: #1a0004; border-radius: 2px; margin-top: 10px; position: relative; }
        .metric-bar-fill { height: 100%; background: #ff0033; width: 0%; box-shadow: 0 0 8px #ff0033; transition: width 1s ease-in-out; }

        /* Modal Structure Setup */
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.9); justify-content: center; align-items: center; z-index: 1000; }
        .modal-content { background: #070101; border: 2px solid #ff0033; border-radius: 4px; padding: 30px; width: 90%; max-width: 600px; max-height: 85vh; overflow-y: auto; box-shadow: 0 0 25px #ff0033; }
        .modal-title { color: #ff0033; font-size: 1.1rem; margin-bottom: 20px; text-shadow: 0 0 5px #ff0033; }
        .close-modal { float: right; color: #aa2222; cursor: pointer; font-size: 1.4rem; }
        .close-modal:hover { color: #ff0033; }

        @keyframes blinker { 0%, 100% { opacity: 1; } 50% { opacity: 0.85; } }
    </style>
</head>
<body>

    <div class="navbar">
        <div class="brand">⚡ SHAYAN_EXPLORER // SYSTEM CORE</div>
        <div class="dots-menu-container">
            <button class="three-dots-btn" onclick="toggleDropdownMenu()">⋮</button>
            <div class="dropdown-menu-content" id="mainDropdownMenu">
                <div class="menu-user-tag">⚡ OPERATOR: {{ current_admin }}</div>
                <a href="/dashboard">🏠 OVERVIEW CONSOLE</a>
                <button onclick="openApisModal()">🌐 ACCESS GATEWAY URLS</button>
                <a href="/logout" style="color: #ff0033; border-top: 1px solid #220005;">❌ SHUTDOWN SESSION</a>
            </div>
        </div>
    </div>

    <div class="section-title">📊 METRIC ANALYSIS DEVIATION GRAPH</div>
    <div class="analytics-grid">
        {% for m_title, m_count, m_pct in telemetry_metrics %}
        <div class="analyzer-card">
            <div class="analyzer-title">ROUTE INTERCEPT: {{ m_title }}</div>
            <div class="analyzer-value">{{ m_count }} <span style="font-size: 0.75rem; color:#550011;">CALLS</span></div>
            <div class="metric-bar-bg">
                <div class="metric-bar-fill" style="width: {{ m_pct }}%;"></div>
            </div>
        </div>
        {% endfor %}
    </div>

    <div class="section-title">• PROPOSE SYSTEM COMMUNICATIONS KEY</div>
    <div class="card">
        <form method="POST" action="/keys/generate">
            <div class="grid-2">
                <div class="input-box">
                    <label>TARGET OWNER IDENTITY NAME</label>
                    <input type="text" name="owner" placeholder="e.g. Premium Client" required autocomplete="off">
                </div>
                <div class="input-box">
                    <label>CUSTOM ASSIGNMENT STRING (TOKEN KEY)</label>
                    <input type="text" name="token" placeholder="Auto-generate tracking hash if empty" autocomplete="off">
                </div>
            </div>
            <div class="grid-2">
                <div class="input-box">
                    <label>DAILY VELOCITY CALL LIMIT VOLUME</label>
                    <input type="number" name="limit" value="2500" required>
                </div>
                <div class="input-box">
                    <label>TARGET EXPIRATION LIFECYCLE</label>
                    <input type="text" name="expiry_date" placeholder="Type 'LIFETIME ACCESS' or YYYY-MM-DD" value="LIFETIME ACCESS">
                </div>
            </div>
            <div class="tools-header">
                <div>ROUTE AUTHORIZATION PRIVILEGES MATRIX SCOPE</div>
                <div style="color: #ff0033; cursor:pointer;" onclick="toggleAllTools('create-form')">[ SELECT ALL TOOLS ]</div>
            </div>
            <div class="tools-grid" id="create-form">
                {% for tool in tools %}
                <label class="tool-check">
                    <input type="checkbox" name="scopes" value="{{ tool }}" class="tool-checkbox"> {{ tool }}
                </label>
                {% endfor %}
            </div>
            <div class="btn-container">
                <button type="submit" class="submit-btn">PROVISION_KEY_GATEWAY</button>
            </div>
        </form>
    </div>

    <div class="section-title">• KEY REGISTRY MATRIX OVERVIEW</div>
    <div class="card" style="overflow-x: auto;">
        <table>
            <thead>
                <tr>
                    <th>OWNER IDENTITY</th>
                    <th>AUTHORIZATION TOKEN KEY</th>
                    <th>EXPIRY TIMELINE</th>
                    <th>USAGE VELOCITY</th>
                    <th>STATUS</th>
                    <th>ROUTE SCOPE PRIVILEGES</th>
                    <th>SYSTEM CONFIGURATION INTERVENTIONS</th>
                </tr>
            </thead>
            <tbody>
                {% for row in rows %}
                {{ row }}
                {% endfor %}
            </tbody>
        </table>
    </div>

    <div class="section-title">• OPERATOR SECURITY ACCESS TIMELOGS</div>
    <div class="card" style="overflow-x: auto;">
        <table>
            <thead>
                <tr>
                    <th>AUTHENTICATION TIMESTAMP</th>
                    <th>IDENTIFIED USER</th>
                    <th>SYSTEM EVENT TRACE</th>
                    <th>SECURITY CLEARANCE LAYER</th>
                </tr>
            </thead>
            <tbody>
                {% for s_log in session_logs_html %}
                {{ s_log }}
                {% endfor %}
            </tbody>
        </table>
    </div>

    <div class="section-title">• INTERCEPTED REQUEST STREAMS PIPELINE LOGS</div>
    <div class="card" style="overflow-x: auto;">
        <table>
            <thead>
                <tr>
                    <th>TIME INTERCEPTED</th>
                    <th>EXECUTING KEY TOKEN ID</th>
                    <th>ENDPOINT ROUTE CALL</th>
                    <th>QUERY DATA PARAMETERS PASSED</th>
                </tr>
            </thead>
            <tbody>
                {% for log in logs %}
                {{ log }}
                {% endfor %}
            </tbody>
        </table>
    </div>

    <div id="editModal" class="modal">
        <div class="modal-content">
            <span class="close-modal" onclick="closeEditModal()">&times;</span>
            <div class="modal-title">🔧 MODIFY MATRIX AUTHORIZATION parameters</div>
            <form method="POST" action="/keys/edit">
                <input type="hidden" name="old_token" id="edit_old_token">
                <div class="grid-2">
                    <div class="input-box">
                        <label>OWNER IDENTITY</label>
                        <input type="text" name="owner" id="edit_owner" required autocomplete="off">
                    </div>
                    <div class="input-box">
                        <label>RE-ASSIGN KEY STRING</label>
                        <input type="text" name="token" id="edit_token" required autocomplete="off">
                    </div>
                </div>
                <div class="grid-2">
                    <div class="input-box">
                        <label>LIMIT VOLUME</label>
                        <input type="number" name="limit" id="edit_limit" required>
                    </div>
                    <div class="input-box">
                        <label>EXPIRATION LIFECYCLE</label>
                        <input type="text" name="expiry_date" id="edit_expiry" required>
                    </div>
                </div>
                <div class="tools-header">
                    <div>ROUTE PRIVILEGES MATRIX SCOPES</div>
                    <div style="color: #ff0033; cursor:pointer;" onclick="toggleAllTools('edit-form')">[ TOGGLE ALL SCOPES ]</div>
                </div>
                <div class="tools-grid" id="edit-form">
                    {% for tool in tools_edit %}
                    <label class="tool-check">
                        <input type="checkbox" name="scopes" value="{{ tool }}" class="edit-tool-checkbox"> {{ tool }}
                    </label>
                    {% endfor %}
                </div>
                <div class="btn-container">
                    <button type="submit" class="submit-btn" style="background: #ffcc00; color:#000;">COMMIT PARAMS UPDATE</button>
                </div>
            </form>
        </div>
    </div>

    <div id="apisModal" class="modal">
        <div class="modal-content" style="max-width: 750px; border-color:#ff0033; box-shadow: 0 0 20px #ff0033;">
            <span class="close-modal" onclick="closeApisModal()">&times;</span>
            <div class="modal-title">🌐 LIVE ROUTE TARGET STRINGS</div>
            <div id="urls-list" style="max-height: 50vh; overflow-y:auto; font-family: monospace; background:#000; padding:15px; border-radius:2px; border:1px solid #33000a;">
            </div>
        </div>
    </div>

    <script>
        function toggleDropdownMenu() {
            let menu = document.getElementById('mainDropdownMenu');
            menu.style.display = (menu.style.display === 'block') ? 'none' : 'block';
        }
        window.onclick = function(event) {
            if (!event.target.matches('.three-dots-btn')) {
                let dropdowns = document.getElementsByClassName("dropdown-menu-content");
                for (let i = 0; i < dropdowns.length; i++) {
                    dropdowns[i].style.display = "none";
                }
            }
        }
        function toggleAllTools(containerId) {
            let checkboxes = document.querySelectorAll('#' + containerId + ' input[type=\"checkbox\"]');
            let allChecked = Array.from(checkboxes).every(cb => cb.checked);
            checkboxes.forEach(cb => cb.checked = !allChecked);
        }
        function openEditModal(oldToken, owner, limit, expiry, activeScopesJson) {
            document.getElementById('edit_old_token').value = oldToken;
            document.getElementById('edit_owner').value = owner;
            document.getElementById('edit_token').value = oldToken;
            document.getElementById('edit_limit').value = limit;
            document.getElementById('edit_expiry').value = expiry;
            
            let activeScopes = JSON.parse(activeScopesJson);
            let checkboxes = document.querySelectorAll('.edit-tool-checkbox');
            checkboxes.forEach(cb => {
                cb.checked = activeScopes.includes('ALL') || activeScopes.includes(cb.value);
            });
            document.getElementById('editModal').style.display = 'flex';
        }
        function closeEditModal() { document.getElementById('editModal').style.display = 'none'; }
        function openApisModal() {
            let currentHost = window.location.origin;
            let tools = ["ADV", "PAYTM", "IMEI", "CALLTRACER", "UPI", "IFSC", "NUMBER", "PINCODE","IP", "CHALLAN", "FF", "BGMI", "SNAP", "EMAIL", "VEHICLE", "GIT", "INSTA", "TG", "TGIDINFO", "NUMLEAK", "PK", "NAME", "AADHAR", "NUMTOUPI", "PAN", "VEH2NUM", "ADHARFAMILY", "BOMBER"];
            let container = document.getElementById('urls-list');
            container.innerHTML = '';
            tools.forEach(t => {
                let lower = t.toLowerCase();
                container.innerHTML += `<div style="margin-bottom:12px; border-bottom:1px solid #220005; padding-bottom:6px;"><span style="color:#ff0033;">[GET]</span> ${currentHost}/api/${lower}?key=<span style="color:#00ff66;">YOUR_KEY</span>&param=value</div>`;
            });
            document.getElementById('apisModal').style.display = 'flex';
        }
        function closeApisModal() { document.getElementById('apisModal').style.display = 'none'; }
    </script>
</body>
</html>
"""

# --- SESSIONS & REBOOT PROTECTION MIDDLEWARE ---
def check_session(request: Request, session_token: Optional[str] = Depends(cookie_sec)):
    if not session_token or session_token != "authenticated_shayan_session":
        raise HTTPException(status_code=303, headers={"Location": "/"})
    return True

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 303:
        return RedirectResponse(url=exc.headers.get("Location"), status_code=303)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

# --- ROUTING CONSOLE PIPELINE ENGINE ---

@app.get("/", response_class=HTMLResponse)
def get_login_page():
    return LOGIN_HTML.replace("{% if error %}<div class=\"error\">{{ error }}</div>{% endif %}", "")

@app.post("/login")
def handle_login(username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USER and password == ADMIN_PASS:
        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        SESSION_LOGS.append({
            "time": timestamp_str,
            "user": username,
            "event": "SUCCESSFUL SYSTEM AUTHENTICATION INITIALIZED",
            "clearance": "ROOT_ADMIN"
        })
        response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(key="session_token", value="authenticated_shayan_session", httponly=True)
        return response
    
    error_msg = '<div class="error">Access Denied: Bad Transmission Token Signature</div>'
    return HTMLResponse(content=LOGIN_HTML.replace('{% if error %}<div class="error">{{ error }}</div>{% endif %}', error_msg))

@app.get("/logout")
def handle_logout():
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    SESSION_LOGS.append({
        "time": timestamp_str,
        "user": ADMIN_USER,
        "event": "MANUAL CONSOLE SHUTDOWN TERMINATED BY OPERATOR",
        "clearance": "EXPIRED"
    })
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("session_token")
    return response

@app.get("/dashboard", response_class=HTMLResponse)
def get_dashboard(auth: bool = Depends(check_session)):
    for k, v in PERMANENT_STATIC_KEYS.items():
        if k not in API_KEYS_DB: 
            API_KEYS_DB[k] = v

    rendered = DASHBOARD_HTML.replace("{{ current_admin }}", ADMIN_USER)
    
    # 1. Inject Tools lists
    tools_html = "".join([f'<label class="tool-check"><input type="checkbox" name="scopes" value="{t}"> {t}</label>' for t in AVAILABLE_TOOLS])
    rendered = rendered.replace('{% for tool in tools %}\n                <label class="tool-check">\n                    <input type="checkbox" name="scopes" value="{{ tool }}" class="tool-checkbox"> {{ tool }}\n                </label>\n                {% endfor %}', tools_html)
    rendered = rendered.replace('{% for tool in tools_edit %}\n                    <label class="tool-check">\n                        <input type="checkbox" name="scopes" value="{{ tool }}" class="edit-tool-checkbox"> {{ tool }}\n                    </label>\n                    {% endfor %}', tools_html)

    # 2. Render Mathematical Calculator Telemetry UI Bars
    total_intercepted_calls = sum(ROUTE_USAGE_COUNTER.values())
    telemetry_list = []
    
    # Take top 4 most used routes or show high-priority tracking items if empty
    sorted_tools = sorted(ROUTE_USAGE_COUNTER.items(), key=lambda x: x[1], reverse=True)[:4]
    for m_title, m_count in sorted_tools:
        pct = (m_count / total_intercepted_calls * 100) if total_intercepted_calls > 0 else 0
        if total_intercepted_calls == 0 and m_title in ["NUMBER", "UPI", "PAYTM", "VEHICLE"]:
            pct = 0 # Default placeholder state visualization engine
        telemetry_list.append((m_title, m_count, pct))
        
    # If no calls made yet, show standard 4 rows with 0 usage tracking
    if total_intercepted_calls == 0:
        telemetry_list = [("NUMBER", 0, 0), ("UPI", 0, 0), ("PAYTM", 0, 0), ("VEHICLE", 0, 0)]

    telemetry_html = ""
    for title, cnt, p_fill in telemetry_list:
        telemetry_html += f"""
        <div class="analyzer-card">
            <div class="analyzer-title">ROUTE INTERCEPT: {title}</div>
            <div class="analyzer-value">{cnt} <span style="font-size: 0.75rem; color:#550011;">CALLS</span></div>
            <div class="metric-bar-bg">
                <div class="metric-bar-fill" style="width: {p_fill}%;"></div>
            </div>
        </div>
        """
    rendered = rendered.replace('{% for m_title, m_count, m_pct in telemetry_metrics %}\n        <div class="analyzer-card">\n            <div class="analyzer-title">ROUTE INTERCEPT: {{ m_title }}</div>\n            <div class="analyzer-value">{{ m_count }} <span style="font-size: 0.75rem; color:#550011;">CALLS</span></div>\n            <div class="metric-bar-bg">\n                <div class="metric-bar-fill" style="width: {{ m_pct }}%;"></div>\n            </div>\n        </div>\n        {% endfor %}', telemetry_html)

    # 3. Dynamic Rows Configuration (Clean Unified Layout to Avoid "Joker Layout Wrapping")
    rows_list = []
    for k, v in API_KEYS_DB.items():
        scopes_badges = "".join([f'<span class="badge-scope">{s}</span>' for s in v["scopes"]])
        status_badge = f'<span class="badge-active">Active</span>' if v["status"] == "Active" else f'<span class="badge-suspended">Suspended</span>'
        scopes_json = json.dumps(v["scopes"]).replace('"', '&quot;')
        owner_escaped = v['owner'].replace("'", "\\'")
        
        row_ui = f"""
        <tr>
            <td>{v['owner']}</td>
            <td style="color: #ff0033; font-weight:bold;">{v['token']}</td>
            <td style="color: #ffaa00;">{v['expiry']}</td>
            <td>{v['used']} / {v['limit']}</td>
            <td>{status_badge}</td>
            <td>{scopes_badges}</td>
            <td>
                <div class="actions-wrapper">
                    <button class="btn-action btn-edit" onclick="openEditModal('{v['token']}', '{owner_escaped}', {v['limit']}, '{v['expiry']}', '{scopes_json}')">EDIT</button>
                    <a href="/keys/reset/{v['token']}" class="btn-action btn-reset">RESET</a>
                    <a href="/keys/toggle/{v['token']}" class="btn-action btn-toggle {'suspended' if v['status'] != 'Active' else ''}">TOGGLE</a>
                    <a href="/keys/delete/{v['token']}" class="btn-action btn-del">DEL</a>
                </div>
            </td>
        </tr>
        """
        rows_list.append(row_ui)
    rendered = rendered.replace("{% for row in rows %}\n                {{ row }}\n                {% endfor %}", "".join(rows_list))

    # 4. Session Tracker UI Parser
    s_logs_html = []
    for s_log in reversed(SESSION_LOGS[-5:]):
        s_logs_html.append(f"""
        <tr>
            <td style="color:#ffcc00;">[{s_log['time']}]</td>
            <td>{s_log['user']}</td>
            <td style="color:#ff3366;">{s_log['event']}</td>
            <td><span class="badge-scope" style="color:#00ff66; border-color:#004411;">{s_log['clearance']}</span></td>
        </tr>
        """)
    if not s_logs_html:
        s_logs_html.append('<tr><td colspan="4" style="text-align: center; color: #550011; padding: 12px 0;">No operator sessions tracked on current core context instance.</td></tr>')
    rendered = rendered.replace("{% for s_log in session_logs_html %}\n                {{ s_log }}\n                {% endfor %}", "".join(s_logs_html))

    # 5. Live Pipeline Request Intercept Streams
    logs_list = []
    for log in reversed(PIPELINE_LOGS[-10:]):
        logs_list.append(f"""
        <tr>
            <td>{log['time']}</td>
            <td>{log['token']}</td>
            <td><span class="badge-scope" style="color:#00ffff; border-color:#004444;">{log['route']}</span></td>
            <td style="font-family: monospace; color: #888;">{log['params']}</td>
        </tr>
        """)
    if not logs_list:
        logs_list.append('<tr><td colspan="4" style="text-align: center; color: #550011; padding: 12px 0;">No raw system intercept streams pipeline detected.</td></tr>')
    rendered = rendered.replace("{% for log in logs %}\n                {{ log }}\n                {% endfor %}", "".join(logs_list))

    return rendered

# --- API LIFECYCLE RESTRUCTURING MANAGEMENT ---

@app.post("/keys/generate")
def generate_key(owner: str = Form(...), token: Optional[str] = Form(None), limit: int = Form(...), expiry_date: Optional[str] = Form(None), scopes: List[str] = Form(None), auth: bool = Depends(check_session)):
    key_token = token.strip() if token and token.strip() else f"vx-{int(time.time())}"
    assigned_scopes = scopes if scopes else ["ALL"]
    expiry_str = expiry_date.strip() if expiry_date and expiry_date.strip() else "LIFETIME ACCESS"

    API_KEYS_DB[key_token] = {
        "owner": owner, "token": key_token, "expiry": expiry_str,
        "limit": limit, "used": 0, "status": "Active", "scopes": assigned_scopes
    }
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/keys/edit")
def edit_key(old_token: str = Form(...), token: str = Form(...), owner: str = Form(...), limit: int = Form(...), expiry_date: str = Form(...), scopes: List[str] = Form(None), auth: bool = Depends(check_session)):
    assigned_scopes = scopes if scopes else ["ALL"]
    previous_usage_count = 0
    previous_status = "Active"
    
    if old_token in API_KEYS_DB:
        previous_usage_count = API_KEYS_DB[old_token]["used"]
        previous_status = API_KEYS_DB[old_token]["status"]
        del API_KEYS_DB[old_token]

    API_KEYS_DB[token] = {
        "owner": owner, "token": token, "expiry": expiry_date,
        "limit": limit, "used": previous_usage_count, "status": previous_status, "scopes": assigned_scopes
    }
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/keys/toggle/{token}")
def toggle_key(token: str, auth: bool = Depends(check_session)):
    if token in API_KEYS_DB:
        current = API_KEYS_DB[token]["status"]
        API_KEYS_DB[token]["status"] = "Suspended" if current == "Active" else "Active"
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/keys/reset/{token}")
def reset_key_usage(token: str, auth: bool = Depends(check_session)):
    if token in API_KEYS_DB:
        API_KEYS_DB[token]["used"] = 0
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/keys/delete/{token}")
def delete_key(token: str, auth: bool = Depends(check_session)):
    if token in API_KEYS_DB: del API_KEYS_DB[token]
    if token in PERMANENT_STATIC_KEYS: del PERMANENT_STATIC_KEYS[token]
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

# --- CORE API PROXY GATEWAY INTEGRATION LAYER ---
@app.get("/api/{route}")
def proxy_gateway(route: str, request: Request, key: str):
    for k, v in PERMANENT_STATIC_KEYS.items():
        if k not in API_KEYS_DB: API_KEYS_DB[k] = v

    if key not in API_KEYS_DB:
        return JSONResponse(status_code=403, content={"error": "Access Revoked: Invalid Token Identification Matrix"})
    
    key_profile = API_KEYS_DB[key]
    if key_profile["status"] != "Active":
        return JSONResponse(status_code=403, content={"error": "Access Denied: This target API Key is currently SUSPENDED"})

    current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    query_params = dict(request.query_params)
    if "key" in query_params: del query_params["key"]
    
    PIPELINE_LOGS.append({"time": current_time_str, "token": key, "route": route.upper(), "params": str(query_params)})
    
    # Increment Analytics Tracker Calculator Matrix counter
    route_upper = route.upper()
    if route_upper in ROUTE_USAGE_COUNTER:
        ROUTE_USAGE_COUNTER[route_upper] += 1
    else:
        ROUTE_USAGE_COUNTER[route_upper] = 1

    if "ALL" not in key_profile["scopes"] and route_upper not in key_profile["scopes"]:
        return JSONResponse(status_code=403, content={"error": f"Unauthorized Access Scope Framework for Sub-Tool: {route_upper}"})

    if key_profile["expiry"] != "LIFETIME ACCESS":
        today_date = datetime.now().strftime("%Y-%m-%d")
        if today_date > key_profile["expiry"]:
            return JSONResponse(status_code=403, content={"error": "Token lifecycle execution window has expired."})
            
    if key_profile["used"] >= key_profile["limit"]:
        return JSONResponse(status_code=429, content={"error": "Transaction call allocation volume limits fully exhausted."})

    key_profile["used"] += 1

    upstream_params = dict(request.query_params)
    upstream_params["key"] = MASTER_KEY 
    
    try:
        target_url = f"{TARGET_BASE_API}/{route}"
        upstream_response = requests.get(target_url, params=upstream_params, timeout=12)
        cleaned_text_payload = white_label_filter(upstream_response.text)
        try:
            return JSONResponse(status_code=upstream_response.status_code, content=json.loads(cleaned_text_payload))
        except json.JSONDecodeError:
            return HTMLResponse(status_code=upstream_response.status_code, content=cleaned_text_payload)
    except requests.exceptions.RequestException as exc:
        return JSONResponse(status_code=502, content={"error": "Upstream communication gateway failure", "details": str(exc)})


