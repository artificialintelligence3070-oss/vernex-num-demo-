from datetime import datetime, timedelta
import io
import json
import os
import sqlite3
from flask import (
    Flask,
    Response,
    flash,
    jsonify,
    redirect,
    render_template_string,
    request,
    send_file,
    session,
    url_for,
)
import requests

app = Flask(__name__)
app.secret_key = os.urandom(24)

DB_PATH = "/tmp/osint_manager_pro.db"


def get_db():
  conn = sqlite3.connect(DB_PATH)
  conn.row_factory = sqlite3.Row
  return conn


def init_db():
  conn = get_db()
  conn.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_string TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            daily_limit INTEGER NOT NULL,
            requests_today INTEGER DEFAULT 0,
            last_reset DATE DEFAULT CURRENT_DATE,
            status TEXT DEFAULT 'Active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
  conn.execute("""
        CREATE TABLE IF NOT EXISTS request_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_string TEXT NOT NULL,
            endpoint TEXT NOT NULL,
            query_params TEXT NOT NULL,
            ip_address TEXT,
            status_code INTEGER DEFAULT 200,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
  conn.commit()
  conn.close()


init_db()

UPSTREAM_BASE = "https://ft-osint-api.duckdns.org/api"

ADMIN_USER = "vernex"
ADMIN_PASS = "vernex@16vx"

ENDPOINTS_LIST = [
    ("Number Lookup", "number", "num=9876543210"),
    ("Advanced OSINT", "adv", "num=9876543210"),
    ("Paytm Info", "paytm", "num=9876543210"),
    ("IMEI Lookup", "imei", "imei=357817383506298"),
    ("Call Tracer", "calltracer", "num=9876543210"),
    ("UPI VPA Lookup", "upi", "upi=example@ybl"),
    ("IFSC Code Info", "ifsc", "ifsc=SBIN0001234"),
    ("Pincode Directory", "pincode", "pin=110001"),
    ("IP Geolocation", "ip", "ip=8.8.8.8"),
    ("Vehicle Challan", "challan", "vehicle=UP42BB2572"),
    ("Free Fire Info", "ff", "uid=3143389983"),
    ("BGMI Info", "bgmi", "uid=5121439477"),
    ("Snapchat Info", "snap", "username=priyapanchal272"),
    ("Email Lookup", "email", "email=airtel123@gmail.com"),
    ("Vehicle Database", "vehicle", "vehicle=MH02FZ0555"),
    ("GitHub Lookup", "git", "username=ftgamer2"),
    ("Instagram Info", "insta", "username=cristiano"),
    ("Telegram Username Info", "tg", "info=username"),
    ("Telegram ID to Number", "tgidinfo", "id=7530266953"),
    ("Number Leak Database", "numleak", "num=9876543210"),
]

TEMPLATE = """
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SHAYAN EXPLORER | Enterprise OSINT Command Hub</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        darkbg: '#070a14',
                        cardbg: '#0f172a',
                        accent: '#3b82f6',
                        accentglow: '#60a5fa'
                    }
                }
            }
        }
    </script>
    <style>
        .glass-card {
            background: rgba(15, 23, 42, 0.75);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.1);
        }
        .glass-input {
            background: rgba(3, 7, 18, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .glass-input:focus {
            border-color: #3b82f6;
            box-shadow: 0 0 20px rgba(59, 130, 246, 0.35);
        }
        .glow-btn {
            box-shadow: 0 0 25px rgba(59, 130, 246, 0.3);
        }
        .glow-btn:hover {
            box-shadow: 0 0 35px rgba(59, 130, 246, 0.6);
        }
    </style>
</head>
<body class="bg-darkbg text-gray-100 min-h-screen font-sans antialiased selection:bg-blue-500 selection:text-white">

    {% if not session.get('logged_in') %}
    <!-- LOGIN SCREEN -->
    <div class="flex items-center justify-center min-h-screen px-4 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-blue-900/20 via-darkbg to-darkbg">
        <div class="glass-card p-8 md:p-10 rounded-3xl w-full max-w-md shadow-2xl relative overflow-hidden">
            <div class="absolute -top-24 -right-24 w-48 h-48 bg-blue-500/10 rounded-full blur-3xl"></div>
            
            <div class="text-center mb-8 relative z-10">
                <div class="inline-flex p-4 rounded-2xl bg-blue-600/20 text-blue-400 mb-4 text-3xl shadow-inner border border-blue-500/30">
                    <i class="fa-solid fa-shield-halved"></i>
                </div>
                <h1 class="text-2xl font-black tracking-wider text-white">SHAYAN EXPLORER</h1>
                <p class="text-xs text-blue-400 font-mono tracking-widest uppercase mt-1">Enterprise API Infrastructure</p>
            </div>
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="mb-5 p-3.5 rounded-xl bg-red-500/20 border border-red-500/50 text-red-300 text-xs flex items-center gap-3">
                            <i class="fa-solid fa-triangle-exclamation text-base"></i> {{ message }}
                        </div>
                    {% endfor %}
                {% endif %}
            {% endwith %}

            <form method="POST" action="/login" class="space-y-5 relative z-10">
                <div>
                    <label class="block text-[11px] uppercase font-bold tracking-wider text-gray-400 mb-2">Admin Username</label>
                    <div class="relative">
                        <span class="absolute inset-y-0 left-0 pl-4 flex items-center text-gray-500"><i class="fa-solid fa-user"></i></span>
                        <input type="text" name="username" required class="glass-input w-full pl-11 pr-4 py-3.5 rounded-xl text-sm text-white focus:outline-none" placeholder="Enter username (vernex)">
                    </div>
                </div>
                <div>
                    <label class="block text-[11px] uppercase font-bold tracking-wider text-gray-400 mb-2">Admin Password</label>
                    <div class="relative">
                        <span class="absolute inset-y-0 left-0 pl-4 flex items-center text-gray-500"><i class="fa-solid fa-lock"></i></span>
                        <input type="password" name="password" required class="glass-input w-full pl-11 pr-4 py-3.5 rounded-xl text-sm text-white focus:outline-none" placeholder="Enter password">
                    </div>
                </div>
                <button type="submit" class="w-full py-3.5 px-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold text-sm tracking-wider uppercase rounded-xl glow-btn transition duration-200">
                    Access Command Hub
                </button>
            </form>
            <div class="mt-8 text-center text-[11px] text-gray-500 tracking-wider">
                Authorized Access Only &bull; Built by <span class="text-blue-400 font-bold">SHAYAN_EXPLORER</span>
            </div>
        </div>
    </div>
    {% else %}
    <!-- MAIN DASHBOARD -->
    <div class="flex h-screen overflow-hidden" x-data="{ currentTab: 'overview', sidebarOpen: false }">
        
        <!-- Sidebar -->
        <aside class="w-72 glass-card border-r border-gray-800/80 flex flex-col z-20">
            <div class="p-6 border-b border-gray-800/60 flex items-center gap-3.5">
                <div class="bg-blue-600/20 text-blue-400 p-3 rounded-2xl border border-blue-500/30">
                    <i class="fa-solid fa-terminal text-lg"></i>
                </div>
                <div>
                    <h2 class="font-black text-sm tracking-wider text-white">SHAYAN EXPLORER</h2>
                    <div class="flex items-center gap-2 mt-0.5">
                        <span class="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
                        <span class="text-[10px] text-emerald-400 font-mono tracking-wide">GATEWAY LIVE</span>
                    </div>
                </div>
            </div>

            <nav class="flex-1 p-4 space-y-1.5 text-xs font-semibold overflow-y-auto">
                <a @click="currentTab = 'overview'" :class="currentTab === 'overview' ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30 shadow-lg shadow-blue-500/10' : 'text-gray-400 hover:bg-gray-800/40 hover:text-white'" class="flex items-center gap-3.5 px-4 py-3 rounded-xl transition cursor-pointer">
                    <i class="fa-solid fa-chart-pie w-5 text-sm"></i> Command Overview
                </a>
                <a @click="currentTab = 'keys'" :class="currentTab === 'keys' ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30 shadow-lg shadow-blue-500/10' : 'text-gray-400 hover:bg-gray-800/40 hover:text-white'" class="flex items-center gap-3.5 px-4 py-3 rounded-xl transition cursor-pointer">
                    <i class="fa-solid fa-key w-5 text-sm"></i> API Key Vault
                </a>
                <a @click="currentTab = 'sandbox'" :class="currentTab === 'sandbox' ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30 shadow-lg shadow-blue-500/10' : 'text-gray-400 hover:bg-gray-800/40 hover:text-white'" class="flex items-center gap-3.5 px-4 py-3 rounded-xl transition cursor-pointer">
                    <i class="fa-solid fa-flask w-5 text-sm"></i> Live API Sandbox
                </a>
                <a @click="currentTab = 'endpoints'" :class="currentTab === 'endpoints' ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30 shadow-lg shadow-blue-500/10' : 'text-gray-400 hover:bg-gray-800/40 hover:text-white'" class="flex items-center gap-3.5 px-4 py-3 rounded-xl transition cursor-pointer">
                    <i class="fa-solid fa-code w-5 text-sm"></i> Endpoints & Snippets
                </a>
                <a @click="currentTab = 'logs'" :class="currentTab === 'logs' ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30 shadow-lg shadow-blue-500/10' : 'text-gray-400 hover:bg-gray-800/40 hover:text-white'" class="flex items-center gap-3.5 px-4 py-3 rounded-xl transition cursor-pointer">
                    <i class="fa-solid fa-clock-rotate-left w-5 text-sm"></i> Audit & Request Logs
                </a>
                <a @click="currentTab = 'health'" :class="currentTab === 'health' ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30 shadow-lg shadow-blue-500/10' : 'text-gray-400 hover:bg-gray-800/40 hover:text-white'" class="flex items-center gap-3.5 px-4 py-3 rounded-xl transition cursor-pointer">
                    <i class="fa-solid fa-heart-pulse w-5 text-sm"></i> System Health Monitor
                </a>
                <a @click="currentTab = 'tools'" :class="currentTab === 'tools' ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30 shadow-lg shadow-blue-500/10' : 'text-gray-400 hover:bg-gray-800/40 hover:text-white'" class="flex items-center gap-3.5 px-4 py-3 rounded-xl transition cursor-pointer">
                    <i class="fa-solid fa-toolbox w-5 text-sm"></i> Backup & Utilities
                </a>
            </nav>

            <div class="p-4 border-t border-gray-800/60">
                <a href="/logout" class="flex items-center gap-3.5 px-4 py-3 rounded-xl text-red-400 hover:bg-red-500/10 transition text-xs font-bold">
                    <i class="fa-solid fa-right-from-bracket w-5 text-sm"></i> Terminate Session
                </a>
            </div>
        </aside>

        <!-- Main Content Area -->
        <main class="flex-1 flex flex-col overflow-y-auto bg-darkbg">
            <!-- Header -->
            <header class="glass-card border-b border-gray-800/80 px-8 py-4 flex justify-between items-center sticky top-0 z-10">
                <div class="flex items-center gap-4">
                    <h1 class="text-base font-bold text-white flex items-center gap-2.5">
                        <i class="fa-solid fa-shield text-blue-500"></i> SHAYAN_EXPLORER Gateway Manager
                    </h1>
                </div>
                <div class="flex items-center gap-4">
                    <div class="text-right hidden sm:block">
                        <div class="text-[10px] text-gray-400 uppercase tracking-widest font-semibold">Architect</div>
                        <div class="text-xs font-mono font-bold text-blue-400">SHAYAN_EXPLORER</div>
                    </div>
                    <div class="h-10 w-10 rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-600 border border-blue-400/30 flex items-center justify-center text-white font-black text-xs shadow-lg">
                        SE
                    </div>
                </div>
            </header>

            <div class="p-8 max-w-7xl mx-auto w-full space-y-8">

                <!-- TAB 1: OVERVIEW -->
                <div x-show="currentTab === 'overview'" class="space-y-6">
                    <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
                        <div class="glass-card p-6 rounded-3xl flex items-center justify-between">
                            <div>
                                <p class="text-[11px] text-gray-400 uppercase font-bold tracking-wider">Active Keys</p>
                                <h3 class="text-3xl font-black text-white mt-1">{{ keys|length }}</h3>
                            </div>
                            <div class="p-3.5 bg-blue-600/20 text-blue-400 rounded-2xl border border-blue-500/30"><i class="fa-solid fa-key text-xl"></i></div>
                        </div>
                        <div class="glass-card p-6 rounded-3xl flex items-center justify-between">
                            <div>
                                <p class="text-[11px] text-gray-400 uppercase font-bold tracking-wider">OSINT Tools</p>
                                <h3 class="text-3xl font-black text-emerald-400 mt-1">20+</h3>
                            </div>
                            <div class="p-3.5 bg-emerald-600/20 text-emerald-400 rounded-2xl border border-emerald-500/30"><i class="fa-solid fa-network-wired text-xl"></i></div>
                        </div>
                        <div class="glass-card p-6 rounded-3xl flex items-center justify-between">
                            <div>
                                <p class="text-[11px] text-gray-400 uppercase font-bold tracking-wider">Total Requests</p>
                                <h3 class="text-3xl font-black text-indigo-400 mt-1">{{ logs|length }}</h3>
                            </div>
                            <div class="p-3.5 bg-indigo-600/20 text-indigo-400 rounded-2xl border border-indigo-500/30"><i class="fa-solid fa-chart-line text-xl"></i></div>
                        </div>
                        <div class="glass-card p-6 rounded-3xl flex items-center justify-between">
                            <div>
                                <p class="text-[11px] text-gray-400 uppercase font-bold tracking-wider">System State</p>
                                <h3 class="text-lg font-black text-emerald-400 mt-1 flex items-center gap-2"><span class="h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse"></span> Optimal</h3>
                            </div>
                            <div class="p-3.5 bg-teal-600/20 text-teal-400 rounded-2xl border border-teal-500/30"><i class="fa-solid fa-server text-xl"></i></div>
                        </div>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div class="glass-card p-6 rounded-3xl space-y-4">
                            <h3 class="font-bold text-white text-sm flex items-center gap-2"><i class="fa-solid fa-bolt text-blue-500"></i> Quick Actions</h3>
                            <div class="grid grid-cols-2 gap-3">
                                <button @click="currentTab = 'keys'" class="p-4 rounded-2xl bg-gray-900/60 border border-gray-800 hover:border-blue-500/50 text-left transition group">
                                    <div class="text-blue-400 mb-2 group-hover:scale-110 transition"><i class="fa-solid fa-plus-circle text-lg"></i></div>
                                    <div class="font-bold text-xs text-white">Create API Key</div>
                                    <div class="text-[10px] text-gray-400 mt-0.5">Generate custom token</div>
                                </button>
                                <button @click="currentTab = 'sandbox'" class="p-4 rounded-2xl bg-gray-900/60 border border-gray-800 hover:border-emerald-500/50 text-left transition group">
                                    <div class="text-emerald-400 mb-2 group-hover:scale-110 transition"><i class="fa-solid fa-flask text-lg"></i></div>
                                    <div class="font-bold text-xs text-white">Test API Sandbox</div>
                                    <div class="text-[10px] text-gray-400 mt-0.5">Live JSON inspector</div>
                                </button>
                                <button @click="currentTab = 'endpoints'" class="p-4 rounded-2xl bg-gray-900/60 border border-gray-800 hover:border-indigo-500/50 text-left transition group">
                                    <div class="text-indigo-400 mb-2 group-hover:scale-110 transition"><i class="fa-solid fa-code text-lg"></i></div>
                                    <div class="font-bold text-xs text-white">View Snippets</div>
                                    <div class="text-[10px] text-gray-400 mt-0.5">Python, cURL, JS code</div>
                                </button>
                                <button @click="currentTab = 'health'" class="p-4 rounded-2xl bg-gray-900/60 border border-gray-800 hover:border-teal-500/50 text-left transition group">
                                    <div class="text-teal-400 mb-2 group-hover:scale-110 transition"><i class="fa-solid fa-heart-pulse text-lg"></i></div>
                                    <div class="font-bold text-xs text-white">Health Monitor</div>
                                    <div class="text-[10px] text-gray-400 mt-0.5">Upstream ping status</div>
                                </button>
                            </div>
                        </div>

                        <div class="glass-card p-6 rounded-3xl space-y-4">
                            <h3 class="font-bold text-white text-sm flex items-center gap-2"><i class="fa-solid fa-circle-info text-blue-500"></i> Deployment Details</h3>
                            <div class="space-y-3 text-xs">
                                <div class="flex justify-between p-3 rounded-xl bg-gray-900/50 border border-gray-800">
                                    <span class="text-gray-400">Environment</span>
                                    <span class="font-mono text-white">Vercel Serverless (Python)</span>
                                </div>
                                <div class="flex justify-between p-3 rounded-xl bg-gray-900/50 border border-gray-800">
                                    <span class="text-gray-400">Database Engine</span>
                                    <span class="font-mono text-white">SQLite (/tmp storage)</span>
                                </div>
                                <div class="flex justify-between p-3 rounded-xl bg-gray-900/50 border border-gray-800">
                                    <span class="text-gray-400">Upstream Provider</span>
                                    <span class="font-mono text-blue-400">ft-osint-api.duckdns.org</span>
                                </div>
                                <div class="flex justify-between p-3 rounded-xl bg-gray-900/50 border border-gray-800">
                                    <span class="text-gray-400">Primary Maintainer</span>
                                    <span class="font-mono text-emerald-400 font-bold">SHAYAN_EXPLORER</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- TAB 2: KEYS MANAGER -->
                <div x-show="currentTab === 'keys'" class="space-y-6" x-data="{ search: '' }">
                    <div class="glass-card p-6 rounded-3xl">
                        <h3 class="text-sm font-bold text-white mb-4 flex items-center gap-2"><i class="fa-solid fa-plus-circle text-blue-500"></i> Generate Secure API Key</h3>
                        <form method="POST" action="/create-key" class="grid grid-cols-1 md:grid-cols-4 gap-4">
                            <div>
                                <label class="block text-[10px] uppercase font-bold text-gray-400 mb-2">Key Identifier / Name</label>
                                <input type="text" name="name" required class="glass-input w-full px-4 py-3 rounded-xl text-xs text-white focus:outline-none" placeholder="e.g. Client_Alpha">
                            </div>
                            <div>
                                <label class="block text-[10px] uppercase font-bold text-gray-400 mb-2">Expiration Date</label>
                                <input type="date" name="expires_at" required class="glass-input w-full px-4 py-3 rounded-xl text-xs text-white focus:outline-none">
                            </div>
                            <div>
                                <label class="block text-[10px] uppercase font-bold text-gray-400 mb-2">Daily Request Limit</label>
                                <input type="number" name="daily_limit" value="1000" required class="glass-input w-full px-4 py-3 rounded-xl text-xs text-white focus:outline-none">
                            </div>
                            <div class="flex items-end">
                                <button type="submit" class="w-full py-3 px-4 bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs uppercase tracking-wider rounded-xl glow-btn transition">
                                    <i class="fa-solid fa-key mr-2"></i> Generate Key
                                </button>
                            </div>
                        </form>
                    </div>

                    <div class="glass-card rounded-3xl overflow-hidden">
                        <div class="p-6 border-b border-gray-800 flex flex-col sm:flex-row justify-between items-center gap-4">
                            <h3 class="text-sm font-bold text-white flex items-center gap-2"><i class="fa-solid fa-database text-blue-500"></i> API Key Vault Inventory</h3>
                            <div class="flex items-center gap-3 w-full sm:w-auto">
                                <input type="text" x-model="search" placeholder="Search keys or names..." class="glass-input px-4 py-2 rounded-xl text-xs text-white focus:outline-none w-full sm:w-64">
                                <a href="/export-keys" class="px-4 py-2 rounded-xl bg-gray-800 hover:bg-gray-700 text-xs font-bold text-blue-400 transition flex items-center gap-2 whitespace-nowrap">
                                    <i class="fa-solid fa-download"></i> Export JSON
                                </a>
                            </div>
                        </div>
                        <div class="overflow-x-auto">
                            <table class="w-full text-left border-collapse">
                                <thead>
                                    <tr class="border-b border-gray-800 text-[10px] uppercase font-bold text-gray-400 bg-gray-900/50">
                                        <th class="p-4">Name</th>
                                        <th class="p-4">API Token String</th>
                                        <th class="p-4">Requests Today</th>
                                        <th class="p-4">Daily Limit</th>
                                        <th class="p-4">Expires At</th>
                                        <th class="p-4 text-right">Actions</th>
                                    </tr>
                                </thead>
                                <tbody class="divide-y divide-gray-800/60 text-xs font-mono">
                                    {% for k in keys %}
                                    <tr class="hover:bg-gray-800/30 transition" x-show="!search || '{{ k.name }}'.toLowerCase().includes(search.toLowerCase()) || '{{ k.key_string }}'.toLowerCase().includes(search.toLowerCase())">
                                        <td class="p-4 font-sans font-bold text-white">{{ k.name }}</td>
                                        <td class="p-4"><code class="bg-gray-900 px-3 py-1 rounded-lg text-blue-400 select-all">{{ k.key_string }}</code></td>
                                        <td class="p-4"><span class="px-2.5 py-1 rounded-full bg-blue-500/10 text-blue-400 font-bold">{{ k.requests_today }}</span></td>
                                        <td class="p-4 text-gray-300">{{ k.daily_limit }}</td>
                                        <td class="p-4 text-gray-300 font-sans">{{ k.expires_at }}</td>
                                        <td class="p-4 text-right">
                                            <a href="/delete-key/{{ k.id }}" onclick="return confirm('Revoke this API key?');" class="px-3 py-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 font-sans font-bold transition">
                                                <i class="fa-solid fa-trash mr-1"></i> Revoke
                                            </a>
                                        </td>
                                    </tr>
                                    {% else %}
                                    <tr>
                                        <td colspan="6" class="p-8 text-center text-gray-500 font-sans">No API keys generated yet. Use the generator above.</td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <!-- TAB 3: LIVE API SANDBOX -->
                <div x-show="currentTab === 'sandbox'" class="space-y-6" x-data="{ endpoint: 'number', key: '', paramName: 'num', paramVal: '9876543210', result: null, loading: false }">
                    <div class="glass-card p-6 rounded-3xl space-y-5">
                        <h3 class="text-sm font-bold text-white flex items-center gap-2"><i class="fa-solid fa-flask text-emerald-500"></i> Interactive API Sandbox</h3>
                        <p class="text-xs text-gray-400">Test any OSINT proxy endpoint directly from your command center and inspect the JSON response instantly.</p>
                        
                        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div>
                                <label class="block text-[10px] uppercase font-bold text-gray-400 mb-2">Select Endpoint</label>
                                <select x-model="endpoint" class="glass-input w-full px-4 py-3 rounded-xl text-xs text-white focus:outline-none">
                                    {% for title, ep, sample in ENDPOINTS_LIST %}
                                    <option value="{{ ep }}">{{ title }} (/api/{{ ep }})</option>
                                    {% endfor %}
                                </select>
                            </div>
                            <div>
                                <label class="block text-[10px] uppercase font-bold text-gray-400 mb-2">API Key</label>
                                <input type="text" x-model="key" placeholder="Enter valid API key" class="glass-input w-full px-4 py-3 rounded-xl text-xs text-white focus:outline-none font-mono">
                            </div>
                            <div>
                                <label class="block text-[10px] uppercase font-bold text-gray-400 mb-2">Query Parameter & Value</label>
                                <div class="flex gap-2">
                                    <input type="text" x-model="paramName" placeholder="param" class="glass-input w-1/3 px-3 py-3 rounded-xl text-xs text-white focus:outline-none font-mono">
                                    <input type="text" x-model="paramVal" placeholder="value" class="glass-input w-2/3 px-3 py-3 rounded-xl text-xs text-white focus:outline-none font-mono">
                                </div>
                            </div>
                        </div>

                        <button @click="
                            if(!key) { alert('Please enter an API key'); return; }
                            loading = true;
                            fetch('/api/' + endpoint + '?key=' + key + '&' + paramName + '=' + encodeURIComponent(paramVal))
                                .then(res => res.json().then(data => ({status: res.status, body: data})))
                                .then(res => { result = res; loading = false; })
                                .catch(err => { result = {status: 500, body: {error: err.toString()}}; loading = false; });
                        " class="px-6 py-3 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs uppercase tracking-wider rounded-xl transition flex items-center gap-2">
                            <i class="fa-solid fa-play"></i> Execute Test Request
                        </button>
                    </div>

                    <div class="glass-card p-6 rounded-3xl space-y-3" x-show="result !== null || loading">
                        <div class="flex justify-between items-center">
                            <h4 class="text-xs font-bold text-white uppercase tracking-wider">Response Inspector</h4>
                            <span x-show="result" :class="result.status === 200 ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' : 'bg-red-500/20 text-red-400 border-red-500/30'" class="px-3 py-1 rounded-full text-xs font-mono font-bold border">
                                HTTP Status: <span x-text="result ? result.status : 'Loading...'"></span>
                            </span>
                        </div>
                        <div x-show="loading" class="text-center py-10 text-gray-400 text-xs font-mono">
                            <i class="fa-solid fa-spinner fa-spin text-lg text-blue-500 mb-2"></i> Executing request through proxy...
                        </div>
                        <pre x-show="!loading && result" class="bg-black/60 p-4 rounded-2xl text-blue-400 font-mono text-xs overflow-x-auto max-h-96 border border-gray-800" x-text="JSON.stringify(result ? result.body : {}, null, 2)"></pre>
                    </div>
                </div>

                <!-- TAB 4: ENDPOINTS & SNIPPETS -->
                <div x-show="currentTab === 'endpoints'" class="space-y-6" x-data="{ selectedEp: 'number' }">
                    <div class="glass-card p-6 rounded-3xl space-y-6">
                        <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                            <div>
                                <h3 class="text-sm font-bold text-white flex items-center gap-2"><i class="fa-solid fa-code text-blue-500"></i> Endpoints Directory & Code Snippets</h3>
                                <p class="text-xs text-gray-400 mt-1">Multi-language code generators for all 20+ OSINT proxy endpoints.</p>
                            </div>
                            <select x-model="selectedEp" class="glass-input px-4 py-2.5 rounded-xl text-xs text-white focus:outline-none">
                                {% for title, ep, sample in ENDPOINTS_LIST %}
                                <option value="{{ ep }}">{{ title }} (/api/{{ ep }})</option>
                                {% endfor %}
                            </select>
                        </div>

                        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div class="space-y-3">
                                <h4 class="text-xs font-bold uppercase tracking-wider text-gray-400">cURL Request</h4>
                                <pre class="bg-black/60 p-4 rounded-2xl text-blue-400 font-mono text-xs overflow-x-auto border border-gray-800" x-text="`curl -X GET 'https://` + window.location.host + `/api/` + selectedEp + `?key=YOUR_KEY&query=VALUE'`"></pre>
                            </div>
                            <div class="space-y-3">
                                <h4 class="text-xs font-bold uppercase tracking-wider text-gray-400">Python (Requests)</h4>
                                <pre class="bg-black/60 p-4 rounded-2xl text-emerald-400 font-mono text-xs overflow-x-auto border border-gray-800" x-text="`import requests\n\nurl = 'https://` + window.location.host + `/api/` + selectedEp + `'\nparams = {'key': 'YOUR_KEY', 'query': 'VALUE'}\nres = requests.get(url, params=params)\nprint(res.json())`"></pre>
                            </div>
                            <div class="space-y-3">
                                <h4 class="text-xs font-bold uppercase tracking-wider text-gray-400">JavaScript (Fetch)</h4>
                                <pre class="bg-black/60 p-4 rounded-2xl text-indigo-400 font-mono text-xs overflow-x-auto border border-gray-800" x-text="`fetch('https://` + window.location.host + `/api/` + selectedEp + `?key=YOUR_KEY&query=VALUE')\n  .then(res => res.json())\n  .then(data => console.log(data));`"></pre>
                            </div>
                            <div class="space-y-3">
                                <h4 class="text-xs font-bold uppercase tracking-wider text-gray-400">PHP (cURL)</h4>
                                <pre class="bg-black/60 p-4 rounded-2xl text-amber-400 font-mono text-xs overflow-x-auto border border-gray-800" x-text="`$ch = curl_init();\ncurl_setopt($ch, CURLOPT_URL, 'https://` + window.location.host + `/api/` + selectedEp + `?key=YOUR_KEY&query=VALUE');\ncurl_setopt($ch, CURLOPT_RETURNTRANSFER, true);\n$response = curl_exec($ch);\ncurl_close($ch);\necho $response;`"></pre>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- TAB 5: AUDIT LOGS -->
                <div x-show="currentTab === 'logs'" class="space-y-6" x-data="{ logSearch: '' }">
                    <div class="glass-card rounded-3xl overflow-hidden">
                        <div class="p-6 border-b border-gray-800 flex flex-col sm:flex-row justify-between items-center gap-4">
                            <h3 class="text-sm font-bold text-white flex items-center gap-2"><i class="fa-solid fa-clock-rotate-left text-blue-500"></i> Request Audit Trail & History</h3>
                            <div class="flex items-center gap-3 w-full sm:w-auto">
                                <input type="text" x-model="logSearch" placeholder="Filter logs by key or endpoint..." class="glass-input px-4 py-2 rounded-xl text-xs text-white focus:outline-none w-full sm:w-64">
                                <a href="/clear-logs" onclick="return confirm('Clear all audit logs?');" class="px-4 py-2 rounded-xl bg-red-500/10 hover:bg-red-500/20 text-red-400 text-xs font-bold transition whitespace-nowrap">
                                    <i class="fa-solid fa-trash mr-1"></i> Clear Logs
                                </a>
                            </div>
                        </div>
                        <div class="overflow-x-auto">
                            <table class="w-full text-left border-collapse">
                                <thead>
                                    <tr class="border-b border-gray-800 text-[10px] uppercase font-bold text-gray-400 bg-gray-900/50">
                                        <th class="p-4">Timestamp</th>
                                        <th class="p-4">API Key</th>
                                        <th class="p-4">Endpoint</th>
                                        <th class="p-4">Query Parameters</th>
                                        <th class="p-4">Client IP</th>
                                    </tr>
                                </thead>
                                <tbody class="divide-y divide-gray-800/60 text-xs font-mono">
                                    {% for log in logs %}
                                    <tr class="hover:bg-gray-800/30 transition" x-show="!logSearch || '{{ log.key_string }}'.toLowerCase().includes(logSearch.toLowerCase()) || '{{ log.endpoint }}'.toLowerCase().includes(logSearch.toLowerCase())">
                                        <td class="p-4 text-gray-400 text-[11px]">{{ log.timestamp }}</td>
                                        <td class="p-4 text-blue-400">{{ log.key_string }}</td>
                                        <td class="p-4 font-sans font-bold text-white">{{ log.endpoint }}</td>
                                        <td class="p-4 text-gray-300">{{ log.query_params }}</td>
                                        <td class="p-4 text-gray-400">{{ log.ip_address }}</td>
                                    </tr>
                                    {% else %}
                                    <tr>
                                        <td colspan="5" class="p-8 text-center text-gray-500 font-sans">No request logs recorded yet.</td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <!-- TAB 6: SYSTEM HEALTH MONITOR -->
                <div x-show="currentTab === 'health'" class="space-y-6" x-data="{ pingStatus: null, checking: false }">
                    <div class="glass-card p-6 rounded-3xl space-y-6">
                        <div class="flex justify-between items-center">
                            <div>
                                <h3 class="text-sm font-bold text-white flex items-center gap-2"><i class="fa-solid fa-heart-pulse text-emerald-500"></i> Upstream Gateway Health Monitor</h3>
                                <p class="text-xs text-gray-400 mt-1">Verify real-time connectivity and response latency to the upstream OSINT provider.</p>
                            </div>
                            <button @click="
                                checking = true;
                                fetch('https://ft-osint-api.duckdns.org/api/number?key=test&num=9876543210')
                                    .then(res => { pingStatus = { status: res.status, online: true }; checking = false; })
                                    .catch(err => { pingStatus = { status: 502, online: false }; checking = false; });
                            " class="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs uppercase tracking-wider rounded-xl transition">
                                <i class="fa-solid fa-rotate mr-1"></i> Run Health Ping
                            </button>
                        </div>

                        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                            <div class="glass-card p-5 rounded-2xl flex items-center justify-between">
                                <div>
                                    <p class="text-[10px] uppercase font-bold text-gray-400">Upstream Status</p>
                                    <h4 class="text-base font-black text-emerald-400 mt-1 flex items-center gap-2">
                                        <span class="h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse"></span> Connected
                                    </h4>
                                </div>
                                <div class="text-emerald-400 text-xl"><i class="fa-solid fa-cloud"></i></div>
                            </div>
                            <div class="glass-card p-5 rounded-2xl flex items-center justify-between">
                                <div>
                                    <p class="text-[10px] uppercase font-bold text-gray-400">Database Integrity</p>
                                    <h4 class="text-base font-black text-blue-400 mt-1">SQLite Operational</h4>
                                </div>
                                <div class="text-blue-400 text-xl"><i class="fa-solid fa-database"></i></div>
                            </div>
                            <div class="glass-card p-5 rounded-2xl flex items-center justify-between">
                                <div>
                                    <p class="text-[10px] uppercase font-bold text-gray-400">Serverless Host</p>
                                    <h4 class="text-base font-black text-indigo-400 mt-1">Vercel Edge</h4>
                                </div>
                                <div class="text-indigo-400 text-xl"><i class="fa-solid fa-bolt"></i></div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- TAB 7: BACKUP & UTILITIES -->
                <div x-show="currentTab === 'tools'" class="space-y-6">
                    <div class="glass-card p-6 rounded-3xl space-y-6">
                        <div>
                            <h3 class="text-sm font-bold text-white flex items-center gap-2"><i class="fa-solid fa-toolbox text-blue-500"></i> Database Backup & Utilities</h3>
                            <p class="text-xs text-gray-400 mt-1">Download complete SQLite backups or export all system logs.</p>
                        </div>

                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <a href="/backup-db" class="p-5 rounded-2xl bg-gray-900/60 border border-gray-800 hover:border-blue-500/50 flex items-center justify-between transition group">
                                <div>
                                    <div class="font-bold text-xs text-white group-hover:text-blue-400 transition">Download SQLite Backup</div>
                                    <div class="text-[10px] text-gray-400 mt-0.5">Secure `.db` file archive</div>
                                </div>
                                <div class="p-3 bg-blue-600/20 text-blue-400 rounded-xl"><i class="fa-solid fa-download"></i></div>
                            </a>
                            <a href="/export-keys" class="p-5 rounded-2xl bg-gray-900/60 border border-gray-800 hover:border-emerald-500/50 flex items-center justify-between transition group">
                                <div>
                                    <div class="font-bold text-xs text-white group-hover:text-emerald-400 transition">Export API Keys JSON</div>
                                    <div class="text-[10px] text-gray-400 mt-0.5">Full inventory dump</div>
                                </div>
                                <div class="p-3 bg-emerald-600/20 text-emerald-400 rounded-xl"><i class="fa-solid fa-file-code"></i></div>
                            </a>
                        </div>
                    </div>
                </div>

            </div>
        </main>
    </div>
    {% endif %}
</body>
</html>
"""


@app.route("/")
def index():
  if not session.get("logged_in"):
    return render_template_string(TEMPLATE)

  conn = get_db()
  keys = conn.execute("SELECT * FROM api_keys ORDER BY id DESC").fetchall()
  logs = conn.execute(
      "SELECT * FROM request_logs ORDER BY id DESC LIMIT 100"
  ).fetchall()
  conn.close()
  return render_template_string(TEMPLATE, keys=keys, logs=logs)


@app.route("/login", methods=["POST"])
def login():
  username = request.form.get("username")
  password = request.form.get("password")
  if username == ADMIN_USER and password == ADMIN_PASS:
    session["logged_in"] = True
    return redirect(url_for("index"))
  else:
    flash("Invalid administrator credentials.", "error")
    return redirect(url_for("index"))


@app.route("/logout")
def logout():
  session.clear()
  return redirect(url_for("index"))


@app.route("/create-key", methods=["POST"])
def create_key():
  if not session.get("logged_in"):
    return redirect(url_for("index"))

  name = request.form.get("name")
  expires_at = request.form.get("expires_at")
  daily_limit = request.form.get("daily_limit", 1000)
  key_string = f"se_live_{os.urandom(8).hex()}"

  conn = get_db()
  conn.execute(
      "INSERT INTO api_keys (key_string, name, expires_at, daily_limit)"
      " VALUES (?, ?, ?, ?)",
      (key_string, name, expires_at, daily_limit),
  )
  conn.commit()
  conn.close()
  return redirect(url_for("index"))


@app.route("/delete-key/<int:key_id>")
def delete_key(key_id):
  if not session.get("logged_in"):
    return redirect(url_for("index"))

  conn = get_db()
  conn.execute("DELETE FROM api_keys WHERE id = ?", (key_id,))
  conn.commit()
  conn.close()
  return redirect(url_for("index"))


@app.route("/clear-logs")
def clear_logs():
  if not session.get("logged_in"):
    return redirect(url_for("index"))

  conn = get_db()
  conn.execute("DELETE FROM request_logs")
  conn.commit()
  conn.close()
  return redirect(url_for("index"))


@app.route("/export-keys")
def export_keys():
  if not session.get("logged_in"):
    return redirect(url_for("index"))

  conn = get_db()
  keys = [dict(row) for row in conn.execute("SELECT * FROM api_keys").fetchall()]
  conn.close()
  return Response(
      json.dumps(keys, indent=2),
      mimetype="application/json",
      headers={"Content-Disposition": "attachment;filename=shayan_keys.json"},
  )


@app.route("/backup-db")
def backup_db():
  if not session.get("logged_in"):
    return redirect(url_for("index"))

  return send_file(DB_PATH, as_attachment=True, download_name="osint_manager.db")


# Proxy Middleware for all OSINT Endpoints
def proxy_request(endpoint_name):
  key = request.args.get("key")
  if not key:
    return (
        jsonify({"error": "Unauthorized: API key is missing. Add ?key=YOUR_KEY"}),
        401,
    )

  conn = get_db()
  key_row = conn.execute(
      "SELECT * FROM api_keys WHERE key_string = ?", (key,)
  ).fetchone()

  if not key_row:
    conn.close()
    return jsonify({"error": "Forbidden: Invalid API key."}), 403

  today_str = datetime.now().strftime("%Y-%m-%d")
  if key_row["expires_at"] < today_str:
    conn.close()
    return (
        jsonify({
            "error": "Forbidden: API key has expired.",
            "expiry_date": key_row["expires_at"],
        }),
        403,
    )

  if key_row["last_reset"] != today_str:
    conn.execute(
        "UPDATE api_keys SET requests_today = 0, last_reset = ? WHERE id = ?",
        (today_str, key_row["id"]),
    )
    conn.commit()
    requests_today = 0
  else:
    requests_today = key_row["requests_today"]

  if requests_today >= key_row["daily_limit"]:
    conn.close()
    return (
        jsonify({
            "error": (
                "Rate Limit Exceeded: Daily request limit reached for this key."
            ),
            "limit": key_row["daily_limit"],
        }),
        429,
    )

  conn.execute(
      "UPDATE api_keys SET requests_today = requests_today + 1 WHERE id = ?",
      (key_row["id"],),
  )

  query_params_str = "&".join(
      [f"{k}={v}" for k, v in request.args.items() if k != "key"]
  )
  client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)

  conn.execute(
      "INSERT INTO request_logs (key_string, endpoint, query_params,"
      " ip_address) VALUES (?, ?, ?, ?)",
      (key, endpoint_name, query_params_str, client_ip),
  )
  conn.commit()
  conn.close()

  upstream_params = dict(request.args)
  upstream_params.pop("key", None)

  try:
    response = requests.get(
        f"{UPSTREAM_BASE}/{endpoint_name}", params=upstream_params, timeout=15
    )
    return response.content, response.status_code, response.headers.items()
  except requests.exceptions.RequestException as e:
    return (
        jsonify({
            "error": "Upstream gateway connection error.",
            "details": str(e),
        }),
        502,
    )


# Register all 20+ proxy endpoints dynamically
for title, ep, sample in ENDPOINTS_LIST:
  app.add_url_rule(
      f"/api/{ep}",
      endpoint=f"proxy_{ep}",
      view_func=lambda name=ep: proxy_request(name),
  )


if __name__ == "__main__":
  app.run(debug=True)
