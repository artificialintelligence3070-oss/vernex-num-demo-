from flask import Flask, request, jsonify, session
from flask_cors import CORS
import threading
import requests
import json
import time
import os
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", os.urandom(24)) 
CORS(app, supports_credentials=True)

running_bots = {}
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "vern19")
DB_NAME = "bot_system.db"

# Dynamically extract Render host URL from environment variables
RENDER_HOST = os.environ.get("RENDER_EXTERNAL_URL", "http://localhost:5990")

# ==============================================================================
# DATABASE LAYER (PERSISTENCE)
# ==============================================================================
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS bots (
                bid TEXT PRIMARY KEY,
                token TEXT,
                chat_id TEXT,
                tools TEXT,
                expiry TEXT,
                is_running INTEGER DEFAULT 0
            )
        """)
        conn.commit()

def save_bot_to_db(bid, token, chat_id, tools, expiry, is_running):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO bots (bid, token, chat_id, tools, expiry, is_running) VALUES (?, ?, ?, ?, ?, ?)",
            (bid, token, chat_id, json.dumps(tools), expiry, 1 if is_running else 0)
        )
        conn.commit()

def update_bot_status_in_db(bid, is_running):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("UPDATE bots SET is_running = ? WHERE bid = ?", (1 if is_running else 0, bid))
        conn.commit()

def delete_bot_from_db(bid):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("DELETE FROM bots WHERE bid = ?", (bid,))
        conn.commit()

# ==============================================================================
# BOT RUNTIME CLASS
# ==============================================================================
class Bot:
    def __init__(self, bid, token, chat_id, tools, expiry=None):
        self.bid = bid
        self.token = token
        self.chat_id = chat_id
        self.tools = tools
        self.expiry = expiry
        self.running = False
        self.offset = None
        self.waiting = {}
        self.user_cooldowns = {}
        self.base = "https://api.telegram.org/bot" + token
        self.key = "ftgamer2"
        
        self.apis = {
            "phone": ("https://ft-osint-api.duckdns.org/api/number", "num"),
            "aadhaar": ("https://ft-osint-api.duckdns.org/api/aadhar", "num"),
            "aadhaar_family": ("https://ft-osint-api.duckdns.org/api/adharfamily", "num"),
            "email": ("https://ft-osint-api.duckdns.org/api/email", "email"),
            "vehicle": ("https://ft-osint-api.duckdns.org/api/vehicle", "vehicle"),
            "github": ("https://ft-osint-api.duckdns.org/api/git", "username"),
            "instagram": ("https://ft-osint-api.duckdns.org/api/insta", "username"),
            "tg_user": ("https://ft-osint-api.duckdns.org/api/tg", "info"),
            "pan": ("https://ft-osint-api.duckdns.org/api/pan", "pan"),
            "tg_id": ("https://ft-osint-api.duckdns.org/api/tgidinfo", "id"),
            "sms_bomber": ("https://ft-osint-api.duckdns.org/api/bomber", "number"),
            "name_search": ("https://ft-osint-api.duckdns.org/api/name", "name"),
            "adv_search": ("https://ft-osint-api.duckdns.org/api/adv", "num"),
            "paytm_lookup": ("https://ft-osint-api.duckdns.org/api/paytm", "num"),
            "imei_lookup": ("https://ft-osint-api.duckdns.org/api/imei", "imei"),
            "call_tracer": ("https://ft-osint-api.duckdns.org/api/calltracer", "num"),
            "upi_lookup": ("https://ft-osint-api.duckdns.org/api/upi", "upi"),
            "ifsc_lookup": ("https://ft-osint-api.duckdns.org/api/ifsc", "ifsc"),
            "pincode_lookup": ("https://ft-osint-api.duckdns.org/api/pincode", "pin"),
            "ip_lookup": ("https://ft-osint-api.duckdns.org/api/ip", "ip"),
            "challan_lookup": ("https://ft-osint-api.duckdns.org/api/challan", "vehicle"),
            "ff_lookup": ("https://ft-osint-api.duckdns.org/api/ff", "uid"),
            "bgmi_lookup": ("https://ft-osint-api.duckdns.org/api/bgmi", "uid")
        }
        
        self.prompts = {
            "phone": ("📱 Phone", "Send 10 digit number:"),
            "aadhaar": ("🆔 Aadhaar", "Send 12 digit number:"),
            "aadhaar_family": ("👨‍👩‍👧 Family", "Send 12 digit number:"),
            "email": ("📧 Email", "Send email:"),
            "vehicle": ("🚗 Vehicle", "Send vehicle number:"),
            "github": ("🐙 GitHub", "Send username:"),
            "instagram": ("📸 Instagram", "Send username:"),
            "tg_user": ("✈️ Telegram", "Send username:"),
            "pan": ("🪪 PAN", "Send PAN number:"),
            "tg_id": ("🆔 TG ID", "Send numeric ID:"),
            "sms_bomber": ("💥 SMS", "Send 10 digit number:"),
            "name_search": ("👤 Name Search", "Send name to search:"),
            "adv_search": ("🔍 Adv Search", "Send number for advanced search:"),
            "paytm_lookup": ("💸 Paytm Lookup", "Send 10 digit number:"),
            "imei_lookup": ("📱 IMEI Check", "Send 15 digit IMEI number:"),
            "call_tracer": ("📡 Call Tracer", "Send 10 digit number to trace:"),
            "upi_lookup": ("💳 UPI Verify", "Send UPI ID (e.g., example@ybl):"),
            "ifsc_lookup": ("🏦 IFSC Code", "Send bank IFSC code:"),
            "pincode_lookup": ("📍 Pincode", "Send 6 digit postal pincode:"),
            "ip_lookup": ("🌐 IP Lookup", "Send target IP address:"),
            "challan_lookup": ("🧾 Challan Info", "Send vehicle number:"),
            "ff_lookup": ("🎮 FreeFire UID", "Send FreeFire Game UID:"),
            "bgmi_lookup": ("🔫 BGMI UID", "Send BGMI Game UID:")
        }

    def update_config(self, token, chat_id, tools):
        self.token = token
        self.chat_id = chat_id
        self.tools = tools
        self.base = "https://api.telegram.org/bot" + token
        self.waiting.clear()
        save_bot_to_db(self.bid, self.token, self.chat_id, self.tools, self.expiry, self.running)

    def send(self, chat, text, markup=None):
        try:
            p = {"chat_id": chat, "text": text, "parse_mode": "HTML"}
            if markup: p["reply_markup"] = json.dumps(markup)
            requests.post(self.base + "/sendMessage", json=p, timeout=5)
        except Exception as e:
            print(f"[Bot {self.bid}] Outbound Error: {str(e)}")

    def get_updates(self):
        try:
            p = {"limit": 100, "timeout": 1}
            if self.offset: p["offset"] = self.offset
            r = requests.get(self.base + "/getUpdates", params=p, timeout=5)
            return r.json()
        except: 
            return {"ok": False, "result": []}

    def call_api(self, url, params):
        try:
            r = requests.get(url, params=params, timeout=10)
            return r.json()
        except Exception as e: return {"error": str(e)}

    def keyboard(self):
        k = []
        r = []
        for t in self.tools:
            if t in self.prompts:
                r.append({"text": self.prompts[t][0]})
                if len(r) == 2: k.append(r); r = []
        if r: k.append(r)
        return {"keyboard": k, "resize_keyboard": True, "one_time_keyboard": False}

    def clear_webhooks_safely(self):
        try: requests.get(self.base + "/deleteWebhook", timeout=5)
        except: pass

    def run(self):
        self.running = True
        update_bot_status_in_db(self.bid, True)
        self.clear_webhooks_safely()
        self.send(self.chat_id, "Bot started! Speed-Optimized Engine Active on Cluster.")
        
        while self.running:
            try:
                u = self.get_updates()
                if not u.get("ok"):
                    time.sleep(1)
                    continue
                    
                updates = u.get("result", [])
                for up in updates:
                    self.offset = up["update_id"] + 1
                    m = up.get("message", {})
                    c = m.get("chat", {}).get("id")
                    u_info = m.get("from", {})
                    user_id = u_info.get("id")
                    t = m.get("text", "")
                    if not c or t is None: continue
                    
                    if t == "/start":
                        self.send(c, "Welcome! Select a tool:", self.keyboard())
                        self.waiting.pop(c, None)
                        continue
                        
                    for tk in self.tools:
                        if tk in self.prompts and t == self.prompts[tk][0]:
                            self.send(c, self.prompts[tk][1])
                            self.waiting[c] = tk
                            break
                    else:
                        if c in self.waiting:
                            now = time.time()
                            if user_id in self.user_cooldowns and (now - self.user_cooldowns[user_id]) < 3.0:
                                self.send(c, "⚠️ <b>Anti-Spam System Active:</b> Please wait 3 seconds.")
                                continue
                            self.user_cooldowns[user_id] = now

                            s = self.waiting[c]
                            self.send(c, "Processing Request...")
                            
                            if str(c) != str(self.chat_id):
                                username = u_info.get("username", "Unknown")
                                log_msg = f"⚙️ <b>[ADMIN ALERT]</b>\nUser: @{username}\nPayload: <code>{s}</code>\nInput: <code>{t}</code>"
                                self.send(self.chat_id, log_msg)

                            url, param = self.apis[s]
                            current_api_key = "ftgamer" if s in ["name_search", "adv_search", "imei_lookup"] else self.key
                            
                            p = {"key": current_api_key, param: t}
                            if s == "sms_bomber": p["counter"] = 100
                            
                            r = self.call_api(url, p)
                            self.send(c, "<pre>" + json.dumps(r, indent=2) + "</pre>")
                            self.waiting.pop(c, None)
                            continue
                        self.send(c, "Use /start or select a tool.")
                if not updates:
                    time.sleep(0.2)
            except Exception as e:
                time.sleep(2)
        self.running = False
        update_bot_status_in_db(self.bid, False)

    def start(self):
        if not self.running:
            threading.Thread(target=self.run, daemon=True).start()
            return True
        return False

    def stop(self):
        self.running = False
        return True

# ==============================================================================
# ENGINE AUTO-RESTORE & ANTI-SLEEP LIFECYCLE
# ==============================================================================
def restore_active_bots():
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT bid, token, chat_id, tools, expiry, is_running FROM bots")
            rows = cursor.fetchall()
            for row in rows:
                bid, token, chat_id, tools_json, expiry, is_running = row
                tools = json.loads(tools_json)
                b = Bot(bid, token, chat_id, tools, expiry)
                running_bots[bid] = b
                if is_running == 1:
                    b.start()
                    print(f"[SYSTEM] Auto-reloaded bot instance: {bid}")
    except Exception as e:
        print(f"[CRITICAL] Crash recovery failure: {e}")

def keep_alive_ping():
    """Background loop that targets its own web interface to abort Render Free sleep mode"""
    while True:
        time.sleep(600)  # Pings every 10 minutes
        if "localhost" not in RENDER_HOST:
            try:
                requests.get(RENDER_HOST, timeout=10)
                print("[SYSTEM KeepAlive] Heartbeat pinged successfully.")
            except:
                pass

# ==============================================================================
# FLASK HTTP ENDPOINTS & ROUTING
# ==============================================================================
def check_auth():
    return session.get("logged_in") is True

@app.route("/")
def index():
    # Retaining your original styled responsive terminal dashboard setup UI template text
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>⚡ MATRIX // FAST BOT CONTROL TERMINAL</title>
    <style>
    :root {
        --bg-color: #0a0b0d;
        --card-bg: rgba(18, 22, 28, 0.75);
        --accent: #00ffaa;
        --accent-glow: rgba(0, 255, 170, 0.35);
        --text-main: #e2e8f0;
        --text-muted: #64748b;
        --border-color: rgba(0, 255, 170, 0.15);
        --error: #ff4a6b;
    }
    body {
        font-family: 'Courier New', Courier, monospace;
        background-color: var(--bg-color);
        color: var(--text-main);
        padding: 15px;
        margin: 0;
        min-height: 100vh;
        box-sizing: border-box;
    }
    .c { max-width: 650px; margin: 0 auto; display: none; }
    .h { text-align: center; padding: 25px 0 15px 0; }
    .h h1 { font-size: 22px; text-transform: uppercase; color: var(--accent); text-shadow: 0 0 10px var(--accent-glow); margin: 0; }
    .h p { font-size: 11px; color: var(--text-muted); margin: 5px 0 0 0; }
    .card { background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 12px; padding: 22px; margin-bottom: 20px; }
    .card h2 { font-size: 14px; text-transform: uppercase; color: var(--accent); margin-top: 0; margin-bottom: 15px; }
    input { width: 100%; padding: 14px; background: rgba(10, 11, 13, 0.8); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; margin-bottom: 12px; box-sizing: border-box; color: #fff; }
    button { width: 100%; padding: 15px; background: linear-gradient(135deg, #00ffaa 0%, #00bfff 100%); color: #000; font-weight: bold; border: none; border-radius: 8px; cursor: pointer; text-transform: uppercase; letter-spacing: 2px; }
    .tools { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 18px; }
    .tool, .edit-tool { padding: 12px; border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 8px; cursor: pointer; background: rgba(255, 255, 255, 0.02); font-size: 12px; }
    .tool.s, .edit-tool.s { border-color: var(--accent); background: rgba(0, 255, 170, 0.12); color: var(--accent); }
    .status { margin-top: 12px; padding: 12px; border-radius: 8px; text-align: center; font-size: 12px; }
    .ok { background: rgba(0, 255, 170, 0.1); color: var(--accent); }
    .err { background: rgba(255, 74, 107, 0.1); color: var(--error); }
    .load { background: rgba(255, 193, 7, 0.1); color: #ffc107; }
    .bot-item { display: flex; flex-direction: column; padding: 16px; border-bottom: 1px solid rgba(255, 255, 255, 0.05); gap: 12px; }
    .bot-header { display: flex; align-items: center; justify-content: space-between; }
    .bot-info b { font-size: 13px; color: #fff; }
    .bot-info small { font-size: 11px; color: var(--text-muted); display: block; }
    .badge { padding: 4px 10px; border-radius: 6px; font-size: 10px; font-weight: bold; }
    .badge.run { background: rgba(0, 255, 170, 0.15); color: var(--accent); }
    .badge.stop { background: rgba(255, 255, 255, 0.05); color: var(--text-muted); }
    .bot-actions { display: flex; gap: 6px; }
    .bot-actions button { padding: 8px; font-size: 10px; width: auto; flex: 1; }
    .btn-start { background: rgba(0, 255, 170, 0.1); color: var(--accent); }
    .btn-stop { background: rgba(255, 193, 7, 0.1); color: #ffc107; }
    .btn-restart { background: rgba(0, 191, 255, 0.1); color: #00bfff; }
    .btn-edit { background: rgba(255, 255, 255, 0.05); color: #e2e8f0; }
    .btn-delete { background: rgba(255, 74, 107, 0.1); color: var(--error); }
    .sel-all { background: rgba(255, 255, 255, 0.03); color: #fff; margin-bottom: 5px; }
    .login-container { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: var(--bg-color); z-index: 2000; display: flex; align-items: center; justify-content: center; }
    .login-box { background: var(--card-bg); border: 1px solid var(--accent); padding: 35px 25px; border-radius: 16px; width: 100%; max-width: 380px; text-align: center; }
    </style>
    </head>
    <body>
    <div id="auth-block" class="login-container">
        <div class="login-box">
            <h2>TERMINAL ACCESS</h2>
            <p>Identity Verification Required</p>
            <input type="text" id="user" placeholder="USERNAME">
            <input type="password" id="pass" placeholder="ACCESS_KEY / PASSWORD">
            <button onclick="attemptLogin()" style="margin-top:15px;">Bypass Gate</button>
            <div id="auth-err" class="status err" style="display:none; margin-top:15px;">AUTHENTICATION_FAILURE</div>
        </div>
    </div>
    <div class="c" id="main-panel">
    <div class="h">
        <h1>// CENTRAL OPERATIONS //</h1>
        <p>SECURE INTERFACE HUB</p>
    </div>
    <div class="card">
        <h2>🔌 Core Parameters</h2>
        <input type="text" id="t" placeholder="ENTER TELEGRAM BOT TOKEN">
        <input type="text" id="c" placeholder="ENTER ADMIN CHAT ID">
    </div>
    <div class="card">
        <h2>🛠️ Service Modules</h2>
        <div class="tools">
            <div class="tool" onclick="tog(this)" data-t="phone">📱 Phone</div>
            <div class="tool" onclick="tog(this)" data-t="aadhaar">🆔 Aadhaar</div>
            <div class="tool" onclick="tog(this)" data-t="aadhaar_family">👨‍👩‍👧 Family</div>
            <div class="tool" onclick="tog(this)" data-t="email">📧 Email</div>
            <div class="tool" onclick="tog(this)" data-t="vehicle">🚗 Vehicle</div>
            <div class="tool" onclick="tog(this)" data-t="github">🐙 GitHub</div>
            <div class="tool" onclick="tog(this)" data-t="instagram">📸 Instagram</div>
            <div class="tool" onclick="tog(this)" data-t="tg_user">✈️ Telegram</div>
            <div class="tool" onclick="tog(this)" data-t="pan">🪪 PAN</div>
            <div class="tool" onclick="tog(this)" data-t="tg_id">🆔 TG ID</div>
            <div class="tool" onclick="tog(this)" data-t="sms_bomber">💥 SMS</div>
            <div class="tool" onclick="tog(this)" data-t="name_search">👤 Name Search</div>
            <div class="tool" onclick="tog(this)" data-t="adv_search">🔍 Adv Search</div>
            <div class="tool" onclick="tog(this)" data-t="paytm_lookup">💸 Paytm</div>
            <div class="tool" onclick="tog(this)" data-t="imei_lookup">📱 IMEI</div>
            <div class="tool" onclick="tog(this)" data-t="call_tracer">📡 Call Tracer</div>
            <div class="tool" onclick="tog(this)" data-t="upi_lookup">💳 UPI Verify</div>
            <div class="tool" onclick="tog(this)" data-t="ifsc_lookup">🏦 IFSC</div>
            <div class="tool" onclick="tog(this)" data-t="pincode_lookup">📍 Pincode</div>
            <div class="tool" onclick="tog(this)" data-t="ip_lookup">🌐 IP Lookup</div>
            <div class="tool" onclick="tog(this)" data-t="challan_lookup">🧾 Challan Info</div>
            <div class="tool" onclick="tog(this)" data-t="ff_lookup">🎮 FreeFire UID</div>
            <div class="tool" onclick="tog(this)" data-t="bgmi_lookup">🔫 BGMI UID</div>
        </div>
        <button class="sel-all" onclick="all()">⚡ TOGGLE ALL PAYLOADS</button>
    </div>
    <div class="card">
        <h2>⏳ Expiry Anchor</h2>
        <input type="date" id="e">
    </div>
    <div class="card">
        <button onclick="go()">🚀 Inject Runtime Engine</button>
        <div id="s" style="display:none;"></div>
    </div>
    <div class="card">
        <h2>📊 Active Process Threads</h2>
        <div id="b"><div class="empty-state">No active modules configured</div></div>
    </div>
    </div>
    <script>
    var sel=new Set();
    function attemptLogin(){
      var u = document.getElementById("user").value;
      var p = document.getElementById("pass").value;
      fetch("/api/login", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({username: u, password: p})
      }).then(r => r.json()).then(d => {
        if(d.success){
          document.getElementById("auth-block").style.display = "none";
          document.getElementById("main-panel").style.display = "block";
          load(); setInterval(load, 4000);
        } else { document.getElementById("auth-err").style.display = "block"; }
      }).catch(() => { document.getElementById("auth-err").style.display = "block"; });
    }
    function tog(el){
      var t=el.getAttribute("data-t");
      if(sel.has(t)){sel.delete(t);el.classList.remove("s");}
      else{sel.add(t);el.classList.add("s");}
    }
    function all(){
      var ak = ["phone","aadhaar","aadhaar_family","email","vehicle","github","instagram","tg_user","pan","tg_id","sms_bomber","name_search","adv_search","paytm_lookup","imei_lookup","call_tracer","upi_lookup","ifsc_lookup","pincode_lookup","ip_lookup","challan_lookup","ff_lookup","bgmi_lookup"];
      if(sel.size == 23){ sel.clear(); document.querySelectorAll(".tool").forEach(e=>e.classList.remove("s")); }
      else { sel = new Set(ak); document.querySelectorAll(".tool").forEach(e=>e.classList.add("s")); }
    }
    defSt = (m,c) => { var s=document.getElementById("s"); s.style.display="block"; s.className="status "+c; s.textContent=m; };
    function go(){
      var t=document.getElementById("t").value.trim(), c=document.getElementById("c").value.trim(), e=document.getElementById("e").value, tools=Array.from(sel);
      if(!t||!c||tools.length==0){defSt("CRITICAL: PARAMS CONFIG INCOMPLETE","err");return;}
      defSt("INITIALIZING PIPELINE...","load");
      fetch("/api/deploy",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({token:t,chat_id:c,tools:tools,expiry:e})})
      .then(r=>r.json()).then(d=>{if(d.success){defSt("DEPLOYED!","ok");load();}else{defSt("FAILURE","err");}});
    }
    function toggleBot(id){ fetch("/api/toggle/"+id,{method:"POST"}).then(()=>load()); }
    function restartBot(id){ fetch("/api/restart/"+id,{method:"POST"}).then(()=>load()); }
    function deleteBot(id){ fetch("/api/delete/"+id,{method:"DELETE"}).then(()=>load()); }
    function load(){
      fetch("/api/bots").then(r=>{if(r.status==401)location.reload(); return r.json();}).then(d=>{
        var b=document.getElementById("b"); if(!d.bots||d.bots.length==0){b.innerHTML='<div class="empty-state">No threads found</div>';return;}
        var html='';
        d.bots.forEach(bot=>{
          var sc=bot.run?"run":"stop", st=bot.run?"ONLINE":"IDLE";
          html+='<div class="bot-item"><div class="bot-header"><div><b>'+bot.tp+'</b><small>Modules: '+bot.tools.length+'</small></div><span class="badge '+sc+'">'+st+'</span></div><div class="bot-actions"><button class="btn-start" onclick="toggleBot(\''+bot.id+'\')">Toggle</button><button class="btn-restart" onclick="restartBot(\''+bot.id+'\')">Recycle</button><button class="btn-delete" onclick="deleteBot(\''+bot.id+'\')">Delete</button></div></div>';
        });
        b.innerHTML=html;
      });
    }
    </script>
    </body>
    </html>
    """

