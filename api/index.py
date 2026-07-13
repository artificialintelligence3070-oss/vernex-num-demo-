import os
import json
import hashlib
import random
import string
import datetime
import requests
import razorpay
import sqlite3
import pytz
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from functools import wraps
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "shayan_explorer_secret_2026_vernex_ultimate"

# ======================= CONFIG =======================
RAZORPAY_KEY_ID = "rzp_live_TCc5USt5FlmfrI"
RAZORPAY_KEY_SECRET = "sMwLGQAEQePA0qSOYvFFII1h"
razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

TELEGRAM_BOT_TOKEN = "8378722740:AAH9GthadrXQlTSp8pmPvlUnogXxhHv371s"
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

UPSTREAM_BASE = "https://ft-osint-api.duckdns.org/api"
UPSTREAM_KEY = "ftgamer2"

ADMIN_USERNAME = "vernex"
ADMIN_PASSWORD = "vernex@16vx"
IST = pytz.timezone('Asia/Kolkata')

# ======================= DATABASE =======================
def get_db():
    conn = sqlite3.connect('/tmp/data.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        name TEXT,
        created_at TEXT DEFAULT (datetime('now')))''')
    c.execute('''CREATE TABLE IF NOT EXISTS api_keys (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key_name TEXT UNIQUE NOT NULL,
        user_email TEXT NOT NULL,
        api_names TEXT NOT NULL,
        all_apis BOOLEAN DEFAULT 0,
        daily_limit INTEGER DEFAULT 100,
        total_limit INTEGER DEFAULT 1000,
        requests_made INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')),
        expires_at TEXT NOT NULL,
        is_active BOOLEAN DEFAULT 1)''')
    c.execute('''CREATE TABLE IF NOT EXISTS api_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key_name TEXT NOT NULL,
        user_email TEXT NOT NULL,
        api_called TEXT NOT NULL,
        query_param TEXT,
        response_code INTEGER,
        ip_address TEXT,
        timestamp TEXT DEFAULT (datetime('now')))''')
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id TEXT UNIQUE NOT NULL,
        user_email TEXT NOT NULL,
        package_name TEXT NOT NULL,
        amount INTEGER NOT NULL,
        currency TEXT DEFAULT 'INR',
        payment_id TEXT,
        status TEXT DEFAULT 'pending',
        key_name TEXT,
        created_at TEXT DEFAULT (datetime('now')))''')
    c.execute('''CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        razorpay_payment_id TEXT,
        razorpay_order_id TEXT,
        user_email TEXT,
        amount INTEGER,
        status TEXT,
        timestamp TEXT DEFAULT (datetime('now')))''')
    conn.commit()
    conn.close()

init_db()

