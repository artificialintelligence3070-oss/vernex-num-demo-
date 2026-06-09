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
            # --- NEW API TARGET ATTACHMENTS ---
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
            # --- NEW PROMPT TEXT SCHEMAS ---
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
                            
                            # Determine custom keys based on requested endpoint configurations
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

    .c {
        max-width: 650px;
        margin: 0 auto;
        display: none;
        animation: fadeIn 0.6s ease-out;
    }

    .h {
        text-align: center;
        padding: 25px 0 15px 0;
    }

    .h h1 {
        font-size: 22px;
        text-transform: uppercase;
        letter-spacing: 3px;
        color: var(--accent);
        text-shadow: 0 0 10px var(--accent-glow);
        margin: 0;
    }
    
    .h p {
        font-size: 11px;
        color: var(--text-muted);
        margin: 5px 0 0 0;
        letter-spacing: 1px;
    }

    .card {
        background: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 22px;
        margin-bottom: 20px;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }

    .card h2 {
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: var(--accent);
        margin-top: 0;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    input {
        width: 100%;
        padding: 14px;
        background: rgba(10, 11, 13, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 8px;
        margin-bottom: 12px;
        box-sizing: border-box;
        font-size: 13px;
        color: #fff;
        font-family: inherit;
        transition: all 0.3s ease;
    }

    input:focus {
        outline: none;
        border-color: var(--accent);
        box-shadow: 0 0 8px var(--accent-glow);
        background: rgba(10, 11, 13, 0.95);
    }

    button {
        width: 100%;
        padding: 15px;
        background: linear-gradient(135deg, #00
