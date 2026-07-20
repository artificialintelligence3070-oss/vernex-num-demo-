from datetime import datetime, timedelta
import csv
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

DB_PATH = "/tmp/osint_luxury_hub.db"


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
            is_lifetime INTEGER DEFAULT 0,
            daily_limit INTEGER NOT NULL,
            requests_today INTEGER DEFAULT 0,
            last_reset DATE DEFAULT CURRENT_DATE,
            status TEXT DEFAULT 'Active',
            allowed_tools TEXT DEFAULT 'ALL',
            ip_whitelist TEXT DEFAULT '',
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
    ("Number to UPI", "numtoupi", "num=8945996482"),
    ("PAN Card Verification", "pan", "pan=AXDPR2606K"),
    ("Vehicle Registration Info", "vehicle", "vehicle=KA01AB1234"),
    ("Vehicle to Number", "veh2num", "vehicle=KL41V3504"),
    ("Aadhaar Data Lookup", "aadhar", "num=9876543210"),
    ("Aadhaar Family Registry", "adharfamily", "num=9876543210"),
    ("Name Directory Search", "name", "name=abhiraaj"),
    ("PK Telecom Database", "pk", "num=9876543210"),
    ("SMS Bomber Utility", "bomber", "number=9876543210&counter=10"),
    ("IFSC Code Directory", "ifsc", "ifsc=SBIN0001234"),
    ("Pincode Directory", "pincode", "pin=110001"),
    ("IP Geolocation", "ip", "ip=8.8.8.8"),
    ("Vehicle Challan", "challan", "vehicle=UP42BB2572"),
    ("Free Fire Info", "ff", "uid=3143389983"),
    ("BGMI Info", "bgmi", "uid=5121439477"),
    ("Snapchat Info", "snap", "username=priyapanchal272"),
    ("Email Lookup", "email", "email=airtel123@gmail.com"),
    ("GitHub Lookup", "git", "username=ftgamer2"),
    ("Instagram Info", "insta", "username=cristiano"),
    ("Telegram Info", "tg", "info=username"),
    ("Telegram ID Lookup", "tgidinfo", "id=7530266953"),
    ("Number Leak Database", "numleak", "num=9876543210"),
]

