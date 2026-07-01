import os
import time
import requests
import json
import hashlib
from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

app = FastAPI(title="SHAYAN_EXPLORER Ultimate Gateway Matrix")

# 🛰️ PERMANENT DATASTORE REPOSITORY CLUSTER
CLOUD_DB_URL = "https://kvbh.vercel.app/api/run/shayan_ultimate_v3_store"

# 🔑 RAZORPAY LIVE ACCESS LABELS
RAZORPAY_KEY_ID = "rzp_live_STCeqa012GtBoO"
RAZORPAY_KEY_SECRET = "YkdgGBF4jPugiyG0fhxCozxq"

# 🤖 TELEGRAM NOTIFICATION DISPATCH TARGETS
TELEGRAM_BOT_TOKEN = "8699920822:AAHuxlRhoUPvo2tkCu9_ENb4YZ_oLLWJo4w" 
TELEGRAM_CHANNELS = ["6624927068", "8505747325"]

# 🔒 CENTRAL MASTER ACCOUNT CREDENTIALS
ADMIN_USER = "vernex"
ADMIN_PASS = "vernex@ft"

# 🎯 SYSTEM ROUTE INFRASTRUCTURE DIRECTORY (ALL 28 CHANNELS)
ENDPOINTS = {
    "adv": "num=9876543210", "paytm": "num=9876543210", "calltracer": "num=9876543210", "number": "num=9876543210",
    "email": "email=airtel123@gmail.com", "numleak": "num=9876543210", "aadhar": "num=[Aadhaar]", 
    "adharfamily": "num=[Aadhaar]", "upi": "upi=ex@ybl", "numtoupi": "num=8945996482", 
    "ifsc": "ifsc=SBIN0001234", "pan": "pan=AXDPR2606K", "pincode": "pin=110001", "ip": "ip=8.8.8.8",
    "vehicle": "vehicle=KA01AB1234", "veh2num": "vehicle=KL41V3504", "challan": "vehicle=UP42BB2572",
    "ff": "uid=3143389983", "bgmi": "uid=5121439477", "snap": "username=priya",
    "bomber": "number=9876543210&counter=100", "pk": "num=9876543210", "insta": "username=cristiano", 
    "git": "username=ftgamer2", "tg": "info=username", "tgidinfo": "id=7530266953",
    "gstin": "gst=07AAAAA1111A1Z1", "domain": "domain=google.com"
}

BASE_TARGET_URL = "https://ft-osint-api.duckdns.org/api"
TARGET_KEY = "vx-osint"

# Fixed default baseline configuration matching your tiered specifications
DEFAULT_STRUCTURE = {
    "users": {},
    "api_keys": {
        "vx-osint-root": {
            "name": "Root Administrative Core", "expires_at": 4102444800,
            "daily_limit": 99999, "used_today": 0, "allowed_tools": ["all"], "status": "active"
        }
    },
    "prices": {
        "number": {"name": "📞 Number API Suite", "m1": 100, "m3": 250, "tools": ["adv", "paytm", "calltracer", "number"]},
        "leak": {"name": "💎 Leak Suite", "m1": 400, "m3": 1100, "tools": ["email", "numleak", "adv"]},
        "aadhaar": {"name": "🪪 Aadhaar + Family Suite", "m1": 200, "m3": 550, "tools": ["aadhar", "adharfamily"]},
        "upi": {"name": "💳 UPI Matrix Suite", "m1": 150, "m3": 400, "tools": ["upi", "numtoupi"]},
        "ifsc": {"name": "🏦 IFSC Lookup Module", "m1": 50, "m3": 120, "tools": ["ifsc"]},
        "pan": {"name": "🪪 PAN to GST Identifier", "m1": 100, "m3": 250, "tools": ["pan"]},
        "pincode": {"name": "📍 Pincode Directory Finder", "m1": 1, "m3": 3, "tools": ["pincode"]}, 
        "ip": {"name": "🌐 IP Lookup Node", "m1": 30, "m3": 80, "tools": ["ip"]},
        "vehicle": {"name": "🚘 Vehicle Owner Suite", "m1": 400, "m3": 1000, "tools": ["vehicle", "veh2num", "challan"]},
        "gaming": {"name": "🎮 FF + BGMI Data Scraper", "m1": 80, "m3": 200, "tools": ["ff", "bgmi"]},
        "snapchat": {"name": "👻 Snapchat Intelligence Node", "m1": 80, "m3": 200, "tools": ["snap"]},
        "bomber": {"name": "💣 SMS Bomber Layer", "m1": 150, "m3": 400, "tools": ["bomber"]},
        "pakistan": {"name": "🇵🇰 Pakistan Data Search", "m1": 100, "m3": 250, "tools": ["pk"]},
        "bundle_starter": {"name": "🔥 Starter Pack Bundle (5 APIs)", "m1": 500, "m3": 1300, "tools": ["adv", "paytm", "calltracer", "number", "git"]},
        "bundle_pro": {"name": "🔥 Pro Pack Bundle (11 APIs)", "m1": 1200, "m3": 3000, "tools": ["adv", "paytm", "calltracer", "number", "git", "email", "numleak", "upi", "numtoupi", "pan", "ifsc"]},
        "bundle_ultimate": {"name": "🔥 Ultimate Pack Bundle (All 28)", "m1": 1600, "m3": 4200, "tools": ["all"]}
    },
    "free_claims": {}
}

