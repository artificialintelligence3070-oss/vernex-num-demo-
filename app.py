from flask import Flask, request, jsonify, session
from flask_cors import CORS
import threading, requests, json, time, os, sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24) 
CORS(app, supports_credentials=True)

running_bots = {}
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "vern19")
DB_NAME = "bot_system.db"

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
# BOT RUNTIME CLASS (WITH EXPANDED API MODULES)
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
        
        # Comprehensive API Routing Map
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
        
        # User Button Descriptions and Interaction Strings
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
        print(f"[Bot {self.bid}] High-Speed Thread Injected.")
        self.clear_webhooks_safely()
        self.send(self.chat_id, "Bot started! Speed-Optimized Engine Active.")
        
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
                                self.send(c, "⚠️ <b>Anti-Spam System Active:</b> Please wait 3 seconds between module requests.")
                                continue
                            self.user_cooldowns[user_id] = now

                            s = self.waiting[c]
                            self.send(c, "Processing Request...")
                            
                            if str(c) != str(self.chat_id):
                                username = u_info.get("username", "Unknown")
                                log_msg = f"⚙️ <b>[ADMIN ALERT]</b>\nUser: @{username} (<code>{c}</code>)\nTriggered Payload: <code>{s}</code>\nInput Buffer: <code>{t}</code>"
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
                    time.sleep(0.1)
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
# ENGINE AUTO-RESTORE LIFECYCLE
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
                    print(f"[SYSTEM] Hot-reloaded and executed bot thread: {bid}")
    except Exception as e:
        print(f"[CRITICAL] Database Hot-patch Recovery Error: {e}")

# ==============================================================================
# FLASK HTTP ENDPOINTS & ROUTING
# ==============================================================================
def check_auth():
    return session.get("logged_in") is True

