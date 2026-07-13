from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
import requests
import datetime
import hmac
import hashlib
import razorpay

app = Flask(__name__)
app.secret_key = "SHAYAN_EXPLORER_SECURE_SESSION_KEY_2026"

# MASTER CONFIGURATION & BRANDING
DEVELOPER_NAME = "SHAYAN_EXPLORER"
TARGET_BASE_URL = "https://ft-osint-api.duckdns.org/api"

# ADMINISTRATIVE ACCESS
ADMIN_USER = "vernex"
ADMIN_PASS = "vernex@16vx"

# INTEGRATION SECRETS
RAZORPAY_KEY_ID = "rzp_live_TCc5USt5FlmfrI"
RAZORPAY_SECRET = "sMwLGQAEQePA0qSOYvFFII1h"
TELEGRAM_BOT_TOKEN = "8378722740:AAH9GthadrXQlTSp8pmPvlUnogXxhHv371s"
TELEGRAM_CHAT_ID = "-1002234567890"  # Replace with your actual Telegram Group/Channel Chat ID

razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_SECRET))

# DATA MATRIX STRUCTURES (Simulated - Swap to Database for persistence)
API_KEYS_DB = {
    "explorer16": {
        "key_name": "Ultimate Master Bypass",
        "owner_email": "admin@shayan.io",
        "expiry_date": "2029-12-31",
        "expiry_time": "23:59",
        "daily_limit": 999999,
        "current_requests": 0,
        "allowed_tools": ["all"]
    }
}
USERS_DB = {}
SYSTEM_LOGS = []
GLOBAL_CONFIG = {"gst_percentage": 18}

# PRICE LIST REGISTRY
API_PRICES = {
    "number": {"title": "Number Lookup Pack", "month": 100, "three_month": 250, "tools": ["number", "paytm", "calltracer", "adv"]},
    "leak": {"title": "HiTeckGroop.in Leak Pack", "month": 400, "three_month": 1100, "tools": ["email", "adv"]},
    "aadhaar": {"title": "Aadhaar System Suite", "month": 200, "three_month": 550, "tools": ["aadhar", "adharfamily"]},
    "upi": {"title": "UPI & Financial Identity Pack", "month": 150, "three_month": 400, "tools": ["upi", "numtoupi"]},
    "ifsc": {"title": "IFSC Routing Directory", "month": 50, "three_month": 120, "tools": ["ifsc"]},
    "pan": {"title": "PAN to GST Validator", "month": 100, "three_month": 250, "tools": ["pan"]},
    "pincode": {"title": "Pincode Regional Index", "month": 30, "three_month": 80, "tools": ["pincode"]},
    "ip": {"title": "IP Geo-Tracer Engine", "month": 30, "three_month": 80, "tools": ["ip"]},
    "vehicle": {"title": "Vehicle & Ownership Register", "month": 400, "three_month": 1000, "tools": ["vehicle", "veh2num", "challan"]},
    "gaming": {"title": "Free Fire & BGMI Matcher", "month": 80, "three_month": 200, "tools": ["ff", "bgmi"]},
    "snapchat": {"title": "Snapchat Info Module", "month": 80, "three_month": 200, "tools": ["snap"]},
    "bomber": {"title": "SMS Stress Validation Bomber", "month": 150, "three_month": 400, "tools": ["bomber"]},
    "pakistan": {"title": "Pakistan Directory Module", "month": 100, "three_month": 250, "tools": ["pk"]},
    "bundle_starter": {"title": "Starter Pack Bundle", "month": 500, "three_month": 1300, "tools": ["number", "paytm", "calltracer", "adv", "aadhar", "adharfamily", "upi", "numtoupi", "pan", "ifsc", "pincode", "ip", "ff", "bgmi"]},
    "bundle_pro": {"title": "Pro Pack Bundle", "month": 1200, "three_month": 3000, "tools": ["all_except_vehicle"]},
    "bundle_ultimate": {"title": "Ultimate Pack Bundle", "month": 1600, "three_month": 4200, "tools": ["all"]}
}

# FREE ENDPOINTS INDEX
FREE_TOOLS = ["insta", "git", "tg", "tgidinfo"]