def fetch_master_db():
    try:
        res = requests.get(CLOUD_DB_URL, timeout=4)
        if res.status_code == 200:
            db = res.json()
            if isinstance(db, dict) and "api_keys" in db:
                if "prices" not in db: db["prices"] = DEFAULT_STRUCTURE["prices"]
                db["prices"]["pincode"]["m1"] = 1
                db["prices"]["pincode"]["m3"] = 3
                return db
        return DEFAULT_STRUCTURE
    except:
        return DEFAULT_STRUCTURE

def commit_master_db(payload):
    try: requests.post(CLOUD_DB_URL, json=payload, timeout=4)
    except: pass

def send_telegram_alert(msg: str):
    for ch in TELEGRAM_CHANNELS:
        try: requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", json={"chat_id": ch, "text": msg, "parse_mode": "Markdown"}, timeout=3)
        except: pass

@app.get("/api/{endpoint}")
async def proxy_gateway(endpoint: str, request: Request):
    if endpoint not in ENDPOINTS: return JSONResponse(status_code=444, content={"error": "Invalid route"})
    params = dict(request.query_params)
    user_key = params.get("key")
    if not user_key: return JSONResponse(status_code=401, content={"error": "Key parameters required"})
    
    db = fetch_master_db()
    if user_key not in db["api_keys"]: return JSONResponse(status_code=401, content={"error": "Access mapping failed"})
    k_info = db["api_keys"][user_key]
    
    if k_info.get("status") == "suspended": return JSONResponse(status_code=403, content={"error": "KEY SUSPENDED"})
    if time.time() > k_info["expires_at"]: return JSONResponse(status_code=403, content={"error": "Key expired"})
    if k_info["used_today"] >= k_info["daily_limit"]: return JSONResponse(status_code=429, content={"error": "Quota full"})
    
    allowed = k_info["allowed_tools"]
    if "all" not in allowed:
        if endpoint not in allowed:
            return JSONResponse(status_code=403, content={"error": "No tool permission allocated for this package tier"})
            
    db["api_keys"][user_key]["used_today"] += 1
    commit_master_db(db)
    
    params["key"] = TARGET_KEY
    try:
        r = requests.get(f"{BASE_TARGET_URL}/{endpoint}", params=params, timeout=10)
        return {"status": "success", "developer": "SHAYAN_EXPLORER", "data": r.json() if r.status_code==200 else r.text}
    except: return JSONResponse(status_code=502, content={"error": "Gateway communication breakdown"})