TEMPLATE = """
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SHAYAN EXPLORER | Luxury OSINT Executive Suite</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        luxurybg: '#08080a',
                        luxurycard: '#121216',
                        goldaccent: '#d4af37',
                        goldlight: '#f3e5ab'
                    }
                }
            }
        }
    </script>
    <style>
        .glass-card {
            background: rgba(18, 18, 22, 0.85);
            backdrop-filter: blur(30px);
            border: 1px solid rgba(212, 175, 55, 0.18);
            box-shadow: 0 30px 60px rgba(0, 0, 0, 0.8), inset 0 1px 0 rgba(255, 255, 255, 0.05);
        }
        .glass-input {
            background: rgba(8, 8, 10, 0.9);
            border: 1px solid rgba(212, 175, 55, 0.2);
            color: #f3e5ab;
        }
        .glass-input:focus {
            border-color: #d4af37;
            box-shadow: 0 0 20px rgba(212, 175, 55, 0.25);
            outline: none;
        }
        .gold-glow {
            box-shadow: 0 0 30px rgba(212, 175, 55, 0.25);
        }
        .gold-glow:hover {
            box-shadow: 0 0 45px rgba(212, 175, 55, 0.45);
        }
        .gold-gradient {
            background: linear-gradient(135deg, #f3e5ab 0%, #d4af37 50%, #aa7c11 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
    </style>
</head>
<body class="bg-luxurybg text-gray-200 min-h-screen font-sans antialiased selection:bg-amber-500 selection:text-black">

    {% if not session.get('logged_in') %}
    <!-- EXECUTIVE LOGIN -->
    <div class="flex items-center justify-center min-h-screen px-4 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-amber-950/20 via-luxurybg to-luxurybg">
        <div class="glass-card p-8 md:p-12 rounded-3xl w-full max-w-md shadow-2xl relative overflow-hidden">
            <div class="absolute -top-28 -right-28 w-56 h-56 bg-amber-500/10 rounded-full blur-3xl"></div>
            
            <div class="text-center mb-8 relative z-10">
                <div class="inline-flex p-4 rounded-2xl bg-amber-500/10 text-goldaccent mb-4 text-3xl shadow-inner border border-amber-500/30">
                    <i class="fa-solid fa-crown"></i>
                </div>
                <h1 class="text-2xl font-black tracking-widest text-white gold-gradient">SHAYAN EXPLORER</h1>
                <p class="text-[11px] text-amber-400 font-mono tracking-widest uppercase mt-1">Executive OSINT Suite</p>
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
                    <label class="block text-[11px] uppercase font-bold tracking-wider text-amber-500/80 mb-2">Executive ID</label>
                    <div class="relative">
                        <span class="absolute inset-y-0 left-0 pl-4 flex items-center text-amber-500/60"><i class="fa-solid fa-user-tie"></i></span>
                        <input type="text" name="username" required class="glass-input w-full pl-11 pr-4 py-3.5 rounded-xl text-sm focus:outline-none" placeholder="Enter username">
                    </div>
                </div>
                <div>
                    <label class="block text-[11px] uppercase font-bold tracking-wider text-amber-500/80 mb-2">Secure Passcode</label>
                    <div class="relative">
                        <span class="absolute inset-y-0 left-0 pl-4 flex items-center text-amber-500/60"><i class="fa-solid fa-lock"></i></span>
                        <input type="password" name="password" required class="glass-input w-full pl-11 pr-4 py-3.5 rounded-xl text-sm focus:outline-none" placeholder="Enter passcode">
                    </div>
                </div>
                <button type="submit" class="w-full py-3.5 px-4 bg-gradient-to-r from-amber-400 via-amber-500 to-yellow-600 hover:from-amber-300 hover:to-yellow-500 text-black font-black text-xs tracking-widest uppercase rounded-xl gold-glow transition duration-200">
                    Authorize Executive Access
                </button>
            </form>
            <div class="mt-8 text-center text-[11px] text-gray-500 tracking-wider">
                Elite Infrastructure &bull; Architect: <span class="text-goldaccent font-bold">SHAYAN_EXPLORER</span>
            </div>
        </div>
    </div>
    {% else %}
    <!-- EXECUTIVE DASHBOARD -->
    <div class="flex h-screen overflow-hidden" x-data="{ currentTab: 'overview', editModalOpen: false, editKey: {} }">
        
        <!-- Sidebar -->
        <aside class="w-72 glass-card border-r border-amber-500/20 flex flex-col z-20">
            <div class="p-6 border-b border-amber-500/10 flex items-center gap-3.5">
                <div class="bg-amber-500/10 text-goldaccent p-3 rounded-2xl border border-amber-500/30">
                    <i class="fa-solid fa-gem text-lg"></i>
                </div>
                <div>
                    <h2 class="font-black text-xs tracking-wider text-white gold-gradient">SHAYAN EXPLORER</h2>
                    <div class="flex items-center gap-2 mt-0.5">
                        <span class="h-2 w-2 rounded-full bg-goldaccent animate-pulse"></span>
                        <span class="text-[10px] text-amber-400 font-mono tracking-wide">LUXURY SUITE</span>
                    </div>
                </div>
            </div>

            <nav class="flex-1 p-4 space-y-1.5 text-xs font-semibold overflow-y-auto">
                <a @click="currentTab = 'overview'" :class="currentTab === 'overview' ? 'bg-amber-500/15 text-goldaccent border border-amber-500/30 shadow-lg' : 'text-gray-400 hover:bg-gray-800/40 hover:text-white'" class="flex items-center gap-3.5 px-4 py-3 rounded-xl transition cursor-pointer">
                    <i class="fa-solid fa-chart-pie w-5 text-sm"></i> Executive Overview
                </a>
                <a @click="currentTab = 'keys'" :class="currentTab === 'keys' ? 'bg-amber-500/15 text-goldaccent border border-amber-500/30 shadow-lg' : 'text-gray-400 hover:bg-gray-800/40 hover:text-white'" class="flex items-center gap-3.5 px-4 py-3 rounded-xl transition cursor-pointer">
                    <i class="fa-solid fa-key w-5 text-sm"></i> API Vault & IP Whitelist
                </a>
                <a @click="currentTab = 'sandbox'" :class="currentTab === 'sandbox' ? 'bg-amber-500/15 text-goldaccent border border-amber-500/30 shadow-lg' : 'text-gray-400 hover:bg-gray-800/40 hover:text-white'" class="flex items-center gap-3.5 px-4 py-3 rounded-xl transition cursor-pointer">
                    <i class="fa-solid fa-terminal w-5 text-sm"></i> Live API Sandbox
                </a>
                <a @click="currentTab = 'endpoints'" :class="currentTab === 'endpoints' ? 'bg-amber-500/15 text-goldaccent border border-amber-500/30 shadow-lg' : 'text-gray-400 hover:bg-gray-800/40 hover:text-white'" class="flex items-center gap-3.5 px-4 py-3 rounded-xl transition cursor-pointer">
                    <i class="fa-solid fa-code w-5 text-sm"></i> Endpoints & Snippets
                </a>
                <a @click="currentTab = 'publicdocs'" :class="currentTab === 'publicdocs' ? 'bg-amber-500/15 text-goldaccent border border-amber-500/30 shadow-lg' : 'text-gray-400 hover:bg-gray-800/40 hover:text-white'" class="flex items-center gap-3.5 px-4 py-3 rounded-xl transition cursor-pointer">
                    <i class="fa-solid fa-globe w-5 text-sm"></i> Public Catalog (/public)
                </a>
                <a @click="currentTab = 'logs'" :class="currentTab === 'logs' ? 'bg-amber-500/15 text-goldaccent border border-amber-500/30 shadow-lg' : 'text-gray-400 hover:bg-gray-800/40 hover:text-white'" class="flex items-center gap-3.5 px-4 py-3 rounded-xl transition cursor-pointer">
                    <i class="fa-solid fa-shield-halved w-5 text-sm"></i> Audit & Activity Stream
                </a>
                <a @click="currentTab = 'health'" :class="currentTab === 'health' ? 'bg-amber-500/15 text-goldaccent border border-amber-500/30 shadow-lg' : 'text-gray-400 hover:bg-gray-800/40 hover:text-white'" class="flex items-center gap-3.5 px-4 py-3 rounded-xl transition cursor-pointer">
                    <i class="fa-solid fa-heart-pulse w-5 text-sm"></i> Gateway Diagnostics
                </a>
                <a @click="currentTab = 'tools'" :class="currentTab === 'tools' ? 'bg-amber-500/15 text-goldaccent border border-amber-500/30 shadow-lg' : 'text-gray-400 hover:bg-gray-800/40 hover:text-white'" class="flex items-center gap-3.5 px-4 py-3 rounded-xl transition cursor-pointer">
                    <i class="fa-solid fa-database w-5 text-sm"></i> Backup & CSV Export
                </a>
            </nav>

            <div class="p-4 border-t border-amber-500/10">
                <a href="/logout" class="flex items-center gap-3.5 px-4 py-3 rounded-xl text-red-400 hover:bg-red-500/10 transition text-xs font-bold">
                    <i class="fa-solid fa-power-off w-5 text-sm"></i> Secure Sign Out
                </a>
            </div>
        </aside>

        <!-- Main Content Area -->
        <main class="flex-1 flex flex-col overflow-y-auto bg-luxurybg">
            <header class="glass-card border-b border-amber-500/20 px-8 py-4 flex justify-between items-center sticky top-0 z-10">
                <div class="flex items-center gap-4">
                    <div class="h-9 w-9 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-goldaccent font-black text-sm">
                        SE
                    </div>
                    <h1 class="text-sm font-bold text-white flex items-center gap-2">
                        SHAYAN_EXPLORER <span class="text-gray-500">|</span> <span class="gold-gradient">Executive OSINT Hub</span>
                    </h1>
                </div>
                <div class="flex items-center gap-4">
                    <div class="text-right hidden sm:block">
                        <div class="text-[10px] text-amber-400/80 uppercase tracking-widest font-semibold">Lead Architect</div>
                        <div class="text-xs font-mono font-bold text-goldaccent">SHAYAN_EXPLORER</div>
                    </div>
                </div>
            </header>

            <div class="p-8 max-w-7xl mx-auto w-full space-y-8">

                <!-- TAB 1: EXECUTIVE OVERVIEW -->
                <div x-show="currentTab === 'overview'" class="space-y-6">
                    <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
                        <div class="glass-card p-6 rounded-3xl flex items-center justify-between">
                            <div>
                                <p class="text-[11px] text-amber-500/80 uppercase font-bold tracking-wider">Active Vault Keys</p>
                                <h3 class="text-3xl font-black text-white mt-1">{{ keys|length }}</h3>
                            </div>
                            <div class="p-3.5 bg-amber-500/10 text-goldaccent rounded-2xl border border-amber-500/30"><i class="fa-solid fa-key text-xl"></i></div>
                        </div>
                        <div class="glass-card p-6 rounded-3xl flex items-center justify-between">
                            <div>
                                <p class="text-[11px] text-amber-500/80 uppercase font-bold tracking-wider">Total OSINT APIs</p>
                                <h3 class="text-3xl font-black text-goldaccent mt-1">28+</h3>
                            </div>
                            <div class="p-3.5 bg-amber-500/10 text-goldaccent rounded-2xl border border-amber-500/30"><i class="fa-solid fa-network-wired text-xl"></i></div>
                        </div>
                        <div class="glass-card p-6 rounded-3xl flex items-center justify-between">
                            <div>
                                <p class="text-[11px] text-amber-500/80 uppercase font-bold tracking-wider">Logged Requests</p>
                                <h3 class="text-3xl font-black text-yellow-400 mt-1">{{ logs|length }}</h3>
                            </div>
                            <div class="p-3.5 bg-yellow-500/10 text-yellow-400 rounded-2xl border border-yellow-500/30"><i class="fa-solid fa-chart-line text-xl"></i></div>
                        </div>
                        <div class="glass-card p-6 rounded-3xl flex items-center justify-between">
                            <div>
                                <p class="text-[11px] text-amber-500/80 uppercase font-bold tracking-wider">Security State</p>
                                <h3 class="text-base font-black text-goldaccent mt-1 flex items-center gap-2"><span class="h-2.5 w-2.5 rounded-full bg-goldaccent animate-pulse"></span> Protected</h3>
                            </div>
                            <div class="p-3.5 bg-amber-500/10 text-goldaccent rounded-2xl border border-amber-500/30"><i class="fa-solid fa-shield-check text-xl"></i></div>
                        </div>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div class="glass-card p-6 rounded-3xl space-y-4">
                            <h3 class="font-bold text-white text-sm flex items-center gap-2"><i class="fa-solid fa-bolt text-goldaccent"></i> Executive Quick Actions</h3>
                            <div class="grid grid-cols-2 gap-3">
                                <button @click="currentTab = 'keys'" class="p-4 rounded-2xl bg-black/40 border border-amber-500/20 hover:border-amber-500/50 text-left transition group">
                                    <div class="text-goldaccent mb-2 group-hover:scale-110 transition"><i class="fa-solid fa-key text-lg"></i></div>
                                    <div class="font-bold text-xs text-white">API Vault & Edit</div>
                                    <div class="text-[10px] text-amber-500/70 mt-0.5">Suspend, lifetime, tools</div>
                                </button>
                                <button @click="currentTab = 'sandbox'" class="p-4 rounded-2xl bg-black/40 border border-amber-500/20 hover:border-amber-500/50 text-left transition group">
                                    <div class="text-goldaccent mb-2 group-hover:scale-110 transition"><i class="fa-solid fa-terminal text-lg"></i></div>
                                    <div class="font-bold text-xs text-white">Live Sandbox</div>
                                    <div class="text-[10px] text-amber-500/70 mt-0.5">Test endpoints instantly</div>
                                </button>
                                <button @click="currentTab = 'publicdocs'" class="p-4 rounded-2xl bg-black/40 border border-amber-500/20 hover:border-amber-500/50 text-left transition group">
                                    <div class="text-goldaccent mb-2 group-hover:scale-110 transition"><i class="fa-solid fa-globe text-lg"></i></div>
                                    <div class="font-bold text-xs text-white">Public Catalog</div>
                                    <div class="text-[10px] text-amber-500/70 mt-0.5">View without key</div>
                                </button>
                                <button @click="currentTab = 'health'" class="p-4 rounded-2xl bg-black/40 border border-amber-500/20 hover:border-amber-500/50 text-left transition group">
                                    <div class="text-goldaccent mb-2 group-hover:scale-110 transition"><i class="fa-solid fa-heart-pulse text-lg"></i></div>
                                    <div class="font-bold text-xs text-white">Diagnostics</div>
                                    <div class="text-[10px] text-amber-500/70 mt-0.5">Gateway latency pings</div>
                                </button>
                            </div>
                        </div>

                        <div class="glass-card p-6 rounded-3xl space-y-4">
                            <h3 class="font-bold text-white text-sm flex items-center gap-2"><i class="fa-solid fa-award text-goldaccent"></i> Luxury Architecture Specs</h3>
                            <div class="space-y-3 text-xs">
                                <div class="flex justify-between p-3 rounded-xl bg-black/50 border border-amber-500/10">
                                    <span class="text-gray-400">Public Documentation Route</span>
                                    <span class="font-mono text-goldaccent">Active (/public/endpoints)</span>
                                </div>
                                <div class="flex justify-between p-3 rounded-xl bg-black/50 border border-amber-500/10">
                                    <span class="text-gray-400">Suspension & Lifecycle</span>
                                    <span class="font-mono text-white">Instant Toggle / Lifetime</span>
                                </div>
                                <div class="flex justify-between p-3 rounded-xl bg-black/50 border border-amber-500/10">
                                    <span class="text-gray-400">Granular Tool Access</span>
                                    <span class="font-mono text-goldaccent">Specific or All Tools</span>
                                </div>
                                <div class="flex justify-between p-3 rounded-xl bg-black/50 border border-amber-500/10">
                                    <span class="text-gray-400">Primary Developer</span>
                                    <span class="font-mono text-goldaccent font-bold">SHAYAN_EXPLORER</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- TAB 2: KEYS MANAGER & EDIT -->
                <div x-show="currentTab === 'keys'" class="space-y-6" x-data="{ search: '', showCreateModal: false, isLifetime: false }">
                    <div class="glass-card p-6 rounded-3xl space-y-4">
                        <div class="flex justify-between items-center">
                            <h3 class="text-sm font-bold text-white flex items-center gap-2"><i class="fa-solid fa-key text-goldaccent"></i> API Key Vault & IP Whitelist</h3>
                            <button @click="showCreateModal = !showCreateModal" class="px-5 py-2.5 bg-gradient-to-r from-amber-400 to-yellow-600 text-black font-black text-xs uppercase tracking-wider rounded-xl gold-glow transition">
                                <i class="fa-solid fa-plus mr-1"></i> Generate New Key
                            </button>
                        </div>

                        <!-- CREATE KEY FORM -->
                        <div x-show="showCreateModal" class="p-6 rounded-2xl bg-black/60 border border-amber-500/30 space-y-4">
                            <h4 class="text-xs font-bold uppercase tracking-wider text-goldaccent">Configure New Key</h4>
                            <form method="POST" action="/create-key" class="space-y-4">
                                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                                    <div>
                                        <label class="block text-[10px] uppercase font-bold text-amber-500/80 mb-2">Key Name / Client ID</label>
                                        <input type="text" name="name" required class="glass-input w-full px-4 py-3 rounded-xl text-xs focus:outline-none" placeholder="e.g. VIP Client">
                                    </div>
                                    <div>
                                        <label class="block text-[10px] uppercase font-bold text-amber-500/80 mb-2">Daily Request Limit</label>
                                        <input type="number" name="daily_limit" value="2000" required class="glass-input w-full px-4 py-3 rounded-xl text-xs focus:outline-none">
                                    </div>
                                    <div>
                                        <label class="block text-[10px] uppercase font-bold text-amber-500/80 mb-2">IP Whitelist (Optional)</label>
                                        <input type="text" name="ip_whitelist" placeholder="e.g. 192.168.1.50 (blank for all)" class="glass-input w-full px-4 py-3 rounded-xl text-xs focus:outline-none font-mono">
                                    </div>
                                </div>

                                <div class="flex items-center gap-6">
                                    <label class="flex items-center gap-2 text-xs text-gray-300 cursor-pointer">
                                        <input type="checkbox" name="is_lifetime" x-model="isLifetime" value="1" class="rounded bg-black border-amber-500/40 text-amber-500 focus:ring-0">
                                        Lifetime / Permanent Expiration
                                    </label>
                                    <div x-show="!isLifetime" class="flex-1">
                                        <input type="date" name="expires_at" class="glass-input px-4 py-2.5 rounded-xl text-xs focus:outline-none">
                                    </div>
                                </div>

                                <div>
                                    <label class="block text-[10px] uppercase font-bold text-amber-500/80 mb-2">Select Endpoints Access (Choose Specific or All)</label>
                                    <div class="grid grid-cols-2 md:grid-cols-4 gap-2 bg-black/50 p-4 rounded-xl border border-amber-500/20 text-[11px] max-h-48 overflow-y-auto">
                                        <label class="flex items-center gap-2 text-goldaccent font-bold"><input type="checkbox" name="tools" value="ALL" checked class="rounded bg-black border-amber-500 text-amber-500"> All Tools (Full Access)</label>
                                        {% for title, ep, sample in ENDPOINTS_LIST %}
                                        <label class="flex items-center gap-2 text-gray-300"><input type="checkbox" name="tools" value="{{ ep }}" class="rounded bg-black border-amber-500/40 text-amber-500"> {{ title }}</label>
                                        {% endfor %}
                                    </div>
                                </div>

                                <div class="flex justify-end gap-3">
                                    <button type="button" @click="showCreateModal = false" class="px-4 py-2.5 rounded-xl bg-gray-800 text-xs font-bold text-gray-300">Cancel</button>
                                    <button type="submit" class="px-6 py-2.5 rounded-xl bg-amber-500 text-black font-black text-xs uppercase tracking-wider gold-glow">Save Key</button>
                                </div>
                            </form>
                        </div>
                    </div>

                    <!-- Keys Table -->
                    <div class="glass-card rounded-3xl overflow-hidden">
                        <div class="p-6 border-b border-amber-500/20 flex flex-col sm:flex-row justify-between items-center gap-4">
                            <h3 class="text-sm font-bold text-white flex items-center gap-2"><i class="fa-solid fa-shield text-goldaccent"></i> Active Inventory & Status Control</h3>
                            <div class="flex items-center gap-3 w-full sm:w-auto">
                                <input type="text" x-model="search" placeholder="Search keys or names..." class="glass-input px-4 py-2 rounded-xl text-xs focus:outline-none w-full sm:w-64">
                                <a href="/export-keys" class="px-4 py-2 rounded-xl bg-gray-800 hover:bg-gray-700 text-xs font-bold text-goldaccent transition flex items-center gap-2 whitespace-nowrap">
                                    <i class="fa-solid fa-download"></i> Export JSON
                                </a>
                            </div>
                        </div>
                        <div class="overflow-x-auto">
                            <table class="w-full text-left border-collapse">
                                <thead>
                                    <tr class="border-b border-amber-500/20 text-[10px] uppercase font-bold text-amber-500/80 bg-black/40">
                                        <th class="p-4">Name</th>
                                        <th class="p-4">API Token String</th>
                                        <th class="p-4">Status</th>
                                        <th class="p-4">Requests Today</th>
                                        <th class="p-4">Limit / IP Whitelist</th>
                                        <th class="p-4">Expiration</th>
                                        <th class="p-4 text-right">Actions</th>
                                    </tr>
                                </thead>
                                <tbody class="divide-y divide-amber-500/10 text-xs font-mono">
                                    {% for k in keys %}
                                    <tr class="hover:bg-amber-500/5 transition" x-show="!search || '{{ k.name }}'.toLowerCase().includes(search.toLowerCase()) || '{{ k.key_string }}'.toLowerCase().includes(search.toLowerCase())">
                                        <td class="p-4 font-sans font-bold text-white">{{ k.name }}</td>
                                        <td class="p-4"><code class="bg-black/60 px-3 py-1 rounded-lg text-goldaccent select-all">{{ k.key_string }}</code></td>
                                        <td class="p-4">
                                            {% if k.status == 'Active' %}
                                            <span class="px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 font-bold border border-emerald-500/30">Active</span>
                                            {% else %}
                                            <span class="px-2.5 py-1 rounded-full bg-red-500/10 text-red-400 font-bold border border-red-500/30">Suspended</span>
                                            {% endif %}
                                        </td>
                                        <td class="p-4 flex items-center gap-2">
                                            <span class="px-2.5 py-1 rounded-full bg-amber-500/10 text-amber-400 font-bold">{{ k.requests_today }}</span>
                                            <a href="/reset-counter/{{ k.id }}" class="text-[10px] text-gray-400 hover:text-goldaccent" title="Reset counter today"><i class="fa-solid fa-rotate-right"></i></a>
                                        </td>
                                        <td class="p-4 text-gray-300">
                                            <div>Limit: {{ k.daily_limit }}</div>
                                            <div class="text-[10px] text-amber-400/80">IP: {{ k.ip_whitelist if k.ip_whitelist else 'Any IP' }}</div>
                                        </td>
                                        <td class="p-4 text-gray-300 font-sans">
                                            {% if k.is_lifetime %}
                                            <span class="text-goldaccent font-bold">Lifetime (Permanent)</span>
                                            {% else %}
                                            {{ k.expires_at }}
                                            {% endif %}
                                        </td>
                                        <td class="p-4 text-right space-x-1 whitespace-nowrap font-sans">
                                            {% if k.status == 'Active' %}
                                            <a href="/suspend-key/{{ k.id }}" class="px-3 py-1.5 rounded-lg bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 font-bold transition text-xs" title="Suspend API">
                                                <i class="fa-solid fa-ban"></i>
                                            </a>
                                            {% else %}
                                            <a href="/unsuspend-key/{{ k.id }}" class="px-3 py-1.5 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 font-bold transition text-xs" title="Unsuspend API">
                                                <i class="fa-solid fa-check"></i>
                                            </a>
                                            {% endif %}
                                            <button @click="editModalOpen = true; editKey = {id: '{{ k.id }}', name: '{{ k.name }}', daily_limit: '{{ k.daily_limit }}', expires_at: '{{ k.expires_at }}', ip_whitelist: '{{ k.ip_whitelist }}'}" class="px-3 py-1.5 rounded-lg bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 font-bold transition text-xs" title="Edit Key">
                                                <i class="fa-solid fa-pen"></i>
                                            </button>
                                            <a href="/delete-key/{{ k.id }}" onclick="return confirm('Permanently delete this API key?');" class="px-3 py-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 font-bold transition text-xs" title="Delete API">
                                                <i class="fa-solid fa-trash"></i>
                                            </a>
                                        </td>
                                    </tr>
                                    {% else %}
                                    <tr>
                                        <td colspan="7" class="p-8 text-center text-gray-500 font-sans">No API keys generated yet.</td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <!-- EDIT KEY MODAL -->
                    <div x-show="editModalOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md px-4">
                        <div class="glass-card p-6 md:p-8 rounded-3xl w-full max-w-lg space-y-6 relative border border-amber-500/30">
                            <h3 class="text-base font-bold text-white flex items-center gap-2"><i class="fa-solid fa-pen-to-square text-goldaccent"></i> Edit Key Parameters</h3>
                            <form method="POST" action="/edit-key" class="space-y-4">
                                <input type="hidden" name="id" x-model="editKey.id">
                                <div>
                                    <label class="block text-[10px] uppercase font-bold text-amber-500/80 mb-2">Key Name</label>
                                    <input type="text" name="name" x-model="editKey.name" required class="glass-input w-full px-4 py-3 rounded-xl text-xs focus:outline-none">
                                </div>
                                <div>
                                    <label class="block text-[10px] uppercase font-bold text-amber-500/80 mb-2">Daily Request Limit</label>
                                    <input type="number" name="daily_limit" x-model="editKey.daily_limit" required class="glass-input w-full px-4 py-3 rounded-xl text-xs focus:outline-none">
                                </div>
                                <div>
                                    <label class="block text-[10px] uppercase font-bold text-amber-500/80 mb-2">IP Whitelist</label>
                                    <input type="text" name="ip_whitelist" x-model="editKey.ip_whitelist" class="glass-input w-full px-4 py-3 rounded-xl text-xs focus:outline-none font-mono">
                                </div>
                                <div>
                                    <label class="block text-[10px] uppercase font-bold text-amber-500/80 mb-2">Expiration Date</label>
                                    <input type="date" name="expires_at" x-model="editKey.expires_at" class="glass-input w-full px-4 py-3 rounded-xl text-xs focus:outline-none">
                                </div>
                                <div class="flex justify-end gap-3 pt-2">
                                    <button type="button" @click="editModalOpen = false" class="px-4 py-2.5 rounded-xl bg-gray-800 text-xs font-bold text-gray-300">Cancel</button>
                                    <button type="submit" class="px-6 py-2.5 rounded-xl bg-amber-500 text-black font-black text-xs uppercase tracking-wider gold-glow">Update Key</button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>

                <!-- TAB 3: LIVE API SANDBOX -->
                <div x-show="currentTab === 'sandbox'" class="space-y-6" x-data="{ endpoint: 'number', key: '', paramName: 'num', paramVal: '9876543210', result: null, loading: false }">
                    <div class="glass-card p-6 rounded-3xl space-y-5">
                        <h3 class="text-sm font-bold text-white flex items-center gap-2"><i class="fa-solid fa-terminal text-goldaccent"></i> Interactive API Sandbox</h3>
                        <p class="text-xs text-gray-400">Test any of the 28+ OSINT proxy endpoints in real-time.</p>
                        
                        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div>
                                <label class="block text-[10px] uppercase font-bold text-amber-500/80 mb-2">Select Endpoint</label>
                                <select x-model="endpoint" class="glass-input w-full px-4 py-3 rounded-xl text-xs focus:outline-none">
                                    {% for title, ep, sample in ENDPOINTS_LIST %}
                                    <option value="{{ ep }}">{{ title }} (/api/{{ ep }})</option>
                                    {% endfor %}
                                </select>
                            </div>
                            <div>
                                <label class="block text-[10px] uppercase font-bold text-amber-500/80 mb-2">API Key</label>
                                <input type="text" x-model="key" placeholder="Enter valid API key" class="glass-input w-full px-4 py-3 rounded-xl text-xs focus:outline-none font-mono">
                            </div>
                            <div>
                                <label class="block text-[10px] uppercase font-bold text-amber-500/80 mb-2">Query Parameter & Value</label>
                                <div class="flex gap-2">
                                    <input type="text" x-model="paramName" placeholder="param" class="glass-input w-1/3 px-3 py-3 rounded-xl text-xs focus:outline-none font-mono">
                                    <input type="text" x-model="paramVal" placeholder="value" class="glass-input w-2/3 px-3 py-3 rounded-xl text-xs focus:outline-none font-mono">
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
                        " class="px-6 py-3 bg-gradient-to-r from-amber-400 to-yellow-600 text-black font-black text-xs uppercase tracking-wider rounded-xl gold-glow transition flex items-center gap-2">
                            <i class="fa-solid fa-play"></i> Execute Sandbox Request
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
                            <i class="fa-solid fa-spinner fa-spin text-lg text-goldaccent mb-2"></i> Querying upstream gateway...
                        </div>
                        <pre x-show="!loading && result" class="bg-black/80 p-4 rounded-2xl text-amber-300 font-mono text-xs overflow-x-auto max-h-96 border border-amber-500/20" x-text="JSON.stringify(result ? result.body : {}, null, 2)"></pre>
                    </div>
                </div>

                <!-- TAB 4: ENDPOINTS & CODE SNIPPETS -->
                <div x-show="currentTab === 'endpoints'" class="space-y-6" x-data="{ selectedEp: 'number' }">
                    <div class="glass-card p-6 rounded-3xl space-y-6">
                        <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                            <div>
                                <h3 class="text-sm font-bold text-white flex items-center gap-2"><i class="fa-solid fa-code text-goldaccent"></i> Endpoints Directory & Code Generators</h3>
                                <p class="text-xs text-gray-400 mt-1">Multi-language SDK snippets for all 28+ OSINT endpoints.</p>
                            </div>
                            <select x-model="selectedEp" class="glass-input px-4 py-2.5 rounded-xl text-xs focus:outline-none">
                                {% for title, ep, sample in ENDPOINTS_LIST %}
                                <option value="{{ ep }}">{{ title }} (/api/{{ ep }})</option>
                                {% endfor %}
                            </select>
                        </div>

                        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div class="space-y-3">
                                <h4 class="text-xs font-bold uppercase tracking-wider text-amber-500/80">cURL</h4>
                                <pre class="bg-black/80 p-4 rounded-2xl text-amber-300 font-mono text-xs overflow-x-auto border border-amber-500/20" x-text="`curl -X GET 'https://` + window.location.host + `/api/` + selectedEp + `?key=YOUR_KEY&query=VALUE'`"></pre>
                            </div>
                            <div class="space-y-3">
                                <h4 class="text-xs font-bold uppercase tracking-wider text-amber-500/80">Python (Requests)</h4>
                                <pre class="bg-black/80 p-4 rounded-2xl text-amber-300 font-mono text-xs overflow-x-auto border border-amber-500/20" x-text="`import requests\n\nurl = 'https://` + window.location.host + `/api/` + selectedEp + `'\nparams = {'key': 'YOUR_KEY', 'query': 'VALUE'}\nres = requests.get(url, params=params)\nprint(res.json())`"></pre>
                            </div>
                            <div class="space-y-3">
                                <h4 class="text-xs font-bold uppercase tracking-wider text-amber-500/80">JavaScript (Fetch)</h4>
                                <pre class="bg-black/80 p-4 rounded-2xl text-yellow-300 font-mono text-xs overflow-x-auto border border-amber-500/20" x-text="`fetch('https://` + window.location.host + `/api/` + selectedEp + `?key=YOUR_KEY&query=VALUE')\n  .then(res => res.json())\n  .then(data => console.log(data));`"></pre>
                            </div>
                            <div class="space-y-3">
                                <h4 class="text-xs font-bold uppercase tracking-wider text-amber-500/80">PHP (cURL)</h4>
                                <pre class="bg-black/80 p-4 rounded-2xl text-amber-200 font-mono text-xs overflow-x-auto border border-amber-500/20" x-text="`$ch = curl_init();\ncurl_setopt($ch, CURLOPT_URL, 'https://` + window.location.host + `/api/` + selectedEp + `?key=YOUR_KEY&query=VALUE');\ncurl_setopt($ch, CURLOPT_RETURNTRANSFER, true);\n$response = curl_exec($ch);\ncurl_close($ch);\necho $response;`"></pre>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- TAB 5: PUBLIC CATALOG (/public/endpoints) -->
                <div x-show="currentTab === 'publicdocs'" class="space-y-6">
                    <div class="glass-card p-6 rounded-3xl space-y-6">
                        <div class="flex justify-between items-center">
                            <div>
                                <h3 class="text-sm font-bold text-white flex items-center gap-2"><i class="fa-solid fa-globe text-goldaccent"></i> Public Unauthenticated Endpoints Catalog</h3>
                                <p class="text-xs text-gray-400 mt-1">This catalog is accessible publicly without requiring an API key at <a href="/public/endpoints" target="_blank" class="text-goldaccent underline">/public/endpoints</a>.</p>
                            </div>
                            <a href="/public/endpoints" target="_blank" class="px-4 py-2 bg-amber-500/10 text-goldaccent border border-amber-500/30 rounded-xl text-xs font-bold hover:bg-amber-500/20 transition">
                                <i class="fa-solid fa-external-link mr-1"></i> Open Public JSON API
                            </a>
                        </div>

                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {% for title, ep, sample in ENDPOINTS_LIST %}
                            <div class="p-4 rounded-2xl bg-black/50 border border-amber-500/15 flex flex-col justify-between space-y-2">
                                <div class="flex justify-between items-center">
                                    <span class="font-bold text-white text-xs">{{ title }}</span>
                                    <span class="font-mono text-[10px] text-goldaccent bg-amber-500/10 px-2 py-0.5 rounded">/api/{{ ep }}</span>
                                </div>
                                <div class="text-[11px] font-mono text-gray-400 bg-black/60 p-2 rounded border border-gray-800">
                                    Example: /api/{{ ep }}?key=YOUR_KEY&{{ sample }}
                                </div>
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                </div>

                <!-- TAB 6: AUDIT LOGS -->
                <div x-show="currentTab === 'logs'" class="space-y-6" x-data="{ logSearch: '' }">
                    <div class="glass-card rounded-3xl overflow-hidden">
                        <div class="p-6 border-b border-amber-500/20 flex flex-col sm:flex-row justify-between items-center gap-4">
                            <h3 class="text-sm font-bold text-white flex items-center gap-2"><i class="fa-solid fa-shield-halved text-goldaccent"></i> Request Audit Trail & Activity Stream</h3>
                            <div class="flex items-center gap-3 w-full sm:w-auto">
                                <input type="text" x-model="logSearch" placeholder="Filter logs by key or endpoint..." class="glass-input px-4 py-2 rounded-xl text-xs focus:outline-none w-full sm:w-64">
                                <a href="/clear-logs" onclick="return confirm('Clear all audit logs?');" class="px-4 py-2 rounded-xl bg-red-500/10 hover:bg-red-500/20 text-red-400 text-xs font-bold transition whitespace-nowrap">
                                    <i class="fa-solid fa-trash mr-1"></i> Clear Logs
                                </a>
                            </div>
                        </div>
                        <div class="overflow-x-auto">
                            <table class="w-full text-left border-collapse">
                                <thead>
                                    <tr class="border-b border-amber-500/20 text-[10px] uppercase font-bold text-amber-500/80 bg-black/40">
                                        <th class="p-4">Timestamp</th>
                                        <th class="p-4">API Key Token</th>
                                        <th class="p-4">Endpoint</th>
                                        <th class="p-4">Query Parameters</th>
                                        <th class="p-4">Client IP</th>
                                    </tr>
                                </thead>
                                <tbody class="divide-y divide-amber-500/10 text-xs font-mono">
                                    {% for log in logs %}
                                    <tr class="hover:bg-amber-500/5 transition" x-show="!logSearch || '{{ log.key_string }}'.toLowerCase().includes(logSearch.toLowerCase()) || '{{ log.endpoint }}'.toLowerCase().includes(logSearch.toLowerCase())">
                                        <td class="p-4 text-gray-400 text-[11px]">{{ log.timestamp }}</td>
                                        <td class="p-4 text-goldaccent">{{ log.key_string }}</td>
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

                <!-- TAB 7: GATEWAY HEALTH -->
                <div x-show="currentTab === 'health'" class="space-y-6">
                    <div class="glass-card p-6 rounded-3xl space-y-6">
                        <div class="flex justify-between items-center">
                            <div>
                                <h3 class="text-sm font-bold text-white flex items-center gap-2"><i class="fa-solid fa-heart-pulse text-goldaccent"></i> Upstream Gateway Diagnostics</h3>
                                <p class="text-xs text-gray-400 mt-1">Real-time status check for connected OSINT infrastructure.</p>
                            </div>
                        </div>

                        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                            <div class="glass-card p-5 rounded-2xl flex items-center justify-between">
                                <div>
                                    <p class="text-[10px] uppercase font-bold text-amber-500/80">Upstream Provider</p>
                                    <h4 class="text-base font-black text-emerald-400 mt-1 flex items-center gap-2">
                                        <span class="h-2.5 w-2.5 rounded-full bg-emerald-400 animate-pulse"></span> Operational
                                    </h4>
                                </div>
                                <div class="text-goldaccent text-xl"><i class="fa-solid fa-cloud-arrow-up"></i></div>
                            </div>
                            <div class="glass-card p-5 rounded-2xl flex items-center justify-between">
                                <div>
                                    <p class="text-[10px] uppercase font-bold text-amber-500/80">SQLite Database</p>
                                    <h4 class="text-base font-black text-goldaccent mt-1">Connected (/tmp)</h4>
                                </div>
                                <div class="text-goldaccent text-xl"><i class="fa-solid fa-database"></i></div>
                            </div>
                            <div class="glass-card p-5 rounded-2xl flex items-center justify-between">
                                <div>
                                    <p class="text-[10px] uppercase font-bold text-amber-500/80">Hosting Platform</p>
                                    <h4 class="text-base font-black text-yellow-400 mt-1">Vercel Serverless</h4>
                                </div>
                                <div class="text-yellow-400 text-xl"><i class="fa-solid fa-bolt"></i></div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- TAB 8: BACKUP & CSV EXPORT -->
                <div x-show="currentTab === 'tools'" class="space-y-6">
                    <div class="glass-card p-6 rounded-3xl space-y-6">
                        <div>
                            <h3 class="text-sm font-bold text-white flex items-center gap-2"><i class="fa-solid fa-database text-goldaccent"></i> Backup & Data Export Utilities</h3>
                            <p class="text-xs text-gray-400 mt-1">Download complete SQLite backups, JSON vaults, or CSV audit reports.</p>
                        </div>

                        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <a href="/backup-db" class="p-5 rounded-2xl bg-black/50 border border-amber-500/20 hover:border-amber-500/50 flex items-center justify-between transition group">
                                <div>
                                    <div class="font-bold text-xs text-white group-hover:text-goldaccent transition">SQLite Database Backup</div>
                                    <div class="text-[10px] text-gray-400 mt-0.5">Secure `.db` file archive</div>
                                </div>
                                <div class="p-3 bg-amber-500/10 text-goldaccent rounded-xl"><i class="fa-solid fa-download"></i></div>
                            </a>
                            <a href="/export-keys" class="p-5 rounded-2xl bg-black/50 border border-amber-500/20 hover:border-amber-500/50 flex items-center justify-between transition group">
                                <div>
                                    <div class="font-bold text-xs text-white group-hover:text-goldaccent transition">Export API Keys JSON</div>
                                    <div class="text-[10px] text-gray-400 mt-0.5">Vault inventory dump</div>
                                </div>
                                <div class="p-3 bg-amber-500/10 text-goldaccent rounded-xl"><i class="fa-solid fa-file-code"></i></div>
                            </a>
                            <a href="/export-csv" class="p-5 rounded-2xl bg-black/50 border border-amber-500/20 hover:border-amber-500/50 flex items-center justify-between transition group">
                                <div>
                                    <div class="font-bold text-xs text-white group-hover:text-goldaccent transition">Export Logs CSV</div>
                                    <div class="text-[10px] text-gray-400 mt-0.5">Spreadsheet audit report</div>
                                </div>
                                <div class="p-3 bg-amber-500/10 text-goldaccent rounded-xl"><i class="fa-solid fa-file-csv"></i></div>
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
    flash("Invalid executive credentials.", "error")
    return redirect(url_for("index"))


@app.route("/logout")
def logout():
  session.clear()
  return redirect(url_for("index"))


@app.route("/public/endpoints")
def public_endpoints():
  """Publicly accessible endpoint catalog without key authentication."""
  catalog = []
  for title, ep, sample in ENDPOINTS_LIST:
    catalog.append({
        "title": title,
        "endpoint": f"/api/{ep}",
        "sample_query": f"https://{request.host}/api/{ep}?key=YOUR_KEY&{sample}",
    })
  return jsonify({
      "architect": "SHAYAN_EXPLORER",
      "suite": "Luxury OSINT Executive Suite",
      "total_endpoints": len(catalog),
      "endpoints": catalog,
  })


@app.route("/create-key", methods=["POST"])
def create_key():
  if not session.get("logged_in"):
    return redirect(url_for("index"))

  name = request.form.get("name")
  daily_limit = request.form.get("daily_limit", 2000)
  is_lifetime = 1 if request.form.get("is_lifetime") else 0
  expires_at = (
      "2099-12-31" if is_lifetime else request.form.get("expires_at", "2099-12-31")
  )
  ip_whitelist = request.form.get("ip_whitelist", "").strip()

  tools = request.form.getlist("tools")
  allowed_tools = "ALL" if "ALL" in tools or not tools else ",".join(tools)

  key_string = f"se_lux_{os.urandom(8).hex()}"

  conn = get_db()
  conn.execute(
      "INSERT INTO api_keys (key_string, name, expires_at, is_lifetime,"
      " daily_limit, allowed_tools, ip_whitelist) VALUES (?, ?, ?, ?, ?, ?, ?)",
      (
          key_string,
          name,
          expires_at,
          is_lifetime,
          daily_limit,
          allowed_tools,
          ip_whitelist,
      ),
  )
  conn.commit()
  conn.close()
  return redirect(url_for("index"))


@app.route("/edit-key", methods=["POST"])
def edit_key():
  if not session.get("logged_in"):
    return redirect(url_for("index"))

  key_id = request.form.get("id")
  name = request.form.get("name")
  daily_limit = request.form.get("daily_limit")
  expires_at = request.form.get("expires_at")
  ip_whitelist = request.form.get("ip_whitelist", "").strip()

  conn = get_db()
  conn.execute(
      "UPDATE api_keys SET name = ?, daily_limit = ?, expires_at = ?,"
      " ip_whitelist = ? WHERE id = ?",
      (name, daily_limit, expires_at, ip_whitelist, key_id),
  )
  conn.commit()
  conn.close()
  return redirect(url_for("index"))


@app.route("/suspend-key/<int:key_id>")
def suspend_key(key_id):
  if not session.get("logged_in"):
    return redirect(url_for("index"))

  conn = get_db()
  conn.execute(
      "UPDATE api_keys SET status = 'Suspended' WHERE id = ?", (key_id,)
  )
  conn.commit()
  conn.close()
  return redirect(url_for("index"))


@app.route("/unsuspend-key/<int:key_id>")
def unsuspend_key(key_id):
  if not session.get("logged_in"):
    return redirect(url_for("index"))

  conn = get_db()
  conn.execute("UPDATE api_keys SET status = 'Active' WHERE id = ?", (key_id,))
  conn.commit()
  conn.close()
  return redirect(url_for("index"))


@app.route("/reset-counter/<int:key_id>")
def reset_counter(key_id):
  if not session.get("logged_in"):
    return redirect(url_for("index"))

  conn = get_db()
  conn.execute(
      "UPDATE api_keys SET requests_today = 0 WHERE id = ?", (key_id,)
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
      headers={"Content-Disposition": "attachment;filename=shayan_vault.json"},
  )


@app.route("/export-csv")
def export_csv():
  if not session.get("logged_in"):
    return redirect(url_for("index"))

  conn = get_db()
  logs = conn.execute("SELECT * FROM request_logs").fetchall()
  conn.close()

  output = io.StringIO()
  writer = csv.writer(output)
  writer.writerow(
      ["ID", "Key String", "Endpoint", "Query Params", "IP Address", "Timestamp"]
  )
  for log in logs:
    writer.writerow([
        log["id"],
        log["key_string"],
        log["endpoint"],
        log["query_params"],
        log["ip_address"],
        log["timestamp"],
    ])

  output.seek(0)
  return Response(
      output.getvalue(),
      mimetype="text/csv",
      headers={
          "Content-Disposition": "attachment;filename=shayan_audit_logs.csv"
      },
  )


@app.route("/backup-db")
def backup_db():
  if not session.get("logged_in"):
    return redirect(url_for("index"))

  return send_file(DB_PATH, as_attachment=True, download_name="shayan_osint.db")


# Proxy Middleware for all OSINT Endpoints
def proxy_request(endpoint_name):
  key = request.args.get("key")
  if not key:
    return (
        jsonify({
            "error": "Unauthorized: API key is missing. Add ?key=YOUR_KEY"
        }),
        401,
    )

  conn = get_db()
  key_row = conn.execute(
      "SELECT * FROM api_keys WHERE key_string = ?", (key,)
  ).fetchone()

  if not key_row:
    conn.close()
    return jsonify({"error": "Forbidden: Invalid API key."}), 403

  if key_row["status"] == "Suspended":
    conn.close()
    return (
        jsonify({
            "error": "Forbidden: This API key has been suspended by executive"
            " command."
        }),
        403,
    )

  # Check IP Whitelist
  client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
  if key_row["ip_whitelist"]:
    whitelisted_ips = [
        ip.strip() for ip in key_row["ip_whitelist"].split(",") if ip.strip()
    ]
    if client_ip not in whitelisted_ips:
      conn.close()
      return (
          jsonify({
              "error": (
                  "Forbidden: Request IP not authorized in key whitelist."
              ),
              "client_ip": client_ip,
          }),
          403,
      )

  # Check Tool Permissions
  allowed_tools = key_row["allowed_tools"]
  if allowed_tools != "ALL":
    tools_list = allowed_tools.split(",")
    if endpoint_name not in tools_list:
      conn.close()
      return (
          jsonify({
              "error": (
                  "Forbidden: This API key does not have access to endpoint"
                  f" /api/{endpoint_name}"
              )
          }),
          403,
      )

  today_str = datetime.now().strftime("%Y-%m-%d")
  if not key_row["is_lifetime"] and key_row["expires_at"] < today_str:
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


# Register all proxy endpoints dynamically
for title, ep, sample in ENDPOINTS_LIST:
  app.add_url_rule(
      f"/api/{ep}",
      endpoint=f"proxy_{ep}",
      view_func=lambda name=ep: proxy_request(name),
  )


if __name__ == "__main__":
  app.run(debug=True)
