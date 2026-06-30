import os
import time
import requests
from fastapi import FastAPI, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="SHAYAN_EXPLORER Gateway")

# Global In-Memory Store (Note: For persistent production, connect to a database like Supabase/Mongo)
API_KEYS = {
    "vx-osint": {
        "name": "Default Admin Key",
        "expires_at": time.time() + 86400 * 30, # 30 Days
        "daily_limit": 1000,
        "used_today": 0,
        "allowed_tools": ["all"],
        "created_at": time.time()
    }
}
LOGS = []

# Admin Credentials
ADMIN_USER = "vernex"
ADMIN_PASS = "vernex@16vx"

# Target Base URL
BASE_TARGET_URL = "https://ft-osint-api.duckdns.org/api"
TARGET_KEY = "vernex-6a9dc4fdd5923c40b0aba27bf1e39e3f"

# Mapping endpoints
ENDPOINTS = {
    "adv": "adv",
    "paytm": "paytm",
    "imei": "imei",
    "calltracer": "calltracer",
    "upi": "upi",
    "ifsc": "ifsc",
    "number": "number",
    "pincode": "pincode",
    "ip": "ip",
    "challan": "challan",
    "ff": "ff",
    "bgmi": "bgmi",
    "snap": "snap",
    "email": "email",
    "vehicle": "vehicle",
    "git": "git",
    "insta": "insta",
    "tg": "tg",
    "tgidinfo": "tgidinfo",
    "numleak": "numleak"
}

def clean_response(data):
    """Recursively removes specific watermarks or telegram promotional text from responses"""
    if isinstance(data, dict):
        return {k: clean_response(v) for k, v in data.items() if k not in ['channel', 'credit']}
    elif isinstance(data, list):
        return [clean_response(item) for item in data]
    elif isinstance(data, str):
        # Strip specific user handles requested
        for target in ["@ftgamer2", "@bornex Ultra", "bornex"]:
            data = data.replace(target, "SHAYAN_EXPLORER")
        return data
    return data

def verify_api_key(key: str, endpoint: str):
    if key not in API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API Key provided.")
    
    key_info = API_KEYS[key]
    
    # Expiry Check
    if time.time() > key_info["expires_at"]:
        raise HTTPException(status_code=403, detail="API Key has expired.")
        
    # Rate Limit Check
    if key_info["used_today"] >= key_info["daily_limit"]:
        raise HTTPException(status_code=429, detail="Daily rate limit reached for this key.")
        
    # Tool Permission Check
    if "all" not in key_info["allowed_tools"] and endpoint not in key_info["allowed_tools"]:
        raise HTTPException(status_code=403, detail=f"This key does not have access to the '{endpoint}' tool.")
        
    # Increment usage
    API_KEYS[key]["used_today"] += 1
    return key_info

@app.get("/api/{endpoint}")
async def proxy_gateway(endpoint: str, request: Request):
    if endpoint not in ENDPOINTS:
        return JSONResponse(status_code=444, content={"error": "Endpoint not found"})
    
    params = dict(request.query_params)
    user_key = params.get("key")
    
    if not user_key:
        return JSONResponse(status_code=401, content={"error": "API key parameter 'key' is required"})
    
    # Validate authorization rules
    try:
        verify_api_key(user_key, endpoint)
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"error": e.detail})

    # Log Request context safely
    search_query = next((v for k, v in params.items() if k != 'key'), "None")
    LOGS.append({
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "key": user_key,
        "endpoint": endpoint,
        "query": search_query
    })

    # Structure payload to remote provider
    params["key"] = TARGET_KEY
    target_url = f"{BASE_TARGET_URL}/{ENDPOINTS[endpoint]}"
    
    try:
        response = requests.get(target_url, params=params, timeout=10)
        response.raise_for_status()
        raw_data = response.json()
        cleaned_data = clean_response(raw_data)
        
        # Inject Custom Branding Header
        return {
            "status": "success",
            "developer": "SHAYAN_EXPLORER",
            "data": cleaned_data
        }
    except requests.exceptions.RequestException as e:
        return JSONResponse(status_code=502, content={"error": "External upstream server error", "details": str(e)})
    except Exception:
        return JSONResponse(status_code=200, content={"status": "success", "developer": "SHAYAN_EXPLORER", "data": response.text})