@app.get("/", response_class=HTMLResponse)
async def home_portal(request: Request):
    auth = request.cookies.get("session_auth")
    user_header = ""
    free_api_banner = ""
    db = fetch_master_db()
    
    if auth:
        uname = auth.replace("user_", "") if auth != "authenticated_securely" else "Admin Root"
        user_header = f"""
        <div class="flex items-center gap-3 bg-cyan-500/10 border border-cyan-500/20 p-3 rounded-xl mb-4">
            <div class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></div>
            <p class="text-xs font-mono text-cyan-400">User: <span class="text-white font-bold">{uname}</span></p>
            <a href="/dashboard" class="ml-auto text-[11px] uppercase bg-cyan-500 text-black px-2.5 py-1 font-bold rounded">Console Hub</a>
        </div>
        """
    else:
        user_header = """
        <div class="grid grid-cols-2 gap-3 mb-6">
            <a href="/login_view" class="text-center bg-white/5 border border-gray-800 text-white font-mono text-xs py-3 rounded-xl font-bold">Login</a>
            <a href="/register_view" class="text-center bg-gradient-to-r from-cyan-500 to-blue-500 text-black font-mono text-xs py-3 rounded-xl font-bold">Register</a>
        </div>
        """
        
    prices_source = db.get("prices", DEFAULT_STRUCTURE["prices"])
    js_prices = json.dumps(prices_source)
    js_endpoints = json.dumps(list(ENDPOINTS.keys()))
    
    catalog_cards = ""
    for k, v in prices_source.items():
        catalog_cards += f"""
        <div class="border border-gray-800 bg-black/40 p-4 rounded-xl flex flex-col justify-between gap-3">
            <div>
                <h3 class="text-sm font-bold text-white font-mono tracking-wide">{v['name']}</h3>
                <div class="mt-3 space-y-1">
                    <label class="flex items-center gap-2 cursor-pointer text-xs font-mono text-gray-400">
                        <input type="radio" name="horizon_{k}" value="m1" checked onchange="calculateCart()" class="accent-cyan-400">
                        1 Month: <span class="text-emerald-400 font-bold">₹{v['m1']}</span>
                    </label>
                    <label class="flex items-center gap-2 cursor-pointer text-xs font-mono text-gray-400">
                        <input type="radio" name="horizon_{k}" value="m3" onchange="calculateCart()" class="accent-cyan-400">
                        3 Months: <span class="text-emerald-400 font-bold">₹{v['m3']}</span>
                    </label>
                </div>
            </div>
            <button onclick="toggleCartItem('{k}')" id="btn_{k}" class="w-full bg-white/5 border border-gray-800 text-gray-300 font-mono text-xs py-2 rounded font-bold uppercase transition-all">Add to Cart</button>
        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>SHAYAN_EXPLORER Hub</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
    </head>
    <body class="bg-[#06070c] text-gray-300 antialiased selection:bg-cyan-500 selection:text-black">
        
        <div class="max-w-md mx-auto px-4 pt-4 flex justify-between items-center">
            <button onclick="openMailbox()" class="relative bg-black/50 border border-gray-800 p-2.5 rounded-xl text-gray-400 hover:text-cyan-400 transition-colors">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M3 19v-8.93a2 2 0 01.89-1.664l8-5.333a2 2 0 012.22 0l8 5.333A2 2 0 0121 10.07V19a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
                    <path stroke-linecap="round" stroke-linejoin="round" d="M3 10l9 6 9-6" />
                </svg>
                <div id="mailbox-dot" class="absolute top-1 right-1 w-2.5 h-2.5 bg-cyan-400 rounded-full hidden animate-ping"></div>
            </button>

            <button onclick="openApiDirectory()" class="bg-gradient-to-r from-cyan-500/10 to-blue-500/10 border border-cyan-500/30 text-cyan-400 text-[11px] font-mono font-bold tracking-wide px-3 py-2 rounded-xl uppercase shadow-sm">
                📁 View All 28 APIs
            </button>
        </div>

        <div class="max-w-md mx-auto p-4 min-h-screen pb-40">
            <header class="text-center py-4 border-b border-gray-900 mb-6">
                <h1 class="text-xl font-black tracking-widest text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500 uppercase font-mono">SHAYAN_EXPLORER API</h1>
                <p class="text-[10px] font-mono text-gray-500 tracking-wider uppercase mt-1">Advanced Real-Time Data Scraper Core Engine</p>
            </header>

            {user_header}

            <h2 class="text-xs font-black text-cyan-400 uppercase tracking-widest mb-4 font-mono">🛒 DIGITAL API MARKET STORES</h2>
            <div class="space-y-3">{catalog_cards}</div>
        </div>

        <div id="sticky-cart-bar" class="fixed bottom-0 left-0 right-0 max-w-md mx-auto bg-[#0a0d14]/95 backdrop-blur border-t border-gray-800 p-4 rounded-t-2xl shadow-2xl hidden z-40">
            <h3 class="text-xs font-black text-cyan-400 uppercase tracking-wider mb-2 font-mono">🧾 Digital Order Summary Details</h3>
            <div class="space-y-1 border-b border-gray-800/60 pb-2 mb-2 text-xs font-mono text-gray-400">
                <div class="flex justify-between"><span>Base API Price Component:</span><span class="text-white" id="summary-base">₹0.00</span></div>
                <div class="flex justify-between" id="platform-row"><span>Platform Automation Fee:</span><span class="text-white" id="summary-platform">₹15.00</span></div>
                <div class="flex justify-between" id="gst-row"><span>Integrated GST Tax (18%):</span><span class="text-white" id="summary-gst">₹0.00</span></div>
            </div>
            <div class="flex justify-between items-center mb-3">
                <span class="text-xs font-black uppercase font-mono text-white">Total Billing Load:</span>
                <span class="text-lg font-black text-emerald-400 font-mono" id="summary-grand">₹0.00</span>
            </div>
            <button onclick="triggerCheckout()" class="w-full py-3.5 bg-gradient-to-r from-cyan-400 to-blue-500 text-black font-mono font-black uppercase text-xs rounded-xl tracking-widest shadow-lg shadow-cyan-500/20">Authorize Real-time Payment</button>
        </div>

        <div id="api-modal" class="fixed inset-0 bg-black/80 backdrop-blur-sm hidden z-50 p-4 overflow-y-auto">
            <div class="max-w-md mx-auto bg-[#0a0d14] border border-gray-800 rounded-2xl p-5 my-8 space-y-4">
                <div class="flex justify-between items-center border-b border-gray-800 pb-2">
                    <h3 class="text-xs font-black text-cyan-400 font-mono uppercase tracking-widest">📋 Complete 28 Core API Route Matrix</h3>
                    <button onclick="closeApiDirectory()" class="text-gray-500 hover:text-white font-mono font-bold text-sm">✕</button>
                </div>
                <div class="space-y-2 max-h-[60vh] overflow-y-auto pr-1 text-[11px] font-mono">
                    {"".join([f'<div class="bg-black/40 border border-gray-900 p-2.5 rounded-lg"><p class="text-emerald-400 font-bold">GET /api/{k}</p><p class="text-gray-500 text-[10px] mt-0.5">Payload Schema: {v}</p></div>' for k, v in ENDPOINTS.items()])}
                </div>
                <button onclick="closeApiDirectory()" class="w-full py-2.5 bg-white/5 border border-gray-800 text-white font-mono font-bold uppercase text-[11px] rounded-xl">Dismiss Matrix View</button>
            </div>
        </div>

        <div id="mailbox-modal" class="fixed inset-0 bg-black/80 backdrop-blur-sm hidden z-50 p-4 flex items-center justify-center">
            <div class="max-w-md w-full bg-[#0d111a] border border-cyan-500/30 rounded-2xl p-6 space-y-4 shadow-2xl shadow-cyan-500/5">
                <div class="flex justify-between items-center border-b border-gray-800 pb-3">
                    <div class="flex items-center gap-2">
                        <span class="text-cyan-400">📥</span>
                        <h3 class="text-xs font-black text-white font-mono uppercase tracking-wider">Secure Delivery Mailbox</h3>
                    </div>
                    <button onclick="closeMailbox()" class="text-gray-500 hover:text-white font-mono font-bold text-sm">✕</button>
                </div>
                <div id="mailbox-content" class="text-xs font-mono text-gray-400 leading-relaxed bg-black/40 p-4 rounded-xl border border-gray-900 min-h-[120px] flex items-center justify-center text-center">
                    No new letters or license transmissions found. New keys appear instantly upon successful real-time payment authentication.
                </div>
                <button onclick="closeMailbox()" class="w-full py-2.5 bg-gradient-to-r from-cyan-500/20 to-blue-500/20 border border-cyan-500/30 text-cyan-400 font-mono font-bold uppercase text-[11px] rounded-xl">Close Mailbox</button>
            </div>
        </div>

        <script>
            const corePrices = {js_prices};
            let activeCart = [];

            function openApiDirectory() {{ document.getElementById('api-modal').classList.remove('hidden'); }}
            function closeApiDirectory() {{ document.getElementById('api-modal').classList.add('hidden'); }}
            function openMailbox() {{ 
                document.getElementById('mailbox-modal').classList.remove('hidden'); 
                document.getElementById('mailbox-dot').classList.add('hidden');
            }}
            function closeMailbox() {{ document.getElementById('mailbox-modal').classList.add('hidden'); }}

            function toggleCartItem(apiId) {{
                const idx = activeCart.indexOf(apiId);
                const btn = document.getElementById('btn_' + apiId);
                if (idx === -1) {{
                    activeCart.push(apiId);
                    btn.className = "w-full bg-cyan-500 text-black font-mono text-xs py-2 rounded font-bold uppercase transition-all";
                    btn.innerText = "Selected ✓";
                }} else {{
                    activeCart.splice(idx, 1);
                    btn.className = "w-full bg-white/5 border border-gray-800 text-gray-300 font-mono text-xs py-2 rounded font-bold uppercase transition-all";
                    btn.innerText = "Add to Cart";
                }}
                calculateCart();
            }}

            function calculateCart() {{
                const cartBar = document.getElementById('sticky-cart-bar');
                if (activeCart.length === 0) {{
                    cartBar.classList.add('hidden');
                    return;
                }}
                cartBar.classList.remove('hidden');

                let totalBase = 0;
                activeCart.forEach(item => {{
                    const selectedHorizon = document.querySelector(`input[name="horizon_${{item}}"]:checked`).value;
                    totalBase += corePrices[item][selectedHorizon];
                }});

                // Check if user is ONLY purchasing the pincode tool
                if (activeCart.length === 1 && activeCart[0] === 'pincode') {{
                    document.getElementById('platform-row').classList.add('hidden');
                    document.getElementById('gst-row').classList.add('hidden');
                    document.getElementById('summary-base').innerText = '₹' + totalBase + '.00';
                    document.getElementById('summary-grand').innerText = '₹' + totalBase + '.00';
                    return;
                }}

                document.getElementById('platform-row').classList.remove('hidden');
                document.getElementById('gst-row').classList.remove('hidden');

                const platformFee = 15;
                const gstComponent = Math.round((totalBase + platformFee) * 0.18);
                const grandTotal = totalBase + platformFee + gstComponent;

                document.getElementById('summary-base').innerText = '₹' + totalBase + '.00';
                document.getElementById('summary-platform').innerText = '₹' + platformFee + '.00';
                document.getElementById('summary-gst').innerText = '₹' + gstComponent + '.00';
                document.getElementById('summary-grand').innerText = '₹' + grandTotal + '.00';
            }}

            async function triggerCheckout() {{
                let username = prompt("Enter your registered operator Username to map the license:");
                if (!username) return alert("Operation canceled.");

                let totalBase = 0;
                let descriptionPayload = [];
                
                activeCart.forEach(item => {{
                    const horizon = document.querySelector(`input[name="horizon_${{item}}"]:checked`).value;
                    totalBase += corePrices[item][horizon];
                    descriptionPayload.push(`${{item}} (${{horizon}})`);
                }});

                let platformFee = 15;
                let gstComponent = Math.round((totalBase + platformFee) * 0.18);
                let grandTotal = totalBase + platformFee + gstComponent;

                if (activeCart.length === 1 && activeCart[0] === 'pincode') {{
                    platformFee = 0;
                    gstComponent = 0;
                    grandTotal = totalBase;
                }}

                var options = {{
                    "key": "{RAZORPAY_KEY_ID}",
                    "amount": grandTotal * 100,
                    "currency": "INR",
                    "name": "SHAYAN_EXPLORER CLOUD",
                    "description": "Cart Transaction: " + descriptionPayload.join(', '),
                    "handler": async function (response) {{
                        const verifyResponse = await fetch('/api/payment/process_cart', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify({{
                                username: username,
                                cart: activeCart.map(item => ({{
                                    id: item,
                                    horizon: document.querySelector(`input[name="horizon_${{item}}"]:checked`).value
                                }})),
                                base_fee: totalBase,
                                gst: gstComponent,
                                grand: grandTotal,
                                payment_id: response.razorpay_payment_id
                            }})
                        }});
                        const resData = await verifyResponse.json();
                        if (resData.status === 'success') {{
                            // In-App Mailbox Letter Injection
                            document.getElementById('mailbox-dot').classList.remove('hidden');
                            document.getElementById('mailbox-content').innerHTML = `
                                <div class="space-y-3 text-left">
                                    <p class="text-cyan-400 font-bold uppercase text-[10px] border-b border-gray-800 pb-1">✉️ OFFICIAL DELIVERY TRANSACTION INVOICE</p>
                                    <p>Dear <span class="text-white font-bold">${{username}}</span>,</p>
                                    <p>We have successfully recognized your settled invoice load of <span class="text-emerald-400 font-bold">₹${{grandTotal}}.00</span> via transaction pointer reference: <span class="text-white select-all font-mono">${{response.razorpay_payment_id}}</span>.</p>
                                    <div class="bg-black/60 p-2.5 rounded border border-gray-800 space-y-1">
                                        <p class="text-gray-500 text-[10px]">PROVISIONED LICENSE ROUTE ACCESS KEY:</p>
                                        <p class="text-white font-black tracking-widest text-center text-sm select-all">${{resData.generated_key}}</p>
                                    </div>
                                    <p class="text-[10px] text-gray-500 italic">Thank you for deploying with SHAYAN_EXPLORER core networks.</p>
                                </div>
                            `;
                            alert("Payment processed! A confirmation letter containing your API token has dropped into your mailbox icon at the top left corner.");
                            
                            // Clear cart interface state
                            activeCart = [];
                            document.querySelectorAll('button[id^="btn_"]').forEach(b => {{
                                b.className = "w-full bg-white/5 border border-gray-800 text-gray-300 font-mono text-xs py-2 rounded font-bold uppercase transition-all";
                                b.innerText = "Add to Cart";
                            }});
                            calculateCart();
                        }} else {{
                            alert("Infrastructure delivery deployment error.");
                        }}
                    }},
                    "prefill": {{ "name": username }},
                    "theme": {{ "color": "#00f2fe" }}
                }};
                var rzp = new Razorpay(options);
                rzp.open();
            }}
        </script>
    </body>
    </html>
    """