@app.route("/")
def index():
    return """<!DOCTYPE html>
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
    background-image: 
        radial-gradient(at 0% 0%, rgba(0, 255, 170, 0.05) 0px, transparent 50%),
        radial-gradient(at 100% 100%, rgba(111, 66, 121, 0.08) 0px, transparent 50%);
    background-attachment: fixed;
    color: var(--text-main);
    padding: 15px;
    margin: 0;
    min-height: 100vh;
    box-sizing: border-box;
}
.c { max-width: 650px; margin: 0 auto; display: none; animation: fadeIn 0.6s ease-out; }
.h { text-align: center; padding: 25px 0 15px 0; }
.h h1 { font-size: 22px; text-transform: uppercase; letter-spacing: 3px; color: var(--accent); text-shadow: 0 0 10px var(--accent-glow); margin: 0; }
.h p { font-size: 11px; color: var(--text-muted); margin: 5px 0 0 0; letter-spacing: 1px; }
.card { background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 12px; padding: 22px; margin-bottom: 20px; backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37); }
.card h2 { font-size: 14px; text-transform: uppercase; letter-spacing: 1.5px; color: var(--accent); margin-top: 0; margin-bottom: 15px; display: flex; align-items: center; gap: 8px; }
input { width: 100%; padding: 14px; background: rgba(10, 11, 13, 0.8); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; margin-bottom: 12px; box-sizing: border-box; font-size: 13px; color: #fff; font-family: inherit; transition: all 0.3s ease; }
input:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 8px var(--accent-glow); background: rgba(10, 11, 13, 0.95); }
button { width: 100%; padding: 15px; background: linear-gradient(135deg, #00ffaa 0%, #00bfff 100%); color: #000; font-weight: bold; border: none; border-radius: 8px; font-size: 14px; cursor: pointer; font-family: inherit; text-transform: uppercase; letter-spacing: 2px; transition: all 0.3s ease; box-shadow: 0 4px 15px rgba(0, 255, 170, 0.2); }
button:hover { transform: translateY(-1px); box-shadow: 0 6px 20px rgba(0, 255, 170, 0.4); }
.tools { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 18px; }
.tool, .edit-tool { padding: 12px; border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 8px; text-align: left; cursor: pointer; background: rgba(255, 255, 255, 0.02); font-size: 12px; transition: all 0.2s ease; display: flex; align-items: center; gap: 8px; }
.tool:hover, .edit-tool:hover { background: rgba(0, 255, 170, 0.05); border-color: rgba(0, 255, 170, 0.3); }
.tool.s, .edit-tool.s { border-color: var(--accent); background: rgba(0, 255, 170, 0.12); color: var(--accent); text-shadow: 0 0 5px rgba(0, 255, 170, 0.3); box-shadow: inset 0 0 8px rgba(0, 255, 170, 0.05); }
.status { margin-top: 12px; padding: 12px; border-radius: 8px; text-align: center; font-size: 12px; letter-spacing: 1px; border: 1px solid transparent; animation: fadeIn 0.3s ease; }
.ok { background: rgba(0, 255, 170, 0.1); color: var(--accent); border-color: rgba(0, 255, 170, 0.2); }
.err { background: rgba(255, 74, 107, 0.1); color: var(--error); border-color: rgba(255, 74, 107, 0.2); }
.load { background: rgba(255, 193, 7, 0.1); color: #ffc107; border-color: rgba(255, 193, 7, 0.2); }
.bot-item { display: flex; flex-direction: column; padding: 16px; border-bottom: 1px solid rgba(255, 255, 255, 0.05); gap: 12px; }
.bot-item:last-child { border-bottom: none; }
.bot-header { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.bot-info { flex: 1; min-width: 0; }
.bot-info b { font-size: 13px; display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: #fff; letter-spacing: 0.5px; }
.bot-info small { font-size: 11px; color: var(--text-muted); display: block; margin-top: 3px; }
.badge { display: inline-block; padding: 4px 10px; border-radius: 6px; font-size: 10px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px; }
.badge.run { background: rgba(0, 255, 170, 0.15); color: var(--accent); border: 1px solid rgba(0, 255, 170, 0.2); }
.badge.stop { background: rgba(255, 255, 255, 0.05); color: var(--text-muted); border: 1px solid rgba(255, 255, 255, 0.1); }
.bot-actions { display: flex; gap: 6px; flex-wrap: wrap; }
.bot-actions button { flex: 1; min-width: 75px; padding: 8px; border: 1px solid transparent; border-radius: 6px; font-size: 10px; cursor: pointer; letter-spacing: 1px; box-shadow: none; text-transform: uppercase; }
.btn-start { background: rgba(0, 255, 170, 0.1); color: var(--accent); border-color: rgba(0, 255, 170, 0.2); }
.btn-stop { background: rgba(255, 193, 7, 0.1); color: #ffc107; border-color: rgba(255, 193, 7, 0.2); }
.btn-restart { background: rgba(0, 191, 255, 0.1); color: #00bfff; border-color: rgba(0, 191, 255, 0.2); }
.btn-edit { background: rgba(255, 255, 255, 0.05); color: #e2e8f0; border-color: rgba(255, 255, 255, 0.1); }
.btn-delete { background: rgba(255, 74, 107, 0.1); color: var(--error); border-color: rgba(255, 74, 107, 0.2); }
.sel-all { background: rgba(255, 255, 255, 0.03); color: #fff; border: 1px solid rgba(255, 255, 255, 0.08); padding: 12px; font-size: 11px; margin-bottom: 5px; box-shadow: none; }
#b { max-height: 450px; overflow-y: auto; }
.empty-state { text-align: center; padding: 25px 0; color: var(--text-muted); font-size: 12px; letter-spacing: 0.5px; }
.overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(5, 6, 8, 0.85); z-index: 1000; display: flex; align-items: center; justify-content: center; backdrop-filter: blur(6px); }
.modal-box { background: #12161c; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 14px; padding: 25px; max-width: 440px; width: 90%; box-shadow: 0 20px 50px rgba(0,0,0,0.5); box-sizing: border-box; text-align: center; }
.modal-box h3 { margin-top: 0; color: #fff; letter-spacing: 1px; font-size: 16px; margin-bottom: 12px; }
.modal-box p { color: var(--text-muted); font-size: 13px; margin-bottom: 20px; line-height: 1.5; }
.modal-actions { display: flex; gap: 10px; margin-top: 18px; }
.modal-actions button { flex: 1; padding: 12px; font-size: 12px; }
.btn-yes { background: var(--error); color: #fff; box-shadow: none; }
.btn-no { background: rgba(255, 255, 255, 0.05); color: #fff; border: 1px solid rgba(255, 255, 255, 0.1); box-shadow: none; }
.btn-save { background: linear-gradient(135deg, #00ffaa 0%, #00bfff 100%); color: #000; box-shadow: none; }
.login-container { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background-color: var(--bg-color); background-image: linear-gradient(rgba(18, 22, 28, 0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(18, 22, 28, 0.3) 1px, transparent 1px); background-size: 20px 20px; z-index: 2000; display: flex; align-items: center; justify-content: center; padding: 15px; box-sizing: border-box; }
.login-box { background: var(--card-bg); border: 1px solid var(--accent); padding: 35px 25px; border-radius: 16px; box-shadow: 0 0 30px rgba(0, 255, 170, 0.15); width: 100%; max-width: 380px; text-align: center; backdrop-filter: blur(15px); -webkit-backdrop-filter: blur(15px); box-sizing: border-box; position: relative; }
.login-box::before { content: 'SYS.AUTH_v3.2_FAST'; position: absolute; top: -10px; left: 20px; background: var(--bg-color); padding: 0 8px; font-size: 10px; color: var(--accent); letter-spacing: 1px; }
.login-box h2 { margin-top: 0; margin-bottom: 8px; color: #fff; font-size: 18px; text-transform: uppercase; letter-spacing: 2px; }
.login-box p { font-size: 11px; color: var(--text-muted); margin-top: 0; margin-bottom: 25px; letter-spacing: 0.5px; }
.login-box input { border-color: rgba(0, 255, 170, 0.2); }
@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
</style>
</head>
<body>
<div id="auth-block" class="login-container">
    <div class="login-box">
        <h2>TERMINAL ACCESS</h2>
        <p>Identity Verification Required</p>
        <input type="text" id="user" placeholder="HEX_ID / USERNAME">
        <input type="password" id="pass" placeholder="ACCESS_KEY / PASSWORD">
        <button onclick="attemptLogin()" style="margin-top:15px;">Bypass Gate</button>
        <div id="auth-err" class="status err" style="display:none; margin-top:15px;">AUTHENTICATION_FAILURE // REJECTED</div>
    </div>
</div>
<div class="c" id="main-panel">
<div class="h">
    <h1>// CENTRAL BOT OPERATIONS //</h1>
    <p>SECURE HIGH-SPEED ENGINE PORT</p>
</div>
<div class="card">
    <h2><span>🔌</span> Core parameters</h2>
    <input type="text" id="t" placeholder="ENTER TELEGRAM BOT TOKEN">
    <input type="text" id="c" placeholder="ENTER ADMIN CHAT ID (NUMERIC)">
</div>
<div class="card">
    <h2><span>🛠️</span> Service module payloads</h2>
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
    <h2><span>⏳</span> Expiry Timestamp</h2>
    <input type="date" id="e">
</div>
<div class="card">
    <button onclick="go()">🚀 Inject & Initialize Runtime</button>
    <div id="s" style="display:none;"></div>
</div>
<div class="card">
    <h2><span>📊</span> Active Process Threads</h2>
    <div id="b"><div class="empty-state">No active sub-processes loaded</div></div>
</div>
</div>
<div id="modal-container" style="display:none"></div>
<script>
var sel=new Set();
var editSel=new Set();
var totalPayloadsCount = 23;
function attemptLogin(){
  var u = document.getElementById("user").value;
  var p = document.getElementById("pass").value;
  var errBox = document.getElementById("auth-err");
  errBox.style.display = "none";
  fetch("/api/login", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({username: u, password: p})
  })
  .then(r => r.json())
  .then(d => {
    if(d.success){
      document.getElementById("auth-block").style.display = "none";
      document.getElementById("main-panel").style.display = "block";
      load();
      setInterval(load, 3000);
    } else {
      errBox.style.display = "block";
    }
  }).catch(() => { errBox.style.display = "block"; });
}
function tog(el){
  var t=el.getAttribute("data-t");
  if(sel.has(t)){sel.delete(t);el.classList.remove("s");}
  else{sel.add(t);el.classList.add("s");}
}
function togEdit(el){
  var t=el.getAttribute("data-t");
  if(editSel.has(t)){editSel.delete(t);el.classList.remove("s");}
  else{editSel.add(t);el.classList.add("s");}
}
function all(){
  var allKeys = ["phone","aadhaar","aadhaar_family","email","vehicle","github","instagram","tg_user","pan","tg_id","sms_bomber",
                 "name_search","adv_search","paytm_lookup","imei_lookup","call_tracer","upi_lookup","ifsc_lookup","pincode_lookup","ip_lookup","challan_lookup","ff_lookup","bgmi_lookup"];
  if(sel.size == totalPayloadsCount){
    sel.clear();
    document.querySelectorAll(".tool").forEach(function(e){e.classList.remove("s");});
  } else {
    sel = new Set(allKeys);
    document.querySelectorAll(".tool").forEach(function(e){e.classList.add("s");});
  }
}
function st(msg,cls){
  var s=document.getElementById("s");
  s.style.display = "block";
  s.className="status "+cls;
  s.textContent=msg;
}
function go(){
  var t=document.getElementById("t").value.trim();
  var c=document.getElementById("c").value.trim();
  var e=document.getElementById("e").value;
  var tools=Array.from(sel);
  if(!t){st("CRITICAL: TOKEN BUFFER EMPTY","err");return;}
  if(!c){st("CRITICAL: TARGET CHAT ID SPECIFICATION REQUIRED","err");return;}
  if(tools.length==0){st("CRITICAL: NO MODULE ATTACHMENTS LOADED","err");return;}
  st("INITIALIZING RUNTIME ENGINE PIPELINE...","load");
  fetch("/api/deploy",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({token:t,chat_id:c,tools:tools,expiry:e})})
  .then(function(r){return r.json();})
  .then(function(d){if(d.success){st("PROCESS THREAD DEPLOYED SUCCESSFULLY!","ok");load();}else{st(d.error||"DEPLOYMENT FAILURE","err");}})
  .catch(function(e){st("ERROR CONNECTING INTERFACE: "+e,"err");});
}
function toggleBot(id){
  fetch("/api/toggle/"+id,{method:"POST"})
  .then(function(r){return r.json();})
  .then(function(d){if(d.success)load();else alert("Operation Rejected");})
  .catch(function(e){alert("Connection Lost");});
}
...
function restartBot(id){
  fetch("/api/restart/"+id,{method:"POST"})
  .then(function(r){return r.json();})
  .then(function(d){if(d.success) load(); else alert("Restart Interrupt Flagged");})
  .catch(function(e){alert("Error recycling pipeline loop");});
}
function confirmDelete(id){
  var mc=document.getElementById("modal-container");
  mc.style.display="flex";
  mc.innerHTML='<div class="overlay"><div class="modal-box"><h3>⚠️ TERMINATE PROCESS</h3><p>Are you sure you want to completely purge and terminate this background bot context thread?</p><div class="modal-actions"><button class="btn-no" onclick="closeModal()">Abort</button><button class="btn-yes" onclick="deleteBot(\''+id+'\')">Purge Thread</button></div></div></div>';
}
function closeModal(){
  document.getElementById("modal-container").style.display="none";
}
function deleteBot(id){
  fetch("/api/delete/"+id,{method:"DELETE"})
  .then(function(r){return r.json();})
  .then(function(d){
    closeModal();
    if(d.success)load();
    else alert("Purge Request Interrupted");
  })
  .catch(function(e){alert("Purge Failure");});
}
function openEditModal(id, currentToken, currentChatId, currentToolsJson){
  var currentTools = JSON.parse(currentToolsJson);
  editSel = new Set(currentTools);
  var toolList = ["phone","aadhaar","aadhaar_family","email","vehicle","github","instagram","tg_user","pan","tg_id","sms_bomber",
                  "name_search","adv_search","paytm_lookup","imei_lookup","call_tracer","upi_lookup","ifsc_lookup","pincode_lookup","ip_lookup","challan_lookup","ff_lookup","bgmi_lookup"];
  var toolNames = {
    "phone":"📱 Phone", "aadhaar":"🆔 Aadhaar", "aadhaar_family":"👨‍👩‍👧 Family", "email":"📧 Email",
    "vehicle":"🚗 Vehicle", "github":"🐙 GitHub", "instagram":"📸 Instagram", "tg_user":"✈️ Telegram",
    "pan":"🪪 PAN", "tg_id":"🆔 TG ID", "sms_bomber":"💥 SMS",
    "name_search":"👤 Name Search", "adv_search":"🔍 Adv Search", "paytm_lookup":"💸 Paytm",
    "imei_lookup":"📱 IMEI", "call_tracer":"📡 Call Tracer", "upi_lookup":"💳 UPI Verify",
    "ifsc_lookup":"🏦 IFSC", "pincode_lookup":"📍 Pincode", "ip_lookup":"🌐 IP Lookup",
    "challan_lookup":"🧾 Challan Info", "ff_lookup":"🎮 FreeFire UID", "bgmi_lookup":"🔫 BGMI UID"
  };
  var toolsHtml = '<div class="tools" style="margin-top:10px; text-align:left; max-height:220px; overflow-y:auto; padding-right:5px;">';
  toolList.forEach(function(t){
    var selectedClass = editSel.has(t) ? "s" : "";
    toolsHtml += '<div class="edit-tool '+selectedClass+'" onclick="togEdit(this)" data-t="'+t+'">'+toolNames[t]+'</div>';
  });
  toolsHtml += '</div>';
  var mc=document.getElementById("modal-container");
  mc.style.display="flex";
  mc.innerHTML='<div class="overlay"><div class="modal-box" style="max-width:460px; border-color: rgba(0, 191, 255, 0.3);">'+
    '<h3>⚙️ RE-CONFIGURING THREAD COMPONENT</h3>'+
    '<div style="text-align:left; font-size:11px; color:var(--text-muted); margin-bottom:5px; text-transform:uppercase;">Bot Token Header:</div>'+
    '<input type="text" id="edit-t" value="'+currentToken+'">'+
    '<div style="text-align:left; font-size:11px; color:var(--text-muted); margin-bottom:5px; text-transform:uppercase;">System Admin Chat ID:</div>'+
    '<input type="text" id="edit-c" value="'+currentChatId+'">'+
    '<div style="text-align:left; font-size:11px; color:var(--text-muted); margin-top:10px; text-transform:uppercase;">Re-allocate Payload Flags:</div>'+
    toolsHtml +
    '<div class="modal-actions">'+
      '<button class="btn-no" onclick="closeModal()">Cancel Changes</button>'+
      '<button class="btn-save" onclick="saveBotEdit(\''+id+'\')">Apply Parameters</button>'+
    '</div>'+
  '</div></div>';
}
function saveBotEdit(id){
  var t = document.getElementById("edit-t").value.trim();
  var c = document.getElementById("edit-c").value.trim();
  var tools = Array.from(editSel);
  if(!t || !c || tools.length == 0){
    alert("Parameters matrix cannot contain empty constraints!");
    return;
  }
  fetch("/api/edit/"+id,{
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify({token:t, chat_id:c, tools:tools})
  })
  .then(function(r){return r.json();})
  .then(function(d){
    if(d.success){
      closeModal();
      load();
    } else {
      alert("Hot-patching parameters operation crashed.");
    }
  }).catch(() => { alert("Error tracking remote socket context"); });
}
function load(){
  fetch("/api/bots").then(function(r){ if(r.status==401){location.reload();}; return r.json(); }).then(function(d){
    var b=document.getElementById("b");
    if(!d.bots||d.bots.length==0){b.innerHTML='<div class="empty-state">No active sub-processes loaded</div>';return;}
    var html='';
    for(var i=0;i<d.bots.length;i++){
      var bot=d.bots[i];
      var statusClass=bot.run?"run":"stop";
      var statusText=bot.run?"ONLINE":"IDLE";
      var toggleBtnText=bot.run?"⏹ Kill":"▶ Fire";
      var toggleBtnClass=bot.run?"btn-stop":"btn-start";
      var toolsJsonStr = JSON.stringify(bot.tools).replace(/"/g, '&quot;');
      html+='<div class="bot-item">'+
        '<div class="bot-header">'+
          '<div class="bot-info">'+
            '<b>ID: '+bot.tp+'</b>'+
            '<small>📊 Active Modules: '+bot.tools.length+' | Expiry Anchor: '+bot.exp+'</small>'+
          '</div>'+
          '<div><span class="badge '+statusClass+'">'+statusText+'</span></div>'+
        '</div>'+
        '<div class="bot-actions">'+
          '<button class="'+toggleBtnClass+'" onclick="toggleBot(\''+bot.id+'\')">'+toggleBtnText+'</button>'+
          '<button class="btn-restart" onclick="restartBot(\''+bot.id+'\')">🔄 Recycle</button>'+
          '<button class="btn-edit" onclick="openEditModal(\''+bot.id+'\',\''+bot.full_token+'\',\''+bot.chat_id+'\',\''+toolsJsonStr+'\')">⚙️ Patch</button>'+
          '<button class="btn-delete" onclick="confirmDelete(\''+bot.id+'\')">🗑 Purge</button>'+
        '</div>'+
      '</div>';
    }
    b.innerHTML=html;
  }).catch(() => {});
}
</script>
</body>
</html>"""