@app.route("/api/login", methods=["POST"])
def api_login():
    try:
        d = request.get_json()
        if d.get("password", "") == ADMIN_PASSWORD:
            session["logged_in"] = True
            return jsonify({"success": True})
        return jsonify({"success": False}), 401
    except:
        return jsonify({"success": False}), 400

@app.route("/api/deploy", methods=["POST"])
def deploy():
    if not check_auth(): return jsonify({"success": False}), 401
    try:
        d = request.get_json()
        token = d.get("token", "").strip()
        chat_id = d.get("chat_id", "").strip()
        tools = d.get("tools", [])
        expiry = d.get("expiry", "")
        
        bid = str(int(time.time()))
        for b in list(running_bots.keys()):
            if running_bots[b].token == token: 
                running_bots[b].stop()
                delete_bot_from_db(b)
                del running_bots[b]
                
        b = Bot(bid, token, chat_id, tools, expiry)
        running_bots[bid] = b
        b.start()
        save_bot_to_db(bid, token, chat_id, tools, expiry, True)
        return jsonify({"success": True})
    except Exception as e: return jsonify({"success": False, "error": str(e)})

@app.route("/api/bots", methods=["GET"])
def list_bots():
    if not check_auth(): return jsonify({"success": False}), 401
    bots = [{
        "id": bid,
        "tp": b.token[:12] + "..." if len(b.token) > 12 else b.token,
        "tools": b.tools,
        "run": b.running
    } for bid, b in running_bots.items()]
    return jsonify({"bots": bots})