def dispatch_telegram_alert(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}, timeout=5)
    except Exception:
        pass

# SECURITY ROUTING LOGIC MIDDLEWARE
def validate_token_access(key, endpoint):
    if key not in API_KEYS_DB:
        return False, "Invalid validation token payload string."
    
    config = API_KEYS_DB[key]
    
    # Enforce Expiration Time Bounds
    try:
        exp_datetime = datetime.datetime.strptime(f"{config['expiry_date']} {config['expiry_time']}", "%Y-%m-%d %H:%M")
        if datetime.datetime.now() > exp_datetime:
            return False, "Requested token authorization has expired."
    except:
        return False, "Format handling validation structural error."
        
    # Enforce Volumetric Counters
    if config['current_requests'] >= config['daily_limit']:
        return False, "Daily access allocation limits exhausted."
        
    # Enforce Scope Control Granularity
    if "all" not in config['allowed_tools']:
        if "all_except_vehicle" in config['allowed_tools'] and endpoint in ["vehicle", "veh2num"]:
            return False, "Unauthorized endpoint scope."
        
        # Resolve mapped endpoints array checks
        matched = False
        for tool_category in config['allowed_tools']:
            if tool_category in API_PRICES and endpoint in API_PRICES[tool_category]['tools']:
                matched = True
            if endpoint in FREE_TOOLS:
                matched = True
        if not matched and config['allowed_tools'] != ["all"]:
            return False, "Endpoint explicitly locked under current licensing scope."
            
    return True, config