# --- ADMIN PANEL FRONTEND (Realistic High-End Cyber Glassmorphism Interface) ---

@app.get("/", response_class=HTMLResponse)
async def login_page():
    return get_html_template("login")

@app.post("/login")
async def handle_login(username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USER and password == ADMIN_PASS:
        response = RedirectResponse(url="/dashboard", status_code=303)
        response.set_cookie(key="session_auth", value="authenticated_securely", httponly=True)
        return response
    return HTMLResponse("<script>alert('Invalid Credentials'); window.location.href='/';</script>")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_view(request: Request):
    auth = request.cookies.get("session_auth")
    if auth != "authenticated_securely":
        return RedirectResponse(url="/", status_code=303)
    return get_html_template("dashboard")

@app.post("/keys/generate")
async def generate_key(
    request: Request,
    custom_name: str = Form(...),
    custom_key: str = Form(...),
    duration_days: int = Form(...),
    limit: int = Form(...),
    tools: str = Form(...)
):
    auth = request.cookies.get("session_auth")
    if auth != "authenticated_securely":
        raise HTTPException(status_code=401)
        
    tool_list = [t.strip() for t in tools.split(",")] if tools else ["all"]
    
    API_KEYS[custom_key] = {
        "name": custom_name,
        "expires_at": time.time() + (86400 * duration_days),
        "daily_limit": limit,
        "used_today": 0,
        "allowed_tools": tool_list,
        "created_at": time.time()
    }
    return RedirectResponse(url="/dashboard", status_code=303)

@app.get("/api/admin/data")
async def get_admin_data(request: Request):
    auth = request.cookies.get("session_auth")
    if auth != "authenticated_securely":
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})
    return {"keys": API_KEYS, "logs": LOGS, "endpoints": list(ENDPOINTS.keys())}

