from datetime import datetime
import csv
import io
import os
import sqlite3
from flask import Flask, Response, jsonify, redirect, render_template_string, request, session, url_for
import requests

app = Flask(__name__)
app.secret_key = os.urandom(24)

DB_PATH = "/tmp/osint_gateway.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_string TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            expiry_date TEXT NOT NULL,
            request_limit INTEGER NOT NULL,
            requests_used INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Active',
            created_at TEXT NOT NULL
        )
    """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS api_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_string TEXT NOT NULL,
            tool TEXT NOT NULL,
            query_params TEXT NOT NULL,
            ip_address TEXT,
            status_code INTEGER,
            timestamp TEXT NOT NULL
        )
    """
    )
    conn.commit()
    conn.close()


init_db()

UPSTREAM_BASE = "https://ft-osint-api.duckdns.org/api"

# Comprehensive list of all requested OSINT endpoints
TOOLS = {
    "pk": {"name": "PK Number Lookup", "param": "num"},
    "name": {"name": "Name Search Lookup", "param": "name"},
    "aadhar": {"name": "Aadhar Information Lookup", "param": "num"},
    "upi": {"name": "UPI ID Lookup", "param": "upi"},
    "numtoupi": {"name": "Number to UPI Lookup", "param": "num"},
    "pan": {"name": "PAN Card Lookup", "param": "pan"},
    "vehicle": {"name": "Vehicle RC Lookup", "param": "vehicle"},
    "veh2num": {"name": "Vehicle to Number Lookup", "param": "vehicle"},
    "adharfamily": {"name": "Aadhar Family Tree Lookup", "param": "num"},
    "bomber": {"name": "SMS / Call Bomber Tool", "param": "number"},
    "adv": {"name": "Advanced Number Lookup", "param": "num"},
    "paytm": {"name": "Paytm Wallet Info", "param": "num"},
    "imei": {"name": "IMEI Lookup", "param": "imei"},
    "calltracer": {"name": "Call Tracer", "param": "num"},
    "ifsc": {"name": "IFSC Code Lookup", "param": "ifsc"},
    "pincode": {"name": "Pincode Info", "param": "pin"},
    "ip": {"name": "IP Geolocation", "param": "ip"},
    "challan": {"name": "Vehicle Challan", "param": "vehicle"},
    "ff": {"name": "Free Fire UID Info", "param": "uid"},
    "bgmi": {"name": "BGMI UID Info", "param": "uid"},
    "snap": {"name": "Snapchat Info", "param": "username"},
    "number": {"name": "Standard Number Lookup", "param": "num"},
    "email": {"name": "Email to Info", "param": "email"},
    "git": {"name": "GitHub Lookup", "param": "username"},
    "insta": {"name": "Instagram Info", "param": "username"},
    "tg": {"name": "Telegram Username Info", "param": "info"},
    "tgidinfo": {"name": "Telegram ID to Num", "param": "id"},
    "numleak": {"name": "Number Leak Check", "param": "num"},
}


# --- UI TEMPLATES (3D Glassmorphism Premium Style) ---

