import os
import time
import requests
from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

app = FastAPI(title="SHAYAN_EXPLORER Gateway")

# Global In-Memory Store
API_KEYS = {
    "vx-osint": {
        "name": "Default Admin Key",
        "expires_at": time.time() + 86400 * 30,
        "daily_limit": 1000,
        "used_today": 0,
        "allowed_tools": ["all"],
        "created_at": time.time()
    }
}
LOGS = []

ADMIN_USER = "vernex"
ADMIN_PASS = "vernex@16vx"

BASE_TARGET_URL = "https://ft-osint-api.duckdns.org/api"
TARGET_KEY = "vernex-6a9dc4fdd5923c40b0aba27bf1e39e3f"

# All endpoints and their example parameter strings for clean UI copy/paste
ENDPOINTS = {
    "adv": "num=9876543210",
    "paytm": "num=9876543210",
    "imei": "imei=357817383506298",
    "calltracer": "num=9876543210",
    "upi": "upi=example@ybl",
    "ifsc": "ifsc=SBIN0001234",
    "number": "num=9876543210",
    "pincode": "pin=110001",
    "ip": "ip=8.8.8.8",
    "challan": "vehicle=UP42BB2572",
    "ff": "uid=3143389983",
    "bgmi": "uid=5121439477",
    "snap": "username=priyapanchal272",
    "email": "email=airtel123@gmail.com",
    "vehicle": "vehicle=MH02FZ0555",
    "git": "username=ftgamer2",
    "insta": "username=cristiano",
    "tg": "info=username",
    "tgidinfo": "id=7530266953",
    "numleak": "num=9876543210"
}

def clean_response(data):
    if isinstance(data, dict):
        return {k: clean_response(v) for k, v in data.items() if k not in ['channel', 'credit']}
    elif isinstance(data, list):
        return [clean_response(item) for item in data]
    elif isinstance(data, str):
        for target in ["@ftgamer2", "@bornex Ultra", "bornex", "channel url"]:
            data = data.replace(target, "SHAYAN_EXPLORER")
        return data
    return data

def verify_api_key(key: str, endpoint: str):
    if key not in API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API Key provided.")
    
    key_info = API_KEYS[key]
    if time.time() > key_info["expires_at"]:
        raise HTTPException(status_code=403, detail="API Key has expired.")
        
    if key_info["used_today"] >= key_info["daily_limit"]:
        raise HTTPException(status_code=429, detail="Daily rate limit reached.")
        
    if "all" not in key_info["allowed_tools"] and endpoint not in key_info["allowed_tools"]:
        raise HTTPException(status_code=403, detail=f"No permission for route: '{endpoint}'.")
        
    API_KEYS[key]["used_today"] += 1
    return key_info

@app.get("/api/{endpoint}")
async def proxy_gateway(endpoint: str, request: Request):
    if endpoint not in ENDPOINTS:
        return JSONResponse(status_code=444, content={"error": "Endpoint not found"})
    
    params = dict(request.query_params)
    user_key = params.get("key")
    
    if not user_key:
        return JSONResponse(status_code=401, content={"error": "API key parameter required"})
    
    try:
        verify_api_key(user_key, endpoint)
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"error": e.detail})

    search_query = next((v for k, v in params.items() if k != 'key'), "None")
    LOGS.append({
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "key": user_key,
        "endpoint": endpoint,
        "query": search_query
    })

    params["key"] = TARGET_KEY
    target_url = f"{BASE_TARGET_URL}/{endpoint}"
    
    try:
        response = requests.get(target_url, params=params, timeout=10)
        response.raise_for_status()
        return {"status": "success", "developer": "SHAYAN_EXPLORER", "data": clean_response(response.json())}
    except Exception:
        try:
            return {"status": "success", "developer": "SHAYAN_EXPLORER", "data": response.text}
        except:
            return JSONResponse(status_code=502, content={"error": "Upstream error"})

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
async def generate_key(request: Request):
    auth = request.cookies.get("session_auth")
    if auth != "authenticated_securely":
        raise HTTPException(status_code=401)
        
    form_data = await request.form()
    custom_name = form_data.get("custom_name")
    custom_key = form_data.get("custom_key")
    duration_days = int(form_data.get("duration_days", 30))
    limit = int(form_data.get("limit", 500))
    
    selected_tools = form_data.getlist("tools")
    if not selected_tools or "all" in selected_tools:
        selected_tools = ["all"]
    
    API_KEYS[custom_key] = {
        "name": custom_name,
        "expires_at": time.time() + (86400 * duration_days),
        "daily_limit": limit,
        "used_today": 0,
        "allowed_tools": selected_tools,
        "created_at": time.time()
    }
    return RedirectResponse(url="/dashboard", status_code=303)

