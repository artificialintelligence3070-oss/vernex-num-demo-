import os
import time
import requests
import json
import hashlib
from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

app = FastAPI(title="SHAYAN_EXPLORER Gateway Premium Ultimate")

# 🛰️ PERMANENT GLOBAL STORE CLOUD CLUSTER
CLOUD_DB_URL = "https://kvbh.vercel.app/api/run/shayan_ultimate_v3_store"

# 🔑 RAZORPAY LIVE AUTHORIZATION KEYS
RAZORPAY_KEY_ID = "rzp_live_STCeqa012GtBoO"
RAZORPAY_KEY_SECRET = "YkdgGBF4jPugiyG0fhxCozxq"

# 🤖 TELEGRAM BOT DISPATCH TARGETS
TELEGRAM_BOT_TOKEN = "8699920822:AAHuxlRhoUPvo2tkCu9_ENb4YZ_oLLWJo4w" # Remember to put your real bot token here
TELEGRAM_CHANNELS = ["6624927068", "8505747325"]

# 🔒 MASTER ADMINISTRATOR ACCREDITATION
ADMIN_USER = "vernex"
ADMIN_PASS = "vernex@ft"

# 🎯 UPSTREAM CORE ENGINE INFRASTRUCTURE
BASE_TARGET_URL = "https://ft-osint-api.duckdns.org/api"
TARGET_KEY = "vx-osint"

# 📋 ALL API ENDPOINTS MAP BY GROUPS
ENDPOINTS = {
    # 📞 Number API Group
    "adv": "num=9876543210",
    "paytm": "num=9876543210",
    "calltracer": "num=9876543210",
    "number": "num=9876543210",
    
    # 💎 Leak Group
    "email": "email=airtel123@gmail.com",
    "numleak": "num=9876543210",
    
    # 🪪 Aadhaar Group
    "aadhar": "num=[Aadhaar Redacted]",
    "adharfamily": "num=[Aadhaar Redacted]",
    
    # 💳 UPI Group
    "upi": "upi=example@ybl",
    "numtoupi": "num=8945996482",
    
    # 🏦 IFSC Group
    "ifsc": "ifsc=SBIN0001234",
    
    # 🪪 PAN Group
    "pan": "pan=AXDPR2606K",
    
    # 📍 Pincode Group
    "pincode": "pin=110001",
    
    # 🌐 IP Group
    "ip": "ip=8.8.8.8",
    
    # 🚘 Vehicle Group
    "vehicle": "vehicle=KA01AB1234",
    "veh2num": "vehicle=KL41V3504",
    "challan": "vehicle=UP42BB2572",
    
    # 🎮 Gaming Group
    "ff": "uid=3143389983",
    "bgmi": "uid=5121439477",
    
    # 👻 Snapchat Group
    "snap": "username=priyapanchal272",
    
    # 💣 SMS Bomber Group
    "bomber": "number=9876543210&counter=100",
    
    # 🇵🇰 Pakistan Group
    "pk": "num=9876543210",
    
    # 🆓 FREE TOOLS GROUP (1 Hour Session Capped)
    "insta": "username=cristiano",
    "git": "username=ftgamer2",
    "tg": "info=username",
    "tgidinfo": "id=7530266953"
}