@app.post("/api/payment/process_cart")
async def process_cart_webhook_callback(data: dict):
    db = fetch_master_db()
    username = data.get("username", "GuestUser").strip()
    cart_items = data.get("cart", [])
    base_fee = data.get("base_fee", 0)
    gst = data.get("gst", 0)
    grand = data.get("grand", 0)
    payment_id = data.get("payment_id", "LIVE_TX_REF")
    
    aggregated_tools = []
    purchased_labels = []
    max_days = 30
    
    prices_ref = db.get("prices", DEFAULT_STRUCTURE["prices"])
    for item in cart_items:
        i_id = item["id"]
        horizon = item["horizon"]
        if i_id in prices_ref:
            cfg = prices_ref[i_id]
            days = 30 if horizon == "m1" else 90
            if days > max_days: max_days = days
            purchased_labels.append(f"{cfg['name']} ({'1 Month' if horizon=='m1' else '3 Months'})")
            
            # Explicit package expansion validation rules
            if i_id == "bundle_starter":
                aggregated_tools.extend(prices_ref["bundle_starter"]["tools"])
            elif i_id == "bundle_pro":
                aggregated_tools.extend(prices_ref["bundle_pro"]["tools"])
            elif i_id == "bundle_ultimate":
                aggregated_tools.append("all")
            else:
                aggregated_tools.extend(cfg["tools"])
            
    allocated_key = f"SHAYAN-{hashlib.md5(str(time.time()).encode()).hexdigest()[:12].upper()}"
    db["api_keys"][allocated_key] = {
        "name": f"{username} - Active License",
        "expires_at": time.time() + (86400 * max_days),
        "daily_limit": 5000, "used_today": 0,
        "allowed_tools": list(set(aggregated_tools)), "status": "active"
    }
    commit_master_db(db)
    
    alert_msg = (
        f"💰 *NEW GATEWAY ACCOUNT PURCHASE EVENT*\n\n"
        f"👤 *Subscriber Username Target:* `{username}`\n"
        f"📦 *Purchased Catalog:* \n" + "\n".join([f"• _{lbl}_" for lbl in purchased_labels]) + f"\n\n"
        f"📊 *Billing Invoice Breakdown:* \n"
        f"└ Base Component Rate: ₹{base_fee}.00\n"
        f"└ Total Collected Premium: `₹{grand}.00` Paid\n\n"
        f"🔑 *Provisioned Token Key:* `{allocated_key}`\n"
        f"🧾 *Transaction ID Reference:* `{payment_id}`\n\n"
        f"⚙️ _SHAYAN_EXPLORER Cluster Network Status: Active and Healthy_"
    )
    send_telegram_alert(alert_msg)
    return {"status": "success", "generated_key": allocated_key}