@app.route("/api/login", methods=["POST"])
def api_login():
    try:
        d = request.get_json()
        password = d.get("password", "")
        if password == ADMIN_PASSWORD:
            session["logged_in"] = True
            return jsonify({"success": True, "message": "Access Granted"})
        return jsonify({"success": False, "error": "Unauthorized Access Detected"}), 401
    except:
        return jsonify({"success": False, "error": "System Malfunction"}), 400

@app.route("/api/deploy", methods=["POST"])
def deploy():
    if not check_auth(): return jsonify({"success": False, "error": "Unauthorized"}), 401
    try:
        d = request.get_json()
        if not d: return jsonify({"success": False, "error": "Null Payload Received"})
        token = d.get("token", "").strip()
        chat_id = d.get("chat_id", "").strip()
        tools = d.get("tools", [])
        expiry = d.get("expiry", "")
        if not token or not chat_id or not tools: return jsonify({"success": False, "error": "Empty Allocation Bounds"})
        
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
        return jsonify({"success": True, "bot_id": bid, "message": "Thread Active"})
    except Exception as e: return jsonify({"success": False, "error": str(e)})

@app.route("/api/bots", methods=["GET"])
def list_bots():
    if not check_auth(): return jsonify({"success": False, "error": "Unauthorized"}), 401
    try:
        bots = []
        for bid, b in running_bots.items():
            bots.append({
                "id": bid,
                "tp": b.token[:12] + "..." if len(b.token) > 12 else b.token,
                "full_token": b.token,
                "chat_id": b.chat_id,
                "tools": b.tools,
                "exp": b.expiry or "INFINITE",
                "run": b.running
            })
        return jsonify({"bots": bots})
    except Exception as e: return jsonify({"bots": [], "error": str(e)})