@app.route("/api/toggle/<bid>", methods=["POST"])
def toggle(bid):
    if not check_auth(): return jsonify({"success": False}), 401
    if bid in running_bots:
        b = running_bots[bid]
        if b.running: b.stop()
        else: b.start()
        update_bot_status_in_db(bid, b.running)
        return jsonify({"success": True})
    return jsonify({"success": False}), 404

@app.route("/api/restart/<bid>", methods=["POST"])
def restart(bid):
    if not check_auth(): return jsonify({"success": False}), 401
    if bid in running_bots:
        b = running_bots[bid]
        b.stop()
        time.sleep(1)
        b.start()
        return jsonify({"success": True})
    return jsonify({"success": False}), 404

@app.route("/api/delete/<bid>", methods=["DELETE"])
def delete(bid):
    if not check_auth(): return jsonify({"success": False}), 401
    if bid in running_bots:
        running_bots[bid].stop()
        delete_bot_from_db(bid)
        del running_bots[bid]
        return jsonify({"success": True})
    return jsonify({"success": False}), 404

if __name__ == "__main__":
    init_db()  
    restore_active_bots()  
    
    # Fire up the automatic anti-sleeping engine
    threading.Thread(target=keep_alive_ping, daemon=True).start()
    
    # Render maps port to standard variable automatically
    port = int(os.environ.get("PORT", 5990))
    app.run(host="0.0.0.0", port=port, debug=False)