@app.get("/login_view", response_class=HTMLResponse)
async def login_view():
    return """
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1.0"><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="bg-[#06070c] text-white flex items-center justify-center min-h-screen p-4">
        <form action="/login" method="POST" class="bg-black/40 border border-gray-800 p-6 rounded-2xl w-full max-w-sm space-y-4">
            <h2 class="text-sm font-black font-mono text-cyan-400 uppercase tracking-widest">Operator Authorization Gate</h2>
            <div><label class="block text-[11px] font-mono text-gray-400 mb-1">Username Reference</label>
            <input type="text" name="username" required class="w-full bg-black/60 border border-gray-800 p-2.5 text-sm rounded focus:outline-none focus:border-cyan-400"></div>
            <div><label class="block text-[11px] font-mono text-gray-400 mb-1">Passphrase Code Token</label>
            <input type="password" name="password" required class="w-full bg-black/60 border border-gray-800 p-2.5 text-sm rounded focus:outline-none focus:border-cyan-400"></div>
            <button type="submit" class="w-full py-3 bg-gradient-to-r from-cyan-400 to-blue-500 text-black font-mono font-bold uppercase text-xs rounded-xl tracking-wider">Initialize Terminal</button>
        </form>
    </body></html>
    """

@app.get("/register_view", response_class=HTMLResponse)
async def register_view():
    return """
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1.0"><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="bg-[#06070c] text-white flex items-center justify-center min-h-screen p-4">
        <form action="/register" method="POST" class="bg-black/40 border border-gray-800 p-6 rounded-2xl w-full max-w-sm space-y-4">
            <h2 class="text-sm font-black font-mono text-blue-400 uppercase tracking-widest">Register Developer Account</h2>
            <div><label class="block text-[11px] font-mono text-gray-400 mb-1">Target Account Name</label>
            <input type="text" name="username" required class="w-full bg-black/60 border border-gray-800 p-2.5 text-sm rounded focus:outline-none"></div>
            <div><label class="block text-[11px] font-mono text-gray-400 mb-1">System Password</label>
            <input type="password" name="password" required class="w-full bg-black/60 border border-gray-800 p-2.5 text-sm rounded focus:outline-none"></div>
            <button type="submit" class="w-full py-3 bg-gradient-to-r from-blue-500 to-cyan-400 text-black font-mono font-bold uppercase text-xs rounded-xl tracking-wider">Register Account</button>
        </form>
    </body></html>
    """