def get_html_template(page: str):
    if page == "login":
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>SHAYAN EXPLORER - Access Control</title>
            <script src="https://cdn.tailwindcss.com"></script>
            <style>
                body { background: #080710; font-family: 'Inter', sans-serif; overflow: hidden; }
                .glow-card { background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(16px); border: 1px solid rgba(255, 255, 255, 0.1); box-shadow: 0 0 40px rgba(0, 242, 254, 0.15); }
                .neon-text { text-shadow: 0 0 10px #00f2fe, 0 0 20px #00f2fe; }
                .neon-btn { background: linear-gradient(45deg, #00f2fe, #4facfe); transition: all 0.3s ease; box-shadow: 0 0 15px rgba(0, 242, 254, 0.4); }
                .neon-btn:hover { transform: translateY(-2px); box-shadow: 0 0 25px rgba(0, 242, 254, 0.7); }
                .orb { position: absolute; border-radius: 50%; filter: blur(80px); z-index: -1; }
            </style>
        </head>
        <body class="flex items-center justify-center min-h-screen">
            <div class="orb w-80 h-80 bg-cyan-500 top-10 left-10 opacity-30"></div>
            <div class="orb w-96 h-96 bg-blue-600 bottom-10 right-10 opacity-20"></div>
            
            <div class="glow-card p-10 rounded-2xl w-full max-w-md mx-4 transform transition-all duration-500 hover:scale-[1.01]">
                <h2 class="text-3xl font-extrabold text-white mb-2 tracking-wide text-center uppercase tracking-widest text-cyan-400 neon-text">Terminal Gate</h2>
                <p class="text-gray-400 text-sm text-center mb-8 font-mono">AUTHORIZED PERSONNEL ONLY</p>
                <form action="/login" method="POST" class="space-y-6">
                    <div>
                        <label class="block text-xs font-mono text-cyan-300 uppercase mb-2 tracking-wider">Operator Identity</label>
                        <input type="text" name="username" required class="w-full bg-black/40 border border-gray-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-cyan-400 font-mono transition-all">
                    </div>
                    <div>
                        <label class="block text-xs font-mono text-cyan-300 uppercase mb-2 tracking-wider">Security Key Token</label>
                        <input type="password" name="password" required class="w-full bg-black/40 border border-gray-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-cyan-400 font-mono transition-all">
                    </div>
                    <button type="submit" class="neon-btn w-full text-black font-bold py-3.5 rounded-lg uppercase tracking-widest text-sm">Initialize Interface</button>
                </form>
            </div>
        </body>
        </html>
        """
    else:
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>SHAYAN_EXPLORER Dashboard</title>
            <script src="https://cdn.tailwindcss.com"></script>
            <style>
                body { background: #0a0b10; color: #e2e8f0; font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }
                .glass-panel { background: rgba(18, 20, 32, 0.7); backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.05); }
                .glow-border:focus { border-color: #00f2fe; box-shadow: 0 0 10px rgba(0, 242, 254, 0.3); }
                ::-webkit-scrollbar { width: 6px; }
                ::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 10px; }
            </style>
        </head>
        <body class="p-4 md:p-8 min-h-screen">
            <header class="max-w-7xl mx-auto flex flex-col sm:flex-row justify-between items-center mb-8 pb-4 border-b border-gray-800 gap-4">
                <div>
                    <h1 class="text-2xl font-black tracking-wider text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500 uppercase">SHAYAN_EXPLORER API CONTROLLER</h1>
                    <p class="text-xs font-mono text-gray-500">Live Infrastructure Gateway Control Panel</p>
                </div>
                <div class="flex items-center gap-4">
                    <span class="px-3 py-1 bg-emerald-500/10 text-emerald-400 rounded-full font-mono text-xs border border-emerald-500/20 flex items-center gap-1.5">
                        <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span> SYSTEM ONLINE
                    </span>
                </div>
            </header>

            <main class="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-8">
                <section class="glass-panel p-6 rounded-2xl h-fit">
                    <h2 class="text-lg font-bold text-white mb-6 border-b border-gray-800 pb-2 flex items-center gap-2">🔑 Issue Access License</h2>
                    <form action="/keys/generate" method="POST" class="space-y-4">
                        <div>
                            <label class="block text-xs font-mono text-gray-400 mb-1">Holder Description Name</label>
                            <input type="text" name="custom_name" placeholder="eg. Premium Client" required class="w-full bg-black/40 border border-gray-700 rounded-lg p-2.5 text-sm glow-border transition-all text-white">
                        </div>
                        <div>
                            <label class="block text-xs font-mono text-gray-400 mb-1">Custom Secret Key String</label>
                            <input type="text" name="custom_key" placeholder="eg. my-custom-premium-key-101" required class="w-full bg-black/40 border border-gray-700 rounded-lg p-2.5 text-sm glow-border transition-all text-white font-mono">
                        </div>
                        <div class="grid grid-cols-2 gap-4">
                            <div>
                                <label class="block text-xs font-mono text-gray-400 mb-1">Lifespan (Days)</label>
                                <input type="number" name="duration_days" value="30" required class="w-full bg-black/40 border border-gray-700 rounded-lg p-2.5 text-sm glow-border transition-all text-white">
                            </div>
                            <div>
                                <label class="block text-xs font-mono text-gray-400 mb-1">Daily Limit Requests</label>
                                <input type="number" name="limit" value="500" required class="w-full bg-black/40 border border-gray-700 rounded-lg p-2.5 text-sm glow-border transition-all text-white">
                            </div>
                        </div>
                        <div>
                            <label class="block text-xs font-mono text-gray-400 mb-1">Allowed Tools Separate with commas (or keep 'all')</label>
                            <input type="text" name="tools" value="all" placeholder="number, upi, ip, all" class="w-full bg-black/40 border border-gray-700 rounded-lg p-2.5 text-sm glow-border transition-all text-white font-mono">
                        </div>
                        <button type="submit" class="w-full py-3 bg-gradient-to-r from-cyan-500 to-blue-600 text-black font-bold uppercase tracking-wider text-xs rounded-lg shadow-lg shadow-cyan-500/10 hover:shadow-cyan-500/20 transition-all mt-2">Forge Access Token</button>
                    </form>
                </section>

                <div class="lg:col-span-2 space-y-8">
                    <section class="glass-panel p-6 rounded-2xl">
                        <h3 class="text-lg font-bold text-white mb-4 flex items-center gap-2">🛡️ Active Infrastructure Licenses</h3>
                        <div class="overflow-x-auto">
                            <table class="w-full text-left text-sm font-mono">
                                <thead class="text-xs uppercase bg-black/30 text-gray-400 border-b border-gray-800">
                                    <tr>
                                        <th class="p-3">Label Alias</th>
                                        <th class="p-3">Secret Key</th>
                                        <th class="p-3">Quota Load</th>
                                        <th class="p-3">Scope Restriction</th>
                                    </tr>
                                </thead>
                                <tbody id="keys-table-body">
                                    </tbody>
                            </table>
                        </div>
                    </section>

                    <section class="glass-panel p-6 rounded-2xl">
                        <h3 class="text-lg font-bold text-white mb-4 flex items-center gap-2">📊 Gateway Operational Telemetry Logs</h3>
                        <div class="overflow-y-auto max-h-64 rounded-xl border border-gray-800 bg-black/20">
                            <table class="w-full text-left text-xs font-mono">
                                <thead class="bg-black/40 text-gray-400 border-b border-gray-800 sticky top-0">
                                    <tr>
                                        <th class="p-3">Timestamp</th>
                                        <th class="p-3">Active Token</th>
                                        <th class="p-3">Endpoint Target</th>
                                        <th class="p-3">Searched Parameter Signature</th>
                                    </tr>
                                </thead>
                                <tbody id="logs-table-body" class="divide-y divide-gray-900">
                                    </tbody>
                            </table>
                        </div>
                    </section>
                </div>
            </main>

            <script>
                async function loadDashboardMetrics() {
                    try {
                        const response = await fetch('/api/admin/data');
                        const data = await response.json();
                        
                        // Populate Token Database
                        const keysBody = document.getElementById('keys-table-body');
                        keysBody.innerHTML = '';
                        for (const [key, details] of Object.entries(data.keys)) {
                            const isExpired = Date.now() / 1000 > details.expires_at;
                            keysBody.innerHTML += `
                                <tr class="border-b border-gray-900 hover:bg-white/5 transition-colors">
                                    <td class="p-3 text-white font-sans">${details.name}</td>
                                    <td class="p-3 text-cyan-400 font-bold">${key}</td>
                                    <td class="p-3">${details.used_today} / ${details.daily_limit}</td>
                                    <td class="p-3"><span class="text-xs px-2 py-0.5 bg-gray-800 text-gray-300 rounded">${details.allowed_tools.join(', ')}</span></td>
                                </tr>
                            `;
                        }

                        // Populate Operations Logger
                        const logsBody = document.getElementById('logs-table-body');
                        logsBody.innerHTML = '';
                        if (data.logs.length === 0) {
                            logsBody.innerHTML = `<tr><td colspan="4" class="p-4 text-center text-gray-600">No telemetry requests processed yet.</td></tr>`;
                        } else {
                            data.logs.reverse().forEach(log => {
                                logsBody.innerHTML += `
                                    <tr class="hover:bg-white/5">
                                        <td class="p-3 text-gray-500">${log.timestamp}</td>
                                        <td class="p-3 text-blue-400 font-semibold">${log.key}</td>
                                        <td class="p-3 text-purple-400">/api/${log.endpoint}</td>
                                        <td class="p-3 text-amber-500 font-bold">${log.query}</td>
                                    </tr>
                                `;
                            });
                        }
                    } catch (err) {
                        console.error("Dashboard synchronization fault:", err);
                    }
                }
                
                setInterval(loadDashboardMetrics, 3000);
                window.onload = loadDashboardMetrics;
            </script>
        </body>
        </html>
        """
