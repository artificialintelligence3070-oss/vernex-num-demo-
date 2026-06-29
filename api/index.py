import os
import time
import requests
from datetime import datetime
from typing import Dict, List, Optional
# Added 'Response' to the import list below to fix the crash
from fastapi import FastAPI, Request, Depends, HTTPException, Form, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel

app = FastAPI(title="SHAYAN_EXPLORER API Gateway")
security = HTTPBasic()

# --- CONFIGURATION & CONSTANTS ---
TARGET_BASE_URL = "https://ft-osint-api.duckdns.org/api"
ADMIN_USERNAME = "SHAYAN_EXPLORER"
ADMIN_PASSWORD = "DEVELOPER_PASSWORD_CHANGE_ME"  # Change this password before hosting

# --- DATA MODELS ---
class APIKeyConfig(BaseModel):
    key: str
    name: str
    expiry_date: str  # Format: YYYY-MM-DD
    daily_limit: int
    current_used: int = 0
    is_active: bool = True
    allowed_tools: List[str] = []

# Mock Database
API_KEYS_DB: Dict[str, dict] = {
    "SHAYAN-TEST-KEY-2026": {
        "key": "SHAYAN-TEST-KEY-2026",
        "name": "Default Premium User",
        "expiry_date": "2026-12-31",
        "daily_limit": 1000,
        "current_used": 0,
        "is_active": True,
        "allowed_tools": ["all"]
    }
}

SEARCH_LOGS: List[dict] = []

AVAILABLE_TOOLS = {
    "number": "📞 Number Lookup",
    "adv": "🔍 Advanced Lookup",
    "paytm": "💰 Paytm Info",
    "imei": "📱 IMEI Tracker",
    "calltracer": "🛰️ Call Tracer",
    "upi": "💳 UPI Lookup",
    "ifsc": "🏦 IFSC Details",
    "pincode": "📍 Pincode Lookup",
    "ip": "🌐 IP Tracker",
    "challan": "🧾 Vehicle Challan",
    "ff": "🎮 FreeFire UID Lookup",
    "bgmi": "⚔️ BGMI UID Lookup",
    "snap": "📸 Snapchat Finder",
    "email": "📧 Email Validator",
    "vehicle": "🚗 Vehicle Lookup",
    "git": "🐙 GitHub Analyzer",
    "insta": "🌟 Instagram Info",
    "tg": "✈️ Telegram Username to Num",
    "tgidinfo": "🆔 Telegram ID Details",
    "numleak": "🔓 Number Leak Check"
}

# --- HELPER UTILITIES ---
def validate_and_update_key(key: str, endpoint: str) -> tuple[bool, str]:
    if key not in API_KEYS_DB:
        return False, "Invalid API Key provided."
    
    key_info = API_KEYS_DB[key]
    if not key_info["is_active"]:
        return False, "This API key has been disabled by the administrator."
        
    try:
        expiry = datetime.strptime(key_info["expiry_date"], "%Y-%m-%d")
        if datetime.now() > expiry:
            return False, f"Key expired on {key_info['expiry_date']}."
    except ValueError:
        return False, "API Key possesses an invalid date configuration format."
        
    if key_info["current_used"] >= key_info["daily_limit"]:
        return False, "Daily request quota limit reached for this key."
        
    if "all" not in key_info["allowed_tools"] and endpoint not in key_info["allowed_tools"]:
        return False, f"Access denied to endpoint: [{endpoint}] for this subscription key."
        
    API_KEYS_DB[key]["current_used"] += 1
    return True, "Authorized"

def log_transaction(key: str, endpoint: str, query: str, status: str):
    SEARCH_LOGS.insert(0, {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "key_name": API_KEYS_DB.get(key, {}).get("name", "Unknown/Invalid"),
        "endpoint": endpoint,
        "query": query,
        "status": status
    })

def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username != ADMIN_USERNAME or credentials.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Unauthorized Admin Access Credentials")
    return credentials.username

# --- PUBLIC INTERFACES ---