# ======================= API LIST =======================
API_LIST = {
    "number": {"name": "📞 Number Lookup", "price_monthly": 100, "price_3months": 250, "endpoint": "/number", "param": "num", "type": "paid"},
    "paytm": {"name": "💳 Paytm Lookup", "price_monthly": 100, "price_3months": 250, "endpoint": "/paytm", "param": "num", "type": "paid"},
    "calltracer": {"name": "📞 Call Tracer", "price_monthly": 100, "price_3months": 250, "endpoint": "/calltracer", "param": "num", "type": "paid"},
    "advance": {"name": "📞 Advance ICMR", "price_monthly": 100, "price_3months": 250, "endpoint": "/adv", "param": "num", "type": "paid"},
    "email": {"name": "📧 Email Leak", "price_monthly": 400, "price_3months": 1100, "endpoint": "/email", "param": "email", "type": "paid"},
    "aadhar": {"name": "🪪 Aadhaar", "price_monthly": 200, "price_3months": 550, "endpoint": "/aadhar", "param": "num", "type": "paid"},
    "adharfamily": {"name": "👨‍👩‍👧‍👦 Aadhaar Family", "price_monthly": 200, "price_3months": 550, "endpoint": "/adharfamily", "param": "num", "type": "paid"},
    "upi": {"name": "💳 UPI Lookup", "price_monthly": 150, "price_3months": 400, "endpoint": "/upi", "param": "upi", "type": "paid"},
    "numtoupi": {"name": "💳 Num to UPI", "price_monthly": 150, "price_3months": 400, "endpoint": "/numtoupi", "param": "num", "type": "paid"},
    "pan": {"name": "🪪 PAN to GST", "price_monthly": 100, "price_3months": 250, "endpoint": "/pan", "param": "pan", "type": "paid"},
    "ifsc": {"name": "🏦 IFSC Lookup", "price_monthly": 50, "price_3months": 120, "endpoint": "/ifsc", "param": "ifsc", "type": "paid"},
    "pincode": {"name": "📍 Pincode", "price_monthly": 30, "price_3months": 80, "endpoint": "/pincode", "param": "pin", "type": "paid"},
    "ip": {"name": "🌐 IP Lookup", "price_monthly": 30, "price_3months": 80, "endpoint": "/ip", "param": "ip", "type": "paid"},
    "vehicle": {"name": "🚘 Vehicle Owner", "price_monthly": 400, "price_3months": 1000, "endpoint": "/vehicle", "param": "vehicle", "type": "paid"},
    "veh2num": {"name": "🚗 Vehicle to Num", "price_monthly": 400, "price_3months": 1000, "endpoint": "/veh2num", "param": "vehicle", "type": "paid"},
    "challan": {"name": "🚘 Challan", "price_monthly": 400, "price_3months": 1000, "endpoint": "/challan", "param": "vehicle", "type": "paid"},
    "freefire": {"name": "🎮 Free Fire", "price_monthly": 80, "price_3months": 200, "endpoint": "/ff", "param": "uid", "type": "paid"},
    "bgmi": {"name": "🎮 BGMI", "price_monthly": 80, "price_3months": 200, "endpoint": "/bgmi", "param": "uid", "type": "paid"},
    "snapchat": {"name": "👻 Snapchat", "price_monthly": 80, "price_3months": 200, "endpoint": "/snap", "param": "username", "type": "paid"},
    "bomber": {"name": "💣 SMS Bomber", "price_monthly": 150, "price_3months": 400, "endpoint": "/bomber", "param": "number", "type": "paid"},
    "pk": {"name": "🇵🇰 Pakistan Num", "price_monthly": 100, "price_3months": 250, "endpoint": "/pk", "param": "num", "type": "paid"},
    "name": {"name": "🔍 Name Lookup", "price_monthly": 400, "price_3months": 1100, "endpoint": "/name", "param": "name", "type": "paid"},
    "instagram": {"name": "📸 Instagram", "price_monthly": 0, "price_3months": 0, "endpoint": "/insta", "param": "username", "type": "free"},
    "github": {"name": "🐙 GitHub", "price_monthly": 0, "price_3months": 0, "endpoint": "/git", "param": "username", "type": "free"},
    "tg": {"name": "✈️ TG Username→Num", "price_monthly": 0, "price_3months": 0, "endpoint": "/tg", "param": "info", "type": "free"},
    "tgidinfo": {"name": "🆔 TG ID Info", "price_monthly": 0, "price_3months": 0, "endpoint": "/tgidinfo", "param": "id", "type": "free"},
    "imei": {"name": "📱 IMEI Lookup", "price_monthly": 100, "price_3months": 250, "endpoint": "/imei", "param": "imei", "type": "paid"},
    "numleak": {"name": "📢 Number Leak", "price_monthly": 100, "price_3months": 250, "endpoint": "/numleak", "param": "num", "type": "paid"},
}

BUNDLES = {
    "starter": {"name": "🔥 Starter Pack", "price_monthly": 500, "price_3months": 1300,
        "apis": ["number","paytm","calltracer","advance","aadhar","adharfamily","upi","numtoupi","pan","ifsc","pincode","ip","freefire","bgmi"]},
    "pro": {"name": "💎 Pro Pack", "price_monthly": 1200, "price_3months": 3000, "apis": "all_except_vehicle"},
    "ultimate": {"name": "👑 Ultimate Pack", "price_monthly": 1600, "price_3months": 4200, "apis": "all"}
}

# ======================= HELPERS =======================
def generate_key():
    return "KEY" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def send_telegram(msg):
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        try:
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=3)
        except: pass

# ======================= ROUTES =======================

