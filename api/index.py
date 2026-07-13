import os
import json
import hashlib
import random
import string
import requests
import razorpay
import sqlite3
import pytz
from flask import Flask, request, redirect, url_for, session, jsonify, flash, get_flashed_messages, render_template_string
from functools import wraps
from datetime import datetime, timedelta

# ======================= INIT APP =======================
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

def render_page(title, content, show_nav=True):
    """Render a full page with consistent design"""
    user_name = session.get('name', session.get('user', ''))
    
    nav = ''
    if show_nav and 'user' in session:
        admin_link = ''
        if session.get('user') == ADMIN_USERNAME:
            admin_link = f'<li class="nav-item"><a class="nav-link text-danger" href="/admin"><i class="bi bi-shield-lock me-1"></i> Admin</a></li>'
        
        nav = f'''<nav class="navbar navbar-expand-lg navbar-dark fixed-top"><div class="container">
        <a class="navbar-brand" href="/dashboard"><i class="bi bi-shield-shaded me-2"></i>VERNEX<span>API</span></a>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#nav"><span class="navbar-toggler-icon"></span></button>
        <div class="collapse navbar-collapse" id="nav"><ul class="navbar-nav ms-auto align-items-center gap-2">
        <li class="nav-item"><a class="nav-link" href="/dashboard"><i class="bi bi-speedometer2 me-1"></i> Dashboard</a></li>
        <li class="nav-item"><a class="nav-link" href="/pricing"><i class="bi bi-cart3 me-1"></i> Pricing</a></li>
        <li class="nav-item"><a class="nav-link" href="/my-keys"><i class="bi bi-key me-1"></i> My Keys</a></li>
        <li class="nav-item"><a class="nav-link" href="/mailbox"><i class="bi bi-envelope me-1"></i> Mailbox</a></li>
        <li class="nav-item"><a class="nav-link" href="/logs"><i class="bi bi-clock-history me-1"></i> Logs</a></li>
        {admin_link}
        <li class="nav-item ms-2"><span class="text-muted small me-2"><i class="bi bi-person-circle me-1"></i>{user_name}</span>
        <a href="/logout" class="btn btn-outline-glow btn-sm"><i class="bi bi-box-arrow-right"></i></a></li></ul></div></div></nav>'''
    
    flash_msgs = ''
    for cat, msg in get_flashed_messages(with_categories=True):
        cls_map = {'success':'alert-success','error':'alert-danger','info':'alert-info','warning':'alert-warning'}
        flash_msgs += f'<div class="alert {cls_map.get(cat,"alert-info")} alert-dismissible fade show" role="alert">{msg}<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>'
    
    particles = ''.join([f'<div class="particle" style="left:{random.randint(0,100)}%;animation-duration:{random.randint(15,35)}s;animation-delay:{random.randint(0,10)}s"></div>' for _ in range(20)])
    
    return f'''<!DOCTYPE html><html lang="en"><head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>{title} - VERNEX API</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Poppins:wght@300;400;600;700;900&display=swap" rel="stylesheet">
    <style>
    *{{margin:0;padding:0;box-sizing:border-box}}
    body{{font-family:'Poppins',sans-serif;background:#0a0a1a;color:#fff;overflow-x:hidden}}
    #bg-canvas{{position:fixed;top:0;left:0;width:100%;height:100%;z-index:0;pointer-events:none}}
    .navbar{{background:rgba(10,10,30,0.95);backdrop-filter:blur(20px);border-bottom:1px solid rgba(0,255,255,0.1);z-index:1000}}
    .navbar-brand{{font-family:'Orbitron',monospace;font-weight:900;font-size:1.5rem;background:linear-gradient(135deg,#00f5ff,#7b2ff7);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
    .navbar-brand span{{-webkit-text-fill-color:#fff;background:none}}
    .nav-link{{color:rgba(255,255,255,0.7)!important;transition:all .3s}}
    .nav-link:hover,.nav-link.active{{color:#00f5ff!important;text-shadow:0 0 20px rgba(0,245,255,0.5)}}
    .content-wrapper{{position:relative;z-index:1;padding-top:80px;min-height:100vh}}
    .glass-card{{background:rgba(255,255,255,0.03);backdrop-filter:blur(20px);border:1px solid rgba(255,255,255,0.05);border-radius:20px;padding:30px;transition:all .3s;animation:fadeInUp 0.6s ease-out}}
    .glass-card:hover{{border-color:rgba(0,245,255,0.2);box-shadow:0 0 40px rgba(0,245,255,0.05);transform:translateY(-5px)}}
    .section-title{{font-family:'Orbitron',monospace;font-weight:700;background:linear-gradient(135deg,#00f5ff,#7b2ff7);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:30px}}
    .btn-glow{{background:linear-gradient(135deg,#00f5ff,#7b2ff7);border:none;color:#fff;font-weight:600;padding:12px 30px;border-radius:50px;transition:all .3s;box-shadow:0 0 30px rgba(0,245,255,0.2)}}
    .btn-glow:hover{{transform:translateY(-2px);box-shadow:0 0 50px rgba(0,245,255,0.4);color:#fff}}
    .btn-outline-glow{{background:transparent;border:1px solid rgba(0,245,255,0.3);color:#00f5ff;font-weight:600;padding:10px 30px;border-radius:50px;transition:all .3s}}
    .btn-outline-glow:hover{{background:rgba(0,245,255,0.1);color:#00f5ff}}
    .table{{--bs-table-bg:transparent;color:#fff;border-color:rgba(255,255,255,0.05)}}
    .table thead th{{background:rgba(0,245,255,0.05)!important;color:#00f5ff!important;font-weight:600;text-transform:uppercase;font-size:0.8rem;letter-spacing:1px}}
    code{{background:rgba(0,245,255,0.1);color:#00f5ff;padding:4px 10px;border-radius:6px}} .form-control{{background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);color:#fff;border-radius:12px;padding:12px 15px}}
    .form-control:focus{{border-color:#00f5ff;box-shadow:0 0 20px rgba(0,245,255,0.1)}
    .form-select{{background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);color:#fff}}
    .particle{{position:fixed;width:4px;height:4px;background:#00f5ff;border-radius:50%;pointer-events:none;animation:float linear infinite;opacity:0.3}}
    @keyframes float{{0%{{transform:translateY(100vh) rotate(0deg);opacity:0}}10%{{opacity:0.5}}90%{{opacity:0.5}}100%{{transform:translateY(-100vh) rotate(720deg);opacity:0}}}}
    @keyframes fadeInUp{{from{{opacity:0;transform:translateY(30px)}}to{{opacity:1;transform:translateY(0)}}}}
    .badge-premium{{background:linear-gradient(135deg,#00f5ff,#7b2ff7);color:#fff;font-weight:600;padding:8px 16px;border-radius:50px}}
    footer{{background:rgba(10,10,30,0.95);border-top:1px solid rgba(0,255,255,0.05);padding:20px 0;text-align:center;position:relative;z-index:1;color:rgba(255,255,255,0.4)}}
    ::-webkit-scrollbar{{width:6px}}::-webkit-scrollbar-track{{background:#0a0a1a}}::-webkit-scrollbar-thumb{{background:linear-gradient(135deg,#00f5ff,#7b2ff7);border-radius:3px}}
    .progress-bar{{background:linear-gradient(90deg,#00f5ff,#7b2ff7)!important}}
    .input-group-text{{background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);color:#00f5ff;border-radius:12px 0 0 12px}}
    </style></head><body>
    <canvas id="bg-canvas"></canvas>
    {particles}
    {nav}
    <div class="content-wrapper"><div class="container mt-4">
    {flash_msgs}
    {content}
    </div></div>
    <footer><div class="container"><p class="mb-0">© 2026 <strong>VERNEX API</strong> — Developed by <span style="color:#00f5ff">SHAYAN_EXPLORER</span>. All rights reserved.</p></div></footer>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
    const c=document.getElementById('bg-canvas'),ctx=c.getContext('2d');c.width=innerWidth;c.height=innerHeight;
    const ps=[];class P{{constructor(){{this.reset()}}reset(){{this.x=Math.random()*c.width;this.y=Math.random()*c.height;this.z=Math.random()*1000;this.size=Math.random()*2+0.5;this.speed=Math.random()*2+0.5;this.color=Math.random()>0.5?'#00f5ff':'#7b2ff7'}}
    update(){{this.z-=this.speed;if(this.z<=0)this.reset()}}draw(){{const s=500/this.z,x=(this.x-c.width/2)*s+c.width/2,y=(this.y-c.height/2)*s+c.height/2,sz=this.size*s;if(x<0||x>c.width||y<0||y>c.height)return;const op=Math.min(1,(500-this.z)/500);ctx.beginPath();ctx.arc(x,y,sz,0,Math.PI*2);ctx.fillStyle=this.color;ctx.globalAlpha=op*0.4;ctx.fill();ctx.shadowBlur=20;ctx.shadowColor=this.color}}}
    for(let i=0;i<80;i++)ps.push(new P());function a(){{ctx.clearRect(0,0,c.width,c.height);ps.forEach(p=>{{p.update();p.draw()}});requestAnimationFrame(a)}}a();
    window.addEventListener('resize',()=>{{c.width=innerWidth;c.height=innerHeight}});
    </script></body></html>'''

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
    
    content = f'''<div class="container py-5"><div class="row justify-content-center"><div class="col-md-5">
    <div class="glass-card text-center">
    <div class="mb-4"><i class="bi bi-shield-shaded" style="font-size:4rem;color:#00f5ff"></i></div>
    <h2 class="section-title">Welcome Back</h2><p class="text-muted mb-4">Login to VERNEX API</p>
    <form method="POST" action="/login">
    <div class="mb-3"><div class="input-group"><span class="input-group-text"><i class="bi bi-person"></i></span>
    <input type="text" name="email" class="form-control" placeholder="Email or Username" required></div></div>
    <div class="mb-4"><div class="input-group"><span class="input-group-text"><i class="bi bi-lock"></i></span>
    <input type="password" name="password" class="form-control" placeholder="Password" required></div></div>
    <button type="submit" class="btn btn-glow w-100"><i class="bi bi-box-arrow-in-right me-2"></i> Login</button></form>
    <p class="mt-4 text-muted">No account? <a href="/register" style="color:#00f5ff;text-decoration:none;">Register</a></p>
    <p class="mt-2" style="font-size:0.8rem;color:rgba(255,255,255,0.3)">Developed by <span style="color:#00f5ff">SHAYAN_EXPLORER</span></p>
    </div></div></div></div>'''
    return render_page('Login', content, show_nav=False)

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
            return render_page('Register', '')
        conn = get_db()
        if conn.execute("SELECT id FROM users WHERE email=?",(email,)).fetchone():
            flash('Email already registered!','error')
            conn.close()
            return render_page('Register', '')
        conn.execute("INSERT INTO users (email,password,name) VALUES (?,?,?)",
            (email,hashlib.sha256(password.encode()).hexdigest(),name or email.split('@')[0]))
        conn.commit()
        conn.close()
        flash('Registration successful! Please login.','success')
        return redirect(url_for('login'))
    
    content = f'''<div class="container py-5"><div class="row justify-content-center"><div class="col-md-5">
    <div class="glass-card text-center">
    <div class="mb-4"><i class="bi bi-person-plus-fill" style="font-size:4rem;color:#7b2ff7"></i></div>
    <h2 class="section-title">Create Account</h2><p class="text-muted mb-4">Join VERNEX API Platform</p>
    <form method="POST" action="/register">
    <div class="mb-3"><div class="input-group"><span class="input-group-text"><i class="bi bi-person"></i></span>
    <input type="text" name="name" class="form-control" placeholder="Full Name"></div></div>
    <div class="mb-3"><div class="input-group"><span class="input-group-text"><i class="bi bi-envelope"></i></span>
    <input type="email" name="email" class="form-control" placeholder="Email Address" required></div></div>
    <div class="mb-4"><div class="input-group"><span class="input-group-text"><i class="bi bi-lock"></i></span>
    <input type="password" name="password" class="form-control" placeholder="Password" required></div></div>
    <button type="submit" class="btn btn-glow w-100"><i class="bi bi-person-plus me-2"></i> Register</button></form>
    <p class="mt-4 text-muted">Already have an account? <a href="/login" style="color:#00f5ff;text-decoration:none;">Login</a></p>
    </div></div></div></div>'''
    return render_page('Register', content, show_nav=False)

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
    
    total_req = sum(k['requests_made'] for k in keys)
    
    keys_html = ''
    if keys:
        rows = ''
        for k in keys:
            pct = round(k['requests_made']/max(k['total_limit'],1)*100)
            expired = k['expires_at'] > datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')
            status_color = 'success' if expired else 'danger'
            status_text = 'Active' if k['is_active'] else 'Inactive'
            rows += f'''<tr>
            <td><code>{k['key_name']}</code></td>
            <td>{"🌐 All APIs" if k['all_apis'] else f'📌 {len(json.loads(k["api_names"]))} APIs'}</td>
            <td><div class="d-flex align-items-center"><div class="progress flex-grow-1 me-2" style="height:6px;background:rgba(255,255,255,0.1)"><div class="progress-bar bg-info" style="width:{pct}%"></div></div><small>{k['requests_made']}/{k['total_limit']}</small></div></td>
            <td><span class="text-{status_color}">{k['expires_at']}</span></td>
            <td><span class="badge bg-{"success" if k['is_active'] else "danger"}">{status_text}</span></td></tr>'''
        keys_html = f'''<div class="table-responsive"><table class="table table-dark table-hover">
        <thead><tr><th>Key Name</th><th>APIs</th><th>Usage</th><th>Expires</th><th>Status</th></tr></thead><tbody>{rows}</tbody></table></div>'''
    else:
        keys_html = '<div class="text-center py-5"><i class="bi bi-key" style="font-size:3rem;color:rgba(255,255,255,0.1)"></i><p class="mt-2 text-muted">No API keys yet. <a href="/pricing" style="color:#00f5ff">Purchase your first key</a></p></div>'
    
    logs_html = ''
    if logs:
        lrows = ''
        for l in logs:
            bc = 'success' if l['response_code'] == 200 else 'danger'
            lrows += f'<tr><td><small class="text-muted">{l["timestamp"]}</small></td><td>{l["api_called"]}</td><td><small>{l["query_param"]}</small></td><td><span class="badge bg-{bc}">{l["response_code"]}</span></td></tr>'
        logs_html = f'''<div class="table-responsive"><table class="table table-dark table-sm"><thead><tr><th>Time</th><th>API</th><th>Query</th><th>Status</th></tr></thead><tbody>{lrows}</tbody></table></div>'''
    else:
        logs_html = '<p class="text-muted text-center py-3">No activity yet. Start using your API keys!</p>'
    
    content = f'''
    <div class="glass-card mb-4"><div class="d-flex justify-content-between align-items-center">
    <div><h2 class="section-title mb-1">Welcome, {session.get("name","User")}! 👋</h2>
    <p class="text-muted mb-0">Manage your API keys, monitor usage, and purchase new plans</p></div>
    <a href="/pricing" class="btn btn-glow"><i class="bi bi-cart-plus me-2"></i>Buy API Keys</a></div></div>
    
    <div class="row mb-4"><div class="col-md-4 mb-3"><div class="glass-card text-center">
    <i class="bi bi-key" style="font-size:2.5rem;color:#00f5ff"></i><h3 class="mt-2">{len(keys)}</h3><p class="text-muted mb-0">Active Keys</p></div></div>
    <div class="col-md-4 mb-3"><div class="glass-card text-center">
    <i class="bi bi-arrow-repeat" style="font-size:2.5rem;color:#7b2ff7"></i><h3 class="mt-2">{len(logs)}</h3><p class="text-muted mb-0">Recent Requests</p></div></div>
    <div class="col-md-4 mb-3"><div class="glass-card text-center">
    <i class="bi bi-credit-card" style="font-size:2.5rem;color:#00ff88"></i><h3 class="mt-2">{total_req}</h3><p class="text-muted mb-0">Total API Calls</p></div></div></div>
    
    <div class="glass-card mb-4"><h3 class="section-title"><i class="bi bi-key me-2"></i>Your API Keys</h3>{keys_html}</div>
    
    <div class="glass-card"><h3 class="section-title"><i class="bi bi-clock-history me-2"></i>Recent Activity</h3>{logs_html}</div>'''
    return render_page('Dashboard', content)