# --- DESIGN LANDING PAGE & USER INTERFACE ---
STOREFRONT_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ dev_name }} | Luxury Cyber Gateway Storefront</title>
    <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
    <style>
        :root { --neon: #00f3ff; --neon-pink: #ff0055; --bg: #050811; --surface: rgba(16, 22, 42, 0.7); }
        body { font-family: 'Segoe UI', system-ui, sans-serif; background: var(--bg); color: #fff; margin:0; padding:0; overflow-x:hidden; }
        .glass { background: var(--surface); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.05); border-radius: 16px; }
        .navbar { display:flex; justify-content:space-between; align-items:center; padding: 20px 40px; border-bottom: 1px solid rgba(0,243,255,0.2); }
        .logo { font-size:24px; font-weight:bold; letter-spacing:3px; color: var(--neon); text-shadow: 0 0 10px var(--neon); }
        .hero { text-align:center; padding: 80px 20px; }
        .hero h1 { font-size: 50px; margin:0; text-transform:uppercase; letter-spacing:4px; background: linear-gradient(90deg, #fff, var(--neon)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .grid { display:grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap:30px; padding:40px; max-width:1400px; margin:0 auto; }
        .card { padding:30px; position:relative; transition: 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); display:flex; flex-direction:column; justify-content:space-between; }
        .card:hover { transform: translateY(-10px); border-color: var(--neon); box-shadow: 0 0 20px rgba(0,243,255,0.2); }
        .price { font-size:32px; color: var(--neon); font-weight:bold; margin:15px 0; }
        .btn { background: linear-gradient(90deg, var(--neon), #00a2ff); color:#000; border:none; padding:12px 24px; font-weight:bold; border-radius:8px; cursor:pointer; text-transform:uppercase; transition:0.3s; }
        .btn:hover { box-shadow: 0 0 15px var(--neon); opacity:0.9; }
        .auth-container { max-width:400px; margin:100px auto; padding:40px; text-align:center; }
        input, select { width:100%; padding:12px; margin:10px 0; background:rgba(0,0,0,0.3); border:1px solid rgba(255,255,255,0.1); color:#fff; border-radius:6px; box-sizing:border-box; }
        input:focus { border-color: var(--neon); outline:none; }
    </style>
</head>
<body>

    <div class="navbar glass">
        <div class="logo">{{ dev_name }}</div>
        <div>
            {% if session.get('user') %}
                <span style="margin-right:20px; color:#8a99ad;">Welcome, {{ session['user'] }}</span>
                {% if session.get('is_admin') %}
                    <a href="/dashboard" style="color:var(--neon); margin-right:15px; text-decoration:none;">Admin</a>
                {% endif %}
                <a href="/logout" style="color:var(--neon-pink); text-decoration:none;">Disconnect</a>
            {% else %}
                <a href="/login" class="btn" style="text-decoration:none; padding:8px 16px;">Access Terminal</a>
            {% endif %}
        </div>
    </div>

    {% if view == "login" %}
    <div class="auth-container glass">
        <h2>System Verification</h2>
        <form method="POST" action="/login">
            <input type="text" name="username" placeholder="Identity Handle / Email" required>
            <input type="password" name="password" placeholder="Passphrase" required>
            <button type="submit" class="btn" style="width:100%; margin-top:15px;">Authenticate</button>
        </form>
        <p style="color:#555; margin:15px 0;">or</p>
        <button class="btn" style="width:100%; background:#fff; color:#000;" onclick="alert('Google OAuth Loop Redirected Execution via Mock Sequence.')">Log In via Google Secure Context</button>
    </div>
    {% elif view == "store" %}
    <div class="hero">
        <h1>Next-Gen OSINT Data Infrastructure</h1>
        <p style="color:#8a99ad; font-size:18px;">Sub-millisecond processing pipelines served seamlessly by SHAYAN_EXPLORER</p>
    </div>

    <div class="grid">
        {% for id, pack in prices.items() %}
        <div class="card glass">
            <div>
                <h3 style="margin:0; font-size:22px; color:#fff;">{{ pack.title }}</h3>
                <p style="color:#8a99ad; font-size:13px; margin:10px 0;">Includes Endpoints: {{ ", ".join(pack.tools) }}</p>
            </div>
            <div>
                <div class="price">₹{{ pack.month }} <span style="font-size:14px; color:#8a99ad;">/ Month</span></div>
                <form method="POST" action="/purchase/initialize">
                    <input type="hidden" name="package_id" value="{{ id }}">
                    <input type="text" name="custom_key" placeholder="Desired Custom Key Name" required style="font-size:12px; padding:8px;">
                    <select name="duration" style="font-size:12px; padding:8px;">
                        <option value="month">1 Month Plan (Standard)</option>
                        <option value="three_month">3 Months Plan (Save 15%)</option>
                    </select>
                    {% if session.get('user') %}
                        <button type="submit" class="btn" style="width:100%; margin-top:10px;">Purchase Node Access</button>
                    {% else %}
                        <button type="button" class="btn" style="width:100%; margin-top:10px; opacity:0.5;" onclick="window.location.href='/login'">Login to Purchase</button>
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

# --- BACKEND LOGIC ROUTING EXECUTIONS ---

@app.route('/', methods=['GET'])
def index_route():
    return render_template_string(STOREFRONT_HTML, dev_name=DEVELOPER_NAME, view="store", prices=API_PRICES)

@app.route('/login', methods=['GET', 'POST'])
def login_route():
    if request.method == 'POST':
        user = request.form.get('username')
        password = request.form.get('password')
        
        if user == ADMIN_USER and password == ADMIN_PASS:
            session['user'] = user
            session['is_admin'] = True
            return redirect('/dashboard')
        
        # Simple generic authentication registration processing pipeline simulation
        session['user'] = user
        return redirect('/')
    return render_template_string(STOREFRONT_HTML, dev_name=DEVELOPER_NAME, view="login")

@app.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return redirect('/')

# --- RAZORPAY INTEGRATION CONTROLLERS ---

@app.route('/purchase/initialize', methods=['POST'])
def purchase_init():
    if not session.get('user'):
        return redirect('/login')
        
    pack_id = request.form.get('package_id')
    custom_key = request.form.get('custom_key')
    duration = request.form.get('duration', 'month')
    
    if pack_id not in API_PRICES:
        return jsonify({"error": "Invalid tier scope catalog profile selection"}), 400
        
    base_cost = API_PRICES[pack_id]['month'] if duration == 'month' else API_PRICES[pack_id]['three_month']
    gst_calc = (base_cost * GLOBAL_CONFIG['gst_percentage']) / 100
    total_payable = int((base_cost + gst_calc) * 100) # Convertible Paise conversion representation

    # Generate Order Handshake Object via native Razorpay Driver Module
    order_payload = {
        "amount": total_payable,
        "currency": "INR",
        "receipt": f"rcpt_{int(datetime.datetime.now().timestamp())}",
        "notes": {
            "custom_key_requested": custom_key,
            "package_scope": pack_id,
            "duration_frame": duration,
            "purchaser_identity": session['user']
        }
    }
    
    razorpay_order = razorpay_client.order.create(data=order_payload)
    
    # Render checkout script sequence automation payload dynamically
    checkout_script = f"""
    <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
    <script>
        var options = {{
            "key": "{RAZORPAY_KEY_ID}",
            "amount": "{razorpay_order['amount']}",
            "currency": "INR",
            "name": "{DEVELOPER_NAME} Gateway Engine",
            "description": "Subscription Deployment Node Access Pack: {pack_id}",
            "order_id": "{razorpay_order['id']}",
            "handler": function (response){{
                window.location.href = "/purchase/callback?payment_id="+response.razorpay_payment_id+"&order_id="+response.razorpay_order_id+"&signature="+response.razorpay_signature;
            }},
            "prefill": {{ "email": "{session['user']}" }},
            "theme": {{ "color": "#00f3ff" }}
        }};
        var rzp1 = new Razorpay(options);
        rzp1.open();
    </script>
    """
    return checkout_script

@app.route('/purchase/callback', methods=['GET', 'POST'])
def payment_verification_callback():
    # Handle both redirect variants seamlessly
    param_source = request.args if request.method == 'GET' else request.form
    
    pay_id = param_source.get('payment_id')
    order_id = param_source.get('order_id')
    signature = param_source.get('signature')
    
    # Re-verify transactional authenticity
    sig_check_payload = f"{order_id}|{pay_id}"
    generated_signature = hmac.new(
        bytes(RAZORPAY_SECRET, 'utf-8'),
        msg=bytes(sig_check_payload, 'utf-8'),
        digestmod=hashlib.sha256
    ).hexdigest()
    
    if generated_signature != signature:
        return "Transaction verification mismatch. Context verification failed signatures.", 400

    # Fetch contextual details straight from Order database tracking to issue nodes cleanly
    order_details = razorpay_client.order.fetch(order_id)
    notes = order_details.get('notes', {})
    
    assigned_key = notes.get('custom_key_requested', f"gen_{pay_id[:8]}")
    selected_pack = notes.get('package_scope')
    duration = notes.get('duration_frame')
    
    days_to_add = 30 if duration == 'month' else 90
    expiration_target = (datetime.datetime.now() + datetime.timedelta(days=days_to_add)).strftime("%Y-%m-%d")

    # Allocate client profile access directly inside the gateway layer lookup registry
    API_KEYS_DB[assigned_key] = {
        "key_name": f"{selected_pack.upper()} Tier Subscription Node",
        "owner_email": notes.get('purchaser_identity'),
        "expiry_date": expiration_target,
        "expiry_time": "23:59",
        "daily_limit": 2500,
        "current_requests": 0,
        "allowed_tools": [selected_pack]
    }

    # Dispatch alerts to the unified operational center
    alert_text = f"🔥 *NEW SUBSCRIPTION ACTIVE*\n\n👤 *User:* {notes.get('purchaser_identity')}\n🔑 *Issued Key:* `{assigned_key}`\n📦 *Module Scope:* `{selected_pack}`\n📅 *Expires:* {expiration_target}\n💰 *Status:* Payment Verified Success"
    dispatch_telegram_alert(alert_text)

    return f"<h1>Payment Success! Your access token key `{assigned_key}` is active until {expiration_target}.</h1><a href='/'>Return to Store</a>"

# --- RE-ROUTING MASTER OSINT ENGINE LOGIC DISPATCHER ---

@app.route('/api/<endpoint>', methods=['GET'])
def core_api_proxy_dispatcher(endpoint):
    client_auth_key = request.args.get('key')
    
    if not client_auth_key:
        return jsonify({"status": "failed", "developer": DEVELOPER_NAME, "message": "Missing node authorization key parameter argument."}), 400
        
    is_valid, configuration_metadata = validate_token_access(client_auth_key, endpoint)
    if not is_valid:
        return jsonify({"status": "failed", "developer": DEVELOPER_NAME, "message": configuration_metadata}), 403

    # Structural scrubbing of parameters before passing them downstream upstream pipelines
    cleaned_forwarding_args = request.args.to_dict()
    if 'key' in cleaned_forwarding_args:
        del cleaned_forwarding_args['key']
    
    # Inject real processing pipeline keys securely inside standard background layer parameters
    cleaned_forwarding_args['key'] = "ftgamer2" 

    # Save transaction history securely inside log registry tracking metrics
    SYSTEM_LOGS.append({
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "key": client_auth_key,
        "endpoint": endpoint,
        "query": str(cleaned_forwarding_args)
    })
    
    # Increment Volumetric Consumption Counter Metrics
    API_KEYS_DB[client_auth_key]['current_requests'] += 1

    try:
        upstream_target_endpoint_url = f"{TARGET_BASE_URL}/{endpoint}"
        upstream_network_response = requests.get(upstream_target_endpoint_url, params=cleaned_forwarding_args, timeout=12)
        
        try:
            json_response_payload = upstream_network_response.json()
            if isinstance(json_response_payload, dict):
                # Hard filter and remove external provider footings seamlessly
                json_response_payload.pop('credits', None)
                json_response_payload.pop('owner', None)
                json_response_payload.pop('telegram', None)
                # Overwrite and claim absolute authoritative branding ownership
                json_response_payload['developer'] = DEVELOPER_NAME
            return jsonify(json_response_payload), upstream_network_response.status_code
        except ValueError:
            return upstream_network_response.text, upstream_network_response.status_code

    except requests.exceptions.RequestException:
        return jsonify({"status": "failed", "developer": DEVELOPER_NAME, "message": "Downstream proxy compilation timeout or execution pipeline failure."}), 504

# --- ADMIN ADMINISTRATIVE COMMAND OPERATIONS PLATFORM ---

ADMIN_DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><title>Master Console Infrastructure</title>
    <style>body{background:#070a13; color:#fff; font-family:sans-serif; padding:30px;} .box{background:#111625; padding:25px; border-radius:12px; margin-bottom:20px; border:1px solid #1e2638;}</style>
</head>
<body>
    <h1>Master API Control Infrastructure Panel</h1>
    <div class="box">
        <h2>Global Platform Config Adjustments</h2>
        <form method="POST" action="/dashboard/config">
            <label>Active GST Tax Rate (%): </label>
            <input type="number" name="gst" value="{{ config.gst_percentage }}">
            <button type="submit">Modify Parameters</button>
        </form>
    </div>
    <div class="box">
        <h2>Active Issued System Nodes Matrix</h2>
        <table border="1" cellpadding="10" style="border-collapse:collapse; width:100%;">
            <tr><th>Authentication Token Key</th><th>Owner Handle</th><th>Allocated Package Scope</th><th>Expiration Bounds</th><th>Consumption Rate</th></tr>
            {% for k,v in keys.items() %}
            <tr><td><code>{{ k }}</code></td><td>{{ v.owner_email }}</td><td>{{ v.key_name }}</td><td>{{ v.expiry_date }} {{ v.expiry_time }}</td><td>{{ v.current_requests }} / {{ v.daily_limit }}</td></tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""

@app.route('/dashboard', methods=['GET'])
def admin_portal():
    auth = request.authorization
    if not auth or auth.username != ADMIN_USER or auth.password != ADMIN_PASS:
        return jsonify({"error": "Administrative contexts unauthorized Access Denied"}), 401, {'WWW-Authenticate': 'Basic realm="Login Required"'}
    return render_template_string(ADMIN_DASHBOARD_HTML, keys=API_KEYS_DB, config=GLOBAL_CONFIG)

@app.route('/dashboard/config', methods=['POST'])
def admin_config_update():
    auth = request.authorization
    if not auth or auth.username != ADMIN_USER or auth.password != ADMIN_PASS:
        return jsonify({"error": "Access Denied"}), 401
    GLOBAL_CONFIG['gst_percentage'] = int(request.form.get('gst', 18))
    return redirect('/dashboard')

if __name__ == '__main__':
    app.run(debug=True)