@app.post("/register")
async def process_registration(username: str = Form(...), password: str = Form(...)):
    db = fetch_master_db()
    username = username.strip()
    if username in db.get("users", {}) or username.lower() == ADMIN_USER:
        return HTMLResponse("<script>alert('Identifier occupied.'); window.history.back();</script>")
    
    if "users" not in db: db["users"] = {}
    db["users"][username] = hashlib.sha256(password.encode()).hexdigest()
    
    if "free_claims" not in db: db["free_claims"] = {}
    if username not in db["free_claims"]:
        trial_token = f"FREE-1HR-{hashlib.md5(username.encode()).hexdigest()[:8].upper()}"
        db["api_keys"][trial_token] = {
            "name": f"🎁 {username} (1 Hour Trial Session)",
            "expires_at": time.time() + 3600,
            "daily_limit": 100, "used_today": 0,
            "allowed_tools": ["insta", "git", "tg", "tgidinfo"], "status": "active"
        }
        db["free_claims"][username] = True
        
    commit_master_db(db)
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(key="session_auth", value=f"user_{username}", httponly=True)
    return response

@app.post("/login")
async def handle_login(username: str = Form(...), password: str = Form(...)):
    db = fetch_master_db()
    if username == ADMIN_USER and password == ADMIN_PASS:
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(key="session_auth", value="authenticated_securely", httponly=True)
        return response
        
    hashed = hashlib.sha256(password.encode()).hexdigest()
    if username in db.get("users", {}) and db["users"][username] == hashed:
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(key="session_auth", value=f"user_{username}", httponly=True)
        return response
    return HTMLResponse("<script>alert('Invalid credentials.'); window.location.href='/login_view';</script>")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_view(request: Request):
    auth = request.cookies.get("session_auth")
    if not auth: return RedirectResponse(url="/login_view", status_code=303)
    is_admin = auth == "authenticated_securely"
    db = fetch_master_db()
    
    admin_controls_ui = ""
    if is_admin:
        prices_ref = db.get("prices", DEFAULT_STRUCTURE["prices"])
        admin_controls_ui = """
        <section class="p-4 rounded-xl bg-black/40 border border-red-500/10 mb-4 space-y-3">
            <h2 class="text-xs font-black text-red-400 uppercase tracking-wider font-mono">🔑 Root Admin: Forge Key 🔑</h2>
            <form action="/keys/generate" method="POST" class="space-y-3">
                <input type="text" name="custom_name" placeholder="Holder Target Label" required class="w-full bg-black/60 border border-gray-800 p-2 rounded text-xs text-white">
                <input type="text" name="custom_key" placeholder="License Token String" required class="w-full bg-black/60 border border-gray-800 p-2 rounded text-xs text-white font-mono">
                <input type="number" name="limit" value="9999" class="w-full bg-black/60 border border-gray-800 p-2 rounded text-xs text-white">
                <button type="submit" class="w-full py-2 bg-red-500 text-black font-bold text-xs rounded uppercase font-mono">Generate Ultimate License</button>
            </form>
        </section>
        """

    key_history_rows_html = ""
    for k, v in db.get("api_keys", {}).items():
        if is_admin or auth.replace("user_", "") in v.get('name', ''):
            readable_expiry = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(v.get('expires_at', time.time())))
            key_history_rows_html += f"""
            <div class="pt-3 first:pt-0 space-y-1">
                <p class="text-white font-bold">{v.get('name', 'License Key')}</p>
                <p class="text-cyan-400 select-all font-bold font-mono tracking-wide bg-black/60 p-1.5 rounded border border-gray-800/40">{k}</p>
                <p class="text-gray-400 text-[11px]">⏳ Expiry: <span class="text-amber-400 font-bold">{readable_expiry}</span></p>
                <p class="text-gray-500">Usage Load: <span class="text-gray-300">{v.get('used_today', 0)} / {v.get('daily_limit', 1000)}</span></p>
                <div class="flex justify-end gap-2 pt-1">
                    <button onclick="fireAction('restart', '{k}')" class="text-[10px] bg-blue-500/10 text-blue-400 border border-blue-500/20 px-2 py-0.5 rounded">Reset</button>
                    <button onclick="fireAction('delete', '{k}')" class="text-[10px] bg-red-500/10 text-red-400 border border-red-500/20 px-2 py-0.5 rounded">Purge</button>
                </div>
            </div>
            """

    return f"""
    <!DOCTYPE html>
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1.0"><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="bg-[#06070c] text-gray-300 p-4 font-mono text-xs">
        <div class="max-w-md mx-auto">
            <header class="flex justify-between items-center mb-6 pb-2 border-b border-gray-800">
                <h1 class="text-sm font-black text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">SYSTEM DASHBOARD</h1>
                <a href="/" class="text-[10px] bg-red-500/10 text-red-400 px-2 py-1 rounded border border-red-500/20">Back to Store</a>
            </header>

            {admin_controls_ui}

            <section class="bg-black/30 border border-gray-800 p-4 rounded-xl space-y-4">
                <h3 class="text-xs font-black text-cyan-400 uppercase tracking-wider">🛡️ Your Active License Key History Logs</h3>
                <div class="space-y-3 divide-y divide-gray-900">
                    {key_history_rows_html if key_history_rows_html else '<p class="text-gray-500">No active keys assigned to this account context.</p>'}
                </div>
            </section>
        </div>
        <script>
            async function fireAction(action, key) {{
                if(!confirm('Execute authorization command override?')) return;
                const res = await fetch('/api/admin/action', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{ action, key }})
                }});
                if(res.ok) window.location.reload();
            }}
        </script>
    </body></html>
    """