@app.route('/pricing')
@login_required
def pricing():
    apis_html = ''
    for aid, a in API_LIST.items():
        buy_form = ''
        if a['type'] == 'paid':
            buy_form = f'''<form method="POST" action="/checkout">
            <input type="hidden" name="package_type" value="single">
            <input type="hidden" name="package_id" value="{aid}">
            <select name="duration" class="form-select mb-2" style="background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);color:#fff">
            <option value="monthly">Monthly - ₹{a['price_monthly']}</option>
            <option value="3months">3 Months - ₹{a['price_3months']}</option></select>
            <input type="text" name="key_name" class="form-control mb-2" placeholder="Custom Key Name (optional)" style="background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);color:#fff">
            <button type="submit" class="btn btn-glow w-100"><i class="bi bi-cart me-2"></i> Buy Now</button></form>'''
        else:
            buy_form = f'<p class="text-success"><i class="bi bi-unlock me-1"></i> Free — 5 requests/day</p><a href="/dashboard" class="btn btn-outline-glow w-100">Use Free API</a>'
        
        badge = f'<span class="badge bg-info">FREE</span>' if a['type'] == 'free' else ''
        
        apis_html += f'''<div class="col-md-4 mb-4"><div class="glass-card h-100">
        <div class="d-flex justify-content-between align-items-start mb-3"><h5 class="mb-0">{a["name"]}</h5>{badge}</div>
        {"".join([f'<p class="mb-1"><strong style="color:#00f5ff;font-size:1.5rem">₹{a["price_monthly"]}</strong> <span class="text-muted">/ month</span></p><p class="mb-0"><strong style="color:#7b2ff7">₹{a["price_3months"]}</strong> <span class="text-muted">/ 3 months</span></p>' if a['type']=='paid' else ''])}
        {buy_form}</div></div>'''
    
    bundles_html = ''
    for bid, b in BUNDLES.items():
        border = 'rgba(255,215,0,0.3)' if bid == 'ultimate' else ('rgba(0,245,255,0.3)' if bid == 'pro' else 'rgba(0,255,100,0.3)')
        best = '<span class="badge-premium mb-3">👑 BEST SELLER</span>' if bid == 'ultimate' else ''
        bundles_html += f'''<div class="col-md-4 mb-4"><div class="glass-card h-100 text-center" style="border-color:{border}">
        {best}<h3>{b["name"]}</h3>
        <div class="my-4"><p class="mb-1"><strong style="color:#00f5ff;font-size:2rem">₹{b["price_monthly"]}</strong> <span class="text-muted">/ month</span></p>
        <p><strong style="color:#7b2ff7;font-size:1.5rem">₹{b["price_3months"]}</strong> <span class="text-muted">/ 3 months</span></p></div>
        <form method="POST" action="/checkout"><input type="hidden" name="package_type" value="bundle"><input type="hidden" name="package_id" value="{bid}">
        <select name="duration" class="form-select mb-2" style="background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);color:#fff">
        <option value="monthly">Monthly - ₹{b["price_monthly"]}</option><option value="3months">3 Months - ₹{b["price_3months"]}</option></select>
        <input type="text" name="key_name" class="form-control mb-2" placeholder="Custom Key Name" style="background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);color:#fff">
        <button type="submit" class="btn btn-glow w-100">Buy Bundle</button></form></div></div>'''
    
    content = f'''
    <div class="text-center mb-5"><h1 class="section-title" style="font-size:3rem">💎 API PRICING</h1><p class="text-muted">Choose the perfect plan for your needs</p></div>
    <h3 class="section-title mb-4">📌 Individual APIs</h3><div class="row">{apis_html}</div>
    <h3 class="section-title mb-4 mt-5">🔥 BUNDLE DEALS</h3><div class="row">{bundles_html}</div>
    <div class="glass-card mt-4 text-center"><h5><i class="bi bi-unlock me-2" style="color:#00ff88"></i> FREE APIs</h5><p class="text-muted">Instagram • GitHub • Telegram Username→Num • Telegram ID Info — <strong>5 requests/day free</strong></p></div>'''
    return render_page('Pricing', content)

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
            
            content = f'''<div class="container py-5"><div class="row justify-content-center"><div class="col-md-6">
            <div class="glass-card text-center">
            <i class="bi bi-credit-card" style="font-size:4rem;color:#00f5ff;margin-bottom:20px"></i>
            <h2 class="section-title">Complete Payment</h2>
            <div class="mb-4"><p class="mb-1"><strong>Package:</strong> {pid} ({dur})</p>
            <p class="mb-1"><strong>Key Name:</strong> <code style="background:rgba(0,245,255,0.1);color:#00f5ff;padding:4px 8px;border-radius:5px">{kname}</code></p>
            <p><strong style="font-size:2rem;color:#00f5ff">₹{amount}</strong></p></div>
            <button id="pay-btn" class="btn btn-glow btn-lg w-100"><i class="bi bi-credit-card me-2"></i> Pay ₹{amount}</button>
            <p class="mt-3 text-muted small"><i class="bi bi-shield-check me-1"></i> Secured by Razorpay</p></div></div></div></div>
            
            <form id="pay-form" method="POST" action="/payment-success">
            <input type="hidden" name="razorpay_payment_id" id="rp_pid">
            <input type="hidden" name="razorpay_order_id" id="rp_oid">
            <input type="hidden" name="razorpay_signature" id="rp_sig">
            <input type="hidden" name="key_name" value="{kname}">
            <input type="hidden" name="package_id" value="{pid}">
            <input type="hidden" name="package_type" value="{ptype}">
            <input type="hidden" name="duration" value="{dur}">
            </form>
            
            <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
            <script>
            document.getElementById('pay-btn').onclick = function(e){{e.preventDefault();
            var opts={{"key":"{RAZORPAY_KEY_ID}","amount":"{order['amount']}","currency":"{order['currency']}",
            "name":"VERNEX API","description":"{pid} - {dur}","order_id":"{order['id']}",
            "handler":function(r){{document.getElementById('rp_pid').value=r.razorpay_payment_id;
            document.getElementById('rp_oid').value=r.razorpay_order_id;
            document.getElementById('rp_sig').value=r.razorpay_signature;
            document.getElementById('pay-form').submit()}},
            "prefill":{{"name":"{session.get('name','')}","email":"{session.get('email','')}"}},
            "theme":{{"color":"#00f5ff"}}}};
            var rzp=new Razorpay(opts);rzp.open()}};
            </script>'''
            return render_page('Checkout', content)
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
    
    if keys:
        cards = ''
        for k in keys:
            pct = round(k['requests_made']/max(k['total_limit'],1)*100)
            expired = k['expires_at'] > datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')
            status = 'Active' if k['is_active'] else 'Inactive'
            sc = 'success' if k['is_active'] else 'danger'
            ec = 'text-success' if expired else 'text-danger'
            cards += f'''<div class="col-md-6 mb-4"><div class="glass-card">
            <div class="d-flex justify-content-between align-items-start mb-3">
            <div><h5 class="mb-1"><code style="background:rgba(0,245,255,0.1);color:#00f5ff;padding:6px 12px;border-radius:8px;font-size:1.1rem">{k['key_name']}</code></h5>
            <small class="text-muted">Created: {k['created_at']}</small></div>
            <span class="badge bg-{sc}">{status}</span></div>
            <div class="mb-3"><small class="text-muted">Access:</small><p class="mb-0">{"🌐 All APIs" if k['all_apis'] else "📌 Selected APIs"}</p></div>
            <div class="mb-3"><div class="d-flex justify-content-between mb-1"><small class="text-muted">Usage</small><small>{k['requests_made']} / {k['total_limit']}</small></div>
            <div class="progress" style="height:8px;background:rgba(255,255,255,0.1)"><div class="progress-bar bg-info" style="width:{pct}%"></div></div></div>
            <div class="d-flex justify-content-between"><div><small class="text-muted">Daily Limit:</small> <span class="text-info">{k['daily_limit']}</span></div>
            <div><small class="text-muted">Expires:</small> <span class="{ec}">{k['expires_at']}</span></div></div>
            <hr style="border-color:rgba(255,255,255,0.05)">
            <button class="btn btn-outline-glow btn-sm w-100" onclick="navigator.clipboard.writeText('{k['key_name']}').then(()=>alert('Copied!'))">
            <i class="bi bi-clipboard me-1"></i> Copy Key</button></div></div>'''
        
        content = f'<h2 class="section-title"><i class="bi bi-key me-2"></i>My API Keys</h2><div class="row">{cards}</div>'
    else:
        content = f'''<div class="glass-card text-center py-5"><i class="bi bi-key" style="font-size:4rem;color:rgba(255,255,255,0.1)"></i>
        <h4 class="mt-3">No API Keys Yet</h4><p class="text-muted">Purchase your first API key to get started</p>
        <a href="/pricing" class="btn btn-glow mt-2"><i class="bi bi-cart me-2"></i> Browse Plans</a></div>'''
    return render_page('My Keys', content)