@app.route("/api/toggle/<bid>", methods=["POST"])
def toggle(bid):
    if not check_auth(): return jsonify({"success": False, "error": "Unauthorized"}), 401
    try:
        if bid not in running_bots: return jsonify({"success": False, "error": "Context Missing"})
        b = running_bots[bid]
        if b.running: 
            b.stop()
            update_bot_status_in_db(bid, False)
            return jsonify({"success": True})
        else: 
            b.start()
            update_bot_status_in_db(bid, True)
            return jsonify({"success": True})
    except Exception as e: return jsonify({"success": False, "error": str(e)})

@app.route("/api/restart/<bid>", methods=["POST"])
def restart(bid):
    if not check_auth(): return jsonify({"success": False, "error": "Unauthorized"}), 401
    try:
        if bid not in running_bots: return jsonify({"success": False, "error": "Context Missing"})
        b = running_bots[bid]
        b.stop()
        time.sleep(1)  
        b.start()
        return jsonify({"success": True})
    except Exception as e: return jsonify({"success": False, "error": str(e)})

@app.route("/api/edit/<bid>", methods=["POST"])
def edit_bot(bid):
    if not check_auth(): return jsonify({"success": False, "error": "Unauthorized"}), 401
    try:
        if bid not in running_bots: return jsonify({"success": False, "error": "Context Missing"})
        d = request.get_json()
        token = d.get("token", "").strip()
        chat_id = d.get("chat_id", "").strip()
        tools = d.get("tools", [])
        
        if not token or not chat_id or not tools: return jsonify({"success": False, "error": "Bad Configuration Array"})
        
        b = running_bots[bid]
        was_running = b.running
        if was_running:
            b.stop()
            time.sleep(1)
            
        b.update_config(token, chat_id, tools)
        if was_running: b.start()
            
        return jsonify({"success": True})
    except Exception as e: return jsonify({"success": False, "error": str(e)})

@app.route("/api/delete/<bid>", methods=["DELETE"])
def delete(bid):
    if not check_auth(): return jsonify({"success": False, "error": "Unauthorized"}), 401
    try:
        if bid not in running_bots: return jsonify({"success": False, "error": "Context Missing"})
        running_bots[bid].stop()
        delete_bot_from_db(bid)
        del running_bots[bid]
        return jsonify({"success": True})
    except Exception as e: return jsonify({"success": False, "error": str(e)})

if __name__ == "__main__":
    init_db()  
    restore_active_bots()  
    port = int(os.environ.get("PORT", 5990))
    app.run(host="0.0.0.0", port=port, debug=False)
