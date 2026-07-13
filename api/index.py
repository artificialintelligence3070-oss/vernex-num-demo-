from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
import requests
import datetime
import hmac
import hashlib
import razorpay

app = Flask(__name__)
# Secure hardcoded string signature for serverless tracking stability
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
TELEGRAM_CHAT_ID = "-1002234567890"

# --- Insulated Lazy Driver Initializer Pattern ---
def get_razorpay_client():
    try:
        return razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_SECRET))
    except Exception as e:
        return None

# DATA MATRIX STRUCTURES
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

FREE_TOOLS = ["insta", "git", "tg", "tgidinfo"]

# GLOBAL 500 CATCHER MIDDLEWARE
@app.errorhandler(500)
def server_error_cleaner(error):
    return jsonify({
        "status": "failed",
        "developer": DEVELOPER_NAME,
        "message": "Internal compilation structural exception caught.",
        "details": str(error)
    }), 500

def dispatch_telegram_alert(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}, timeout=5)
    except Exception:
        pass

def validate_token_access(key, endpoint):
    if key not in API_KEYS_DB:
        return False, "Invalid validation token payload string."
    
    config = API_KEYS_DB[key]
    
    try:
        exp_datetime = datetime.datetime.strptime(f"{config['expiry_date']} {config['expiry_time']}", "%Y-%m-%d %H:%M")
        if datetime.datetime.now() > exp_datetime:
            return False, "Requested token authorization has expired."
    except:
        return False, "Format handling validation structural error."
        
    if config['current_requests'] >= config['daily_limit']:
        return False, "Daily access allocation limits exhausted."
        
    if "all" not in config['allowed_tools']:
        if "all_except_vehicle" in config['allowed_tools'] and endpoint in ["vehicle", "veh2num"]:
            return False, "Unauthorized endpoint scope."
        
        matched = False
        for tool_category in config['allowed_tools']:
            if tool_category in API_PRICES and endpoint in API_PRICES[tool_category]['tools']:
                matched = True
            if endpoint in FREE_TOOLS:
                matched = True
        if not matched and config['allowed_tools'] != ["all"]:
            return False, "Endpoint explicitly locked under current licensing scope."
            
    return True, config

