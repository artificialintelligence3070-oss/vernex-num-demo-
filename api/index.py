import os
import hmac
import hashlib
import datetime
import requests
import razorpay
from flask import Flask, request, jsonify, render_template_string, redirect, session

# ==========================================
# VERCEL MANDATORY GLOBAL EXPOSURE
# ==========================================
app = Flask(__name__)
app.secret_key = "SHAYAN_EXPLORER_PREMIUM_CORE_2026"

# ==========================================
# SYSTEM CORE CONFIGURATION & CREDENTIALS
# ==========================================
DEVELOPER_NAME = "SHAYAN_EXPLORER"
TARGET_BASE_URL = "https://ft-osint-api.duckdns.org/api"

ADMIN_USER = "vernex"
ADMIN_PASS = "vernex@16vx"

RAZORPAY_KEY_ID = "rzp_live_TCc5USt5FlmfrI"
RAZORPAY_SECRET = "sMwLGQAEQePA0qSOYvFFII1h"
TELEGRAM_BOT_TOKEN = "8378722740:AAH9GthadrXQlTSp8pmPvlUnogXxhHv371s"
TELEGRAM_CHAT_ID = "-1003950462418"

GLOBAL_CONFIG = {"gst_percentage": 18}

# ==========================================
# IN-MEMORY DATA STORAGE
# ==========================================
API_KEYS_DB = {
    "explorer16": {
        "key_name": "Ultimate Master Override Key",
        "owner_email": "admin@shayan.io",
        "expiry_date": "2030-12-31",
        "daily_limit": 999999,
        "current_requests": 0,
        "allowed_tools": ["all"]
    }
}

API_PRICES = {
    "number": {"title": "Number Lookup Pack", "month": 100, "three_month": 250, "tools": ["number", "paytm", "calltracer", "adv"]},
    "leak": {"title": "HiTeckGroop Leak Pack", "month": 400, "three_month": 1100, "tools": ["email", "adv", "numleak"]},
    "aadhaar": {"title": "Aadhaar Core Suite", "month": 200, "three_month": 550, "tools": ["aadhar", "adharfamily"]},
    "upi": {"title": "UPI Financial Identity", "month": 150, "three_month": 400, "tools": ["upi", "numtoupi"]},
    "ifsc": {"title": "IFSC Routing Index", "month": 50, "three_month": 120, "tools": ["ifsc"]},
    "pan": {"title": "PAN to GST Matrix", "month": 100, "three_month": 250, "tools": ["pan"]},
    "pincode": {"title": "Pincode Regional Index", "month": 30, "three_month": 80, "tools": ["pincode"]},
    "ip": {"title": "IP Geo-Tracer Engine", "month": 30, "three_month": 80, "tools": ["ip"]},
    "vehicle": {"title": "Vehicle Registration Suite", "month": 400, "three_month": 1000, "tools": ["vehicle", "veh2num", "challan"]},
    "gaming": {"title": "Free Fire & BGMI Suite", "month": 80, "three_month": 200, "tools": ["ff", "bgmi"]},
    "snapchat": {"title": "Snapchat Intel Module", "month": 80, "three_month": 200, "tools": ["snap"]},
    "bomber": {"title": "SMS Stress Bomber", "month": 150, "three_month": 400, "tools": ["bomber"]},
    "pakistan": {"title": "Pakistan Network Index", "month": 100, "three_month": 250, "tools": ["pk"]},
    "bundle_starter": {"title": "Starter Pack Bundle", "month": 500, "three_month": 1300, "tools": ["number", "aadhar", "upi", "pan", "ifsc", "pincode", "ip", "ff", "bgmi"]},
    "bundle_ultimate": {"title": "Ultimate Unlimited Bundle", "month": 1600, "three_month": 4200, "tools": ["all"]}
}

FREE_TOOLS = ["insta", "git", "tg", "tgidinfo"]

# ==========================================
# SECURITY & UTILITY ENGINES
# ==========================================
def get_razorpay_client():
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

