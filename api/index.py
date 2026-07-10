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
# Add your keys here to keep them safe from serverless cleanups forever!
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

# --- APPS LIVE MEMORY MATRIX ---
API_KEYS_DB = {}
API_KEYS_DB.update(PERMANENT_STATIC_KEYS)
PIPELINE_LOGS = []

AVAILABLE_TOOLS = [
    "ADV", "PAYTM", "IMEI", "CALLTRACER", "UPI", "IFSC", "NUMBER", "PINCODE",
    "IP", "CHALLAN", "FF", "BGMI", "SNAP", "EMAIL", "VEHICLE", "GIT", "INSTA", 
    "TG", "TGIDINFO", "NUMLEAK", "PK", "NAME", "AADHAR", "NUMTOUPI", "PAN", 
    "VEH2NUM", "ADHARFAMILY", "BOMBER"
]

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
        body { background-color: #060608; color: #e2e8f0; font-family: 'Courier New', monospace; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-card { background: #0c0c12; border: 1px solid #bc13fe; padding: 40px; border-radius: 8px; box-shadow: 0 0 15px rgba(188, 19, 254, 0.2); width: 320px; }
        h2 { color: #bc13fe; text-align: center; font-size: 1.4rem; margin-bottom: 30px; letter-spacing: 2px; }
        .input-group { margin-bottom: 20px; }
        label { display: block; font-size: 0.8rem; color: #8a8aa3; margin-bottom: 5px; }
        input { width: 100%; padding: 10px; background: #13131c; border: 1px solid #27273a; color: #fff; border-radius: 4px; box-sizing: border-box; }
        input:focus { border-color: #bc13fe; outline: none; }
        button { width: 100%; padding: 12px; background: linear-gradient(90deg, #bc13fe, #7a13fe); border: none; color: white; font-weight: bold; cursor: pointer; border-radius: 4px; transition: 0.3s; }
        button:hover { opacity: 0.9; box-shadow: 0 0 10px rgba(188, 19, 254, 0.5); }
        .error { color: #ff4a4a; font-size: 0.8rem; text-align: center; margin-bottom: 15px; }
    </style>
</head>
<body>
    <div class="login-card">
        <h2>SHAYAN_EXPLORER HUB</h2>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        <form method="POST" action="/login">
            <div class="input-group">
                <label>IDENTITY USERNAME</label>
                <input type="text" name="username" required>
            </div>
            <div class="input-group">
                <label>ACCESS SECURITY PASSWORD</label>
                <input type="password" name="password" required>
            </div>
            <button type="submit">INITIALIZE SESSION</button>
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
        body { background-color: #060608; color: #d1d5db; font-family: 'Courier New', monospace; margin: 0; padding: 20px; }
        .navbar { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1f1f2e; padding-bottom: 15px; margin-bottom: 30px; }
        .brand { color: #bc13fe; font-weight: bold; font-size: 1.2rem; letter-spacing: 1px; }
        .nav-btn { background: #13131c; border: 1px solid #27273a; color: #8a8aa3; padding: 6px 12px; text-decoration: none; font-size: 0.8rem; border-radius: 4px; margin-left: 10px; cursor: pointer; }
        .nav-btn:hover { border-color: #bc13fe; color: #fff; }
        .alert-banner { background: rgba(234, 179, 8, 0.1); border: 1px solid #eab308; padding: 12px; color: #eab308; border-radius: 4px; font-size: 0.75rem; margin-bottom: 25px; line-height: 1.4; }
        .section-title { color: #bc13fe; font-size: 0.9rem; margin-top: 40px; margin-bottom: 20px; letter-spacing: 1px; text-transform: uppercase; }
        .card { background: #0c0c12; border: 1px solid #1f1f2e; padding: 25px; border-radius: 6px; margin-bottom: 25px; }
        .grid-2 { display: grid; grid-template-columns: 1fr; gap: 20px; margin-bottom: 20px; }
        @media(min-width: 768px) { .grid-2 { grid-template-columns: 1fr 1fr; } }
        .input-box { display: flex; flex-direction: column; }
        .input-box label { font-size: 0.75rem; color: #6b7280; margin-bottom: 6px; }
        .input-box input, .input-box select { background: #13131c; border: 1px solid #27273a; padding: 10px; color: #fff; border-radius: 4px; }
        .tools-header { display: flex; justify-content: space-between; font-size: 0.75rem; margin-top: 20px; margin-bottom: 10px; color: #6b7280; }
        .tools-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 12px; }
        .tool-check { background: #13131c; border: 1px solid #27273a; padding: 10px; border-radius: 4px; display: flex; align-items: center; font-size: 0.75rem; cursor: pointer; }
        .tool-check input { margin-right: 10px; accent-color: #bc13fe; }
        .btn-container { display: flex; justify-content: flex-end; margin-top: 25px; }
        .submit-btn { background: linear-gradient(90deg, #bc13fe, #7a13fe); border: none; color: white; padding: 12px 24px; font-weight: bold; border-radius: 4px; cursor: pointer; font-size: 0.8rem; }
        table { width: 100%; border-collapse: collapse; font-size: 0.75rem; text-align: left; }
        th { color: #6b7280; font-weight: normal; padding-bottom: 12px; border-bottom: 1px solid #1f1f2e; }
        td { padding: 12px 0; border-bottom: 1px solid #11111a; vertical-align: middle; }
        .badge-active { color: #10b981; font-weight: bold; }
        .badge-suspended { color: #ef4444; font-weight: bold; }
        .badge-scope { background: #27273a; padding: 2px 6px; border-radius: 3px; color: #d1d5db; display: inline-block; margin: 2px; }
        .btn-action { padding: 4px 8px; border-radius: 3px; font-size: 0.7rem; font-weight: bold; text-decoration: none; cursor: pointer; border: none; margin-right: 4px; }
        .btn-edit { background: #eab308; color: #000; }
        .btn-reset { background: #3b82f6; color: #fff; }
        .btn-toggle { background: #10b981; color: #fff; }
        .btn-toggle.suspended { background: #ef4444; }
        .btn-del { background: #dc2626; color: #fff; }
        
        /* Modal Framework */
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); justify-content: center; align-items: center; z-index: 1000; }
        .modal-content { background: #0c0c12; border: 1px solid #bc13fe; border-radius: 8px; padding: 30px; width: 90%; max-width: 600px; max-height: 85vh; overflow-y: auto; }
        .modal-title { color: #bc13fe; font-size: 1.1rem; margin-bottom: 20px; }
        .close-modal { float: right; color: #8a8aa3; cursor: pointer; font-size: 1.2rem; }
    </style>
</head>
<body>

    <div class="navbar">
        <div class="brand">• SHAYAN_EXPLORER HUB</div>
        <div>
            <button class="nav-btn" onclick="openApisModal()">VIEW_SYSTEM_APIS</button>
            <a href="/logout" class="nav-btn">LOGOUT</a>
        </div>
    </div>

    <div class="alert-banner">
        ⚠️ <strong>SERVERLESS PLATFORM ARCHITECTURE NOTICE:</strong> Keys created dynamically through this web interface will automatically reset when Vercel scales down. To create a <strong>permanent key that never gets deleted</strong>, please add it directly to the <code>PERMANENT_STATIC_KEYS</code> object inside your <code>api/index.py</code> file configuration block.
    </div>

    <div class="section-title">• PROPOSE SYSTEM COMMUNICATIONS KEY</div>
    <div class="card">
        <form method="POST" action="/keys/generate">
            <div class="grid-2">
                <div class="input-box">
                    <label>TARGET OWNER NAME</label>
                    <input type="text" name="owner" placeholder="e.g. Client Profile" required>
                </div>
                <div class="input-box">
                    <label>CUSTOM ASSIGNMENT STRING (KEY)</label>
                    <input type="text" name="token" placeholder="Random token if empty">
                </div>
            </div>
            <div class="grid-2">
                <div class="input-box">
                    <label>DAILY CALL LIMIT VOLUME</label>
                    <input type="number" name="limit" value="2500" required>
                </div>
                <div class="input-box">
                    <label>TARGET EXPIRATION LIFECYCLE (YYYY-MM-DD)</label>
                    <input type="text" name="expiry_date" placeholder="Leave empty or type LIFETIME ACCESS">
                </div>
            </div>
            <div class="tools-header">
                <div>ROUTE AUTHORIZATION PRIVILEGES SCOPE</div>
                <div style="color: #ff007f; cursor:pointer;" onclick="toggleAllTools('create-form')">Select All Available Sub-Tools</div>
            </div>
            <div class="tools-grid" id="create-form">
                {% for tool in tools %}
                <label class="tool-check">
                    <input type="checkbox" name="scopes" value="{{ tool }}" class="tool-checkbox"> {{ tool }}
                </label>
                {% endfor %}
            </div>
            <div class="btn-container">
                <button type="submit" class="submit-btn">PROVISION_KEY</button>
            </div>
        </form>
    </div>

    <div class="section-title">• KEY REGISTRY MATRIX</div>
    <div class="card" style="overflow-x: auto;">
        <table>
            <thead>
                <tr>
                    <th>OWNER IDENTITY</th>
                    <th>AUTHORIZATION TOKEN KEY</th>
                    <th>DYNAMIC EXPIRY STATUS COUNTER</th>
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
            <div class="modal-title">🔧 EDIT APIS CONFIGURATION MATRIX</div>
            <form method="POST" action="/keys/edit">
                <input type="hidden" name="old_token" id="edit_old_token">
                <div class="grid-2">
                    <div class="input-box">
                        <label>OWNER IDENTITY</label>
                        <input type="text" name="owner" id="edit_owner" required>
                    </div>
                    <div class="input-box">
                        <label>RE-ASSIGN KEY STRING</label>
                        <input type="text" name="token" id="edit_token" required>
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
                    <div style="color: #ff007f; cursor:pointer;" onclick="toggleAllTools('edit-form')">Toggle All</div>
                </div>
                <div class="tools-grid" id="edit-form">
                    {% for tool in tools_edit %}
                    <label class="tool-check">
                        <input type="checkbox" name="scopes" value="{{ tool }}" class="edit-tool-checkbox"> {{ tool }}
                    </label>
                    {% endfor %}
                </div>
                <div class="btn-container">
                    <button type="submit" class="submit-btn" style="background: #eab308; color:#000;">SAVE CHANGES</button>
                </div>
            </form>
        </div>
    </div>

    <div id="apisModal" class="modal">
        <div class="modal-content" style="max-width: 750px;">
            <span class="close-modal" onclick="closeApisModal()">&times;</span>
            <div class="modal-title">🌐 LIVE SYSTEM AUTHORIZED ROUTE ENDPOINTS</div>
            <div style="font-size:0.75rem; color:#8a8aa3; margin-bottom:15px;">Your dynamic URLs matching your deployed gateway parameters:</div>
            <div id="urls-list" style="max-height: 50vh; overflow-y:auto; font-family: monospace; background:#13131c; padding:15px; border-radius:4px; border:1px solid #27273a;">
            </div>
        </div>
    </div>

    <script>
        function toggleAllTools(containerId) {
            let checkboxes = document.querySelectorAll('#' + containerId + ' input[type="checkbox"]');
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
         Gentile context logic parameters updates execution trigger 
        function closeEditModal() { document.getElementById('editModal').style.display = 'none'; }
        function openApisModal() {
            let currentHost = window.location.origin;
            let tools = ["ADV", "PAYTM", "IMEI", "CALLTRACER", "UPI", "IFSC", "NUMBER", "PINCODE","IP", "CHALLAN", "FF", "BGMI", "SNAP", "EMAIL", "VEHICLE", "GIT", "INSTA", "TG", "TGIDINFO", "NUMLEAK", "PK", "NAME", "AADHAR", "NUMTOUPI", "PAN", "VEH2NUM", "ADHARFAMILY", "BOMBER"];
            let container = document.getElementById('urls-list');
            container.innerHTML = '';
            tools.forEach(t => {
                let lower = t.toLowerCase();
                container.innerHTML += `<div style="margin-bottom:12px; border-bottom:1px solid #27273a; padding-bottom:6px;"><span style="color:#bc13fe;">[GET]</span> ${currentHost}/api/${lower}?key=<span style="color:#10b981;">YOUR_KEY</span>&param=value</div>`;
            });
            document.getElementById('apisModal').style.display = 'flex';
        }
        function closeApisModal() { document.getElementById('apisModal').style.display = 'none'; }
    </script>
</body>
</html>
"""

# --- SESSIONS & REBOOT RECOVERY PROTECTION MIDDLEWARE ---
def check_session(request: Request, session_token: Optional[str] = Depends(cookie_sec)):
    # Direct system exception conversion protection strategy to eliminate raw standard "Unauthorized" panels
    if not session_token or session_token != "authenticated_shayan_session":
        raise HTTPException(status_code=303, headers={"Location": "/"})
    return True

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 303:
        return RedirectResponse(url=exc.headers.get("Location"), status_code=303)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

# --- ROUTING PLATFORM PIPELINE ENGINE ---

@app.get("/", response_class=HTMLResponse)
def get_login_page():
    return LOGIN_HTML.replace("{% if error %}<div class=\"error\">{{ error }}</div>{% endif %}", "")

@app.post("/login")
def handle_login(username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USER and password == ADMIN_PASS:
        response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(key="session_token", value="authenticated_shayan_session", httponly=True)
        return response
    error_msg = '<div class="error">Access Denied: Invalid System Credentials</div>'
    return HTMLResponse(content=LOGIN_HTML.replace('{% if error %}<div class="error">{{ error }}</div>{% endif %}', error_msg))

@app.get("/logout")
def handle_logout():
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("session_token")
    return response

@app.get("/dashboard", response_class=HTMLResponse)
def get_dashboard(auth: bool = Depends(check_session)):
    # Inject static structures securely back to execution matrix if serverless cold boot wiped them
    for k, v in PERMANENT_STATIC_KEYS.items():
        if k not in API_KEYS_DB:
            API_KEYS_DB[k] = v

    rendered = DASHBOARD_HTML
    
    # 1. Tools Mapping
    tools_html = "".join([f'<label class="tool-check"><input type="checkbox" name="scopes" value="{t}"> {t}</label>' for t in AVAILABLE_TOOLS])
    rendered = rendered.replace('{% for tool in tools %}\n                <label class="tool-check">\n                    <input type="checkbox" name="scopes" value="{{ tool }}" class="tool-checkbox"> {{ tool }}\n                </label>\n                {% endfor %}', tools_html)
    rendered = rendered.replace('{% for tool in tools_edit %}\n                    <label class="tool-check">\n                        <input type="checkbox" name="scopes" value="{{ tool }}" class="edit-tool-checkbox"> {{ tool }}\n                    </label>\n                    {% endfor %}', tools_html)

    # 2. Dynamic Rows Configuration Builder (Fully Functional Interventions Logic Matrix)
    rows_list = []
    for k, v in API_KEYS_DB.items():
        scopes_badges = "".join([f'<span class="badge-scope">{s}</span>' for s in v["scopes"]])
        status_badge = f'<span class="badge-active">Active</span>' if v["status"] == "Active" else f'<span class="badge-suspended">Suspended</span>'
        
        scopes_json = json.dumps(v["scopes"]).replace('"', '&quot;')
        owner_escaped = v['owner'].replace("'", "\\'")
        
        row_ui = f"""
        <tr>
            <td>{v['owner']}</td>
            <td style="color: #bc13fe; font-weight:bold;">{v['token']}</td>
            <td style="color: #ff007f;">{v['expiry']}</td>
            <td>{v['used']} / {v['limit']}</td>
            <td>{status_badge}</td>
            <td>{scopes_badges}</td>
            <td>
                <button class="btn-action btn-edit" onclick="openEditModal('{v['token']}', '{owner_escaped}', {v['limit']}, '{v['expiry']}', '{scopes_json}')">EDIT</button>
                <a href="/keys/reset/{v['token']}" class="btn-action btn-reset">RESET</a>
                <a href="/keys/toggle/{v['token']}" class="btn-action btn-toggle {'suspended' if v['status'] != 'Active' else ''}">TOGGLE</a>
                <a href="/keys/delete/{v['token']}" class="btn-action btn-del">DEL</a>
            </td>
        </tr>
        """
        rows_list.append(row_ui)
    
    rendered = rendered.replace("{% for row in rows %}\n                {{ row }}\n                {% endfor %}", "".join(rows_list))

    # 3. Request Streams Tracking Logs Matrix Builder
    logs_list = []
    for log in reversed(PIPELINE_LOGS[-15:]):
        logs_list.append(f"""
        <tr>
            <td>{log['time']}</td>
            <td>{log['token']}</td>
            <td><span class="badge-scope" style="color:#00ffcc;">{log['route']}</span></td>
            <td style="font-family: monospace; color: #8a8aa3;">{log['params']}</td>
        </tr>
        """)
    if not logs_list:
        logs_list.append('<tr><td colspan="4" style="text-align: center; color: #6b7280; padding: 20px 0;">No active request stream metrics tracking currently.</td></tr>')
        
    rendered = rendered.replace("{% for log in logs %}\n                {{ log }}\n                {% endfor %}", "".join(logs_list))
    return rendered

# --- API LIFECYCLE MANAGEMENT MUTATION ROUTES ---

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
    
    # Retrieve previous runtime usage statistics to keep counts accurate
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

    if "ALL" not in key_profile["scopes"] and route.upper() not in key_profile["scopes"]:
        return JSONResponse(status_code=403, content={"error": f"Unauthorized Access Scope Framework for Sub-Tool: {route.upper()}"})

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