BASE_LAYOUT = """
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}SHAYAN_EXPLORER OSINT Command Center{% endblock %}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        darkbg: '#030712',
                        cardbg: 'rgba(15, 23, 42, 0.7)',
                    }
                }
            }
        }
    </script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap');
        body { font-family: 'Plus Jakarta Sans', sans-serif; background: #030712; color: #f8fafc; overflow-x: hidden; }
        code, pre { font-family: 'JetBrains Mono', monospace; }
        .glass-3d {
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.6) 0%, rgba(15, 23, 42, 0.8) 100%);
            backdrop-filter: blur(25px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.8), inset 0 1px 0 rgba(255, 255, 255, 0.1);
        }
        .glass-card-hover {
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .glass-card-hover:hover {
            transform: translateY(-4px);
            border-color: rgba(59, 130, 246, 0.4);
            box-shadow: 0 30px 60px -12px rgba(59, 130, 246, 0.15), inset 0 1px 0 rgba(255, 255, 255, 0.2);
        }
        .glow-blue { box-shadow: 0 0 50px rgba(59, 130, 246, 0.25); }
        .glow-purple { box-shadow: 0 0 50px rgba(168, 85, 247, 0.25); }
        .gradient-text { background: linear-gradient(135deg, #60a5fa 0%, #c084fc 50%, #f472b6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .custom-scrollbar::-webkit-scrollbar { width: 6px; height: 6px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: rgba(3, 7, 18, 0.5); }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.15); border-radius: 4px; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.3); }
    </style>
</head>
<body class="min-h-screen flex flex-col selection:bg-blue-600 selection:text-white">
    <!-- Navbar -->
    <nav class="border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-2xl sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
            <a href="/" class="flex items-center space-x-3.5 group">
                <div class="w-12 h-12 rounded-2xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-purple-600 flex items-center justify-center shadow-2xl shadow-blue-500/40 group-hover:scale-105 transition">
                    <i class="fa-solid fa-shield-halved text-white text-xl"></i>
                </div>
                <div>
                    <span class="font-extrabold text-xl tracking-tight gradient-text">SHAYAN_EXPLORER</span>
                    <span class="block text-[10px] text-slate-400 font-bold tracking-widest uppercase">Enterprise OSINT Intelligence API</span>
                </div>
            </a>
            <div class="flex items-center space-x-3">
                <a href="/" class="px-4 py-2 text-xs font-semibold rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 transition flex items-center gap-2">
                    <code class="text-blue-400 font-bold">28+</code> Endpoints
                </a>
                {% if session.get('logged_in') %}
                    <a href="/dashboard" class="px-4 py-2 text-xs font-bold rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:opacity-95 text-white shadow-lg shadow-blue-600/30 transition flex items-center gap-2">
                        <i class="fa-solid fa-gauge-high"></i> Command Center
                    </a>
                    <a href="/logout" title="Logout" class="p-2.5 text-xs font-medium rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/20 transition">
                        <i class="fa-solid fa-power-off"></i>
                    </a>
                {% else %}
                    <a href="/login" class="px-4 py-2 text-xs font-bold rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700 transition flex items-center gap-2">
                        <i class="fa-solid fa-lock"></i> Admin Portal
                    </a>
                {% endif %}
            </div>
        </div>
    </nav>

    <!-- Main Content -->
    <main class="flex-grow max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {% block content %}{% endblock %}
    </main>

    <!-- Footer -->
    <footer class="border-t border-slate-900 bg-slate-950/90 py-8 text-center text-xs text-slate-500">
        <p>&copy; 2026 <span class="text-slate-400 font-semibold">SHAYAN_EXPLORER</span>. Enterprise OSINT Gateway & API Management Suite. All rights reserved.</p>
    </footer>
</body>
</html>
"""