STOREFRONT_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ dev_name }} | Luxury Cyber Gateway Storefront</title>
    <style>
        :root { --neon: #00f3ff; --neon-pink: #ff0055; --bg: #050811; --surface: rgba(16, 22, 42, 0.7); }
        body { font-family: 'Segoe UI', system-ui, sans-serif; background: var(--bg); color: #fff; margin:0; padding:0; overflow-x:hidden; }
        .glass { background: var(--surface); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.05); border-radius: 16px; }
        .navbar { display:flex; justify-content:space-between; align-items:center; padding: 20px 40px; border-bottom: 1px solid rgba(0,243,255,0.2); }
        .logo { font-size:24px; font-weight:bold; letter-spacing:3px; color: var(--neon); text-shadow: 0 0 10px var(--neon); }
        .hero { text-align:center; padding: 80px 20px; }
        .hero h1 { font-size: 50px; margin:0; text-transform:uppercase; letter-spacing:4px; background: linear-gradient(90deg, #fff, var(--neon)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .grid { display:grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap:30px; padding:40px; max-width:1400px; margin:0 auto; }
        .card { padding:30px; position:relative; transition: 0.4s; display:flex; flex-direction:column; justify-content:space-between; }
        .card:hover { transform: translateY(-10px); border-color: var(--neon); box-shadow: 0 0 20px rgba(0,243,255,0.2); }
        .price { font-size:32px; color: var(--neon); font-weight:bold; margin:15px 0; }
        .btn { background: linear-gradient(90deg, var(--neon), #00a2ff); color:#000; border:none; padding:12px 24px; font-weight:bold; border-radius:8px; cursor:pointer; text-transform:uppercase; transition:0.3s; }
        .btn:hover { box-shadow: 0 0 15px var(--neon); opacity:0.9; }
        .auth-container { max-width:400px; margin:100px auto; padding:40px; text-align:center; }
        input, select { width:100%; padding:12px; margin:10px 0; background:rgba(0,0,0,0.3); border:1px solid rgba(255,255,255,0.1); color:#fff; border-radius:6px; box-sizing:border-box; }
    </style>
</head>
<body>

    <div class="navbar glass">
        <div class="logo">{{ dev_name }}</div>
        <div>
            {% if session.get('user') %}
                <span style="margin-right:20px; color:#8a99ad;">Welcome, {{ session['user'] }}</span>
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
    </div>
    {% elif view == "store" %}
    <div class="hero">
        <h1>Next-Gen OSINT Data Infrastructure</h1>
        <p style="color:#8a99ad; font-size:18px;">Served seamlessly by {{ dev_name }}</p>
    </div>

    <div class="grid">
        {% for id, pack in prices.items() %}
        <div class="card glass">
            <div>
                <h3 style="margin:0; font-size:22px; color:#fff;">{{ pack.title }}</h3>
                <p style="color:#8a99ad; font-size:13px; margin:10px 0;">Endpoints: {{ ", ".join(pack.tools[:4]) }}...</p>
            </div>
            <div>
                <div class="price">₹{{ pack.month }}</div>
                <form method="POST" action="/purchase/initialize">
                    <input type="hidden" name="package_id" value="{{ id }}">
                    <input type="text" name="custom_key" placeholder="Desired Custom Key Name" required style="font-size:12px; padding:8px;">
                    <select name="duration" style="font-size:12px; padding:8px;">
                        <option value="month">1 Month Plan</option>
                        <option value="three_month">3 Months Plan</option>
                    </select>
                    {% if session.get('user') %}
                        <button type="submit" class="btn" style="width:100%; margin-top:10px;">Purchase Node</button>
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
            return redirect('/')
        
        session['user'] = user
        return redirect('/')
    return render_template_string(STOREFRONT_HTML, dev_name=DEVELOPER_NAME, view="login", prices=API_PRICES)

@app.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return redirect('/')

@app.route('/purchase/initialize', methods=['POST'])
def purchase_init():
    if not session.get('user'):
        return redirect('/login')
        
    client = get_razorpay_client()
    if not client:
        return jsonify({"status": "failed", "message": "Payment system gateway driver offline."}), 503

    pack_id = request.form.get('package_id')
    custom_key = request.form.get('custom_key')
    duration = request.form.get('duration', 'month')
    
    if pack_id not in API_PRICES:
        return jsonify({"error": "Invalid tier scope"}), 400
        
    base_cost = API_PRICES[pack_id]['month'] if duration == 'month' else API_PRICES[pack_id]['three_month']
    gst_calc = (base_cost * GLOBAL_CONFIG['gst_percentage']) / 100
    total_payable = int((base_cost + gst_calc) * 100) 

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
    
    try:
        razorpay_order = client.order.create(data=order_payload)
    except Exception as e:
        return jsonify({"status": "failed", "message": "Failed to negotiate order payload token with Razorpay API.", "details": str(e)}), 400
    
    checkout_script = f"""
    <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
    <script>
        var options = {{
            "key": "{RAZORPAY_KEY_ID}",
            "amount": "{razorpay_order['amount']}",
            "currency": "INR",
            "name": "{DEVELOPER_NAME} Gateway",
            "description": "Subscription Token: {pack_id}",
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
    client = get_razorpay_client()
    if not client:
        return "Gateway verification client driver unavailable.", 503

    param_source = request.args if request.method == 'GET' else request.form
    
    pay_id = param_source.get('payment_id')
    order_id = param_source.get('order_id')
    signature = param_source.get('signature')
    
    if not pay_id or not order_id or not signature:
        return "Missing tracking authorization arguments.", 400

    sig_check_payload = f"{order_id}|{pay_id}"
    generated_signature = hmac.new(
        bytes(RAZORPAY_SECRET, 'utf-8'),
        msg=bytes(sig_check_payload, 'utf-8'),
        digestmod=hashlib.sha256
    ).hexdigest()
    
    if generated_signature != signature:
        return "Signature match failed.", 400

    try:
        order_details = client.order.fetch(order_id)
    except Exception as e:
        return f"Order verification tracking failed: {str(e)}", 400

    notes = order_details.get('notes', {})
    assigned_key = notes.get('custom_key_requested', f"gen_{pay_id[:8]}")
    selected_pack = notes.get('package_scope')
    duration = notes.get('duration_frame')
    
    days_to_add = 30 if duration == 'month' else 90
    expiration_target = (datetime.datetime.now() + datetime.timedelta(days=days_to_add)).strftime("%Y-%m-%d")

    API_KEYS_DB[assigned_key] = {
        "key_name": f"{selected_pack.upper()} Subscription",
        "owner_email": notes.get('purchaser_identity'),
        "expiry_date": expiration_target,
        "expiry_time": "23:59",
        "daily_limit": 2500,
        "current_requests": 0,
        "allowed_tools": [selected_pack]
    }

    alert_text = f"🔥 *NEW SUBSCRIPTION ACTIVE*\n\n👤 *User:* {notes.get('purchaser_identity')}\n🔑 *Key:* `{assigned_key}`\n📦 *Scope:* `{selected_pack}`\n📅 *Expires:* {expiration_target}"
    dispatch_telegram_alert(alert_text)

    return f"<h1>Payment Success! Your access token key `{assigned_key}` is active until {expiration_target}.</h1><a href='/'>Return to Store</a>"

@app.route('/api/<endpoint>', methods=['GET'])
def core_api_proxy_dispatcher(endpoint):
    client_auth_key = request.args.get('key')
    
    if not client_auth_key:
        return jsonify({"status": "failed", "developer": DEVELOPER_NAME, "message": "Missing key parameters."}), 400
        
    is_valid, configuration_metadata = validate_token_access(client_auth_key, endpoint)
    if not is_valid:
        return jsonify({"status": "failed", "developer": DEVELOPER_NAME, "message": configuration_metadata}), 403

    cleaned_forwarding_args = request.args.to_dict()
    if 'key' in cleaned_forwarding_args:
        del cleaned_forwarding_args['key']
    
    cleaned_forwarding_args['key'] = "ftgamer2" 

    try:
        upstream_target_endpoint_url = f"{TARGET_BASE_URL}/{endpoint}"
        upstream_network_response = requests.get(upstream_target_endpoint_url, params=cleaned_forwarding_args, timeout=12)
        
        try:
            json_response_payload = upstream_network_response.json()
            if isinstance(json_response_payload, dict):
                json_response_payload.pop('credits', None)
                json_response_payload.pop('owner', None)
                json_response_payload.pop('telegram', None)
                json_response_payload['developer'] = DEVELOPER_NAME
            return jsonify(json_response_payload), upstream_network_response.status_code
        except ValueError:
            return upstream_network_response.text, upstream_network_response.status_code

    except requests.exceptions.RequestException:
        return jsonify({"status": "failed", "developer": DEVELOPER_NAME, "message": "Upstream timeout infrastructure handshake failure."}), 504

if __name__ == '__main__':
    app.run(debug=True)
