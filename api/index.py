import os
import time
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

# --- PERSISTENCE LAYER (In-Memory Simulation for Serverless) ---
# Note: For production, bind these dictionaries to a persistent DB
API_KEYS_DB = {
    "vx-osint": {
        "owner": "Master Deployment",
        "token": "vx-osint",
        "expiry": "LIFETIME ACCESS",
        "limit": 5000,
        "used": 0,
        "status": "Active",
        "scopes": ["ALL"]
    }
}
PIPELINE_LOGS = []

AVAILABLE_TOOLS = [
    "ADV", "PAYTM", "IMEI", "CALLTRACER", "UPI", "IFSC", "NUMBER", "PINCODE",
    "IP", "CHALLAN", "FF", "BGMI", "SNAP", "EMAIL", "VEHICLE", "GIT", "INSTA", 
    "TG", "TGIDINFO", "NUMLEAK"
]

# --- UI TEMPLATES (Embedded for seamless single-file Vercel deploy) ---
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
        .nav-btn { background: #13131c; border: 1px solid #27273a; color: #8a8aa3; padding: 6px 12px; text-decoration: none; font-size: 0.8rem; border-radius: 4px; margin-left: 10px; }
        .nav-btn:hover { border-color: #bc13fe; color: #fff; }
        .section-title { color: #bc13fe; font-size: 0.9rem; margin-top: 40px; margin-bottom: 20px; letter-spacing: 1px; text-transform: uppercase; }
        .card { background: #0c0c12; border: 1px solid #1f1f2e; padding: 25px; border-radius: 6px; margin-bottom: 25px; }
        .grid-2 { display: grid; grid-template-columns: 1xl 1fr; gap: 20px; margin-bottom: 20px; }
        @media(min-width: 768px) { .grid-2 { grid-template-columns: 1fr 1fr; } }
        .input-box { display: flex; flex-direction: column; }
        .input-box label { font-size: 0.75rem; color: #6b7280; margin-bottom: 6px; }
        .input-box input, .input-box select { background: #13131c; border: 1px solid #27273a; padding: 10px; color: #fff; border-radius: 4px; }
        .input-box input:focus { border-color: #bc13fe; outline: none; }
        .tools-header { display: flex; justify-content: space-between; font-size: 0.75rem; margin-top: 20px; margin-bottom: 10px; color: #6b7280; }
        .tools-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 12px; }
        .tool-check { background: #13131c; border: 1px solid #27273a; padding: 10px; border-radius: 4px; display: flex; align-items: center; font-size: 0.75rem; cursor: pointer; }
        .tool-check input { margin-right: 10px; accent-color: #bc13fe; }
        .btn-container { display: flex; justify-content: flex-end; margin-top: 25px; }
        .submit-btn { background: linear-gradient(90deg, #bc13fe, #7a13fe); border: none; color: white; padding: 12px 24px; font-weight: bold; border-radius: 4px; cursor: pointer; font-size: 0.8rem; }
        .submit-btn:hover { box-shadow: 0 0 10px rgba(188, 19, 254, 0.4); }
        table { width: 100%; border-collapse: collapse; font-size: 0.75rem; text-align: left; }
        th { color: #6b7280; font-weight: normal; padding-bottom: 12px; border-bottom: 1px solid #1f1f2e; }
        td { padding: 12px 0; border-bottom: 1px solid #11111a; }
        .badge-active { color: #10b981; font-weight: bold; }
        .badge-scope { background: #27273a; padding: 2px 6px; border-radius: 3px; color: #d1d5db; }
        .action-link { color: #ff4a4a; text-decoration: none; margin-left: 8px; }
        .action-link:hover { text-decoration: underline; }
    </style>
</head>
<body>

    <div class="navbar">
        <div class="brand">• SHAYAN_EXPLORER HUB</div>
        <div>
            <a href="#" class="nav-btn">VIEW_SYSTEM_APIS</a>
            <a href="/logout" class="nav-btn">LOGOUT</a>
        </div>
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
                    <label>TARGET EXPIRATION LIFECYCLE</label>
                    <input type="date" name="expiry_date" required>
                </div>
            </div>

            <div class="tools-header">
                <div>ROUTE AUTHORIZATION PRIVILEGES SCOPE</div>
                <div style="color: #ff007f; cursor:pointer;" onclick="toggleAllTools()">Select All Available Sub-Tools</div>
            </div>
            
            <div class="tools-grid">
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
                {% for k, v in keys_db.items() %}
                <tr>
                    <td>{{ v.owner }}</td>
                    <td style="color: #bc13fe;">{{ v.token }}</td>
                    <td style="color: #ff007f;">{{ v.expiry }}</td>
                    <td>{{ v.used }} / {{ v.limit }}</td>
                    <td><span class="badge-active">{{ v.status }}</span></td>
                    <td>
                        {% for scope in v.scopes %}
                        <span class="badge-scope">{{ scope }}</span>
                        {% endfor %}
                    </td>
                    <td>
                        <a href="/keys/delete/{{ v.token }}" class="action-link">DEL</a>
                    </td>
                </tr>
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
                {% if not logs %}
                <tr>
                    <td colspan="4" style="text-align: center; color: #6b7280; padding: 20px 0;">No active request stream metrics tracking currently.</td>
                </tr>
                {% endif %}
                {% for log in logs %}
                <tr>
                    <td>{{ log.time }}</td>
                    <td>{{ log.token }}</td>
                    <td><span class="badge-scope" style="color:#00ffcc;">{{ log.route }}</span></td>
                    <td style="font-family: monospace; color: #8a8aa3;">{{ log.params }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <script>
        function toggleAllTools() {
            let checkboxes = document.querySelectorAll('.tool-checkbox');
            let allChecked = Array.from(checkboxes).every(cb => cb.checked);
            checkboxes.forEach(cb => cb.checked = !allChecked);
        }
    </script>
</body>
</html>
"""

# --- MIDDLEWARE & AUTH FUNCTIONALITY ---
def check_session(session_token: Optional[str] = Depends(cookie_sec)):
    if not session_token or session_token != "authenticated_shayan_session":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return True

# --- ROUTING ENGINE ---

@app.get("/", response_class=HTMLResponse)
def get_login_page():
    return LOGIN_HTML.replace("{% if error %}<div class=\"error\">{{ error }}</div>{% endif %}", "")

@app.post("/login", response_class=HTMLResponse)
def handle_login(username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USER and password == ADMIN_PASS:
        response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(key="session_token", value="authenticated_shayan_session", httponly=True)
        return response
    
    error_msg = '<div class="error">Access Denied: Invalid System Credentials</div>'
    return LOGIN_HTML.replace('{% if error %}<div class="error">{{ error }}</div>{% endif %}', error_msg)

@app.get("/logout")
def handle_logout():
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("session_token")
    return response

@app.get("/dashboard", response_class=HTMLResponse)
def get_dashboard(auth: bool = Depends(check_session)):
    # Simple formatting engine replacement
    rendered = DASHBOARD_HTML
    
    # Render loop for tools checkboxes
    tools_html = "".join([f'<label class="tool-check"><input type="checkbox" name="scopes" value="{t}" class="tool-checkbox"> {t}</label>' for t in AVAILABLE_TOOLS])
    rendered = rendered.replace("{% for tool in tools %}\n                <label class=\"tool-check\">\n                    <input type=\"checkbox\" name=\"scopes\" value=\"{{ tool }}\" class=\"tool-checkbox\"> {{ tool }}\n                </label>\n                {% endfor %}", tools_html)
    
    # Render table rows for Keys Database
    rows_html = ""
    for k, v in API_KEYS_DB.items():
        scopes_badges = "".join([f'<span class="badge-scope">{s}</span>' for s in v["scopes"]])
        rows_html += f"""
        <tr>
            <td>{v['owner']}</td>
            <td style="color: #bc13fe;">{v['token']}</td>
            <td style="color: #ff007f;">{v['expiry']}</td>
            <td>{v['used']} / {v['limit']}</td>
            <td><span class="badge-active">{v['status']}</span></td>
            <td>{scopes_badges}</td>
            <td><a href="/keys/delete/{v['token']}" class="action-link">DEL</a></td>
        </tr>
        """
    rendered = rendered.replace("{% for k, v in keys_db.items() %}\n                <tr>\n                    <td>{{ v.owner }}</td>\n                    <td style=\"color: #bc13fe;\">{{ v.token }}</td>\n                    <td style=\"color: #ff007f;\">{{ v.expiry }}</td>\n                    <td>{{ v.used }} / {{ v.limit }}</td>\n                    <td><span class=\"badge-active\">{{ v.status }}</span></td>\n                    <td>\n                        {% for scope in v.scopes %}\n                        <span class=\"badge-scope\">{{ scope }}</span>\n                        {% endfor %}\n                    </td>\n                    <td>\n                        <a href=\"/keys/delete/{{ v.token }}\" class=\"action-link\">DEL</a>\n                    </td>\n                </tr>\n                {% endfor %}", rows_html)

    # Render pipeline logs
    logs_html = ""
    for log in reversed(PIPELINE_LOGS[-15:]): # Show last 15 elements
        logs_html += f"""
        <tr>
            <td>{log['time']}</td>
            <td>{log['token']}</td>
            <td><span class="badge-scope" style="color:#00ffcc;">{log['route']}</span></td>
            <td style="font-family: monospace; color: #8a8aa3;">{log['params']}</td>
        </tr>
        """
    if logs_html:
        rendered = rendered.replace("{% if not logs %}\n                <tr>\n                    <td colspan=\"4\" style=\"text-align: center; color: #6b7280; padding: 20px 0;\">No active request stream metrics tracking currently.</td>\n                </tr>\n                {% endif %}\n                {% for log in logs %}\n                <tr>\n                    <td>{{ log.time }}</td>\n                    <td>{{ log.token }}</td>\n                    <td><span class=\"badge-scope\" style=\"color:#00ffcc;\">{{ log.route }}</span></td>\n                    <td style=\"font-family: monospace; color: #8a8aa3;\">{{ log.params }}</td>\n                </tr>\n                {% endfor %}", logs_html)
    else:
        rendered = rendered.replace("{% for log in logs %}\n                <tr>\n                    <td>{{ log.time }}</td>\n                    <td>{{ log.token }}</td>\n                    <td><span class=\"badge-scope\" style=\"color:#00ffcc;\">{{ log.route }}</span></td>\n                    <td style=\"font-family: monospace; color: #8a8aa3;\">{{ log.params }}</td>\n                </tr>\n                {% endfor %}", "")

    return rendered

@app.post("/keys/generate")
def generate_key(owner: str = Form(...), token: Optional[str] = Form(None), limit: int = Form(...), expiry_date: str = Form(...), scopes: List[str] = Form(None), auth: bool = Depends(check_session)):
    key_token = token.strip() if token and token.strip() else f"vx-{int(time.time())}"
    assigned_scopes = scopes if scopes else ["ALL"]
    
    # Format date string cleanly
    try:
        parsed_date = datetime.strptime(expiry_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        parsed_date = "LIFETIME ACCESS"

    API_KEYS_DB[key_token] = {
        "owner": owner,
        "token": key_token,
        "expiry": parsed_date,
        "limit": limit,
        "used": 0,
        "status": "Active",
        "scopes": assigned_scopes
    }
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/keys/delete/{token}")
def delete_key(token: str, auth: bool = Depends(check_session)):
    if token in API_KEYS_DB:
        del API_KEYS_DB[token]
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)


# --- CORE API PROXY INTEGRATION LAYER ---
@app.get("/api/{route}")
def proxy_gateway(route: str, request: Request, key: str):
    # 1. Validate Custom Key Existence
    if key not in API_KEYS_DB:
        return JSONResponse(status_code=403, content={"error": "Access Revoked: Invalid Token Identification Matrix"})
    
    key_profile = API_KEYS_DB[key]
    current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    query_params = dict(request.query_params)
    
    # Clean proxy verification parameter out of forwarding logs
    if "key" in query_params:
        del query_params["key"]
    
    # 2. Append Intercept logs
    PIPELINE_LOGS.append({
        "time": current_time_str,
        "token": key,
        "route": route.upper(),
        "params": str(query_params)
    })

    # 3. Check Route Privilege Scopes
    if "ALL" not in key_profile["scopes"] and route.upper() not in key_profile["scopes"]:
        return JSONResponse(status_code=403, content={"error": f"Unauthorized Access Scope Framework for Sub-Tool: {route.upper()}"})

    # 4. Check Rate/Limit Velocity Expirations
    if key_profile["expiry"] != "LIFETIME ACCESS":
        today_date = datetime.now().strftime("%Y-%m-%d")
        if today_date > key_profile["expiry"]:
            return JSONResponse(status_code=403, content={"error": "Token lifecycle execution window has expired."})
            
    if key_profile["used"] >= key_profile["limit"]:
        return JSONResponse(status_code=429, content={"error": "Transaction call allocation volume limits fully exhausted."})

    # Increment metric tracking counter
    key_profile["used"] += 1

    # 5. Forward Execution Pipeline to Target API Host
    upstream_params = dict(request.query_params)
    upstream_params["key"] = MASTER_KEY # Seamless transparent payload swapping
    
    try:
        target_url = f"{TARGET_BASE_API}/{route}"
        upstream_response = requests.get(target_url, params=upstream_params, timeout=12)
        return JSONResponse(status_code=upstream_response.status_code, content=upstream_response.json())
    except requests.exceptions.RequestException as exc:
        return JSONResponse(status_code=502, content={"error": "Upstream communication gateway failure", "details": str(exc)})