@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET','POST'])
def login():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form.get('email','').strip()
        password = request.form.get('password','')
        if email == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['user'] = ADMIN_USERNAME
            session['email'] = "admin@vernex.com"
            session['name'] = "Admin"
            flash('Welcome Admin!','success')
            return redirect(url_for('admin_dashboard'))
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email=?",(email,)).fetchone()
        conn.close()
        if user and user['password'] == hashlib.sha256(password.encode()).hexdigest():
            session['user'] = email
            session['email'] = email
            session['name'] = user['name'] or email.split('@')[0]
            flash('Login successful!','success')
            return redirect(url_for('dashboard'))
        flash('Invalid credentials!','error')
    return render_template('login.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form.get('email','').strip()
        password = request.form.get('password','')
        name = request.form.get('name','').strip()
        if not email or not password:
            flash('Email and password required!','error')
            return render_template('register.html')
        conn = get_db()
        if conn.execute("SELECT id FROM users WHERE email=?",(email,)).fetchone():
            flash('Email already registered!','error')
            conn.close()
            return render_template('register.html')
        conn.execute("INSERT INTO users (email,password,name) VALUES (?,?,?)",
            (email,hashlib.sha256(password.encode()).hexdigest(),name or email.split('@')[0]))
        conn.commit()
        conn.close()
        flash('Registration successful! Please login.','success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out!','info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    email = session.get('email', session.get('user'))
    conn = get_db()
    keys = conn.execute("SELECT * FROM api_keys WHERE user_email=? ORDER BY created_at DESC",(email,)).fetchall()
    logs = conn.execute("SELECT * FROM api_logs WHERE user_email=? ORDER BY timestamp DESC LIMIT 10",(email,)).fetchall()
    conn.close()
    return render_template('dashboard.html', keys=keys, logs=logs, api_list=API_LIST, bundles=BUNDLES)

@app.route('/pricing')
@login_required
def pricing():
    return render_template('pricing.html', api_list=API_LIST, bundles=BUNDLES)

@app.route('/checkout', methods=['GET','POST'])
@login_required
def checkout():
    if request.method == 'POST':
        ptype = request.form.get('package_type','')
        pid = request.form.get('package_id','')
        dur = request.form.get('duration','monthly')
        kname = request.form.get('key_name','') or generate_key()
        days = 30 if dur == 'monthly' else 90
        
        amount = 0
        if ptype == 'bundle':
            b = BUNDLES.get(pid)
            if b: amount = b[f'price_{dur}']
        else:
            a = API_LIST.get(pid)
            if a: amount = a[f'price_{dur}']
        
        if amount <= 0:
            flash('Invalid package!','error')
            return redirect(url_for('pricing'))
        
        try:
            order = razorpay_client.order.create({
                'amount': amount*100, 'currency': 'INR',
                'receipt': f'receipt_{kname}_{datetime.now().timestamp()}',
                'notes': {'user_email': session.get('email'), 'package': pid, 'key_name': kname, 'duration': dur}
            })
            conn = get_db()
            conn.execute("INSERT INTO orders (order_id,user_email,package_name,amount,currency,key_name) VALUES (?,?,?,?,?,?)",
                (order['id'], session.get('email'), f"{ptype}_{pid}", amount, 'INR', kname))
            conn.commit()
            conn.close()
            return render_template('checkout.html', order=order, razorpay_key=RAZORPAY_KEY_ID,
                amount=amount, key_name=kname, duration=dur, package_id=pid, package_type=ptype)
        except Exception as e:
            flash(f'Payment error: {str(e)}','error')
            return redirect(url_for('pricing'))
    return redirect(url_for('pricing'))

@app.route('/payment-success', methods=['POST'])
@login_required
def payment_success():
    pid = request.form.get('razorpay_payment_id')
    oid = request.form.get('razorpay_order_id')
    sig = request.form.get('razorpay_signature')
    kname = request.form.get('key_name', generate_key())
    pkg_id = request.form.get('package_id','')
    ptype = request.form.get('package_type','single')
    dur = request.form.get('duration','monthly')
    email = session.get('email')
    
    try:
        razorpay_client.utility.verify_payment_signature({
            'razorpay_order_id': oid, 'razorpay_payment_id': pid, 'razorpay_signature': sig
        })
    except:
        flash('Payment verification failed!','error')
        return redirect(url_for('dashboard'))
    
    apis = []
    all_apis = False
    if ptype == 'bundle':
        b = BUNDLES.get(pkg_id)
        if b:
            if b['apis'] == 'all': all_apis = True; apis = list(API_LIST.keys())
            elif b['apis'] == 'all_except_vehicle': apis = [k for k in API_LIST if k not in ['vehicle','veh2num','challan']]
            else: apis = b['apis']
    else:
        apis = [pkg_id]
    
    days = 30 if dur == 'monthly' else 90
    expires = (datetime.now(IST) + timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
    daily_limit = 1000 if all_apis else 100
    total_limit = 10000 if all_apis else 1000
    
    conn = get_db()
    try:
        conn.execute("""INSERT INTO api_keys (key_name,user_email,api_names,all_apis,daily_limit,total_limit,requests_made,expires_at,is_active)
            VALUES (?,?,?,?,?,?,0,?,1)""", (kname, email, json.dumps(apis), 1 if all_apis else 0, daily_limit, total_limit, expires))
        conn.execute("UPDATE orders SET payment_id=?, status='completed' WHERE order_id=?", (pid, oid))
        conn.execute("INSERT INTO payments (razorpay_payment_id,razorpay_order_id,user_email,amount,status) VALUES (?,?,?,?,'completed')",
            (pid, oid, email, 0))
        conn.commit()
        send_telegram(f"✅ <b>New Purchase!</b>\n👤 {email}\n🔑 {kname}\n📦 {pkg_id} ({dur})\n📅 Exp: {expires}\n💳 {pid}")
        flash(f'🎉 Payment successful! Your key: <strong>{kname}</strong>','success')
    except Exception as e:
        flash(f'Error: {str(e)}','error')
    finally:
        conn.close()
    return redirect(url_for('mykeys'))

@app.route('/my-keys')
@login_required
def mykeys():
    email = session.get('email', session.get('user'))
    conn = get_db()
    keys = conn.execute("SELECT * FROM api_keys WHERE user_email=? ORDER BY created_at DESC",(email,)).fetchall()
    conn.close()
    return render_template('mykeys.html', keys=keys)

@app.route('/logs')
@login_required
def logs():
    email = session.get('email', session.get('user'))
    conn = get_db()
    logs = conn.execute("SELECT * FROM api_logs WHERE user_email=? ORDER BY timestamp DESC LIMIT 100",(email,)).fetchall()
    conn.close()
    return render_template('logs.html', logs=logs)

@app.route('/mailbox')
@login_required
def mailbox():
    email = session.get('email', session.get('user'))
    conn = get_db()
    keys = conn.execute("SELECT * FROM api_keys WHERE user_email=? ORDER BY created_at DESC",(email,)).fetchall()
    conn.close()
    return render_template('mailbox.html', keys=keys)

@app.route('/api/v1/<api_name>', methods=['GET'])
def api_gateway(api_name):
    kname = request.args.get('key','')
    if not kname:
        return jsonify({"error":"API key required","status":"error"}), 401
    conn = get_db()
    ak = conn.execute("SELECT * FROM api_keys WHERE key_name=? AND is_active=1",(kname,)).fetchone()
    if not ak:
        conn.close()
        return jsonify({"error":"Invalid API key","status":"error"}), 403
    if datetime.now(IST) > datetime.strptime(ak['expires_at'],'%Y-%m-%d %H:%M:%S').replace(tzinfo=IST):
        conn.execute("UPDATE api_keys SET is_active=0 WHERE key_name=?",(kname,))
        conn.commit()
        conn.close()
        return jsonify({"error":"Key expired","status":"error"}), 403
    if ak['requests_made'] >= ak['total_limit']:
        conn.close()
        return jsonify({"error":"Request limit exhausted","status":"error"}), 429
    today = datetime.now(IST).strftime('%Y-%m-%d')
    daily = conn.execute("SELECT COUNT(*) as c FROM api_logs WHERE key_name=? AND timestamp LIKE ?",(kname,f"{today}%")).fetchone()
    if daily and daily['c'] >= ak['daily_limit']:
        conn.close()
        return jsonify({"error":"Daily limit exhausted","status":"error"}), 429
    allowed = json.loads(ak['api_names'])
    if api_name not in allowed and not ak['all_apis']:
        conn.close()
        return jsonify({"error":f"API '{api_name}' not in your plan","status":"error"}), 403
    ac = API_LIST.get(api_name)
    if not ac:
        conn.close()
        return jsonify({"error":"Unknown API","status":"error"}), 404
    pname = ac['param']
    pval = request.args.get(pname,'')
    if not pval:
        conn.close()
        return jsonify({"error":f"Missing param: {pname}","status":"error"}), 400
    url = f"{UPSTREAM_BASE}{ac['endpoint']}?key={UPSTREAM_KEY}&{pname}={pval}"
    if api_name == 'bomber':
        url += f"&counter={request.args.get('counter','100')}"
    try:
        resp = requests.get(url, timeout=30)
        data = resp.json() if 'application/json' in resp.headers.get('content-type','') else resp.text
        conn.execute("INSERT INTO api_logs (key_name,user_email,api_called,query_param,response_code,ip_address) VALUES (?,?,?,?,?,?)",
            (kname, ak['user_email'], api_name, f"{pname}={pval}", resp.status_code, request.remote_addr or '0.0.0.0'))
        conn.execute("UPDATE api_keys SET requests_made=requests_made+1 WHERE key_name=?",(kname,))
        conn.commit()
        conn.close()
        return jsonify({"status":"success","data":data,"key_info":{"key_name":kname,"used":ak['requests_made']+1,"limit":ak['total_limit'],"expires":ak['expires_at']}})
    except Exception as e:
        conn.close()
        return jsonify({"error":f"Upstream error: {str(e)}","status":"error"}), 502

@app.route('/admin')
@login_required
def admin_dashboard():
    if session.get('user') != ADMIN_USERNAME:
        flash('Admin only!','error')
        return redirect(url_for('dashboard'))
    conn = get_db()
    users = conn.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    keys = conn.execute("SELECT * FROM api_keys ORDER BY created_at DESC").fetchall()
    logs = conn.execute("SELECT * FROM api_logs ORDER BY timestamp DESC LIMIT 50").fetchall()
    orders = conn.execute("SELECT * FROM orders ORDER BY created_at DESC").fetchall()
    payments = conn.execute("SELECT * FROM payments ORDER BY timestamp DESC LIMIT 20").fetchall()
    stats = {
        'total_users': conn.execute("SELECT COUNT(*) as c FROM users").fetchone()['c'],
        'total_keys': conn.execute("SELECT COUNT(*) as c FROM api_keys").fetchone()['c'],
        'active_keys': conn.execute("SELECT COUNT(*) as c FROM api_keys WHERE is_active=1").fetchone()['c'],
        'total_requests': conn.execute("SELECT COUNT(*) as c FROM api_logs").fetchone()['c'],
        'total_revenue': conn.execute("SELECT SUM(amount) as s FROM orders WHERE status='completed'").fetchone()['s'] or 0,
    }
    conn.close()
    return render_template('admin.html', users=users, keys=keys, logs=logs, orders=orders, payments=payments, stats=stats, api_list=API_LIST)

@app.route('/admin/create-key', methods=['POST'])
@login_required
def admin_create_key():
    if session.get('user') != ADMIN_USERNAME:
        return jsonify({"error":"Unauthorized"}), 403
    kname = request.form.get('key_name','') or generate_key()
    uemail = request.form.get('user_email','')
    anames = request.form.get('api_names','all')
    dlim = int(request.form.get('daily_limit',1000))
    tlim = int(request.form.get('total_limit',10000))
    exp = request.form.get('expires_at',(datetime.now(IST)+timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S'))
    if anames == 'all':
        all_apis = True
        apilist = list(API_LIST.keys())
    else:
        all_apis = False
        apilist = anames.split(',')
    conn = get_db()
    try:
        conn.execute("INSERT INTO api_keys (key_name,user_email,api_names,all_apis,daily_limit,total_limit,expires_at) VALUES (?,?,?,?,?,?,?)",
            (kname, uemail, json.dumps(apilist), 1 if all_apis else 0, dlim, tlim, exp))
        conn.commit()
        flash(f'Key {kname} created!','success')
    except Exception as e:
        flash(f'Error: {str(e)}','error')
    finally:
        conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/toggle-key/<key_name>')
@login_required
def admin_toggle_key(key_name):
    if session.get('user') != ADMIN_USERNAME:
        return jsonify({"error":"Unauthorized"}), 403
    conn = get_db()
    k = conn.execute("SELECT * FROM api_keys WHERE key_name=?",(key_name,)).fetchone()
    if k:
        ns = 0 if k['is_active'] else 1
        conn.execute("UPDATE api_keys SET is_active=? WHERE key_name=?",(ns,key_name))
        conn.commit()
        flash(f'Key {"activated" if ns else "deactivated"}!','success')
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete-key/<key_name>')
@login_required
def admin_delete_key(key_name):
    if session.get('user') != ADMIN_USERNAME:
        return jsonify({"error":"Unauthorized"}), 403
    conn = get_db()
    conn.execute("DELETE FROM api_keys WHERE key_name=?",(key_name,))
    conn.commit()
    conn.close()
    flash(f'Key deleted!','info')
    return redirect(url_for('admin_dashboard'))

@app.route('/health')
def health():
    return jsonify({"status":"ok","developer":"SHAYAN_EXPLORER","version":"2.0.0"})

# ======================= TEMPLATES (inline) =======================

@app.route('/templates/<name>')
def serve_template(name):
    templates = {
        'login.html': '''<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Login - VERNEX API</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"><link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css"><link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Poppins:wght@300;400;600;700;900&display=swap" rel="stylesheet"><style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:'Poppins',sans-serif;background:#0a0a1a;color:#fff;overflow-x:hidden;min-height:100vh;display:flex;align-items:center;justify-content:center}#bg-canvas{position:fixed;top:0;left:0;width:100%;height:100%;z-index:0;pointer-events:none}.glass-card{background:rgba(255,255,255,0.03);backdrop-filter:blur(20px);border:1px solid rgba(255,255,255,0.05);border-radius:20px;padding:40px;transition:all .3s;position:relative;z-index:1;width:100%;max-width:450px}.glass-card:hover{border-color:rgba(0,245,255,0.2);box-shadow:0 0 40px rgba(0,245,255,0.05)}.section-title{font-family:'Orbitron',monospace;font-weight:700;background:linear-gradient(135deg,#00f5ff,#7b2ff7);-webkit-background-clip:text;-webkit-text-fill-color:transparent}.btn-glow{background:linear-gradient(135deg,#00f5ff,#7b2ff7);border:none;color:#fff;font-weight:600;padding:12px 30px;border-radius:50px;transition:all .3s;box-shadow:0 0 30px rgba(0,245,255,0.2)}.btn-glow:hover{transform:translateY(-2px);box-shadow:0 0 50px rgba(0,245,255,0.4);color:#fff}.form-control{background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);color:#fff;border-radius:12px;padding:12px 15px}.form-control:focus{border-color:#00f5ff;box-shadow:0 0 20px rgba(0,245,255,0.1)}.input-group-text{background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);color:#00f5ff;border-radius:12px 0 0 12px}.particle{position:fixed;width:4px;height:4px;background:#00f5ff;border-radius:50%;pointer-events:none;animation:float linear infinite;opacity:0.3}@keyframes float{0%{transform:translateY(100vh) rotate(0deg);opacity:0}10%{opacity:0.5}90%{opacity:0.5}100%{transform:translateY(-100vh) rotate(720deg);opacity:0}}</style></head><body><canvas id="bg-canvas"></canvas>''' + ''.join([f'<div class="particle" style="left:{random.randint(0,100)}%;animation-duration:{random.randint(15,35)}s;animation-delay:{random.randint(0,10)}s;width:{random.randint(2,6)}px;height:{random.randint(2,6)}px"></div>' for _ in range(20)]) + '''
<div class="container"><div class="row justify-content-center"><div class="col-md-5">
<div class="glass-card text-center"><div class="mb-4"><i class="bi bi-shield-shaded" style="font-size:4rem;color:#00f5ff"></i></div>
<h2 class="section-title">Welcome Back</h2><p class="text-muted mb-4">Login to VERNEX API</p>
<form method="POST" action="/login"><div class="mb-3"><div class="input-group"><span class="input-group-text"><i class="bi bi-person"></i></span>
<input type="text" name="email" class="form-control" placeholder="Email or Username" required></div></div>
<div class="mb-4"><div class="input-group"><span class="input-group-text"><i class="bi bi-lock"></i></span>
<input type="password" name="password" class="form-control" placeholder="Password" required></div></div>
<button type="submit" class="btn btn-glow w-100"><i class="bi bi-box-arrow-in-right me-2"></i> Login</button></form>
<p class="mt-4 text-muted">No account? <a href="/register" style="color:#00f5ff;text-decoration:none;">Register</a></p>
<p class="mt-2" style="font-size:0.8rem;color:rgba(255,255,255,0.3)">Developed by <span style="color:#00f5ff">SHAYAN_EXPLORER</span></p></div></div></div></div>
<script>const c=document.getElementById('bg-canvas'),ctx=c.getContext('2d');c.width=innerWidth;c.height=innerHeight;
const ps=[];class P{constructor(){this.reset()}reset(){this.x=Math.random()*c.width;this.y=Math.random()*c.height;this.z=Math.random()*1000;this.size=Math.random()*2+0.5;this.speed=Math.random()*2+0.5;this.color=Math.random()>0.5?'#00f5ff':'#7b2ff7'}
update(){this.z-=this.speed;if(this.z<=0)this.reset()}draw(){const s=500/this.z,x=(this.x-c.width/2)*s+c.width/2,y=(this.y-c.height/2)*s+c.height/2,sz=this.size*s;if(x<0||x>c.width||y<0||y>c.height)return;const op=Math.min(1,(500-this.z)/500);ctx.beginPath();ctx.arc(x,y,sz,0,Math.PI*2);ctx.fillStyle=this.color;ctx.globalAlpha=op*0.4;ctx.fill();ctx.shadowBlur=20;ctx.shadowColor=this.color}}
for(let i=0;i<80;i++)ps.push(new P());function a(){ctx.clearRect(0,0,c.width,c.height);ps.forEach(p=>{p.update();p.draw()});requestAnimationFrame(a)}a();
window.addEventListener('resize',()=>{c.width=innerWidth;c.height=innerHeight});</script></body></html>''',

        'register.html': '''<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Register - VERNEX API</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"><link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css"><link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Poppins:wght@300;400;600;700;900&display=swap" rel="stylesheet"><style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:'Poppins',sans-serif;background:#0a0a1a;color:#fff;overflow-x:hidden;min-height:100vh;display:flex;align-items:center;justify-content:center}#bg-canvas{position:fixed;top:0;left:0;width:100%;height:100%;z-index:0;pointer-events:none}.glass-card{background:rgba(255,255,255,0.03);backdrop-filter:blur(20px);border:1px solid rgba(255,255,255,0.05);border-radius:20px;padding:40px;transition:all .3s;position:relative;z-index:1;width:100%;max-width:450px}.section-title{font-family:'Orbitron',monospace;font-weight:700;background:linear-gradient(135deg,#00f5ff,#7b2ff7);-webkit-background-clip:text;-webkit-text-fill-color:transparent}.btn-glow{background:linear-gradient(135deg,#00f5ff,#7b2ff7);border:none;color:#fff;font-weight:600;padding:12px 30px;border-radius:50px;transition:all .3s;box-shadow:0 0 30px rgba(0,245,255,0.2)}.btn-glow:hover{transform:translateY(-2px);box-shadow:0 0 50px rgba(0,245,255,0.4);color:#fff}.form-control{background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);color:#fff;border-radius:12px;padding:12px 15px}.form-control:focus{border-color:#00f5ff;box-shadow:0 0 20px rgba(0,245,255,0.1)}.input-group-text{background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);color:#7b2ff7;border-radius:12px 0 0 12px}</style></head><body><canvas id="bg-canvas"></canvas>
<div class="container"><div class="row justify-content-center"><div class="col-md-5">
<div class="glass-card text-center"><div class="mb-4"><i class="bi bi-person-plus-fill" style="font-size:4rem;color:#7b2ff7"></i></div>
<h2 class="section-title">Create Account</h2><p class="text-muted mb-4">Join VERNEX API Platform</p>
<form method="POST" action="/register"><div class="mb-3"><div class="input-group"><span class="input-group-text"><i class="bi bi-person"></i></span>
<input type="text" name="name" class="form-control" placeholder="Full Name"></div></div>
<div class="mb-3"><div class="input-group"><span class="input-group-text"><i class="bi bi-envelope"></i></span>
<input type="email" name="email" class="form-control" placeholder="Email Address" required></div></div>
<div class="mb-4"><div class="input-group"><span class="input-group-text"><i class="bi bi-lock"></i></span>
<input type="password" name="password" class="form-control" placeholder="Password" required></div></div>
<button type="submit" class="btn btn-glow w-100"><i class="bi bi-person-plus me-2"></i> Register</button></form>
<p class="mt-4 text-muted">Already have an account? <a href="/login" style="color:#00f5ff;text-decoration:none;">Login</a></p></div></div></div></div></body></html>''',

        'dashboard.html': f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Dashboard - VERNEX API</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"><link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css"><link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Poppins:wght@300;400;600;700;900&display=swap" rel="stylesheet"><style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:'Poppins',sans-serif;background:#0a0a1a;color:#fff;overflow-x:hidden}}#bg-canvas{{position:fixed;top:0;left:0;width:100%;height:100%;z-index:0;pointer-events:none}}.navbar{{background:rgba(10,10,30,0.95);backdrop-filter:blur(20px);border-bottom:1px solid rgba(0,255,255,0.1);z-index:1000}}.navbar-brand{{font-family:'Orbitron',monospace;font-weight:900;font-size:1.5rem;background:linear-gradient(135deg,#00f5ff,#7b2ff7);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}.navbar-brand span{{-webkit-text-fill-color:#fff;background:none}}.nav-link{{color:rgba(255,255,255,0.7)!important;transition:all .3s}}.nav-link:hover,.nav-link.active{{color:#00f5ff!important;text-shadow:0 0 20px rgba(0,245,255,0.5)}}.content-wrapper{{position:relative;z-index:1;padding-top:80px;min-height:100vh}}.glass-card{{background:rgba(255,255,255,0.03);backdrop-filter:blur(20px);border:1px solid rgba(255,255,255,0.05);border-radius:20px;padding:30px;transition:all .3s}}.glass-card:hover{{border-color:rgba(0,245,255,0.2);box-shadow:0 0 40px rgba(0,245,255,0.05);transform:translateY(-5px)}}.section-title{{font-family:'Orbitron',monospace;font-weight:700;background:linear-gradient(135deg,#00f5ff,#7b2ff7);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}.btn-glow{{background:linear-gradient(135deg,#00f5ff,#7b2ff7);border:none;color:#fff;font-weight:600;padding:10px 30px;border-radius:50px;transition:all .3s;box-shadow:0 0 30px rgba(0,245,255,0.2)}}.btn-glow:hover{{transform:translateY(-2px);box-shadow:0 0 50px rgba(0,245,255,0.4);color:#fff}}.btn-outline-glow{{background:transparent;border:1px solid rgba(0,245,255,0.3);color:#00f5ff;font-weight:600;padding:10px 30px;border-radius:50px;transition:all .3s}}.btn-outline-glow:hover{{background:rgba(0,245,255,0.1);color:#00f5ff}}.table{{--bs-table-bg:transparent;color:#fff;border-color:rgba(255,255,255,0.05)}}code{{background:rgba(0,245,255,0.1);color:#00f5ff;padding:4px 8px;border-radius:5px}}footer{{background:rgba(10,10,30,0.95);border-top:1px solid rgba(0,255,255,0.05);padding:20px 0;text-align:center;position:relative;z-index:1;color:rgba(255,255,255,0.4)}}::-webkit-scrollbar{{width:6px}}::-webkit-scrollbar-track{{background:#0a0a1a}}::-webkit-scrollbar-thumb{{background:linear-gradient(135deg,#00f5ff,#7b2ff7);border-radius:3px}}</style></head><body><canvas id="bg-canvas"></canvas>
<nav class="navbar navbar-expand-lg navbar-dark fixed-top"><div class="container"><a class="navbar-brand" href="/dashboard"><i class="bi bi-shield-shaded me-2"></i>VERNEX<span>API</span></a>
<button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#nav"><span class="navbar-toggler-icon"></span></button>
<div class="collapse navbar-collapse" id="nav"><ul class="navbar-nav ms-auto align-items-center gap-2">
<li class="nav-item"><a class="nav-link active" href="/dashboard"><i class="bi bi-speedometer2 me-1"></i> Dashboard</a></li>
<li class="nav-item"><a class="nav-link" href="/pricing"><i class="bi bi-cart3 me-1"></i> Pricing</a></li>
<li class="nav-item"><a class="nav-link" href="/my-keys"><i class="bi bi-key me-1"></i> My Keys</a></li>
<li class="nav-item"><a class="nav-link" href="/mailbox"><i class="bi bi-envelope me-1"></i> Mailbox</a></li>
<li class="nav-item"><a class="nav-link" href="/logs"><i class="bi bi-clock-history me-1"></i> Logs</a></li>
<li class="nav-item ms-2"><span class="text-muted small me-2"><i class="bi bi-person-circle me-1"></i>{{session.get("name",session.get("user"))}}</span>
<a href="/logout" class="btn btn-outline-glow btn-sm"><i class="bi bi-box-arrow-right"></i></a></li></ul></div></div></nav>
<div class="content-wrapper"><div class="container mt-4">
{{get_flashed_messages_html()|safe}}
<div class="glass-card mb-4"><div class="d-flex justify-content-between align-items-center"><div><h2 class="section-title mb-1">Welcome, {session.get("name","User")}! 👋</h2><p class="text-muted mb-0">Manage your API keys, monitor usage, and purchase new plans</p></div>
<a href="/pricing" class="btn btn-glow"><i class="bi bi-cart-plus me-2"></i>Buy API Keys</a></div></div>
<div class="row mb-4"><div class="col-md-4 mb-3"><div class="glass-card text-center"><i class="bi bi-key" style="font-size:2.5rem;color:#00f5ff"></i><h3 class="mt-2">{len(keys)}</h3><p class="text-muted mb-0">Active Keys</p></div></div>
<div class="col-md-4 mb-3"><div class="glass-card text-center"><i class="bi bi-arrow-repeat" style="font-size:2.5rem;color:#7b2ff7"></i><h3 class="mt-2">{len(logs)}</h3><p class="text-muted mb-0">Recent Requests</p></div></div>
<div class="col-md-4 mb-3"><div class="glass-card text-center"><i class="bi bi-credit-card" style="font-size:2.5rem;color:#00ff88"></i><h3 class="mt-2">{sum(k["requests_made"] for k in keys)}</h3><p class="text-muted mb-0">Total API Calls</p></div></div></div>
<div class="glass-card mb-4"><h3 class="section-title"><i class="bi bi-key me-2"></i>Your API Keys</h3>
{f'''<div class="table-responsive"><table class="table table-dark table-hover"><thead><tr><th>Key Name</th><th>APIs</th><th>Usage</th><th>Expires</th><th>Status</th></tr></thead><tbody>
{"".join(f'<tr><td><code>{k["key_name"]}</code></td><td>{"All APIs" if k["all_apis"] else f"{len(json.loads(k["api_names"]))} APIs"}</td><td><div class="d-flex align-items-center"><div class="progress flex-grow-1 me-2" style="height:6px;background:rgba(255,255,255,0.1)"><div class="progress-bar bg-info" style="width:{round(k["requests_made"]/k["total_limit"]*100)}%"></div></div><small>{k["requests_made"]}/{k["total_limit"]}</small></div></td><td><span class="{"text-success" if k["expires_at"] > datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S") else "text-danger"}">{k["expires_at"]}</span></td><td><span class="badge bg-{"success" if k["is_active"] else "danger"}">{"Active" if k["is_active"] else "Inactive"}</span></td></tr>' for k in keys)}
</tbody></table></div>' if keys else '<div class="text-center py-5"><i class="bi bi-key" style="font-size:3rem;color:rgba(255,255,255,0.1)"></i><p class="mt-2 text-muted">No API keys yet. <a href="/pricing" style="color:#00f5ff">Purchase your first key</a></p></div>'}
</div></div></div>
<footer><div class="container"><p class="mb-0">© 2026 <strong>VERNEX API</strong> — Developed by <span style="color:#00f5ff">SHAYAN_EXPLORER</span></p></div></footer>
<script>const c=document.getElementById('bg-canvas'),ctx=c.getContext('2d');c.width=innerWidth;c.height=innerHeight;
const ps=[];class P{constructor(){this.reset()}reset(){this.x=Math.random()*c.width;this.y=Math.random()*c.height;this.z=Math.random()*1000;this.size=Math.random()*2+0.5;this.speed=Math.random()*2+0.5;this.color=Math.random()>0.5?'#00f5ff':'#7b2ff7'}
update(){this.z-=this.speed;if(this.z<=0)this.reset()}draw(){const s=500/this.z,x=(this.x-c.width/2)*s+c.width/2,y=(this.y-c.height/2)*s+c.height/2,sz=this.size*s;if(x<0||x>c.width||y<0||y>c.height)return;const op=Math.min(1,(500-this.z)/500);ctx.beginPath();ctx.arc(x,y,sz,0,Math.PI*2);ctx.fillStyle=this.color;ctx.globalAlpha=op*0.4;ctx.fill();ctx.shadowBlur=20;ctx.shadowColor=this.color}}
for(let i=0;i<80;i++)ps.push(new P());function a(){ctx.clearRect(0,0,c.width,c.height);ps.forEach(p=>{p.update();p.draw()});requestAnimationFrame(a)}a();
window.addEventListener('resize',()=>{c.width=innerWidth;c.height=innerHeight});</script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script></body></html>'''
    }
    if name in templates:
        return templates[name]
    return "<h1>Not Found</h1>"

# Replace render_template
def render_template(name, **kwargs):
    return serve_template(name)

# Flash messages helper
def get_flashed_messages_html():
    import flask
    msgs = flask.get_flashed_messages(with_categories=True)
    if not msgs: return ''
    html = ''
    for cat, msg in msgs:
        cls = {'success':'alert-success','error':'alert-danger','info':'alert-info','warning':'alert-warning'}.get(cat,'alert-info')
        html += f'<div class="alert {cls} alert-dismissible fade show" role="alert">{msg}<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>'
    return html

# Override flask render_template
import flask
flask.render_template = render_template
flask.get_flashed_messages_html = get_flashed_messages_html

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
