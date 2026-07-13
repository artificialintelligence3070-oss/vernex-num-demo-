from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
import requests
import datetime
import hmac
import hashlib
import razorpay
import os

# ==========================================
# 1. TOP-LEVEL APP INITIALIZATION (CRITICAL FOR VERCEL)
# ==========================================
app = Flask(__name__)
app.secret_key = "SHAYAN_EXPLORER_ULTRA_SECURE_2026"

# ==========================================
# 2. MASTER CONFIGURATION
# ==========================================
DEVELOPER_NAME = "SHAYAN_EXPLORER"
TARGET_BASE_URL = "https://ft-osint-api.duckdns.org/api"

# Admin Credentials
ADMIN_USER = "vernex"
ADMIN_PASS = "vernex@16vx"

# Integrations
RAZORPAY_KEY_ID = "rzp_live_TCc5USt5FlmfrI"
RAZORPAY_SECRET = "sMwLGQAEQePA0qSOYvFFII1h"
TELEGRAM_BOT_TOKEN = "8378722740:AAH9GthadrXQlTSp8pmPvlUnogXxhHv371s"
TELEGRAM_CHAT_ID = "-1003950462418"  # Replace with your actual Group ID

# ==========================================
# 3. DATABASE STRUCTURES (Memory Cached)
# ==========================================
GLOBAL_CONFIG = {"gst_percentage": 18, "maintenance": False}

API_KEYS_DB = {
    "explorer16": {
        "key_name": "Developer Master Key",
        "owner_email": "shayan@admin.com",
        "expiry_date": "2030-12-31",
        "daily_limit": 999999,
        "current_requests": 0,
        "allowed_tools": ["all"]
    }
}

SYSTEM_LOGS = []

API_PRICES = {
    "number": {"title": "Number API Pack", "month": 100, "three_month": 250, "tools": ["number", "paytm", "calltracer", "adv"]},
    "leak": {"title": "HiTeckGroop.in Leak", "month": 400, "three_month": 1100, "tools": ["email", "adv", "numleak"]},
    "aadhaar": {"title": "Aadhaar + Family", "month": 200, "three_month": 550, "tools": ["aadhar", "adharfamily"]},
    "upi": {"title": "UPI Full + Num to UPI", "month": 150, "three_month": 400, "tools": ["upi", "numtoupi"]},
    "ifsc": {"title": "IFSC Lookup", "month": 50, "three_month": 120, "tools": ["ifsc"]},
    "pan": {"title": "PAN to GST", "month": 100, "three_month": 250, "tools": ["pan"]},
    "pincode": {"title": "Pincode", "month": 30, "three_month": 80, "tools": ["pincode"]},
    "ip": {"title": "IP Lookup", "month": 30, "three_month": 80, "tools": ["ip"]},
    "vehicle": {"title": "Vehicle to Owner", "month": 400, "three_month": 1000, "tools": ["vehicle", "veh2num", "challan"]},
    "gaming": {"title": "Free Fire + BGMI", "month": 80, "three_month": 200, "tools": ["ff", "bgmi"]},
    "snapchat": {"title": "Snapchat", "month": 80, "three_month": 200, "tools": ["snap"]},
    "bomber": {"title": "SMS Bomber", "month": 150, "three_month": 400, "tools": ["bomber"]},
    "pakistan": {"title": "Pakistan Number", "month": 100, "three_month": 250, "tools": ["pk"]},
    "bundle_starter": {"title": "Starter Pack", "month": 500, "three_month": 1300, "tools": ["number", "aadhar", "upi", "pan", "ifsc", "pincode", "ip", "ff", "bgmi"]},
    "bundle_ultimate": {"title": "Ultimate Pack (All APIs)", "month": 1600, "three_month": 4200, "tools": ["all"]}
}

FREE_TOOLS = ["insta", "git", "tg", "tgidinfo", "name"]

# ==========================================
# 4. UTILITY FUNCTIONS
# ==========================================
def get_rzp_client():
    try:
        return razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_SECRET))
    except Exception:
        return None

def dispatch_telegram_alert(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}, timeout=5)
    except Exception:
        pass

def check_auth(key, endpoint):
    if key not in API_KEYS_DB:
        return False, "Invalid API Key."
    
    config = API_KEYS_DB[key]
    
    try:
        exp_date = datetime.datetime.strptime(config['expiry_date'], "%Y-%m-%d")
        if datetime.datetime.now() > exp_date:
            return False, "API Key Expired."
    except Exception:
        pass
        
    if config['current_requests'] >= config['daily_limit']:
        return False, "Daily limit reached."
        
    if "all" not in config['allowed_tools']:
        matched = False
        for category in config['allowed_tools']:
            if category in API_PRICES and endpoint in API_PRICES[category]['tools']:
                matched = True
        if endpoint in FREE_TOOLS:
            matched = True
        if not matched:
            return False, "Endpoint not permitted by your plan."
            
    return True, config