def validate_token(key, endpoint):
    if key not in API_KEYS_DB:
        return False, "Invalid validation token payload."
    config = API_KEYS_DB[key]
    try:
        exp_date = datetime.datetime.strptime(config['expiry_date'], "%Y-%m-%d")
        if datetime.datetime.now() > exp_date:
            return False, "Your key license validation window has expired."
    except Exception:
        return False, "Key time-stamp parsing exception."
    if config['current_requests'] >= config['daily_limit']:
        return False, "Daily access bandwidth exhausted."
    if "all" not in config['allowed_tools']:
        matched = False
        for category in config['allowed_tools']:
            if category in API_PRICES and endpoint in API_PRICES[category]['tools']:
                matched = True
        if endpoint in FREE_TOOLS:
            matched = True
        if not matched:
            return False, "Endpoint explicitly locked under current licensing scope."
    return True, config

# ==========================================
# PREMIUM UI TEMPLATES
# ==========================================
STOREFRONT_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ dev_name }} | Enterprise Data Store</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@500;600;700&display=swap');
        :root { --neon-blue: #00f3ff; --neon-purple: #b026ff; --bg-dark: #060913; --glass-card: rgba(13, 20, 38, 0.65); --neon-pink: #ff0055; }
        body { margin: 0; background: var(--bg-dark); color: #ffffff; font-family: 'Rajdhani', sans-serif; background-image: radial-gradient(circle at 50% -20%, #152244 0%, transparent 60%); overflow-x: hidden; }
        .glass { background: var(--glass-card); backdrop-filter: blur(14px); border: 1px solid rgba(0, 243, 255, 0.15); border-radius: 16px; box-shadow: 0 10px 40px rgba(0,0,0,0.4); }
        .nav-bar { display: flex; justify-content: space-between; align-items: center; padding: 20px 45px; border-bottom: 1px solid rgba(0, 243, 255, 0.2); }
        .brand { font-family: 'Orbitron', sans-serif; font-size: 26px; font-weight: 700; color: var(--neon-blue); letter-spacing: 3px; text-shadow: 0 0 15px var(--neon-blue); text-transform: uppercase; }
        .btn { background: linear-gradient(90deg, var(--neon-blue), #0072ff); color: #000; padding: 12px 28px; font-weight: 700; font-family: 'Orbitron'; border: none; border-radius: 8px; cursor: pointer; transition: 0.3s; text-decoration: none; text-transform: uppercase; display: inline-block; }
        .btn:hover { transform: translateY(-3px); box-shadow: 0 0 25px var(--neon-blue); }
        .hero { text-align: center; padding: 90px 20px; }
        .hero h1 { font-family: 'Orbitron'; font-size: 55px; margin: 0; text-transform: uppercase; letter-spacing: 4px; background: linear-gradient(90deg, #fff, var(--neon-blue)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .grid-layout { display: grid; grid-template-columns: repeat(auto-fit, minmax(330px, 1fr)); gap: 35px; padding: 40px; max-width: 1450px; margin: 0 auto; }
        .api-card { padding: 35px; display: flex; flex-direction: column; justify-content: space-between; transition: 0.4s; }
        .api-card:hover { transform: translateY(-8px); border-color: var(--neon-purple); box-shadow: 0 0 30px rgba(176, 38, 255, 0.25); }
        .cost-matrix { font-size: 38px; color: var(--neon-blue); font-weight: 700; font-family: 'Orbitron'; margin: 20px 0; }
        input, select { width: 100%; padding: 14px; margin: 10px 0; background: rgba(0,0,0,0.4); border: 1px solid rgba(0,243,255,0.2); color: #fff; border-radius: 6px; box-sizing: border-box; font-family: 'Rajdhani'; font-size: 16px; }
    </style>
</head>
<body>

    <div class="nav-bar glass" style="border-radius: 0;">
        <div class="brand">{{ dev_name }}</div>
        <div>
            {% if session.get('user') %}
                <span style="margin-right:20px; font-size:18px;">Operator: <span style="color:var(--neon-blue);">{{ session['user'] }}</span></span>
                {% if session.get('is_admin') %}
                    <a href="/admin" class="btn" style="background: var(--neon-pink); color:#fff; margin-right:10px;">Terminal Override</a>
                {% endif %}
                <a href="/logout" class="btn" style="background:transparent; border:1px solid var(--neon-pink); color:var(--neon-pink);">Disconnect</a>
            {% else %}
                <a href="/login" class="btn">Establish Handshake</a>
            {% endif %}
        </div>
    </div>

    {% if view == "login" %}
    <div style="max-width:440px; margin:110px auto; padding:45px;" class="glass">
        <h2 style="font-family:'Orbitron'; text-align:center; color:var(--neon-blue);">AUTHENTICATE INSTANCE</h2>
        <form method="POST" action="/login">
            <input type="text" name="username" placeholder="Access Handle / Email" required>
            <input type="password" name="password" placeholder="Passphrase Matrix" required>
            <button type="submit" class="btn" style="width:100%; margin-top:15px;">Verify Credentials</button>
        </form>
    </div>

    {% elif view == "store" %}
    <div class="hero">
        <h1>High-Performance Data Routing Infrastructure</h1>
        <p style="color:#a4b3cd; font-size:22px; margin-top:15px;">Maintained Securely under Node Framework: {{ dev_name }}</p>
    </div>

    <div class="grid-layout">
        {% for pack_id, details in prices.items() %}
        <div class="api-card glass">
            <div>
                <h3 style="margin:0; font-family:'Orbitron'; font-size:24px;">{{ details.title }}</h3>
                <p style="color:#7e8eaf; font-size:15px; margin:15px 0;">
                    Scope Capacity:<br>
                    <span style="color:#fff; font-weight:600;">{{ ", ".join(details.tools) }}</span>
                </p>
            </div>
            <div>
                <div class="cost-matrix">₹{{ details.month }} <span style="font-size:15px; color:#7e8eaf;">/ Month</span></div>
                <form method="POST" action="/purchase/initialize">
                    <input type="hidden" name="package_id" value="{{ pack_id }}">
                    <input type="text" name="custom_key" placeholder="Define Custom Token Identifier" required>
                    <select name="duration_frame">
                        <option value="month">1-Month License Deployment</option>
                        <option value="three_month">3-Month Extended Lifecycle</option>
                    </select>
                    {% if session.get('user') %}
                        <button type="submit" class="btn" style="width:100%; margin-top:10px;">Execute Node Order</button>
                    {% else %}
                        <button type="button" class="btn" style="width:100%; margin-top:10px; opacity:0.4;" onclick="window.location.href='/login'">Authenticate to Unlock</button>
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
    <title>Core Terminal Override | {{ dev_name }}</title>
    <style>
        body { font-family: 'Courier New', monospace; background: #02040a; color: #00ff66; padding: 30px; }
        .container { border: 1px solid #00ff66; padding: 25px; margin-bottom: 25px; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { border: 1px solid #00ff66; padding: 12px; text-align: left; }
        input, button { background: #000; color: #00ff66; border: 1px solid #00ff66; padding: 12px; margin: 5px 0; }
        button:hover { background: #00ff66; color: #000; cursor: pointer; }
    </style>
</head>
<body>
    <h1>[// CORE MATRIX MANAGEMENT INTERFACE - {{ dev_name }}]</h1>
    
    <div class="container">
        <h3>> DIRECT TOKEN LICENSE INJECTION</h3>
        <form method="POST" action="/admin/inject">
            <input type="text" name="key" placeholder="Desired Key Phrase" required>
            <input type="text" name="owner" placeholder="Owner Operator Email" required>
            <input type="text" name="scope" placeholder="Allowed Endpoint Scope" required>
            <button type="submit">Inject Token Space</button>
        </form>
    </div>

    <div class="container">
        <h3>> REGISTERED ACCESS TOKEN MATRIX</h3>
        <table>
            <thead>
                <tr><th>Access Key</th><th>Owner Identity</th><th>Access Scope</th><th>Expiry Vector</th><th>Hits Logged</th></tr>
            </thead>
            <tbody>
                {% for k, v in keys_registry.items() %}
                <tr>
                    <td><code>{{ k }}</code></td>
                    <td>{{ v.owner_email }}</td>
                    <td><span style="color:#00ffff;">{{ v.allowed_tools }}</span></td>
                    <td>{{ v.expiry_date }}</td>
                    <td>{{ v.current_requests }} Requests</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    <br>
    <a href="/"><button><< Return to System Storefront</button></a>
</body>
</html>
"""

# ==========================================
# SYSTEM FRAMEWORK ROUTING PORTS
# ==========================================
@app.route('/', methods=['GET'])
def route_index():
    return render_template_string(STOREFRONT_HTML, dev_name=DEVELOPER_NAME, view="store", prices=API_PRICES)

@app.route('/login', methods=['GET', 'POST'])
def route_login():
    if request.method == 'POST':
        user = request.form.get('username')
        passphrase = request.form.get('password')
        if user == ADMIN_USER and passphrase == ADMIN_PASS:
            session['user'] = user
            session['is_admin'] = True
        else:
            session['user'] = user
            session['is_admin'] = False
        return redirect('/')
    return render_template_string(STOREFRONT_HTML, dev_name=DEVELOPER_NAME, view="login", prices=API_PRICES)

@app.route('/logout', methods=['GET'])
def route_logout():
    session.clear()
    return redirect('/')

@app.route('/admin', methods=['GET'])
def route_admin_dashboard():
    if not session.get('is_admin'):
        return "CRITICAL SYSTEM EXCEPTION: SECURITY ACCESS VIOLATION DETECTED.", 403
    return render_template_string(ADMIN_HTML, dev_name=DEVELOPER_NAME, keys_registry=API_KEYS_DB)

@app.route('/admin/inject', methods=['POST'])
def route_admin_inject():
    if not session.get('is_admin'):
        return "CRITICAL SYSTEM EXCEPTION: SECURITY ACCESS VIOLATION DETECTED.", 403
    key_phrase = request.form.get('key')
    API_KEYS_DB[key_phrase] = {
        "key_name": "Manual Override Token",
        "owner_email": request.form.get('owner'),
        "expiry_date": "2029-12-31",
        "daily_limit": 5000,
        "current_requests": 0,
        "allowed_tools": [request.form.get('scope')]
    }
    return redirect('/admin')

@app.route('/purchase/initialize', methods=['POST'])
def route_payment_init():
    if not session.get('user'):
        return redirect('/login')
        
    client = get_razorpay_client()
    if not client:
        return jsonify({"status": "failed", "message": "Razorpay connection failure."}), 500

    pack_id = request.form.get('package_id')
    custom_key = request.form.get('custom_key')
    duration = request.form.get('duration_frame', 'month')
    
    if pack_id not in API_PRICES:
        return jsonify({"status": "failed", "message": "Invalid pricing scope index."}), 400
        
    base_price = API_PRICES[pack_id]['month'] if duration == 'month' else API_PRICES[pack_id]['three_month']
    calculated_tax = (base_price * GLOBAL_CONFIG['gst_percentage']) / 100
    total_payable_paise = int((base_price + calculated_tax) * 100)

    order_payload = {
        "amount": total_payable_paise,
        "currency": "INR",
        "receipt": f"rcpt_{int(datetime.datetime.now().timestamp())}",
        "notes": {
            "requested_key": custom_key,
            "target_pack": pack_id,
            "duration": duration,
            "buyer": session['user']
        }
    }
    
    try:
        razorpay_order = client.order.create(data=order_payload)
    except Exception as e:
        return jsonify({"status": "failed", "message": "Failed order handshake with Razorpay.", "details": str(e)}), 400
        
    return f"""
    <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
    <script>
        var options = {{
            "key": "{RAZORPAY_KEY_ID}",
            "amount": "{razorpay_order['amount']}",
            "currency": "INR",
            "name": "{DEVELOPER_NAME} Core Gateway",
            "description": "Deployment Allocation: {pack_id}",
            "order_id": "{razorpay_order['id']}",
            "handler": function (response){{
                window.location.href = "/purchase/callback?payment_id="+response.razorpay_payment_id+"&order_id="+response.razorpay_order_id+"&signature="+response.razorpay_signature;
            }},
            "prefill": {{ "email": "{session['user']}" }},
            "theme": {{ "color": "#00f3ff" }}
        }};
        var rzp = new Razorpay(options);
        rzp.open();
    </script>
    """

@app.route('/purchase/callback', methods=['GET', 'POST'])
def route_payment_callback():
    client = get_razorpay_client()
    if not client:
        return "Payment verification client engine is offline.", 503

    query_params = request.args if request.method == 'GET' else request.form
    pay_id = query_params.get('payment_id')
    order_id = query_params.get('order_id')
    signature = query_params.get('signature')
    
    if not pay_id or not order_id or not signature:
        return "Tracking trace telemetry elements missing.", 400

    signing_payload = f"{order_id}|{pay_id}"
    computed_signature = hmac.new(
        bytes(RAZORPAY_SECRET, 'utf-8'),
        msg=bytes(signing_payload, 'utf-8'),
        digestmod=hashlib.sha256
    ).hexdigest()
    
    if computed_signature != signature:
        return "Transaction security token validation mismatched signature.", 400

    try:
        order_meta = client.order.fetch(order_id)
    except Exception as e:
        return f"Order verification pipeline exception tracking: {str(e)}", 400

    metadata_notes = order_meta.get('notes', {})
    generated_key_id = metadata_notes.get('requested_key', f"gen_token_{pay_id[:7]}")
    assigned_package = metadata_notes.get('target_pack')
    duration_selected = metadata_notes.get('duration')
    
    days_span = 30 if duration_selected == 'month' else 90
    target_expiry = (datetime.datetime.now() + datetime.timedelta(days=days_span)).strftime("%Y-%m-%d")

    API_KEYS_DB[generated_key_id] = {
        "key_name": f"{assigned_package.upper()} License Allocation",
        "owner_email": metadata_notes.get('buyer'),
        "expiry_date": target_expiry,
        "daily_limit": 3000,
        "current_requests": 0,
        "allowed_tools": [assigned_package]
    }

    telegram_alert_string = f"💰 *NEW SUBSCRIPTION DISPATCHED*\n\n👤 *Operator:* {metadata_notes.get('buyer')}\n🔑 *Token:* `{generated_key_id}`\n📦 *License Matrix:* `{assigned_package}`\n📅 *Expiration Lifecycle:* {target_expiry}"
    dispatch_telegram_alert(telegram_alert_string)

    return f"""
    <body style="background:#060913; color:#fff; text-align:center; padding-top:100px; font-family:sans-serif;">
        <h1 style="color:#00f3ff;">TRANSACTION SECURED SUCCESSFULLY</h1>
        <h2>Your Premium Access License Token is Active: <span style="color:#b026ff;">{generated_key_id}</span></h2>
        <p>Active Duration: Valid until target frame {target_expiry}</p>
        <br><a href="/" style="color:#00f3ff; font-weight:bold; text-decoration:none;">[ Return to System Terminal ]</a>
    </body>
    """

@app.route('/api/<endpoint>', methods=['GET'])
def route_api_proxy_gateway(endpoint):
    token_arg = request.args.get('key')
    if not token_arg:
        return jsonify({"status": "failed", "developer": DEVELOPER_NAME, "message": "Authorization license key argument missing."}), 400
        
    is_authorized, payload_context = validate_token(token_arg, endpoint)
    if not is_authorized:
        return jsonify({"status": "failed", "developer": DEVELOPER_NAME, "message": payload_context}), 403

    API_KEYS_DB[token_arg]['current_requests'] += 1

    forwarded_arguments = request.args.to_dict()
    if 'key' in forwarded_arguments:
        del forwarded_arguments['key']
    
    forwarded_arguments['key'] = "ftgamer2"

    try:
        upstream_url_endpoint = f"{TARGET_BASE_URL}/{endpoint}"
        network_response = requests.get(upstream_url_endpoint, params=forwarded_arguments, timeout=14)
        
        try:
            json_payload = network_response.json()
            if isinstance(json_payload, dict):
                json_payload.pop('credits', None)
                json_payload.pop('owner', None)
                json_payload.pop('telegram', None)
                json_payload['developer'] = DEVELOPER_NAME
            return jsonify(json_payload), network_response.status_code
        except ValueError:
            return network_response.text, network_response.status_code
            
    except requests.exceptions.RequestException:
        return jsonify({"status": "failed", "developer": DEVELOPER_NAME, "message": "Upstream proxy interface sync timeout."}), 504

if __name__ == '__main__':
    app.run(debug=True)