@app.get("/api/admin/data")
async def get_admin_data(request: Request):
    auth = request.cookies.get("session_auth")
    if auth != "authenticated_securely":
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})
    return {"keys": API_KEYS, "logs": LOGS, "endpoints": ENDPOINTS}

def get_html_template(page: str):
    if page == "login":
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>SHAYAN EXPLORER - Terminal</title>
            <script src="https://cdn.tailwindcss.com"></script>
            <style>
                body { background: #06070d; font-family: 'Inter', sans-serif; overflow: hidden; }
                .glow-card { background: rgba(255, 255, 255, 0.02); backdrop-filter: blur(20px); border: 1px solid rgba(0, 242, 254, 0.15); box-shadow: 0 0 50px rgba(0, 242, 254, 0.1); }
                .neon-text { text-shadow: 0 0 10px rgba(0, 242, 254, 0.6); color: #00f2fe; }
            </style>
        </head>
        <body class="flex items-center justify-center min-h-screen">
            <div class="glow-card p-10 rounded-2xl w-full max-w-md mx-4">
                <h2 class="text-2xl font-black mb-1 text-center tracking-widest neon-text">SHAYAN EXPLORER</h2>
                <p class="text-gray-500 text-xs text-center mb-8 font-mono tracking-wider">SECURE TERMINAL GATE</p>
                <form action="/login" method="POST" class="space-y-5">
                    <div>
                        <label class="block text-xs font-mono text-cyan-400 mb-2 uppercase">Operator Identity</label>
                        <input type="text" name="username" required class="w-full bg-black/60 border border-gray-800 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-cyan-400 font-mono">
                    </div>
                    <div>
                        <label class="block text-xs font-mono text-cyan-400 mb-2 uppercase">Security Access Token</label>
                        <input type="password" name="password" required class="w-full bg-black/60 border border-gray-800 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-cyan-400 font-mono">
                    </div>
                    <button type="submit" class="w-full bg-gradient-to-r from-cyan-400 to-blue-500 text-black font-black py-3.5 rounded-lg uppercase tracking-widest text-xs">Initialize Control</button>
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
                body { background: #08090f; color: #e2e8f0; font-family: 'Inter', sans-serif; }
                .glass-panel { background: rgba(15, 17, 28, 0.75); backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.04); box-shadow: 0 20px 50px rgba(0,0,0,0.3); }
                .glow-border:focus { border-color: #00f2fe; box-shadow: 0 0 12px rgba(0, 242, 254, 0.4); }
                .checkbox-card { background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.05); transition: all 0.2s ease; }
                .checkbox-card:hover { border-color: rgba(0, 242, 254, 0.3); background: rgba(0, 242, 254, 0.02); }
                ::-webkit-scrollbar { width: 6px; }
                ::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 10px; }
            </style>
        </head>
        <body class="p-4 md:p-8 min-h-screen">
            <header class="max-w-7xl mx-auto flex flex-col sm:flex-row justify-between items-center mb-8 pb-4 border-b border-gray-800 gap-4">
                <div>
                    <h1 class="text-2xl font-black tracking-widest text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500 uppercase">SHAYAN_EXPLORER GATEWAY</h1>
                    <p class="text-xs font-mono text-gray-500">Live API Authorization & Feature Configuration Platform</p>
                </div>
                <div class="flex items-center gap-4 bg-black/40 border border-cyan-500/20 px-4 py-2 rounded-xl">
                    <div class="text-right">
                        <p class="text-xs font-mono text-cyan-400 font-bold tracking-wider">API DEVELOPER</p>
                        <p class="text-sm font-black text-white tracking-widest font-mono">SHAYAN_EXPLORER</p>
                    </div>
                </div>
            </header>

            <main class="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div class="space-y-6 lg:col-span-1">
                    <section class="glass-panel p-6 rounded-2xl h-fit">
                        <h2 class="text-sm font-black text-white mb-6 uppercase tracking-wider text-cyan-400 flex items-center gap-2">🔑 Issue Access License</h2>
                        <form action="/keys/generate" method="POST" class="space-y-4">
                            <div>
                                <label class="block text-xs font-mono text-gray-400 mb-1">Holder Alias Name</label>
                                <input type="text" name="custom_name" placeholder="Premium Client" required class="w-full bg-black/50 border border-gray-800 rounded-lg p-2.5 text-sm glow-border transition-all text-white focus:outline-none">
                            </div>
                            <div>
                                <label class="block text-xs font-mono text-gray-400 mb-1">Custom Secret Key String</label>
                                <input type="text" name="custom_key" placeholder="client-secret-token" required class="w-full bg-black/50 border border-gray-800 rounded-lg p-2.5 text-sm glow-border transition-all text-white font-mono focus:outline-none">
                            </div>
                            <div class="grid grid-cols-2 gap-4">
                                <div>
                                    <label class="block text-xs font-mono text-gray-400 mb-1">Lifespan (Days)</label>
                                    <input type="number" name="duration_days" value="30" required class="w-full bg-black/50 border border-gray-800 rounded-lg p-2.5 text-sm glow-border text-white focus:outline-none">
                                </div>
                                <div>
                                    <label class="block text-xs font-mono text-gray-400 mb-1">Daily Limit Load</label>
                                    <input type="number" name="limit" value="500" required class="w-full bg-black/50 border border-gray-800 rounded-lg p-2.5 text-sm glow-border text-white focus:outline-none">
                                </div>
                            </div>

                            <div class="pt-2">
                                <div class="flex justify-between items-center mb-2">
                                    <label class="block text-xs font-mono text-cyan-400 uppercase tracking-wider font-bold">Scope Restrictions</label>
                                    <button type="button" onclick="toggleSelectAllAll()" id="master-toggle-btn" class="text-[10px] uppercase font-mono px-2 py-0.5 bg-cyan-500/10 text-cyan-400 rounded border border-cyan-500/20">Select All</button>
                                </div>
                                <div class="grid grid-cols-2 gap-2 max-h-40 overflow-y-auto p-2 bg-black/40 rounded-xl border border-gray-900" id="checkbox-grid">
                                    <label class="checkbox-card flex items-center gap-2 p-2 rounded-lg cursor-pointer text-xs font-mono text-white">
                                        <input type="checkbox" name="tools" value="all" id="chk-all" onchange="handleAllChange(this)" class="accent-cyan-400 rounded">
                                        <span class="text-cyan-400 font-bold">ALL TOOLS</span>
                                    </label>
                                </div>
                            </div>
                            <button type="submit" class="w-full py-3 bg-gradient-to-r from-cyan-400 to-blue-500 text-black font-black uppercase tracking-widest text-xs rounded-lg mt-2">Forge System License</button>
                        </form>
                    </section>
                </div>

                <div class="lg:col-span-2 space-y-6">
                    <section class="glass-panel p-6 rounded-2xl">
                        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 mb-4">
                            <h3 class="text-sm font-black text-white uppercase tracking-wider text-cyan-400">🔗 Live API Endpoints Hub</h3>
                            <input type="text" id="quick-key-input" oninput="updateUrlsWithKey()" placeholder="Type key here to attach automatically..." class="bg-black/60 border border-gray-800 rounded px-2.5 py-1 text-xs font-mono text-cyan-400 focus:outline-none focus:border-cyan-400 min-w-[240px]">
                        </div>
                        <div class="max-h-60 overflow-y-auto border border-gray-900 rounded-xl bg-black/30 divide-y divide-gray-900" id="endpoints-list-box">
                            </div>
                    </section>

                    <section class="glass-panel p-6 rounded-2xl">
                        <h3 class="text-sm font-black text-white mb-4 uppercase tracking-wider text-cyan-400">🛡️ Active Infrastructure Licenses</h3>
                        <div class="overflow-x-auto">
                            <table class="w-full text-left text-xs font-mono">
                                <thead class="bg-black/40 text-gray-400 uppercase border-b border-gray-800">
                                    <tr>
                                        <th class="p-3">Label</th>
                                        <th class="p-3">Secret Token</th>
                                        <th class="p-3">Quota Usage</th>
                                        <th class="p-3">Allowed Tools Scope</th>
                                    </tr>
                                </thead>
                                <tbody id="keys-table-body" class="divide-y divide-gray-900"></tbody>
                            </table>
                        </div>
                    </section>

                    <section class="glass-panel p-6 rounded-2xl">
                        <h3 class="text-sm font-black text-white mb-4 uppercase tracking-wider text-cyan-400">📊 Gateway Route Telemetry Logs</h3>
                        <div class="overflow-y-auto max-h-48 rounded-xl border border-gray-800 bg-black/20">
                            <table class="w-full text-left text-[11px] font-mono">
                                <thead class="bg-black/50 text-gray-400 border-b border-gray-800 sticky top-0">
                                    <tr>
                                        <th class="p-3">Timestamp</th>
                                        <th class="p-3">License Key</th>
                                        <th class="p-3">Route Path</th>
                                        <th class="p-3">Target Query</th>
                                    </tr>
                                </thead>
                                <tbody id="logs-table-body" class="divide-y divide-gray-900"></tbody>
                            </table>
                        </div>
                    </section>
                </div>
            </main>

            <script>
                let storedEndpoints = {};
                
                function handleAllChange(masterObj) {
                    const checkboxes = document.querySelectorAll('.tool-checkbox');
                    checkboxes.forEach(cb => {
                        cb.checked = masterObj.checked;
                        cb.disabled = masterObj.checked;
                    });
                    document.getElementById('master-toggle-btn').innerText = masterObj.checked ? "Deselect All" : "Select All";
                }

                function toggleSelectAllAll() {
                    const master = document.getElementById('chk-all');
                    master.checked = !master.checked;
                    handleAllChange(master);
                }

                function updateUrlsWithKey() {
                    const currentHost = window.location.origin;
                    const inputtedKey = document.getElementById('quick-key-input').value.trim() || "YOUR_KEY";
                    const container = document.getElementById('endpoints-list-box');
                    
                    container.innerHTML = '';
                    Object.entries(storedEndpoints).forEach(([endpoint, queryParam]) => {
                        const directUrl = `${currentHost}/api/${endpoint}?key=${inputtedKey}&${queryParam}`;
                        container.innerHTML += `
                            <div class="p-2.5 flex justify-between items-center gap-4 text-xs font-mono hover:bg-white/5 transition-colors">
                                <span class="text-purple-400 font-bold min-w-[70px]">/${endpoint}</span>
                                <input type="text" readonly value="${directUrl}" class="bg-transparent border-none text-gray-400 w-full focus:outline-none select-all text-[11px]">
                                <button onclick="navigator.clipboard.writeText('${directUrl}'); alert('Copied endpoint string!');" class="text-[10px] uppercase bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 px-2 py-1 rounded hover:bg-cyan-500/20 font-bold shrink-0">Copy</button>
                            </div>
                        `;
                    });
                }

                async function loadDashboardMetrics() {
                    try {
                        const response = await fetch('/api/admin/data');
                        const data = await response.json();
                        
                        // Dynamically update the checkboxes the very first time
                        if(Object.keys(storedEndpoints).length === 0) {
                            storedEndpoints = data.endpoints;
                            const grid = document.getElementById('checkbox-grid');
                            Object.keys(storedEndpoints).forEach(tool => {
                                grid.innerHTML += `
                                    <label class="checkbox-card flex items-center gap-2 p-2 rounded-lg cursor-pointer text-[11px] font-mono text-gray-300">
                                        <input type="checkbox" name="tools" value="${tool}" class="tool-checkbox accent-cyan-400 rounded">
                                        <span>/${tool}</span>
                                    </label>
                                `;
                            });
                            updateUrlsWithKey();
                        }
                        
                        const keysBody = document.getElementById('keys-table-body');
                        keysBody.innerHTML = '';
                        for (const [key, details] of Object.entries(data.keys)) {
                            let badgeStyle = "bg-gray-800 text-gray-300";
                            let displayedScope = details.allowed_tools.join(', ');
                            if(details.allowed_tools.includes("all")) {
                                badgeStyle = "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20";
                                displayedScope = "FULL ROOT ACCESS";
                            }
                            keysBody.innerHTML += `
                                <tr class="border-b border-gray-900 hover:bg-white/5 transition-colors">
                                    <td class="p-3 text-white font-sans font-bold">${details.name}</td>
                                    <td class="p-3 text-cyan-400 font-bold cursor-pointer" onclick="document.getElementById('quick-key-input').value='${key}'; updateUrlsWithKey();">${key}</td>
                                    <td class="p-3 text-gray-300">${details.used_today} / ${details.daily_limit}</td>
                                    <td class="p-3"><span class="text-[10px] px-2 py-1 rounded font-bold ${badgeStyle}">${displayedScope}</span></td>
                                </tr>
                            `;
                        }

                        const logsBody = document.getElementById('logs-table-body');
                        logsBody.innerHTML = '';
                        if (data.logs.length === 0) {
                            logsBody.innerHTML = `<tr><td colspan="4" class="p-4 text-center text-gray-600">No telemetry requests metrics captured.</td></tr>`;
                        } else {
                            data.logs.slice().reverse().forEach(log => {
                                logsBody.innerHTML += `
                                    <tr class="hover:bg-white/5">
                                        <td class="p-3 text-gray-500">${log.timestamp}</td>
                                        <td class="p-3 text-blue-400">${log.key}</td>
                                        <td class="p-3 text-purple-400">/api/${log.endpoint}</td>
                                        <td class="p-3 text-amber-500 font-bold">${log.query}</td>
                                    </tr>
                                `;
                            });
                        }
                    } catch (err) {
                        console.error("Metrics Sync Fault:", err);
                    }
                }
                
                setInterval(loadDashboardMetrics, 4000);
                window.onload = loadDashboardMetrics;
            </script>
        </body>
        </html>
        """