@app.route('/logs')
@login_required
def logs():
    email = session.get('email', session.get('user'))
    conn = get_db()
    logs = conn.execute("SELECT * FROM api_logs WHERE user_email=? ORDER BY timestamp DESC LIMIT 100",(email,)).fetchall()
    conn.close()
    
    if logs:
        rows = ''
        for i, l in enumerate(logs):
            bc = 'success' if l['response_code'] == 200 else 'danger'
            rows += f'<tr><td>{i+1}</td><td><small class="text-muted">{l["timestamp"]}</small></td><td><code style="font-size:0.8rem">{l["key_name"][:8]}...</code></td><td>{l["api_called"]}</td><td><small>{l["query_param"]}</small></td><td><span class="badge bg-{bc}">{l["response_code"]}</span></td><td><small class="text-muted">{l["ip_address"]}</small></td></tr>'
        content = f'''<div class="glass-card"><div class="table-responsive"><table class="table table-dark" style="border-color:rgba(255,255,255,0.05)">
        <thead><tr><th>#</th><th>Timestamp</th><th>Key</th><th>API</th><th>Query</th><th>Status</th><th>IP</th></tr></thead><tbody>{rows}</tbody></table></div></div>'''
    else:
        content = f'''<div class="glass-card text-center py-5"><i class="bi bi-clock" style="font-size:4rem;color:rgba(255,255,255,0.1)"></i>
        <h4 class="mt-3">No Logs Yet</h4><p class="text-muted">Activity will appear here when you use your API keys</p></div>'''
    return render_page('Activity Logs', content)