def fetch_master_db():
    """Retrieves all schema configurations securely from the global storage bin cluster."""
    default_structure = {
        "users": {},
        "api_keys": {
            "vx-osint-root": {
                "name": "Root Administrative Core",
                "expires_at": time.time() + 31536000,
                "daily_limit": 99999,
                "used_today": 0,
                "allowed_tools": ["all"],
                "status": "active"
            }
        },
        "prices": {
            "number": {"name": "📞 Number API (Paytm, Tracer, ICMR)", "m1": 100, "m3": 250, "tools": ["adv", "paytm", "calltracer", "number"]},
            "leak": {"name": "💎 HiTeckGroop.in Leak (Email, Adv)", "m1": 400, "m3": 1100, "tools": ["email", "numleak", "adv"]},
            "aadhaar": {"name": "🪪 Aadhaar + Family Data Suite", "m1": 200, "m3": 550, "tools": ["aadhar", "adharfamily"]},
            "upi": {"name": "💳 UPI Full + Num to UPI Matrix", "m1": 150, "m3": 400, "tools": ["upi", "numtoupi"]},
            "ifsc": {"name": "🏦 IFSC Financial Lookup", "m1": 50, "m3": 120, "tools": ["ifsc"]},
            "pan": {"name": "🪪 PAN to GST Corporate Identifier", "m1": 100, "m3": 250, "tools": ["pan"]},
            "pincode": {"name": "📍 Pincode Geo-Directory", "m1": 30, "m3": 80, "tools": ["pincode"]},
            "ip": {"name": "🌐 IP Lookup Information Node", "m1": 30, "m3": 80, "tools": ["ip"]},
            "vehicle": {"name": "🚘 Vehicle to Owner Registry", "m1": 400, "m3": 1000, "tools": ["vehicle", "veh2num", "challan"]},
            "gaming": {"name": "🎮 Free Fire + BGMI Profile Scraper", "m1": 80, "m3": 200, "tools": ["ff", "bgmi"]},
            "snapchat": {"name": "👻 Snapchat Username Intel Extraction", "m1": 80, "m3": 200, "tools": ["snap"]},
            "bomber": {"name": "💣 SMS Bomber High-Speed Layer", "m1": 150, "m3": 400, "tools": ["bomber"]},
            "pakistan": {"name": "🇵🇰 Pakistan Cross-Border Number Search", "m1": 100, "m3": 250, "tools": ["pk"]},
            "bundle_starter": {"name": "🔥 Starter Pack Bundle", "m1": 500, "m3": 1300, "tools": ["adv", "paytm", "calltracer", "number", "aadhar", "adharfamily", "upi", "numtoupi", "pan", "ifsc", "pincode", "ip", "ff", "bgmi"]},
            "bundle_pro": {"name": "🔥 Pro Pack Bundle (All without Vehicle)", "m1": 1200, "m3": 3000, "tools": ["all_except_vehicle"]},
            "bundle_ultimate": {"name": "🔥 Ultimate Pack Bundle (Access All)", "m1": 1600, "m3": 4200, "tools": ["all"]}
        },
        "free_claims": {}
    }
    try:
        res = requests.get(CLOUD_DB_URL, timeout=6)
        if res.status_code == 200 and isinstance(res.json(), dict) and "api_keys" in res.json():
            return res.json()
        requests.post(CLOUD_DB_URL, json=default_structure, timeout=5)
        return default_structure
    except:
        return default_structure

def commit_master_db(db_payload):
    try:
        requests.post(CLOUD_DB_URL, json=db_payload, timeout=6)
    except:
        pass

LOGS = []

def send_telegram_alert(message: str):
    for channel in TELEGRAM_CHANNELS:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            requests.post(url, json={"chat_id": channel, "text": message, "parse_mode": "Markdown"}, timeout=4)
        except:
            pass

def clean_response(data):
    if isinstance(data, str):
        try:
            unpacked = json.loads(data)
            if isinstance(unpacked, (dict, list)): data = unpacked
        except ValueError: pass

    if isinstance(data, dict):
        cleaned_dict = {}
        for k, v in data.items():
            if k in ['channel', 'credit', 'by']: continue
            cleaned_dict[k] = clean_response(v)
        return cleaned_dict
    elif isinstance(data, list):
        return [clean_response(item) for item in data]
    elif isinstance(data, str):
        for target in ["@ftgamer2", "@bornex Ultra", "bornex Ultra", "bornex", "channel url"]:
            data = data.replace(target, "SHAYAN_EXPLORER")
        return data
    return data