INDEX_TEMPLATE = (
    BASE_LAYOUT
    + """
{% block content %}
<div class="space-y-12">
    <!-- Hero Banner -->
    <div class="glass-3d rounded-3xl p-8 sm:p-14 text-center relative overflow-hidden glow-blue">
        <div class="absolute -top-32 -left-32 w-96 h-96 bg-blue-600/15 rounded-full blur-3xl pointer-events-none"></div>
        <div class="absolute -bottom-32 -right-32 w-96 h-96 bg-purple-600/15 rounded-full blur-3xl pointer-events-none"></div>
        
        <div class="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-bold bg-blue-500/10 text-blue-400 border border-blue-500/20 mb-6 shadow-inner">
            <span class="w-2.5 h-2.5 rounded-full bg-blue-400 animate-ping"></span> 28+ OSINT Endpoints Activated & Verified
        </div>
        <h1 class="text-4xl sm:text-6xl font-extrabold tracking-tight mb-6">
            Next-Gen <span class="gradient-text">OSINT Intelligence</span> & API Gateway
        </h1>
        <p class="text-slate-400 text-base sm:text-lg max-w-3xl mx-auto mb-8 leading-relaxed">
            Engineered by <strong class="text-white">SHAYAN_EXPLORER</strong>. Access high-performance intelligence APIs including Aadhar, PAN, UPI, PK lookups, vehicle databases, and digital forensics with real-time rate limiting and dynamic key security.
        </p>
        <div class="flex flex-wrap justify-center gap-4">
            <a href="#endpoints" class="px-7 py-3.5 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:opacity-95 text-white font-bold shadow-xl shadow-blue-500/30 transition flex items-center gap-2">
                <i class="fa-solid fa-code"></i> Explore All Endpoints
            </a>
            <a href="/login" class="px-7 py-3.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-800 font-bold transition flex items-center gap-2">
                <i class="fa-solid fa-key"></i> Key Management Portal
            </a>
        </div>
    </div>

    <!-- Features Grid Bar -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div class="glass-3d rounded-2xl p-5 border-slate-800/80">
            <div class="text-blue-400 text-2xl mb-2"><i class="fa-solid fa-shield-cat"></i></div>
            <h4 class="font-bold text-sm mb-1 text-white">Token Security</h4>
            <p class="text-xs text-slate-400">Custom expiration dates & dynamic rate limits.</p>
        </div>
        <div class="glass-3d rounded-2xl p-5 border-slate-800/80">
            <div class="text-purple-400 text-2xl mb-2"><i class="fa-solid fa-terminal"></i></div>
            <h4 class="font-bold text-sm mb-1 text-white">Instant cURL</h4>
            <p class="text-xs text-slate-400">One-click copy code snippets for every tool.</p>
        </div>
        <div class="glass-3d rounded-2xl p-5 border-slate-800/80">
            <div class="text-emerald-400 text-2xl mb-2"><i class="fa-solid fa-chart-line"></i></div>
            <h4 class="font-bold text-sm mb-1 text-white">Live Audit Logs</h4>
            <p class="text-xs text-slate-400">Track client IPs, parameters, and response status.</p>
        </div>
        <div class="glass-3d rounded-2xl p-5 border-slate-800/80">
            <div class="text-pink-400 text-2xl mb-2"><i class="fa-solid fa-file-csv"></i></div>
            <h4 class="font-bold text-sm mb-1 text-white">CSV Data Export</h4>
            <p class="text-xs text-slate-400">Download query logs for analysis anytime.</p>
        </div>
    </div>

    <!-- Endpoints Documentation -->
    <div id="endpoints" class="space-y-6">
        <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
                <h2 class="text-2xl font-bold tracking-tight">Active API Endpoints Reference</h2>
                <p class="text-xs text-slate-400 mt-1">Base URL: <code class="text-blue-400">https://&lt;your-vercel-domain&gt;/api/&lt;tool_name&gt;?key=explorer16&amp;&lt;param&gt;=value</code></p>
            </div>
            <span class="px-3.5 py-1.5 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20 text-xs font-bold">
                <i class="fa-solid fa-layer-group mr-1.5"></i> All APIs Connected
            </span>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
            {% for code, info in tools.items() %}
            <div class="glass-3d rounded-2xl p-6 border-slate-800/80 glass-card-hover flex flex-col justify-between">
                <div>
                    <div class="flex items-center justify-between mb-3">
                        <span class="px-3 py-1 rounded-lg text-xs font-mono font-bold bg-slate-900 text-blue-400 border border-slate-800">/api/{{ code }}</span>
                        <span class="text-xs text-slate-400">Required Param: <code class="text-purple-400 font-bold">{{ info.param }}</code></span>
                    </div>
                    <h3 class="text-base font-bold text-white mb-2">{{ info.name }}</h3>
                </div>
                <div class="mt-4 space-y-3">
                    <div class="bg-slate-950/90 rounded-xl p-3 font-mono text-xs text-slate-300 overflow-x-auto border border-slate-900 flex items-center justify-between">
                        <span>curl -X GET "https://YOUR_DOMAIN/api/{{ code }}?key=explorer16&{{ info.param }}=VALUE"</span>
                        <button onclick="navigator.clipboard.writeText('curl -X GET \"https://' + window.location.host + '/api/{{ code }}?key=explorer16&{{ info.param }}=SAMPLE\"'); alert('cURL copied to clipboard!');" class="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition text-xs shrink-0 ml-2" title="Copy cURL">
                            <i class="fa-solid fa-copy"></i>
                        </button>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
</div>
{% endblock `
)

LOGIN_TEMPLATE = (
    BASE_LAYOUT
    + """
{% block content %}
<div class="max-w-md mx-auto mt-20">
    <div class="glass-3d rounded-3xl p-8 sm:p-10 border-slate-800 shadow-2xl glow-purple">
        <div class="text-center mb-8">
            <div class="w-16 h-16 rounded-2xl bg-gradient-to-tr from-purple-600 to-blue-600 text-white flex items-center justify-center text-2xl mx-auto mb-4 shadow-xl shadow-purple-500/40">
                <i class="fa-solid fa-shield-keyhole"></i>
            </div>
            <h2 class="text-2xl font-bold">Admin Portal Login</h2>
            <p class="text-slate-400 text-xs mt-1">SHAYAN_EXPLORER Secure Command Center</p>
        </div>

        {% if error %}
        <div class="mb-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center gap-3">
            <i class="fa-solid fa-triangle-exclamation text-base"></i> {{ error }}
        </div>
        {% endif %}

        <form method="POST" class="space-y-5">
            <div>
                <label class="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Username</label>
                <div class="relative">
                    <span class="absolute inset-y-0 left-0 pl-4 flex items-center text-slate-500"><i class="fa-solid fa-user"></i></span>
                    <input type="text" name="username" required value="vernex" class="w-full pl-11 pr-4 py-3 bg-slate-900 border border-slate-800 rounded-xl text-white placeholder-slate-600 focus:outline-none focus:border-blue-500 transition text-sm">
                </div>
            </div>
            <div>
                <label class="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Password</label>
                <div class="relative">
                    <span class="absolute inset-y-0 left-0 pl-4 flex items-center text-slate-500"><i class="fa-solid fa-lock"></i></span>
                    <input type="password" name="password" required value="vernex@16vx" class="w-full pl-11 pr-4 py-3 bg-slate-900 border border-slate-800 rounded-xl text-white placeholder-slate-600 focus:outline-none focus:border-blue-500 transition text-sm">
                </div>
            </div>
            <button type="submit" class="w-full py-3.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:opacity-95 text-white font-bold shadow-lg shadow-blue-600/30 transition text-sm">
                Authenticate Session
            </button>
        </form>
    </div>
</div>
{% endblock %}
"""
)

DASHBOARD_TEMPLATE = (
    BASE_LAYOUT
    + """
{% block content %}
<div class="space-y-8">
    <!-- Header Stats -->
    <div class="grid grid-cols-1 sm:grid-cols-4 gap-5">
        <div class="glass-3d rounded-2xl p-6 border-slate-800 flex items-center justify-between">
            <div>
                <p class="text-[10px] uppercase font-bold text-slate-400 mb-1">Active Keys</p>
                <h3 class="text-3xl font-extrabold text-white">{{ keys|length }}</h3>
            </div>
            <div class="w-12 h-12 rounded-xl bg-blue-500/10 text-blue-400 flex items-center justify-center text-xl border border-blue-500/20">
                <i class="fa-solid fa-key"></i>
            </div>
        </div>
        <div class="glass-3d rounded-2xl p-6 border-slate-800 flex items-center justify-between">
            <div>
                <p class="text-[10px] uppercase font-bold text-slate-400 mb-1">Total Audit Logs</p>
                <h3 class="text-3xl font-extrabold text-white">{{ logs|length }}</h3>
            </div>
            <div class="w-12 h-12 rounded-xl bg-purple-500/10 text-purple-400 flex items-center justify-center text-xl border border-purple-500/20">
                <i class="fa-solid fa-rectangle-list"></i>
            </div>
        </div>
        <div class="glass-3d rounded-2xl p-6 border-slate-800 flex items-center justify-between">
            <div>
                <p class="text-[10px] uppercase font-bold text-slate-400 mb-1">Gateway Engine</p>
                <h3 class="text-lg font-extrabold text-emerald-400 flex items-center gap-2 mt-1">
                    <span class="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping"></span> Online
                </h3>
            </div>
            <div class="w-12 h-12 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center text-xl border border-emerald-500/20">
                <i class="fa-solid fa-server"></i>
            </div>
        </div>
        <div class="glass-3d rounded-2xl p-6 border-slate-800 flex items-center justify-between">
            <div>
                <p class="text-[10px] uppercase font-bold text-slate-400 mb-1">Data Actions</p>
                <div class="flex gap-2 mt-1">
                    <a href="/dashboard/export-csv" class="px-3 py-1.5 rounded-lg bg-pink-500/10 hover:bg-pink-500/20 text-pink-400 text-xs font-bold border border-pink-500/20 transition flex items-center gap-1.5">
                        <i class="fa-solid fa-download"></i> CSV
                    </a>
                    <a href="/dashboard/clear-logs" onclick="return confirm('Clear all query audit logs?');" class="px-3 py-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 text-xs font-bold border border-rose-500/20 transition flex items-center gap-1.5">
                        <i class="fa-solid fa-trash-can"></i> Clear
                    </a>
                </div>
            </div>
            <div class="w-12 h-12 rounded-xl bg-pink-500/10 text-pink-400 flex items-center justify-center text-xl border border-pink-500/20">
                <i class="fa-solid fa-database"></i>
            </div>
        </div>
    </div>

    <!-- Generate Custom API Key Form -->
    <div class="glass-3d rounded-3xl p-8 border-slate-800">
        <h2 class="text-xl font-bold mb-6 flex items-center gap-3">
            <i class="fa-solid fa-circle-plus text-blue-500"></i> Generate Custom API Key (Name, Expiry Date & Request Limit)
        </h2>
        <form method="POST" action="/dashboard/create-key" class="grid grid-cols-1 sm:grid-cols-4 gap-5 items-end">
            <div>
                <label class="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Key Owner / Name</label>
                <input type="text" name="name" required placeholder="e.g. SHAYAN_VIP_CLIENT" class="w-full px-4 py-3 bg-slate-900 border border-slate-800 rounded-xl text-white text-sm focus:outline-none focus:border-blue-500">
            </div>
            <div>
                <label class="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Custom Key String</label>
                <input type="text" name="key_string" required value="explorer16" class="w-full px-4 py-3 bg-slate-900 border border-slate-800 rounded-xl text-blue-400 font-mono text-sm focus:outline-none focus:border-blue-500">
            </div>
            <div>
                <label class="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Expiry Date & Time</label>
                <input type="datetime-local" name="expiry_date" required class="w-full px-4 py-3 bg-slate-900 border border-slate-800 rounded-xl text-white text-sm focus:outline-none focus:border-blue-500">
            </div>
            <div>
                <label class="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Request Limit</label>
                <input type="number" name="request_limit" required value="10000" class="w-full px-4 py-3 bg-slate-900 border border-slate-800 rounded-xl text-white text-sm focus:outline-none focus:border-blue-500 font-mono">
            </div>
            <div class="sm:col-span-4 mt-2">
                <button type="submit" class="px-6 py-3.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:opacity-95 text-white font-bold shadow-lg shadow-blue-600/30 transition text-sm flex items-center gap-2">
                    <i class="fa-solid fa-key"></i> Provision & Save Custom API Key
                </button>
            </div>
        </form>
    </div>

    <!-- Active API Keys Table -->
    <div class="glass-3d rounded-3xl p-8 border-slate-800">
        <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
            <h2 class="text-xl font-bold flex items-center gap-3">
                <i class="fa-solid fa-keys text-purple-500"></i> Active API Keys & Usage Control
            </h2>
            <input type="text" id="keySearch" onkeyup="filterKeys()" placeholder="Search keys or names..." class="px-4 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-blue-500 w-full sm:w-64">
        </div>
        <div class="overflow-x-auto custom-scrollbar">
            <table class="w-full text-left text-sm text-slate-300" id="keysTable">
                <thead class="bg-slate-900/80 text-[10px] uppercase text-slate-400 font-bold border-b border-slate-800">
                    <tr>
                        <th class="py-4 px-4">Identifier Name</th>
                        <th class="py-4 px-4">API Key</th>
                        <th class="py-4 px-4">Expiry Date</th>
                        <th class="py-4 px-4">Usage / Limit</th>
                        <th class="py-4 px-4">Status</th>
                        <th class="py-4 px-4 text-right">Actions</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-slate-800/60">
                    {% for k in keys %}
                    <tr class="hover:bg-slate-900/40 transition">
                        <td class="py-4 px-4 font-bold text-white">{{ k[2] }}</td>
                        <td class="py-4 px-4 font-mono text-blue-400 select-all">{{ k[1] }}</td>
                        <td class="py-4 px-4 text-slate-400 text-xs">{{ k[3] }}</td>
                        <td class="py-4 px-4">
                            <div class="flex items-center gap-3">
                                <span class="font-mono text-xs">{{ k[5] }} / {{ k[4] }}</span>
                                <div class="w-24 bg-slate-800 rounded-full h-2 overflow-hidden">
                                    <div class="bg-gradient-to-r from-blue-500 to-purple-500 h-full rounded-full" style="width: {{ (k[5] / k[4] * 100) if k[4] > 0 else 0 }}%"></div>
                                </div>
                            </div>
                        </td>
                        <td class="py-4 px-4">
                            <span class="px-2.5 py-1 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                                {{ k[6] }}
                            </span>
                        </td>
                        <td class="py-4 px-4 text-right space-x-2">
                            <form method="POST" action="/dashboard/reset-usage" class="inline">
                                <input type="hidden" name="key_id" value="{{ k[0] }}">
                                <button type="submit" title="Reset Usage Counter" class="px-2.5 py-1.5 rounded-lg bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 text-xs font-bold border border-blue-500/20 transition">
                                    <i class="fa-solid fa-rotate-right"></i>
                                </button>
                            </form>
                            <form method="POST" action="/dashboard/delete-key" class="inline">
                                <input type="hidden" name="key_id" value="{{ k[0] }}">
                                <button type="submit" title="Revoke Key" class="px-2.5 py-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 text-xs font-bold border border-rose-500/20 transition">
                                    <i class="fa-solid fa-trash"></i>
                                </button>
                            </form>
                        </td>
                    </tr>
                    {% else %}
                    <tr>
                        <td colspan="6" class="py-8 text-center text-slate-500">No API keys provisioned yet. Use the form above.</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

    <!-- Live Audit Logs & Search History -->
    <div class="glass-3d rounded-3xl p-8 border-slate-800">
        <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
            <h2 class="text-xl font-bold flex items-center gap-3">
                <i class="fa-solid fa-clock-rotate-left text-pink-500"></i> Real-Time Audit Query Logs & Search History
            </h2>
            <input type="text" id="logSearch" onkeyup="filterLogs()" placeholder="Search logs by IP, tool or query..." class="px-4 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-blue-500 w-full sm:w-64">
        </div>
        <div class="overflow-x-auto custom-scrollbar">
            <table class="w-full text-left text-sm text-slate-300" id="logsTable">
                <thead class="bg-slate-900/80 text-[10px] uppercase text-slate-400 font-bold border-b border-slate-800">
                    <tr>
                        <th class="py-4 px-4">Timestamp</th>
                        <th class="py-4 px-4">API Key Used</th>
                        <th class="py-4 px-4">Tool Endpoint</th>
                        <th class="py-4 px-4">Query Parameters</th>
                        <th class="py-4 px-4">Status</th>
                        <th class="py-4 px-4">Client IP</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-slate-800/60 font-mono text-xs">
                    {% for l in logs %}
                    <tr class="hover:bg-slate-900/40 transition">
                        <td class="py-4 px-4 text-slate-400">{{ l[5] }}</td>
                        <td class="py-4 px-4 text-blue-400">{{ l[1] }}</td>
                        <td class="py-4 px-4 text-purple-400">/api/{{ l[2] }}</td>
                        <td class="py-4 px-4 text-slate-300 max-w-xs truncate" title="{{ l[3] }}">{{ l[3] }}</td>
                        <td class="py-4 px-4">
                            <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                                {{ l[4] }} OK
                            </span>
                        </td>
                        <td class="py-4 px-4 text-slate-500">{{ l[6] }}</td>
                    </tr>
                    {% else %}
                    <tr>
                        <td colspan="6" class="py-8 text-center text-slate-500 font-sans">No search queries logged yet.</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>

<script>
function filterKeys() {
    let input = document.getElementById("keySearch").value.toLowerCase();
    let trs = document.getElementById("keysTable").getElementsByTagName("tr");
    for (let i = 1; i < trs.length; i++) {
        let td = trs[i].innerText.toLowerCase();
        trs[i].style.display = td.includes(input) ? "" : "none";
    }
}
function filterLogs() {
    let input = document.getElementById("logSearch").value.toLowerCase();
    let trs = document.getElementById("logsTable").getElementsByTagName("tr");
    for (let i = 1; i < trs.length; i++) {
        let td = trs[i].innerText.toLowerCase();
        trs[i].style.display = td.includes(input) ? "" : "none";
    }
}
</script>
{% endblock %}
"""
)


# --- FLASK ROUTES ---


@app.route("/")
def index():
    return render_template_string(INDEX_TEMPLATE, tools=TOOLS)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == "vernex" and password == "vernex@16vx":
            session["logged_in"] = True
            return redirect(url_for("dashboard"))
        else:
            error = "Invalid administrator credentials. Please check your username and password."
    return render_template_string(LOGIN_TEMPLATE, error=error)


@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("index"))


@app.route("/dashboard")
def dashboard():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM api_keys ORDER BY id DESC")
    keys = cursor.fetchall()
    cursor.execute("SELECT * FROM api_logs ORDER BY id DESC LIMIT 100")
    logs = cursor.fetchall()
    conn.close()

    return render_template_string(
        DASHBOARD_TEMPLATE, keys=keys, logs=logs, tools=TOOLS
    )


@app.route("/dashboard/create-key", methods=["POST"])
def create_key():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    name = request.form.get("name")
    key_string = request.form.get("key_string")
    expiry_date = request.form.get("expiry_date")
    request_limit = int(request.form.get("request_limit", 10000))
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO api_keys (key_string, name, expiry_date, request_limit, status, created_at) VALUES (?, ?, ?, ?, 'Active', ?)",
            (key_string, name, expiry_date, request_limit, created_at),
        )
        conn.commit()
    except Exception as e:
        print(f"Error creating key: {e}")
    finally:
        conn.close()

    return redirect(url_for("dashboard"))


@app.route("/dashboard/delete-key", methods=["POST"])
def delete_key():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    key_id = request.form.get("key_id")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM api_keys WHERE id = ?", (key_id,))
    conn.commit()
    conn.close()

    return redirect(url_for("dashboard"))


@app.route("/dashboard/reset-usage", methods=["POST"])
def reset_usage():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    key_id = request.form.get("key_id")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE api_keys SET requests_used = 0 WHERE id = ?", (key_id,)
    )
    conn.commit()
    conn.close()

    return redirect(url_for("dashboard"))


@app.route("/dashboard/clear-logs")
def clear_logs():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM api_logs")
    conn.commit()
    conn.close()

    return redirect(url_for("dashboard"))


@app.route("/dashboard/export-csv")
def export_csv():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, key_string, tool, query_params, status_code, ip_address, timestamp FROM api_logs ORDER BY id DESC"
    )
    rows = cursor.fetchall()
    conn.close()

    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(
        [
            "ID",
            "API Key",
            "Tool",
            "Query Parameters",
            "Status Code",
            "Client IP",
            "Timestamp",
        ]
    )
    cw.writerows(rows)

    output = si.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment;filename=shayan_explorer_audit_logs.csv"
        },
    )


# --- API PROXY & VALIDATION ENDPOINT ---


@app.route("/api/<tool_name>", methods=["GET"])
def proxy_api(tool_name):
    if tool_name not in TOOLS:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Invalid API tool endpoint requested. Check documentation.",
                }
            ),
            404,
        )

    api_key = request.args.get("key")
    if not api_key:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "API key missing. Append ?key=explorer16 to request.",
                }
            ),
            401,
        )

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, expiry_date, request_limit, requests_used, status FROM api_keys WHERE key_string = ?",
        (api_key,),
    )
    key_row = cursor.fetchone()

    if not key_row:
        conn.close()
        return (
            jsonify(
                {"status": "error", "message": "Invalid or unrecognized API key."}
            ),
            403,
        )

    key_id, expiry_date, request_limit, requests_used, key_status = (
        key_row[0],
        key_row[1],
        key_row[2],
        key_row[3],
        key_row[4],
    )

    if key_status != "Active":
        conn.close()
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "API key is currently suspended or revoked.",
                }
            ),
            403,
        )

    if requests_used >= request_limit:
        conn.close()
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "API key request limit exhausted.",
                }
            ),
            429,
        )

    try:
        exp_dt = datetime.strptime(expiry_date, "%Y-%m-%dT%H:%M")
        if datetime.now() > exp_dt:
            conn.close()
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "API key has expired based on scheduled expiry date.",
                    }
                ),
                403,
            )
    except Exception:
        pass

    cursor.execute(
        "UPDATE api_keys SET requests_used = requests_used + 1 WHERE id = ?",
        (key_id,),
    )

    query_str = "&".join(
        [f"{k}={v}" for k, v in request.args.items() if k != "key"]
    )
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    upstream_url = f"{UPSTREAM_BASE}/{tool_name}"
    status_code = 200
    try:
        resp = requests.get(upstream_url, params=request.args, timeout=25)
        status_code = resp.status_code
        response_text = resp.text
        response_headers = list(resp.headers.items())
    except Exception as e:
        status_code = 500
        response_text = jsonify(
            {
                "status": "error",
                "message": f"Upstream OSINT gateway timeout/error: {str(e)}",
            }
        ).get_data(as_text=True)
        response_headers = [("Content-Type", "application/json")]

    cursor.execute(
        "INSERT INTO api_logs (key_string, tool, query_params, ip_address, status_code, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
        (api_key, tool_name, query_str, client_ip, status_code, timestamp),
    )
    conn.commit()
    conn.close()

    return response_text, status_code, response_headers


if __name__ == "__main__":
    app.run(debug=True, port=5000)