@app.route('/mailbox')
@login_required
def mailbox():
    email = session.get('email', session.get('user'))
    conn = get_db()
    keys = conn.execute("SELECT * FROM api_keys WHERE user_email=? ORDER BY created_at DESC",(email,)).fetchall()
    conn.close()
    
    if keys:
        cards = ''
        for k in keys:
            expired = k['expires_at'] > datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')
            ec = 'text-success' if expired else 'text-danger'
            cards += f'''<div class="col-md-6 mb-4"><div class="glass-card">
            <div class="d-flex justify-content-between mb-2"><span class="badge-premium"><i class="bi bi-key me-1"></i> {k['key_name']}</span>
            <span class="{"text-success" if k['is_active'] else "text-danger"}"><i class="bi {"bi-check-circle" if k['is_active'] else "bi-x-circle"}"></i> {"Active" if k['is_active'] else "Inactive"}</span></div>
            <hr style="border-color:rgba(255,255,255,0.05)">
            <div class="row text-center"><div class="col-4"><small class="text-muted d-block">Requests</small><strong style="color:#00f5ff">{k['requests_made']}</strong></div>
            <div class="col-4"><small class="text-muted d-block">Limit</small><strong style="color:#7b2ff7">{k['total_limit']}</strong></div>
            <div class="col-4"><small class="text-muted d-block">Expires</small><strong class="{ec}" style="font-size:0.85rem">{k['expires_at'][:10]}</strong></div></div>
            <div class="mt-3"><button class="btn btn-outline-glow btn-sm w-100" onclick="navigator.clipboard.writeText('{k['key_name']}').then(()=>alert('Copied!'))">
            <i class="bi bi-clipboard me-1"></i> Copy Key</button></div></div></div>'''
        content = f'<h2 class="section-title"><i class="bi bi-envelope me-2"></i>Key Mailbox</h2><p class="text-muted mb-4">Your purchased API keys and their details</p><div class="row">{cards}</div>'
    else:
        content = f'''<div class="glass-card text-center py-5"><i class="bi bi-inbox" style="font-size:4rem;color:rgba(255,255,255,0.1)"></i>
        <h4 class="mt-3">Mailbox Empty</h4><p class="text-muted">No keys found. Purchase an API plan to receive your keys here.</p>
        <a href="/pricing" class="btn btn-glow mt-2"><i class="bi bi-cart me-2"></i> Browse Plans</a></div>'''
    return render_page('Mailbox', content)

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
    klogs = conn.execute("SELECT * FROM api_logs ORDER BY timestamp DESC LIMIT 50").fetchall()
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
    
    api_opts = ''.join([f'<option value="{aid}">{a["name"]}</option>' for aid, a in API_LIST.items()])
    
    key_rows = ''
    for k in keys:
        key_rows += f'''<tr><td><small>{k['key_name'][:12]}...</small></td><td><small>{k['user_email'][:15]}...</small></td>
        <td><small>{"All" if k['all_apis'] else k['api_names'][:20]}</small></td><td>{k['requests_made']}</td><td>{k['total_limit']}</td>
        <td><small>{k['expires_at'][:10]}</small></td>
        <td><a href="/admin/toggle/{k['key_name']}" class="btn btn-sm {"btn-success" if k['is_active'] else "btn-secondary"}">{"Active" if k['is_active'] else "Inactive"}</a></td>
        <td><a href="/admin/delete/{k['key_name']}" class="btn btn-sm btn-danger" onclick="return confirm('Delete?')"><i class="bi bi-trash"></i></a></td></tr>'''
    
    order_rows = ''
    for o in orders:
        bs = 'success' if o['status'] == 'completed' else 'warning'
        order_rows += f'<tr><td><small>{o["order_id"][:12]}...</small></td><td><small>{o["user_email"][:15]}...</small></td><td><small>{o["package_name"]}</small></td><td>₹{o["amount"]}</td><td><span class="badge bg-{bs}">{o["status"]}</span></td><td><small>{o["created_at"][:10]}</small></td></tr>'''
    
    content = f'''
    <h2 class="section-title"><i class="bi bi-shield-lock me-2"></i>Admin Panel</h2>
    <div class="row mb-4">
    <div class="col-md-2 mb-3"><div class="glass-card text-center"><h3>{stats['total_users']}</h3><small class="text-muted">Users</small></div></div>
    <div class="col-md-2 mb-3"><div class="glass-card text-center"><h3>{stats['total_keys']}</h3><small class="text-muted">Total Keys</small></div></div>
    <div class="col-md-2 mb-3"><div class="glass-card text-center"><h3>{stats['active_keys']}</h3><small class="text-muted">Active</small></div></div>
    <div class="col-md-2 mb-3"><div class="glass-card text-center"><h3>{stats['total_requests']}</h3><small class="text-muted">Requests</small></div></div>
    <div class="col-md-2 mb-3"><div class="glass-card text-center"><h3 style="color:#00ff88">₹{stats['total_revenue']}</h3><small class="text-muted">Revenue</small></div></div>
    <div class="col-md-2 mb-3"><div class="glass-card text-center"><h3>{len(payments)}</h3><small class="text-muted">Payments</small></div></div></div>
    
    <div class="glass-card mb-4"><h4><i class="bi bi-plus-circle me-2" style="color:#00f5ff"></i>Create New API Key</h4>
    <form method="POST" action="/admin/create-key" class="row g-3">
    <div class="col-md-3"><input type="text" name="key_name" class="form-control" placeholder="Key Name (auto)"></div>
    <div class="col-md-3"><input type="email" name="user_email" class="form-control" placeholder="User Email" required></div>
    <div class="col-md-2"><select name="api_names" class="form-select" style="background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);color:#fff"><option value="all">All APIs</option>{api_opts}</select></div>
    <div class="col-md-2"><input type="number" name="daily_limit" class="form-control" placeholder="Daily Limit" value="1000"></div>
    <div class="col-md-2"><input type="datetime-local" name="expires_at" class="form-control" style="background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);color:#fff"></div>
    <div class="col-12"><button type="submit" class="btn btn-glow"><i class="bi bi-key me-1"></i> Generate Key</button></div></form></div>
    
    <div class="glass-card mb-4"><h4><i class="bi bi-key me-2" style="color:#7b2ff7"></i>All API Keys</h4>
    <div class="table-responsive"><table class="table table-dark table-sm">
    <thead><tr><th>Key</th><th>User</th><th>APIs</th><th>Used</th><th>Total</th><th>Expires</th><th>Status</th><th>Actions</th></tr></thead><tbody>{key_rows}</tbody></table></div></div>
    
    <div class="glass-card mb-4"><h4><i class="bi bi-cart me-2" style="color:#00ff88"></i>Recent Orders</h4>
    <div class="table-responsive"><table class="table table-dark table-sm">
    <thead><tr><th>Order ID</th><th>User</th><th>Package</th><th>Amount</th><th>Status</th><th>Date</th></tr></thead><tbody>{order_rows}</tbody></table></div></div>'''
    return render_page('Admin', content)

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

@app.route('/admin/toggle/<key_name>')
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

@app.route('/admin/delete/<key_name>')
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

# ======================= THIS IS CRITICAL FOR VERCEL =======================
# The 'app' object MUST be at module level
# app is already defined at the top of this file