@app.post("/keys/generate")
async def admin_forge_key(custom_name: str = Form(...), custom_key: str = Form(...), limit: int = Form(...)):
    db = fetch_master_db()
    if "api_keys" not in db: db["api_keys"] = {}
    db["api_keys"][custom_key.strip()] = {
        "name": f"⭐ ADM: {custom_name}", "expires_at": 4102444800,
        "daily_limit": limit, "used_today": 0, "allowed_tools": ["all"], "status": "active"
    }
    commit_master_db(db)
    return RedirectResponse(url="/dashboard", status_code=303)

@app.post("/api/admin/action")
async def admin_action(request: Request, data: dict):
    auth = request.cookies.get("session_auth")
    if not auth: return JSONResponse(status_code=401, content={"error": "Unauthorized"})
    action, target_key = data.get("action"), data.get("key")
    db = fetch_master_db()
    if "api_keys" in db and target_key in db["api_keys"]:
        if auth != "authenticated_securely" and auth.replace("user_", "") not in db["api_keys"][target_key]["name"]:
            return JSONResponse(status_code=403)
        if action == "restart": db["api_keys"][target_key]["used_today"] = 0
        elif action == "delete": del db["api_keys"][target_key]
        commit_master_db(db)
        return {"status": "success"}
    return JSONResponse(status_code=444)