# ==========================================
# 5. PREMIUM FRONTEND TEMPLATES
# ==========================================
STOREFRONT_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ dev_name }} | Premium API Gateway</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@500;700&display=swap');
        :root { --primary: #00ffcc; --dark: #090b14; --glass: rgba(15, 23, 42, 0.7); --border: rgba(0, 255, 204, 0.2); }
        body { margin: 0; font-family: 'Rajdhani', sans-serif; background: var(--dark); color: #fff; background-image: radial-gradient(circle at 50% 0%, #1a253c 0%, transparent 50%); }
        .glass-panel { background: var(--glass); backdrop-filter: blur(16px); border: 1px solid var(--border); border-radius: 20px; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5); }
        .nav { display: flex; justify-content: space-between; padding: 20px 50px; align-items: center; border-bottom: 1px solid var(--border); }
        .logo { font-family: 'Orbitron', sans-serif; font-size: 28px; color: var(--primary); text-transform: uppercase; letter-spacing: 3px; text-shadow: 0 0 15px var(--primary); }
        .btn { background: linear-gradient(45deg, var(--primary), #0088ff); color: #000; padding: 12px 30px; font-weight: bold; font-family: 'Orbitron'; border: none; border-radius: 8px; cursor: pointer; transition: 0.3s; text-decoration: none; text-transform: uppercase; }
        .btn:hover { transform: scale(1.05); box-shadow: 0 0 20px var(--primary); }
        .btn-google { background: #fff; color: #000; display: flex; align-items: center; justify-content: center; gap: 10px; width: 100%; margin-top: 15px; }
        .hero { text-align: center; padding: 100px 20px; }
        .hero h1 { font-family: 'Orbitron'; font-size: 60px; margin: 0; background: linear-gradient(to right, #fff, var(--primary)); -webkit-background-clip: text; color: transparent; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 30px; padding: 50px; max-width: 1400px; margin: auto; }
        .card { padding: 30px; display: flex; flex-direction: column; justify-content: space-between; transition: 0.4s; position: relative; overflow: hidden; }
        .card::before { content: ''; position: absolute; top: 0; left: -100%; width: 50%; height: 100%; background: linear-gradient(to right, transparent, rgba(255,255,255,0.1), transparent); transform: skewX(-20deg); transition: 0.5s; }
        .card:hover::before { left: 150%; }
        .card:hover { transform: translateY(-10px); border-color: var(--primary); box-shadow: 0 10px 40px rgba(0, 255, 204, 0.2); }
        .price { font-size: 40px; font-weight: bold; color: var(--primary); margin: 20px 0; font-family: 'Orbitron'; }
        input, select { width: 100%; padding: 15px; margin-bottom: 15px; background: rgba(0,0,0,0.5); border: 1px solid var(--border); color: #fff; border-radius: 8px; font-family: 'Rajdhani'; font-size: 16px; box-sizing: border-box; }
        input:focus { outline: none; border-color: var(--primary); box-shadow: 0 0 10px var(--primary); }
        .auth-box { max-width: 450px; margin: 100px auto; padding: 40px; text-align: center; }
    </style>
</head>
<body>
    <div class="nav glass-panel" style="border-radius: 0; border-top: none; border-left: none; border-right: none;">
        <div class="logo">{{ dev_name }}</div>
        <div>
            {% if session.get('user') %}
                <span style="margin-right: 20px; font-size: 18px;">Connected: <span style="color:var(--primary);">{{ session['user'] }}</span></span>
                {% if session.get('is_admin') %}
                    <a href="/admin" class="btn" style="margin-right: 15px; background: #ff0055; color: white;">Admin Panel</a>
                {% endif %}
                <a href="/logout" class="btn" style="background: transparent; border: 1px solid var(--primary); color: var(--primary);">Logout</a>
            {% else %}
                <a href="/login" class="btn">Login / Register</a>
            {% endif %}
        </div>
    </div>

    {% if view == "login" %}
    <div class="auth-box glass-panel">
        <h2 style="font-family: 'Orbitron'; color: var(--primary); font-size: 30px;">SECURE LOGIN</h2>
        <form method="POST" action="/login">
            <input type="text" name="username" placeholder="Email / Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit" class="btn" style="width: 100%;">Authenticate</button>
        </form>
        <div style="margin: 20px 0; color: #888;">--- OR ---</div>
        <button class="btn btn-google" onclick="alert('Google Auth Endpoint Initializing...')">
            <img src="https://upload.wikimedia.org/wikipedia/commons/5/53/Google_%22G%22_Logo.svg" width="20"> Login with Google
        </button>
    </div>

    {% elif view == "store" %}
    <div class="hero">
        <h1>ENTERPRISE OSINT API</h1>
        <p style="font-size: 24px; color: #a0aec0;">High-Performance Data Infrastructure by {{ dev_name }}</p>
    </div>

    <div class="grid">
        {% for id, pack in prices.items() %}
        <div class="card glass-panel">
            <div>
                <h2 style="margin: 0; font-family: 'Orbitron';">{{ pack.title }}</h2>
                <div style="color: #888; margin-top: 10px; font-size: 16px;">
                    Endpoints included:<br>
                    <span style="color: #fff;">{{ ", ".join(pack.tools) }}</span>
                </div>
            </div>
            <div>
                <div class="price">₹{{ pack.month }}<span style="font-size: 16px; color: #888;">/mo</span></div>
                <form method="POST" action="/purchase/init">
                    <input type="hidden" name="package_id" value="{{ id }}">
                    <input type="text" name="custom_key" placeholder="Create your Custom Key Name" required>
                    <select name="duration">
                        <option value="month">1 Month (₹{{ pack.month }})</option>
                        <option value="three_month">3 Months (₹{{ pack.three_month }} - Save!)</option>
                    </select>
                    {% if session.get('user') %}
                        <button type="submit" class="btn" style="width: 100%;">Buy via Razorpay</button>
                    {% else %}
                        <button type="button" class="btn" style="width: 100%; opacity: 0.5;" onclick="window.location.href='/login'">Login to Buy</button>
                    {% endif %}
                </form>
            </div>
        </div>
        {% endfor %}
    </div>
    {% endif %}
</body>
</html>
"""

ADMIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Master Control | {{ dev_name }}</title>
    <style>
        body { font-family: monospace; background: #000; color: #0f0; padding: 20px; }
        .panel { border: 1px solid #0f0; padding: 20px; margin-bottom: 20px; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { border: 1px solid #0f0; padding: 10px; text-align: left; }
        input, button { background: #000; color: #0f0; border: 1px solid #0f0; padding: 10px; margin: 5px 0; }
        button:hover { background: #0f0; color: #000; cursor: pointer; }
    </style>
</head>
<body>
    <h1>> {{ dev_name }} // SYSTEM OVERRIDE</h1>
    
    <div class="panel">
        <h2>> MANUALLY GENERATE KEY</h2>
        <form method="POST" action="/admin/generate">
            <input type="text" name="key" placeholder="Key String" required>
            <input type="text" name="owner" placeholder="Owner Email" required>
            <input type="text" name="scope" placeholder="Scope (e.g., all, number, gaming)" required>
            <button type="submit">Deploy Node</button>
        </form>
    </div>

    <div class="panel">
        <h2>> ACTIVE KEYS MATRIX</h2>
        <table>
            <tr><th>Key</th><th>Owner</th><th>Scope</th><th>Expires</th><th>Usage</th></tr>
            {% for k, v in keys.items() %}
            <tr>
                <td>{{ k }}</td>
                <td>{{ v.owner_email }}</td>
                <td>{{ v.allowed_tools[0] }}</td>
                <td>{{ v.expiry_date }}</td>
                <td>{{ v.current_requests }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>
    
    <a href="/"><button><< Return to Frontend</button></a>
</body>
</html>
"""

# ==========================================
# 6. ROUTING LOGIC
# ==========================================

@app.route('/')
def home():
    return render_template_string(STOREFRONT_HTML, dev_name=DEVELOPER_NAME, view="store", prices=API_PRICES)

@app.route('/login', methods=['GET', 'POST'])
def auth():
    if request.method == 'POST':
        user = request.form.get('username')
        pwd = request.form.get('password')
        if user == ADMIN_USER and pwd == ADMIN_PASS:
            session['user'] = user
            session['is_admin'] = True
        else:
            session['user'] = user
        return redirect('/')
    return render_template_string(STOREFRONT_HTML, dev_name=DEVELOPER_NAME, view="login")

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# --- ADMIN ROUTES ---
@app.route('/admin')
def admin_panel():
    if not session.get('is_admin'): return "Access Denied", 403
    return render_template_string(ADMIN_HTML, dev_name=DEVELOPER_NAME, keys=API_KEYS_DB)

@app.route('/admin/generate', methods=['POST'])
def admin_generate():
    if not session.get('is_admin'): return "Access Denied", 403
    key = request.form.get('key')
    API_KEYS_DB[key] = {
        "key_name": "Admin Generated",
        "owner_email": request.form.get('owner'),
        "expiry_date": "2027-01-01",
        "daily_limit": 5000,
        "current_requests": 0,
        "allowed_tools": [request.form.get('scope')]
    }
    return redirect('/admin')

# --- RAZORPAY ROUTES ---
@app.route('/purchase/init', methods=['POST'])
def buy_init():
    if not session.get('user'): return redirect('/login')
    client = get_rzp_client()
    if not client: return "Razorpay Client Error", 500
    
    pack_id = request.form.get('package_id')
    custom_key = request.form.get('custom_key')
    duration = request.form.get('duration')
    
    cost = API_PRICES[pack_id]['month'] if duration == 'month' else API_PRICES[pack_id]['three_month']
    total_paise = int((cost + (cost * GLOBAL_CONFIG['gst_percentage'] / 100)) * 100)
    
    order = client.order.create({
        "amount": total_paise,
        "currency": "INR",
        "notes": {"key": custom_key, "pack": pack_id, "dur": duration, "user": session['user']}
    })
    
    return f"""
    <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
    <script>
        var options = {{
            "key": "{RAZORPAY_KEY_ID}",
            "amount": "{order['amount']}",
            "currency": "INR",
            "name": "{DEVELOPER_NAME}",
            "order_id": "{order['id']}",
            "handler": function (response){{
                window.location.href = "/purchase/verify?pid="+response.razorpay_payment_id+"&oid="+response.razorpay_order_id+"&sig="+response.razorpay_signature;
            }},
            "theme": {{"color": "#00ffcc"}}
        }};
        new Razorpay(options).open();
    </script>
    """

@app.route('/purchase/verify')
def buy_verify():
    pid = request.args.get('pid')
    oid = request.args.get('oid')
    sig = request.args.get('sig')
    
    expected_sig = hmac.new(bytes(RAZORPAY_SECRET, 'utf-8'), bytes(f"{oid}|{pid}", 'utf-8'), hashlib.sha256).hexdigest()
    if expected_sig != sig: return "Signature Failed", 400
    
    order_data = get_rzp_client().order.fetch(oid)
    notes = order_data.get('notes', {})
    
    key = notes.get('key')
    pack = notes.get('pack')
    dur = notes.get('dur')
    
    days = 30 if dur == 'month' else 90
    exp_date = (datetime.datetime.now() + datetime.timedelta(days=days)).strftime("%Y-%m-%d")
    
    API_KEYS_DB[key] = {
        "key_name": f"{pack} Subscription",
        "owner_email": notes.get('user'),
        "expiry_date": exp_date,
        "daily_limit": 2500,
        "current_requests": 0,
        "allowed_tools": [pack]
    }
    
    dispatch_telegram_alert(f"💰 *NEW SALE!*\nUser: {notes.get('user')}\nPack: {pack}\nKey generated: `{key}`")
    
    return f"<body style='background:#000;color:#0f0;text-align:center;padding:50px;font-family:monospace;'><h1>PAYMENT SUCCESSFUL</h1><h2>Your API Key: {key}</h2><a href='/' style='color:#fff;'>Return Home</a></body>"

# --- CORE API PROXY ---
@app.route('/api/<endpoint>')
def proxy(endpoint):
    client_key = request.args.get('key')
    if not client_key: return jsonify({"developer": DEVELOPER_NAME, "error": "Missing key"}), 400
    
    valid, msg = check_auth(client_key, endpoint)
    if not valid: return jsonify({"developer": DEVELOPER_NAME, "error": msg}), 403
    
    API_KEYS_DB[client_key]['current_requests'] += 1
    
    # Forward the request to your target upstream server
    args = request.args.to_dict()
    args['key'] = "ftgamer2" # Injecting your master upstream key
    
    try:
        url = f"{TARGET_BASE_URL}/{endpoint}"
        resp = requests.get(url, params=args, timeout=15)
        
        try:
            data = resp.json()
            # Clean branding
            data.pop('credits', None)
            data.pop('owner', None)
            data['developer'] = DEVELOPER_NAME
            return jsonify(data), resp.status_code
        except:
            return resp.text, resp.status_code
    except:
        return jsonify({"developer": DEVELOPER_NAME, "error": "Upstream Down"}), 502

if __name__ == '__main__':
    app.run(debug=True)