@app.get("/api/{endpoint}")
async def proxy_gateway(endpoint: str, request: Request):
    if endpoint not in ENDPOINTS:
        return JSONResponse(status_code=444, content={"error": "Endpoint not found"})
    
    params = dict(request.query_params)
    user_key = params.get("key")
    
    if not user_key:
        return JSONResponse(status_code=401, content={"error": "API key parameter required"})
    
    db = fetch_master_db()
    if user_key not in db["api_keys"]:
        return JSONResponse(status_code=401, content={"error": "Invalid API Key provided."})
        
    key_info = db["api_keys"][user_key]
    
    if key_info.get("status") == "suspended":
        return JSONResponse(status_code=403, content={"error": "KEY SUSPENDED ❌"})

    if time.time() > key_info["expires_at"]:
        return JSONResponse(status_code=403, content={"error": "API Key has expired."})
        
    if key_info["used_today"] >= key_info["daily_limit"]:
        return JSONResponse(status_code=429, content={"status": "error", "message": "DAILY QUOTA LIMIT REACHED ✅"})
        
    allowed = key_info["allowed_tools"]
    if "all" not in allowed:
        if "all_except_vehicle" in allowed:
            if endpoint in ["vehicle", "veh2num", "challan"]:
                return JSONResponse(status_code=403, content={"error": "Pro Pack restriction: Vehicle routes barred."})
        elif endpoint not in allowed:
            return JSONResponse(status_code=403, content={"error": "No permissions allocated for this tool subset."})
        
    db["api_keys"][user_key]["used_today"] += 1
    commit_master_db(db)

    search_query = next((v for k, v in params.items() if k != 'key'), "None")
    LOGS.append({"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "key": user_key, "endpoint": endpoint, "query": search_query})

    params["key"] = TARGET_KEY
    try:
        response = requests.get(f"{BASE_TARGET_URL}/{endpoint}", params=params, timeout=12)
        return {"status": "success", "developer": "SHAYAN_EXPLORER", "data": clean_response(response.json() if response.status_code==200 else response.text)}
    except Exception:
        return JSONResponse(status_code=502, content={"error": "Upstream proxy transaction fault."})

@app.get("/", response_class=HTMLResponse)
async def storefront_portal():
    db = fetch_master_db()
    prices = db["prices"]
    
    options_html = ""
    for k, v in prices.items():
        options_html += f"""
        <div class="border border-gray-800 bg-black/40 p-4 rounded-xl flex flex-col justify-between gap-4">
            <div>
                <h3 class="text-sm font-bold text-white font-mono tracking-wide">{v['name']}</h3>
                <p class="text-xs text-gray-500 mt-1 font-mono">⚡ 1 Month Plan: <span class="text-emerald-400 font-bold">₹{v['m1']}</span></p>
                <p class="text-xs text-gray-500 font-mono">⚡ 3 Month Plan: <span class="text-emerald-400 font-bold">₹{v['m3']}</span></p>
            </div>
            <div class="grid grid-cols-2 gap-2">
                <button onclick="initializeOrder('{k}', 'm1', {v['m1']})" class="bg-cyan-500/10 hover:bg-cyan-500 text-cyan-400 hover:text-black font-mono font-bold text-[11px] py-2 px-1 rounded transition-all uppercase">Buy 1 Mo</button>
                <button onclick="initializeOrder('{k}', 'm3', {v['m3']})" class="bg-blue-500/10 hover:bg-blue-500 text-blue-400 hover:text-black font-mono font-bold text-[11px] py-2 px-1 rounded transition-all uppercase">Buy 3 Mo</button>
            </div>
        </div>
        """
        
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SHAYAN_EXPLORER Storefront</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
    </head>
    <body class="bg-[#07080e] text-gray-300 min-h-screen p-4 sm:p-8">
        <div class="max-w-6xl mx-auto">
            <header class="flex justify-between items-center border-b border-gray-800 pb-6 mb-8">
                <div>
                    <h1 class="text-2xl font-black text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500 font-mono">SHAYAN_EXPLORER API</h1>
                    <p class="text-xs font-mono text-gray-500">Premium Real-time High-Speed Developer Gateways</p>
                </div>
                <div class="flex gap-3">
                    <a href="/login_view" class="border border-gray-800 bg-white/5 hover:bg-white/10 px-4 py-2 text-xs font-mono font-bold rounded-lg text-white">Console Login</a>
                    <a href="/register_view" class="bg-gradient-to-r from-cyan-500 to-blue-500 text-black px-4 py-2 text-xs font-bold font-mono rounded-lg">Create Account</a>
                </div>
            </header>

            <section class="mb-8 p-6 border border-amber-500/20 bg-amber-500/5 rounded-2xl flex flex-col sm:flex-row justify-between items-center gap-4">
                <div>
                    <h2 class="text-sm font-black text-amber-400 font-mono uppercase tracking-wider">🎁 Registration Promo Free Trial</h2>
                    <p class="text-xs text-gray-400 font-mono mt-1">Register an account and claim a 1-Hour full access trial session deployment token instantly (Instagram, GitHub, TG Toolsets).</p>
                </div>
                <a href="/register_view" class="bg-amber-400 text-black px-4 py-2 rounded-xl text-xs font-bold font-mono uppercase tracking-wide">Claim 1 HR Trial</a>
            </section>

            <h2 class="text-sm font-black text-cyan-400 uppercase tracking-widest mb-4 font-mono">💰 API COMMERCE STORES</h2>
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">{options_html}</div>
        </div>

        <script>
            async function initializeOrder(apiId, plan, price) {{
                const token = prompt("Please enter your registered account Username to bind the license automatically:");
                if(!token) return alert("Action canceled. Username identifier is required.");
                
                var options = {{
                    "key": "{RAZORPAY_KEY_ID}",
                    "amount": price * 100,
                    "currency": "INR",
                    "name": "SHAYAN_EXPLORER API",
                    "description": "Purchase License for: " + apiId + " Plan " + plan,
                    "handler": async function (response) {{
                        const verifyRes = await fetch('/api/payment/process', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify({{
                                username: token,
                                item_id: apiId,
                                duration_type: plan,
                                payment_id: response.razorpay_payment_id
                            }})
                        }});
                        const data = await verifyRes.json();
                        if(data.status === 'success') {{
                            alert("Payment Verified! Your Active API Token Generated: " + data.generated_key);
                            window.location.href = "/login_view";
                        }} else {{
                            alert("Error provisioning backend license infrastructure.");
                        }}
                    }},
                    "prefill": {{ "name": token }},
                    "theme": {{ "color": "#00f2fe" }}
                }};
                var rzp1 = new Razorpay(options);
                rzp1.open();
            }}
        </script>
    </body>
    </html>
    """

@app.post("/api/payment/process")
async def process_payment_callback(data: dict):
    db = fetch_master_db()
    username = data.get("username", "GuestUser").strip()
    item_id = data.get("item_id")
    duration_type = data.get("duration_type")
    payment_id = data.get("payment_id", "Manual_Or_Razor_Live")
    
    if item_id not in db["prices"]:
        return JSONResponse(status_code=400, content={"error": "Invalid configuration key."})
        
    config = db["prices"][item_id]
    days = 30 if duration_type == "m1" else 90
    allocated_key = f"SHAYAN-{hashlib.md5(str(time.time()).encode()).hexdigest()[:12].upper()}"
    
    db["api_keys"][allocated_key] = {
        "name": f"{username} - {config['name']}",
        "expires_at": time.time() + (86400 * days),
        "daily_limit": 2000,
        "used_today": 0,
        "allowed_tools": config["tools"],
        "status": "active"
    }
    commit_master_db(db)
    
    alert_msg = (
        f"💰 *A PERSON BUY AN API*\n\n"
        f"👤 *Subscriber User:* `{username}`\n"
        f"📦 *Purchased Product:* `{config['name']}`\n"
        f"⏳ *Access Horizon Duration:* {days} Days Plan\n"
        f"🔑 *Generated Active Token Key:* `{allocated_key}`\n"
        f"🧾 *Transaction Link ID Reference:* `{payment_id}`\n\n"
        f"⚙️ _SHAYAN_EXPLORER Core Deployment Cluster Execution Status: Balanced_"
    )
    send_telegram_alert(alert_msg)
    return {"status": "success", "generated_key": allocated_key}

@app.get("/login_view", response_class=HTMLResponse)
async def login_view():
    return """
    <html><head><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="bg-[#07080e] text-white flex items-center justify-center min-h-screen">
        <form action="/login" method="POST" class="bg-black/40 border border-gray-800 p-8 rounded-2xl w-full max-w-sm space-y-4">
            <h2 class="text-lg font-bold font-mono text-cyan-400 uppercase">Console Authentication</h2>
            <div><label class="block text-xs font-mono text-gray-400 mb-1">User Identifier</label>
            <input type="text" name="username" required class="w-full bg-black/60 border border-gray-800 p-2.5 rounded text-sm text-white focus:outline-none"></div>
            <div><label class="block text-xs font-mono text-gray-400 mb-1">Passphrase Secret</label>
            <input type="password" name="password" required class="w-full bg-black/60 border border-gray-800 p-2.5 rounded text-sm text-white focus:outline-none"></div>
            <button type="submit" class="w-full py-3 bg-gradient-to-r from-cyan-400 to-blue-500 text-black font-mono font-bold uppercase text-xs rounded-lg">Login</button>
        </form>
    </body></html>
    """

@app.get("/register_view", response_class=HTMLResponse)
async def register_view():
    return """
    <html><head><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="bg-[#07080e] text-white flex items-center justify-center min-h-screen">
        <form action="/register" method="POST" class="bg-black/40 border border-gray-800 p-8 rounded-2xl w-full max-w-sm space-y-4">
            <h2 class="text-lg font-bold font-mono text-blue-400 uppercase">Create Developer Account</h2>
            <div><label class="block text-xs font-mono text-gray-400 mb-1">Choose Username</label>
            <input type="text" name="username" required class="w-full bg-black/60 border border-gray-800 p-2.5 rounded text-sm text-white focus:outline-none"></div>
            <div><label class="block text-xs font-mono text-gray-400 mb-1">Choose Password</label>
            <input type="password" name="password" required class="w-full bg-black/60 border border-gray-800 p-2.5 rounded text-sm text-white focus:outline-none"></div>
            <button type="submit" class="w-full py-3 bg-gradient-to-r from-blue-500 to-cyan-400 text-black font-mono font-bold uppercase text-xs rounded-lg">Register & Claim 1-Hour Key</button>
        </form>
    </body></html>
    """

@app.post("/register")
async def process_registration(username: str = Form(...), password: str = Form(...)):
    db = fetch_master_db()
    username = username.strip()
    if username in db["users"] or username.lower() == ADMIN_USER:
        return HTMLResponse("<script>alert('Account Identity already active.'); window.history.back();</script>")
        
    db["users"][username] = hashlib.sha256(password.encode()).hexdigest()
    
    if username not in db["free_claims"]:
        trial_token = f"FREE-1HR-{hashlib.md5(username.encode()).hexdigest()[:8].upper()}"
        db["api_keys"][trial_token] = {
            "name": f"🎁 {username} (1 Hour Trial Session Key)",
            "expires_at": time.time() + 3600, # Hard cap strictly to 1 hour (3600 seconds) only!
            "daily_limit": 100,
            "used_today": 0,
            "allowed_tools": ["insta", "git", "tg", "tgidinfo"],
            "status": "active"
        }
        db["free_claims"][username] = True
        commit_master_db(db)
        return HTMLResponse(f"<script>alert('Account Created! Your 1-HOUR Token Key is: {trial_token}'); window.location.href='/';</script>")
        
    commit_master_db(db)
    return RedirectResponse(url="/", status_code=303)

@app.post("/login")
async def handle_login(username: str = Form(...), password: str = Form(...)):
    db = fetch_master_db()
    if username == ADMIN_USER and password == ADMIN_PASS:
        response = RedirectResponse(url="/dashboard", status_code=303)
        response.set_cookie(key="session_auth", value="authenticated_securely", httponly=True)
        return response
        
    hashed_input = hashlib.sha256(password.encode()).hexdigest()
    if username in db["users"] and db["users"][username] == hashed_input:
        response = RedirectResponse(url="/dashboard", status_code=303)
        response.set_cookie(key="session_auth", value=f"user_{username}", httponly=True)
        return response
        
    return HTMLResponse("<script>alert('Invalid Access Token Profiles.'); window.location.href='/login_view';</script>")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_view(request: Request):
    auth = request.cookies.get("session_auth")
    if not auth: return RedirectResponse(url="/login_view", status_code=303)
    
    is_admin = auth == "authenticated_securely"
    db = fetch_master_db()
    
    admin_controls_ui = ""
    if is_admin:
        admin_controls_ui = """
        <section class="p-6 rounded-2xl bg-black/40 border border-red-500/10 mb-6">
            <h2 class="text-sm font-black text-red-400 mb-4 uppercase tracking-wider">🔑 Admin - Create Custom Token (Ultimate Access 🔑)</h2>
            <form action="/keys/generate" method="POST" class="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
                <div><label class="block text-xs text-gray-400 mb-1">Holder Name</label>
                <input type="text" name="custom_name" required class="w-full bg-black/60 border border-gray-800 p-2 rounded text-xs text-white"></div>
                <div><label class="block text-xs text-gray-400 mb-1">License Key String</label>
                <input type="text" name="custom_key" required class="w-full bg-black/60 border border-gray-800 p-2 rounded text-xs text-white font-mono"></div>
                <div><label class="block text-xs text-gray-400 mb-1">Daily Limit Requests</label>
                <input type="number" name="limit" value="9999" class="w-full bg-black/60 border border-gray-800 p-2 rounded text-xs text-white"></div>
                <button type="submit" class="bg-red-500 text-black font-bold text-xs py-2 px-4 rounded uppercase h-[34px]">Forge Custom Token</button>
            </form>
        </section>

        <section class="p-6 rounded-2xl bg-black/40 border border-cyan-500/10 mb-6">
            <h2 class="text-sm font-black text-cyan-400 mb-4 uppercase tracking-wider">🛠️ Core API Price Control Panels</h2>
            <form action="/api/admin/modify_price" method="POST" class="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
                <div><label class="block text-xs text-gray-400 mb-1">Target API Route Section</label>
                <select name="api_id" class="w-full bg-black/60 border border-gray-800 p-2 rounded text-xs text-white focus:outline-none">
        """
        for k, v in db["prices"].items():
            admin_controls_ui += f'<option value="{k}">{v["name"]}</option>'
        admin_controls_ui += """
                </select></div>
                <div><label class="block text-xs text-gray-400 mb-1">New 1-Mo Price (₹)</label>
                <input type="number" name="m1" required class="w-full bg-black/60 border border-gray-800 p-2 rounded text-xs text-white"></div>
                <div><label class="block text-xs text-gray-400 mb-1">New 3-Mo Price (₹)</label>
                <input type="number" name="m3" required class="w-full bg-black/60 border border-gray-800 p-2 rounded text-xs text-white"></div>
                <button type="submit" class="bg-cyan-500 text-black font-bold text-xs py-2 px-4 rounded uppercase h-[34px]">Update Price Record</button>
            </form>
        </section>
        """

    return f"""
    <!DOCTYPE html>
    <html><head><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="bg-[#08090f] text-gray-300 p-4 md:p-8 font-mono">
        <div class="max-w-7xl mx-auto">
            <header class="flex justify-between items-center mb-8 pb-4 border-b border-gray-800">
                <div>
                    <h1 class="text-lg font-black text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">SHAYAN_EXPLORER MASTER CONSOLE</h1>
                    <p class="text-[11px] text-gray-500">Live Active Licenses Authorization System Matrix</p>
                </div>
                <a href="/" class="text-xs bg-red-500/10 border border-red-500/20 text-red-400 px-3 py-1.5 rounded">Exit Terminal</a>
            </header>

            {admin_controls_ui}

            <section class="bg-black/30 border border-gray-800 p-6 rounded-2xl">
                <h3 class="text-sm font-black text-cyan-400 mb-4 uppercase tracking-wider">🛡️ Your Registered Active License History</h3>
                <div class="overflow-x-auto">
                    <table class="w-full text-left text-xs">
                        <thead class="bg-black/50 text-gray-400 border-b border-gray-800">
                            <tr>
                                <th class="p-3">Reference Alias Label</th>
                                <th class="p-3">Secret Client Token Key</th>
                                <th class="p-3">Daily Usage Load</th>
                                <th class="p-3">Scope Boundary</th>
                                <th class="p-3 text-right">System Management Actions</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-900">
    """ + "".join([f"""
                            <tr class="hover:bg-white/5 font-mono">
                                <td class="p-3 text-white font-bold">{v['name']}</td>
                                <td class="p-3 text-cyan-400 select-all font-bold">{k}</td>
                                <td class="p-3 text-gray-400">{v['used_today']} / {v['daily_limit']}</td>
                                <td class="p-3"><span class="text-[10px] px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400">{" ,".join(v['allowed_tools'])}</span></td>
                                <td class="p-3 text-right space-x-2">
                                    <button onclick="fireAction('restart', '{k}')" class="text-[10px] bg-blue-500/20 text-blue-400 px-2 py-0.5 rounded">Reset Quota</button>
                                    <button onclick="fireAction('delete', '{k}')" class="text-[10px] bg-red-500/20 text-red-400 px-2 py-0.5 rounded">Purge Key</button>
                                </td>
                            </tr>
    """ for k, v in db["api_keys"].items() if is_admin or auth.replace("user_", "") in v['name']]) + """
                        </tbody>
                    </table>
                </div>
            </section>
        </div>
        <script>
            async function fireAction(action, key) {
                if(!confirm('Execute authorization trigger override code?')) return;
                const res = await fetch('/api/admin/action', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ action, key })
                });
                if(res.ok) window.location.reload();
            }
        </script>
    </body></html>
    """

@app.post("/keys/generate")
async def admin_forge_key(request: Request, custom_name: str = Form(...), custom_key: str = Form(...), limit: int = Form(...)):
    auth = request.cookies.get("session_auth")
    if auth != "authenticated_securely": raise HTTPException(status_code=401)
    
    db = fetch_master_db()
    db["api_keys"][custom_key.strip()] = {
        "name": f"⭐ ADM: {custom_name}",
        "expires_at": time.time() + 31536000,
        "daily_limit": limit,
        "used_today": 0,
        "allowed_tools": ["all"],
        "status": "active"
    }
    commit_master_db(db)
    return RedirectResponse(url="/dashboard", status_code=303)

@app.post("/api/admin/modify_price")
async def modify_price_endpoint(request: Request, api_id: str = Form(...), m1: int = Form(...), m3: int = Form(...)):
    auth = request.cookies.get("session_auth")
    if auth != "authenticated_securely": raise HTTPException(status_code=401)
    
    db = fetch_master_db()
    if api_id in db["prices"]:
        db["prices"][api_id]["m1"] = m1
        db["prices"][api_id]["m3"] = m3
        commit_master_db(db)
    return RedirectResponse(url="/dashboard", status_code=303)

@app.post("/api/admin/action")
async def admin_action(request: Request, data: dict):
    auth = request.cookies.get("session_auth")
    if not auth: return JSONResponse(status_code=401, content={"error": "Unauthorized"})
    
    action = data.get("action")
    target_key = data.get("key")
    
    db = fetch_master_db()
    if target_key in db["api_keys"]:
        if auth != "authenticated_securely" and auth.replace("user_", "") not in db["api_keys"][target_key]["name"]:
            return JSONResponse(status_code=403, content={"error": "Bypassing restrictions rejected."})
            
        if action == "restart": db["api_keys"][target_key]["used_today"] = 0
        elif action == "delete": del db["api_keys"][target_key]
        
        commit_master_db(db)
        return {"status": "success"}
    return JSONResponse(status_code=444, content={"error": "License not found"})

@app.get("/api/admin/data")
async def get_admin_data(request: Request):
    auth = request.cookies.get("session_auth")
    if auth != "authenticated_securely": return JSONResponse(status_code=401, content={"error": "Unauthorized"})
    db = fetch_master_db()
    return {"keys": db["api_keys"], "logs": LOGS, "endpoints": ENDPOINTS}
