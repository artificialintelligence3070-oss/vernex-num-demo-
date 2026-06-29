import os
import time
import requests
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import FastAPI, Request, Depends, HTTPException, Form, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel

# Initialize App Instance
app = FastAPI(title="SHAYAN_EXPLORER API Gateway")
security = HTTPBasic()

# --- CONFIGURATION & CONSTANTS ---
TARGET_BASE_URL = "https://ft-osint-api.duckdns.org/api"
ADMIN_USERNAME = "SHAYAN_EXPLORER"
ADMIN_PASSWORD = "DEVELOPER_PASSWORD_CHANGE_ME"

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

# --- ROUTES ---

@app.get("/", response_class=HTMLResponse)
def public_dashboard_interface():
    tools_options = "".join([f'<option value="{k}">{v}</option>' for k, v in AVAILABLE_TOOLS.items()])
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SHAYAN_EXPLORER | Elite OSINT API Suite</title>
        <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@500;700&display=swap" rel="stylesheet">
        <style>
            :root {{ --primary: #00f0ff; --bg: #0a0a12; --card-bg: rgba(20, 20, 35, 0.7); }}
            body {{ margin: 0; padding: 0; background: var(--bg); color: #fff; font-family: 'Rajdhani', sans-serif; min-height: 100vh; background-image: radial-gradient(circle at 50% 50%, #14142b 0%, #0a0a12 100%); }}
            .navbar {{ display: flex; justify-content: space-between; align-items: center; padding: 20px 40px; border-bottom: 1px solid rgba(0, 240, 255, 0.2); backdrop-filter: blur(10px); }}
            .logo {{ font-family: 'Orbitron', sans-serif; font-size: 24px; font-weight: bold; color: var(--primary); text-shadow: 0 0 10px var(--primary); }}
            .container {{ max-width: 900px; margin: 40px auto; padding: 20px; }}
            .card {{ background: var(--card-bg); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; padding: 30px; box-shadow: 0 20px 50px rgba(0,0,0,0.5); }}
            h2 {{ font-family: 'Orbitron', sans-serif; border-left: 4px solid var(--primary); padding-left: 10px; }}
            .form-group {{ margin-bottom: 20px; }}
            label {{ display: block; margin-bottom: 8px; color: #aaa; font-weight: bold; }}
            input, select {{ width: 100%; padding: 12px; background: rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; color: #fff; }}
            button {{ width: 100%; padding: 14px; background: linear-gradient(45deg, var(--primary), #0072ff); border: none; border-radius: 8px; color: #fff; font-family: 'Orbitron', sans-serif; font-weight: bold; cursor: pointer; letter-spacing: 2px; }}
            .response-box {{ margin-top: 30px; background: #05050a; border: 1px solid rgba(255,255,255,0.05); border-radius: 8px; padding: 20px; display: none; max-height: 400px; overflow-y: auto; }}
            pre {{ margin: 0; font-family: monospace; color: #00ff66; white-space: pre-wrap; word-break: break-all; }}
            .footer {{ text-align: center; margin-top: 40px; color: #666; }}
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
                    <input type="text" id="apiKey" placeholder="Enter valid API Key">
                </div>
                <div class="form-group">
                    <label>Target Execution Module</label>
                    <select id="endpointSelector">{tools_options}</select>
                </div>
                <div class="form-group">
                    <label>Target Identity Parameter Value</label>
                    <input type="text" id="targetQuery" placeholder="Ex: 9876543210">
                </div>
                <button onclick="executeLookup()">EXECUTE LOOKUP INSTANCE</button>
                <div class="response-box" id="resBox">
                    <pre id="jsonOutput">Ready...</pre>
                </div>
            </div>
        </div>
        <div class="footer">&copy; 2026 Developed by <strong>SHAYAN_EXPLORER</strong></div>
        <script>
            async function executeLookup() {{
                const key = document.getElementById('apiKey').value;
                const endpoint = document.getElementById('endpointSelector').value;
                const target = document.getElementById('targetQuery').value;
                if(!key || !target) return;
                document.getElementById('resBox').style.display = "block";
                document.getElementById('jsonOutput').innerText = "Processing...";
                try {{
                    let p = "num";
                    if(["upi", "ifsc", "pincode", "ip", "challan", "email", "vehicle"].includes(endpoint)) p = endpoint;
                    if(endpoint === "imei") p = "imei";
                    if(["snap", "git", "insta"].includes(endpoint)) p = "username";
                    if(endpoint === "ff" || endpoint === "bgmi") p = "uid";
                    if(endpoint === "tg") p = "info";
                    if(endpoint === "tgidinfo") p = "id";

                    const res = await fetch(`/api/gateway/${{endpoint}}?key=${{encodeURIComponent(key)}}&${{p}}=${{encodeURIComponent(target)}}`);
                    const data = await res.json();
                    document.getElementById('jsonOutput').innerText = JSON.stringify(data, null, 4);
                }} catch(e) {{ document.getElementById('jsonOutput').innerText = "Error: " + e.message; }}
            }}
        </script>
    </body>
    </html>
    """

@app.get("/admin", response_class=HTMLResponse)
def admin_control_panel(username: str = Depends(verify_admin)):
    log_rows = "".join([f"<tr><td>{l['timestamp']}</td><td>{l['key_name']}</td><td>{l['endpoint']}</td><td>{l['query']}</td><td>{l['status']}</td></tr>" for l in SEARCH_LOGS])
    key_rows = "".join([f"""<tr>
        <td>{k['name']}<br><small>{k['key']}</small></td>
        <td>{k['expiry_date']}</td>
        <td>{k['current_used']} / {k['daily_limit']}</td>
        <td>{'Active' if k['is_active'] else 'Suspended'}</td>
        <td>
            <form action="/admin/action/reset" method="post" style="display:inline;"><input type="hidden" name="key" value="{k['key']}"><button type="submit">Reset</button></form>
            <form action="/admin/action/toggle" method="post" style="display:inline;"><input type="hidden" name="key" value="{k['key']}"><button type="submit">Toggle</button></form>
        </td>
    </tr>""" for k in API_KEYS_DB.values()])
    return f"""
    <!DOCTYPE html>
    <html>
    <head><title>Admin Dashboard</title><style>body{{background:#111;color:#fff;font-family:sans-serif;padding:20px;}}table{{width:100%;border-collapse:collapse;margin:20px 0;}}td,th{{padding:10px;border:1px solid #333;text-align:left;}}input,select{{padding:8px;margin:5px 0;width:100%;}}</style></head>
    <body>
        <h1>SHAYAN_EXPLORER Admin Core</h1>
        <div style="display:flex;gap:40px;">
            <div style="flex:1;">
                <h2>Generate New Key</h2>
                <form action="/admin/action/generate" method="post">
                    Key: <input type="text" name="key" required><br>
                    Name: <input type="text" name="name" required><br>
                    Expiry: <input type="date" name="expiry_date" required><br>
                    Limit: <input type="number" name="daily_limit" required><br>
                    Tools: <select name="allowed_tools"><option value="all">All Tools</option></select><br>
                    <button type="submit" style="margin-top:10px;padding:10px;width:100%;">Create Key</button>
                </form>
            </div>
            <div style="flex:2;">
                <h2>Keys Registry</h2>
                <table><thead><tr><th>Key</th><th>Expiry</th><th>Usage</th><th>Status</th><th>Actions</th></tr></thead><tbody>{key_rows}</tbody></table>
                <h2>Logs</h2>
                <table><thead><tr><th>Time</th><th>Key</th><th>Tool</th><th>Query</th><th>Status</th></tr></thead><tbody>{log_rows}</tbody></table>
            </div>
        </div>
    </body>
    </html>
    """

@app.post("/admin/action/generate")
def action_generate_key(key: str = Form(...), name: str = Form(...), expiry_date: str = Form(...), daily_limit: int = Form(...), allowed_tools: str = Form(...), username: str = Depends(verify_admin)):
    API_KEYS_DB[key] = {"key": key, "name": name, "expiry_date": expiry_date, "daily_limit": daily_limit, "current_used": 0, "is_active": True, "allowed_tools": [allowed_tools]}
    return HTMLResponse("<script>window.location.href='/admin';</script>")

@app.post("/admin/action/reset")
def action_reset_limit(key: str = Form(...), username: str = Depends(verify_admin)):
    if key in API_KEYS_DB: API_KEYS_DB[key]["current_used"] = 0
    return HTMLResponse("<script>window.location.href='/admin';</script>")

@app.post("/admin/action/toggle")
def action_toggle_key(key: str = Form(...), username: str = Depends(verify_admin)):
    if key in API_KEYS_DB: API_KEYS_DB[key]["is_active"] = not API_KEYS_DB[key]["is_active"]
    return HTMLResponse("<script>window.location.href='/admin';</script>")

@app.get("/api/gateway/{endpoint}")
def core_proxy_gateway(endpoint: str, request: Request):
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
            return Response(content=response.text, media_type="text/plain")
    except Exception as e:
        log_transaction(client_key, endpoint, search_query, f"FAULT: {str(e)}")
        return JSONResponse(status_code=502, content={"status": "fail", "developer": "SHAYAN_EXPLORER", "reason": "Timeout encountered."})