@app.get("/", response_class=HTMLResponse)
async def public_dashboard_interface():
    tools_options = "".join([f'<option value="{k}">{v}</option>' for k, v in AVAILABLE_TOOLS.items()])
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SHAYAN_EXPLORER | Elite OSINT API Suite</title>
        <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@500;700&display=swap" rel="stylesheet">
        <style>
            :root {{ --primary: #00f0ff; --bg: #0a0a12; --card-bg: rgba(20, 20, 35, 0.7); --accent: #ff007f; }}
            body {{ margin: 0; padding: 0; background: var(--bg); color: #fff; font-family: 'Rajdhani', sans-serif; min-height: 100vh; background-image: radial-gradient(circle at 50% 50%, #14142b 0%, #0a0a12 100%); }}
            .navbar {{ display: flex; justify-content: space-between; align-items: center; padding: 20px 40px; border-bottom: 1px solid rgba(0, 240, 255, 0.2); backdrop-filter: blur(10px); }}
            .logo {{ font-family: 'Orbitron', sans-serif; font-size: 24px; font-weight: bold; color: var(--primary); text-shadow: 0 0 10px var(--primary); }}
            .container {{ max-width: 900px; margin: 40px auto; padding: 20px; }}
            .card {{ background: var(--card-bg); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; padding: 30px; backdrop-filter: blur(15px); box-shadow: 0 20px 50px rgba(0,0,0,0.5); transition: all 0.3s ease; }}
            .card:hover {{ border-color: var(--primary); box-shadow: 0 20px 50px rgba(0, 240, 255, 0.15); }}
            h2 {{ font-family: 'Orbitron', sans-serif; text-transform: uppercase; color: #fff; border-left: 4px solid var(--primary); padding-left: 10px; }}
            .form-group {{ margin-bottom: 20px; }}
            label {{ display: block; margin-bottom: 8px; font-weight: bold; color: #aaa; }}
            input, select {{ width: 100%; padding: 12px; background: rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; color: #fff; font-size: 16px; box-sizing: border-box; }}
            button {{ width: 100%; padding: 14px; background: linear-gradient(45deg, var(--primary), #0072ff); border: none; border-radius: 8px; color: #fff; font-size: 18px; font-weight: bold; cursor: pointer; font-family: 'Orbitron', sans-serif; letter-spacing: 2px; }}
            .response-box {{ margin-top: 30px; background: #05050a; border: 1px solid rgba(255,255,255,0.05); border-radius: 8px; padding: 20px; display: none; max-height: 400px; overflow-y: auto; }}
            pre {{ margin: 0; font-family: monospace; color: #00ff66; white-space: pre-wrap; word-break: break-all; }}
            .footer {{ text-align: center; margin-top: 40px; padding: 20px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="navbar">
            <div class="logo">SHAYAN_EXPLORER</div>
            <div><a href="/admin" style="color: var(--primary); text-decoration: none; font-weight: bold;">🔑 Admin Terminal</a></div>
        </div>
        <div class="container">
            <div class="card">
                <h2>⚡ Intelligence Operations Center</h2>
                <div class="form-group">
                    <label>Developer Gateway Key</label>
                    <input type="text" id="apiKey" placeholder="Enter valid SHAYAN_EXPLORER API Key">
                </div>
                <div class="form-group">
                    <label>Target Execution Module</label>
                    <select id="endpointSelector">{tools_options}</select>
                </div>
                <div class="form-group">
                    <label>Target Identity Parameter Value</label>
                    <input type="text" id="targetQuery" placeholder="Ex: 9876543210, example@ybl">
                </div>
                <button onclick="executeLookup()">EXECUTE LOOKUP INSTANCE</button>
                <div class="response-box" id="resBox">
                    <h3 style="margin-top:0; color:var(--primary); font-family:'Orbitron';">Execution Target Output Stream</h3>
                    <pre id="jsonOutput">Awaiting initialization...</pre>
                </div>
            </div>
        </div>
        <div class="footer">&copy; 2026 Developed by <strong>SHAYAN_EXPLORER</strong></div>
        <script>
            async function executeLookup() {{
                const key = document.getElementById('apiKey').value;
                const endpoint = document.getElementById('endpointSelector').value;
                const target = document.getElementById('targetQuery').value;
                const resBox = document.getElementById('resBox');
                const output = document.getElementById('jsonOutput');
                if(!key || !target) {{ alert('Missing inputs'); return; }}
                resBox.style.display = "block";
                output.innerText = "Querying...";
                try {{
                    let paramName = "num";
                    if(["upi", "ifsc", "pincode", "ip", "challan", "email", "vehicle"].includes(endpoint)) paramName = endpoint;
                    if(endpoint === "imei") paramName = "imei";
                    if(["snap", "git", "insta"].includes(endpoint)) paramName = "username";
                    if(endpoint === "ff" || endpoint === "bgmi") paramName = "uid";
                    if(endpoint === "tg") paramName = "info";
                    if(endpoint === "tgidinfo") paramName = "id";

                    const res = await fetch(`/api/gateway/${{endpoint}}?key=${{encodeURIComponent(key)}}&${{paramName}}=${{encodeURIComponent(target)}}`);
                    const data = await res.json();
                    output.innerText = JSON.stringify(data, null, 4);
                }} catch(err) {{ output.innerText = "Error: " + err.message; }}
            }}
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/admin", response_class=HTMLResponse)
async def admin_control_panel(username: str = Depends(verify_admin)):
    log_rows = "".join([
        f"<tr><td>{l['timestamp']}</td><td>{l['key_name']}</td><td><span class='badge'>{l['endpoint']}</span></td><td>{l['query']}</td><td>{l['status']}</td></tr>"
        for l in SEARCH_LOGS
    ])
    key_rows = "".join([
        f"""<tr>
            <td><strong>{k['name']}</strong><br><small style='color:#666;'>{k['key']}</small></td>
            <td>{k['expiry_date']}</td>
            <td>{k['current_used']} / {k['daily_limit']}</td>
            <td><span class="status-indicator {'active' if k['is_active'] else 'disabled'}"></span> {'Active' if k['is_active'] else 'Suspended'}</td>
            <td>
                <form action="/admin/action/reset" method="post" style="display:inline;">
                    <input type="hidden" name="key" value="{k['key']}">
                    <button type="submit" class="tbl-btn">Reset</button>
                </form>
                <form action="/admin/action/toggle" method="post" style="display:inline;">
                    <input type="hidden" name="key" value="{k['key']}">
                    <button type="submit" class="tbl-btn style-toggle">Toggle</button>
                </form>
            </td>
        </tr>"""
        for k in API_KEYS_DB.values()
    ])

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>SHAYAN_EXPLORER | Admin</title>
        <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700&family=Rajdhani:wght@500;600&display=swap" rel="stylesheet">
        <style>
            body {{ background-color: #0b0c10; color: #c5c6c7; font-family: 'Rajdhani', sans-serif; margin:0; }}
            .header {{ background: #1f2833; padding: 20px 40px; display:flex; justify-content:space-between; align-items:center; border-bottom: 2px solid #66fcf1; }}
            .header h1 {{ font-family: 'Orbitron', sans-serif; color: #66fcf1; margin:0; font-size:22px; }}
            .main-layout {{ max-width: 1200px; margin: 30px auto; padding: 0 20px; display: grid; grid-template-columns: 1fr 2fr; gap: 30px; }}
            .panel {{ background: #1f2833; border-radius: 8px; padding: 25px; }}
            h2 {{ font-family: 'Orbitron', sans-serif; font-size: 18px; color: #66fcf1; margin-top:0; border-bottom: 1px solid #45a29e; padding-bottom:10px; }}
            label {{ display:block; margin: 12px 0 6px 0; color: #45a29e; font-weight: bold; }}
            input, select {{ width:100%; padding: 10px; background: #0b0c10; border: 1px solid #45a29e; border-radius:4px; color:#fff; box-sizing:border-box; }}
            button.btn {{ width:100%; padding:12px; background:#66fcf1; border:none; border-radius:4px; color:#0b0c10; font-family:'Orbitron'; font-weight:bold; cursor:pointer; margin-top:15px; }}
            table {{ width:100%; border-collapse: collapse; }}
            th, td {{ padding: 12px; text-align:left; border-bottom: 1px solid #45a29e; }}
            .status-indicator {{ width:10px; height:10px; border-radius:50%; display:inline-block; }}
            .status-indicator.active {{ background: #00ff66; }}
            .status-indicator.disabled {{ background: #ff0055; }}
            .tbl-btn {{ background:#0b0c10; color:#66fcf1; border:1px solid #66fcf1; padding:4px 8px; border-radius:4px; cursor:pointer; }}
            .logs-container {{ max-height: 300px; overflow-y:auto; background:#0b0c10; padding:10px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>SHAYAN_EXPLORER // KERNEL PANEL</h1>
            <div>Admin: <strong style="color:#66fcf1;">{username}</strong></div>
        </div>
        <div class="main-layout">
            <div class="panel">
                <h2>🛠️ Generate Token Node</h2>
                <form action="/admin/action/generate" method="post">
                    <label>Unique Key ID</label>
                    <input type="text" name="key" required>
                    <label>Client Reference Name</label>
                    <input type="text" name="name" required>
                    <label>Expiration Timeline Date</label>
                    <input type="date" name="expiry_date" required>
                    <label>Daily Request Threshold</label>
                    <input type="number" name="daily_limit" value="100" required>
                    <label>Module Permission Provision</label>
                    <select name="allowed_tools">
                        <option value="all">Grant All Functional Modules</option>
                    </select>
                    <button type="submit" class="btn">PROVISION ACCESS KEY</button>
                </form>
            </div>
            <div class="panel">
                <h2>🔑 Active Key Registry</h2>
                <table>
                    <thead><tr><th>Key / Identity</th><th>Expiry</th><th>Requests Used</th><th>Status</th><th>Actions</th></tr></thead>
                    <tbody>{key_rows}</tbody>
                </table>
                <h2 style="margin-top:40px;">📋 Live Gateway Audit Logs</h2>
                <div class="logs-container">
                    <table>
                        <thead><tr><th>Time</th><th>Key Client</th><th>Module</th><th>Query</th><th>Status</th></tr></thead>
                        <tbody>{log_rows}</tbody>
                    </table>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# --- BACKEND COMMAND OPERATION ACTIONS ---

@app.post("/admin/action/generate")
async def action_generate_key(
    key: str = Form(...), name: str = Form(...), expiry_date: str = Form(...), 
    daily_limit: int = Form(...), allowed_tools: str = Form(...), username: str = Depends(verify_admin)
):
    API_KEYS_DB[key] = {
        "key": key, "name": name, "expiry_date": expiry_date, "daily_limit": daily_limit,
        "current_used": 0, "is_active": True, "allowed_tools": [allowed_tools]
    }
    return HTMLResponse("<script>window.location.href='/admin';</script>")

@app.post("/admin/action/reset")
async def action_reset_limit(key: str = Form(...), username: str = Depends(verify_admin)):
    if key in API_KEYS_DB:
        API_KEYS_DB[key]["current_used"] = 0
    return HTMLResponse("<script>window.location.href='/admin';</script>")

@app.post("/admin/action/toggle")
async def action_toggle_key(key: str = Form(...), username: str = Depends(verify_admin)):
    if key in API_KEYS_DB:
        API_KEYS_DB[key]["is_active"] = not API_KEYS_DB[key]["is_active"]
    return HTMLResponse("<script>window.location.href='/admin';</script>")

# --- CORE GATEWAY PROXY ROUTE ENGINE ---

@app.get("/api/gateway/{endpoint}")
async def core_proxy_gateway(endpoint: str, request: Request):
    query_params = dict(request.query_params)
    client_key = query_params.get("key", "")
    
    is_valid, msg = validate_and_update_key(client_key, endpoint)
    search_query = next((v for k, v in query_params.items() if k != "key"), "N/A")
    
    if not is_valid:
        log_transaction(client_key, endpoint, search_query, f"DENIED: {msg}")
        return JSONResponse(status_code=403, content={"status": "error", "developer": "SHAYAN_EXPLORER", "message": msg})
        
    proxy_params = query_params.copy()
    proxy_params["key"] = ""
    
    try:
        response = requests.get(f"{TARGET_BASE_URL}/{endpoint}", params=proxy_params, timeout=10)
        log_transaction(client_key, endpoint, search_query, f"SUCCESS ({response.status_code})")
        
        try:
            payload_data = response.json()
            if isinstance(payload_data, dict):
                payload_data.pop("credit", None)
                payload_data.pop("channel", None)
                payload_data["developer"] = "SHAYAN_EXPLORER"
            return payload_data
        except ValueError:
            return Response(content=response.text, media_type="text/plain") # This will now work perfectly
            
    except Exception as e:
        log_transaction(client_key, endpoint, search_query, f"FORWARDING FAULT: {str(e)}")
        return JSONResponse(status_code=502, content={"status": "fail", "developer": "SHAYAN_EXPLORER", "reason": "Connection execution timeout encountered."})
