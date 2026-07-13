import os
import json
import logging
from datetime import datetime, date
from typing import Dict, List, Optional
from fastapi import FastAPI, Depends, HTTPException, Header, status, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="SHAYAN_EXPLORER Premium Gateway", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔐 SECURITY CONFIGURATION (Environment variables)
RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "rzp_live_TCc5USt5FlmfrI")
ADMIN_USERNAME = "vernex"
ADMIN_PASSWORD = "vernex@16vx"

# In-memory database architecture
api_keys_db: Dict[str, Dict] = {
    "explorer16": {
        "key_name": "VIP Enterprise Access",
        "expires_at": "2026-12-31T23:59:59",
        "daily_limit": 5000,
        "request_count": 42,
        "last_reset": str(date.today()),
        "allowed_tools": ["all"]
    }
}

logs_db: List[Dict] = [
    {"timestamp": "2026-07-13T16:20:11", "key_used": "explorer16", "tool": "Core_Identity_Verify", "status": "Success"},
    {"timestamp": "2026-07-13T16:22:45", "key_used": "explorer16", "tool": "Network_Telemetry", "status": "Success"}
]

# Pydantic Schemas
class KeyGenerateRequest(BaseModel):
    key_name: str
    custom_key: str
    expires_at: str
    daily_limit: int
    allowed_tools: List[str]

class LoginRequest(BaseModel):
    username: str
    password: str

# --- API ENDPOINTS ---
@app.post("/api/admin/login")
async def admin_login(data: LoginRequest):
    if data.username == ADMIN_USERNAME and data.password == ADMIN_PASSWORD:
        return {"status": "success", "token": "premium_secure_session_token"}
    raise HTTPException(status_code=401, detail="Unauthorized: Access Credentials Invalid.")

@app.post("/api/admin/generate-key")
async def generate_key(data: KeyGenerateRequest):
    api_keys_db[data.custom_key] = {
        "key_name": data.key_name,
        "expires_at": data.expires_at,
        "daily_limit": data.daily_limit,
        "request_count": 0,
        "last_reset": str(date.today()),
        "allowed_tools": data.allowed_tools
    }
    return {"status": "success", "message": f"Token Key '{data.custom_key}' integrated."}

@app.get("/api/admin/dashboard-data")
async def get_dashboard_data():
    return {
        "keys": api_keys_db,
        "logs": logs_db[-20:] # Return last 20 operations
    }

# --- PREMIUM USER INTERFACE SURFACE ---
@app.get("/", response_class=HTMLResponse)
async def render_luxury_portal():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SHAYAN EXPLORER | Luxury API Management Network</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
        <script src="https://unpkg.com/lucide@latest"></script>
        <script>
            tailwind.config = {
                theme: {
                    extend: {
                        colors: {
                            gold: { 400: '#E6C15C', 500: '#D4AF37', 600: '#AA882C' },
                            darkspace: '#070A12'
                        }
                    }
                }
            }
        </script>
        <style>
            canvas { position: fixed; top:0; left:0; width:100%; height:100%; z-index:1; pointer-events:none; }
            .glass { background: rgba(15, 22, 42, 0.65); backdrop-filter: blur(14px); border: 1px solid rgba(212, 175, 55, 0.15); }
            .glass-gold { background: linear-gradient(135deg, rgba(212,175,55,0.1) 0%, rgba(7,10,18,0.4) 100%); border: 1px solid rgba(212, 175, 55, 0.3); }
        </style>
    </head>
    <body class="bg-darkspace text-slate-100 min-h-screen overflow-x-hidden font-sans">
        
        <!-- 3D Background Space Graph -->
        <canvas id="three-canvas"></canvas>

        <div class="relative z-10 min-h-screen flex flex-col justify-between">
            <!-- Header Panel -->
            <header class="glass px-6 py-4 flex justify-between items-center border-b border-gold-500/20">
                <div class="flex items-center space-x-3">
                    <div class="p-2 bg-gold-500/10 rounded-lg border border-gold-500/30">
                        <i data-lucide="shield-alert" class="text-gold-400 w-6 h-6"></i>
                    </div>
                    <div>
                        <h1 class="text-lg font-bold tracking-widest text-transparent bg-clip-text bg-gradient-to-r from-amber-200 to-gold-400">SHAYAN EXPLORER</h1>
                        <p class="text-[10px] text-slate-400 uppercase tracking-widest">Next-Gen Data Telemetry Portal</p>
                    </div>
                </div>

                <!-- Right Side Interacting Items -->
                <div class="flex items-center space-x-4">
                    <button onclick="toggleAdminPanel()" class="flex items-center space-x-2 text-sm font-semibold text-gold-400 px-4 py-2 border border-gold-500/30 rounded-lg hover:bg-gold-500/10 transition-all">
                        <i data-lucide="sliders" class="w-4 h-4"></i>
                        <span>Admin Console</span>
                    </button>
                    <!-- Mailbox System -->
                    <div class="relative">
                        <button onclick="toggleMailbox()" class="p-2 glass rounded-lg hover:border-gold-500/50 text-slate-300 relative">
                            <i data-lucide="mail" class="w-5 h-5"></i>
                            <span id="mail-dot" class="absolute top-1 right-1 w-2.5 h-2.5 bg-emerald-500 rounded-full animate-pulse"></span>
                        </button>
                        <!-- Floating Mailbox Dropdown -->
                        <div id="mailbox-panel" class="hidden absolute right-0 mt-3 w-80 glass rounded-xl p-4 shadow-2xl z-50 animate-fade-in">
                            <h3 class="text-sm font-bold text-gold-400 border-b border-slate-700 pb-2 mb-2 flex items-center justify-between">
                                <span>Secure Key Delivery Vault</span>
                                <i data-lucide="inbox" class="w-4 h-4 text-gold-400"></i>
                            </h3>
                            <div id="mail-contents" class="space-y-2 text-xs text-slate-300">
                                <div class="p-2 bg-slate-900/80 rounded border border-emerald-500/30">
                                    <p class="font-bold text-emerald-400 mb-1">System Allocation Complete</p>
                                    <p>Your master test token key <code class="text-gold-400 font-mono">explorer16</code> is globally active with complete route clearing profiles.</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </header>

            <!-- Main Layout Space -->
            <main class="container mx-auto px-4 py-8 flex-grow">
                
                <!-- Admin Dashboard (Initially Hidden via JS configuration) -->
                <section id="admin-view" class="hidden mb-12 glass rounded-2xl p-6 border border-gold-500/30">
                    <div class="flex justify-between items-center border-b border-slate-800 pb-4 mb-6">
                        <div class="flex items-center space-x-2">
                            <i data-lucide="command" class="text-gold-400 w-5 h-5"></i>
                            <h2 class="text-xl font-bold text-gold-400">Infrastructure Configuration</h2>
                        </div>
                        <span class="text-xs bg-gold-500/10 text-gold-400 px-3 py-1 rounded-full border border-gold-500/20">Authorized Terminal Instance</span>
                    </div>

                    <!-- Key Generation Grid -->
                    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        <div class="glass-gold p-5 rounded-xl space-y-4">
                            <h3 class="font-bold text-sm uppercase text-slate-300 tracking-wider flex items-center space-x-2">
                                <i data-lucide="key-round" class="w-4 h-4 text-gold-400"></i>
                                <span>Generate Secure Client Token</span>
                            </h3>
                            <div class="space-y-3 text-xs">
                                <div>
                                    <label class="block text-slate-400 mb-1">Client Description Name</label>
                                    <input id="new-name" type="text" class="w-full bg-slate-950 border border-slate-700 rounded p-2 text-slate-200 focus:outline-none focus:border-gold-500" placeholder="e.g., Enterprise Client Alpha">
                                </div>
                                <div>
                                    <label class="block text-slate-400 mb-1">Custom Secret Authentication Key</label>
                                    <input id="new-key" type="text" class="w-full bg-slate-950 border border-slate-700 rounded p-2 text-slate-200 focus:outline-none focus:border-gold-500" placeholder="e.g., alpha-secret-2026">
                                </div>
                                <div class="grid grid-cols-2 gap-2">
                                    <div>
                                        <label class="block text-slate-400 mb-1">Daily Cap Limit</label>
                                        <input id="new-limit" type="number" class="w-full bg-slate-950 border border-slate-700 rounded p-2 text-slate-200 focus:outline-none focus:border-gold-500" value="1000">
                                    </div>
                                    <div>
                                        <label class="block text-slate-400 mb-1">Expiration Timeline</label>
                                        <input id="new-expiry" type="date" class="w-full bg-slate-950 border border-slate-700 rounded p-2 text-slate-200 focus:outline-none focus:border-gold-500">
                                    </div>
                                </div>
                                <button onclick="executeGenerateKey()" class="w-full bg-gradient-to-r from-gold-600 to-gold-400 text-slate-950 font-bold py-2 rounded.hover:opacity-90 transition-all flex items-center justify-center space-x-2 mt-4 text-sm">
                                    <i data-lucide="plus-circle" class="w-4 h-4"></i>
                                    <span>Deploy Token Key</span>
                                </button>
                            </div>
                        </div>

                        <!-- Active System Allocations -->
                        <div class="lg:col-span-2 glass p-5 rounded-xl overflow-hidden flex flex-col">
                            <h3 class="font-bold text-sm uppercase text-slate-300 tracking-wider mb-3 flex items-center space-x-2">
                                <i data-lucide="database" class="w-4 h-4 text-gold-400"></i>
                                <span>Active Security Allocations</span>
                            </h3>
                            <div class="overflow-x-auto text-xs flex-grow">
                                <table class="w-full text-left border-collapse">
                                    <thead>
                                        <tr class="border-b border-slate-800 text-slate-400">
                                            <th class="pb-2 font-medium">Identifier Profile</th>
                                            <th class="pb-2 font-medium">Token Key Payload</th>
                                            <th class="pb-2 font-medium">Daily Utilization</th>
                                            <th class="pb-2 font-medium">System Lifespan</th>
                                        </tr>
                                    </thead>
                                    <tbody id="active-keys-table" class="divide-y divide-slate-900">
                                        <!-- Dynamically injected via script processing -->
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </section>

                <!-- Commercial Showroom Presentation Matrix -->
                <div class="text-center max-w-2xl mx-auto mb-12 space-y-3">
                    <span class="text-xs tracking-widest text-gold-400 uppercase font-semibold bg-gold-500/10 px-4 py-1.5 rounded-full border border-gold-500/30">Enterprise Data Node Distribution Architecture</span>
                    <h2 class="text-4xl font-extrabold tracking-tight text-white">Premium Monetized Telemetry Gateway</h2>
                    <p class="text-slate-400 text-sm">Deploy modular operational structures with nanosecond execution speed. Choose targeted data access streams backed by hardware-grade transaction compliance models.</p>
                </div>

                <!-- Interactive Pricing Infrastructure Matrix Grid -->
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                    <!-- Standard Tier Layer -->
                    <div class="glass rounded-2xl p-6 flex flex-col justify-between relative group hover:border-gold-500/40 transition-all duration-300">
                        <div>
                            <div class="flex justify-between items-start mb-4">
                                <div>
                                    <h3 class="text-xl font-bold tracking-wide text-white">Identity Core Bundle</h3>
                                    <p class="text-xs text-slate-400 mt-1">Foundational verification matrix</p>
                                </div>
                                <div class="p-2 bg-slate-900 rounded-xl border border-slate-800"><i data-lucide="user-check" class="text-gold-400 w-5 h-5"></i></div>
                            </div>
                            <div class="my-6 border-b border-slate-800/60 pb-6">
                                <span class="text-3xl font-extrabold text-white">₹100</span>
                                <span class="text-xs text-slate-400"> / monthly tier cyclic</span>
                            </div>
                            <ul class="space-y-3 text-xs text-slate-300 mb-8">
                                <li class="flex items-center space-x-2.5"><i data-lucide="check" class="w-4 h-4 text-gold-400"></i><span>Paytm Verification Systems Wrapper</span></li>
                                <li class="flex items-center space-x-2.5"><i data-lucide="check" class="w-4 h-4 text-gold-400"></i><span>Advanced Call Tracer Routing</span></li>
                                <li class="flex items-center space-x-2.5"><i data-lucide="check" class="w-4 h-4 text-gold-400"></i><span>Infrastructure Ledger Integrations</span></li>
                            </ul>
                        </div>
                        <button onclick="triggerPurchase('Identity Core Bundle', 100)" class="w-full py-3 rounded-xl bg-slate-900 hover:bg-gold-500/10 border border-gold-500/30 text-gold-400 font-bold tracking-wider text-xs uppercase transition-all">Initialize Smart Checkout</button>
                    </div>

                    <!-- Enterprise Core Bundle Layer (Featured) -->
                    <div class="glass-gold rounded-2xl p-6 flex flex-col justify-between relative scale-105 border-gold-500/40 shadow-2xl shadow-gold-500/5">
                        <span class="absolute -top-3 left-1/2 -translate-x-1/2 bg-gradient-to-r from-gold-600 to-gold-400 text-slate-950 font-black tracking-widest text-[9px] uppercase px-4 py-1 rounded-full shadow-lg">HIGH UTILIZATION BANDWIDTH</span>
                        <div>
                            <div class="flex justify-between items-start mb-4">
                                <div>
                                    <h3 class="text-xl font-bold tracking-wide text-white">Global Telemetry Pack</h3>
                                    <p class="text-xs text-amber-100/60 mt-1">Unified geographical data mapping</p>
                                </div>
                                <div class="p-2 bg-gold-500/20 rounded-xl border border-gold-500/40"><i data-lucide="globe" class="text-gold-400 w-5 h-5"></i></div>
                            </div>
                            <div class="my-6 border-b border-gold-500/20 pb-6">
                                <span class="text-3xl font-extrabold text-white">₹500</span>
                                <span class="text-xs text-amber-100/60"> / monthly tier cyclic</span>
                            </div>
                            <ul class="space-y-3 text-xs text-amber-100/80 mb-8">
                                <li class="flex items-center space-x-2.5"><i data-lucide="shield-check" class="w-4 h-4 text-gold-400"></i><span>Core Financial IFSC API Matrix</span></li>
                                <li class="flex items-center space-x-2.5"><i data-lucide="shield-check" class="w-4 h-4 text-gold-400"></i><span>Regional Pincode Registry Stream</span></li>
                                <li class="flex items-center space-x-2.5"><i data-lucide="shield-check" class="w-4 h-4 text-gold-400"></i><span>Network Architecture IP Resolution</span></li>
                                <li class="flex items-center space-x-2.5"><i data-lucide="shield-check" class="w-4 h-4 text-gold-400"></i><span>Unified Settlement Address Protocols</span></li>
                            </ul>
                        </div>
                        <button onclick="triggerPurchase('Global Telemetry Pack', 500)" class="w-full py-3 rounded-xl bg-gradient-to-r from-gold-500 to-amber-500 hover:opacity-90 text-slate-950 font-black tracking-wider text-xs uppercase transition-all shadow-md shadow-gold-500/20">Initialize Smart Checkout</button>
                    </div>

                    <!-- Ultimate Apex Portfolio Bundle Layer -->
                    <div class="glass rounded-2xl p-6 flex flex-col justify-between relative group hover:border-gold-500/40 transition-all duration-300">
                        <div>
                            <div class="flex justify-between items-start mb-4">
                                <div>
                                    <h3 class="text-xl font-bold tracking-wide text-white">Ultimate Apex Suite</h3>
                                    <p class="text-xs text-slate-400 mt-1">Complete analytical execution system</p>
                                </div>
                                <div class="p-2 bg-slate-900 rounded-xl border border-slate-800"><i data-lucide="cpu" class="text-gold-400 w-5 h-5"></i></div>
                            </div>
                            <div class="my-6 border-b border-slate-800/60 pb-6">
                                <span class="text-3xl font-extrabold text-white">₹1600</span>
                                <span class="text-xs text-slate-400"> / monthly tier cyclic</span>
                            </div>
                            <ul class="space-y-3 text-xs text-slate-300 mb-8">
                                <li class="flex items-center space-x-2.5"><i data-lucide="check" class="w-4 h-4 text-gold-400"></i><span>Access clearance across all 20 API streams</span></li>
                                <li class="flex items-center space-x-2.5"><i data-lucide="check" class="w-4 h-4 text-gold-400"></i><span>Real-time server log export functionality</span></li>
                                <li class="flex items-center space-x-2.5"><i data-lucide="check" class="w-4 h-4 text-gold-400"></i><span>Dedicated support channel tracking routing</span></li>
                            </ul>
                        </div>
                        <button onclick="triggerPurchase('Ultimate Apex Suite', 1600)" class="w-full py-3 rounded-xl bg-slate-900 hover:bg-gold-500/10 border border-gold-500/30 text-gold-400 font-bold tracking-wider text-xs uppercase transition-all">Initialize Smart Checkout</button>
                    </div>
                </div>
            </main>

            <!-- Sticky Admin Authentication Security Overlay Window -->
            <div id="login-modal" class="hidden fixed inset-0 flex items-center justify-center bg-slate-950/80 backdrop-blur-xl z-50 p-4">
                <div class="glass max-w-sm w-full p-6 rounded-2xl shadow-2xl border border-gold-500/40">
                    <div class="text-center space-y-2 mb-6">
                        <div class="mx-auto w-12 h-12 bg-gold-500/10 rounded-full flex items-center justify-center border border-gold-500/30 mb-2">
                            <i data-lucide="lock" class="text-gold-400 w-5 h-5"></i>
                        </div>
                        <h3 class="text-lg font-bold text-white tracking-wide">Infrastructure Gatekeeper</h3>
                        <p class="text-xs text-slate-400">Enter high-level validation tokens to access key config controls</p>
                    </div>
                    <div class="space-y-4 text-xs">
                        <div>
                            <label class="block text-slate-400 mb-1 font-semibold">Security Username ID</label>
                            <input id="login-user" type="text" class="w-full bg-slate-900 border border-slate-700 rounded-xl p-3 text-white focus:outline-none focus:border-gold-500 font-mono">
                        </div>
                        <div>
                            <label class="block text-slate-400 mb-1 font-semibold">Cryptographic Security Passphrase</label>
                            <input id="login-pass" type="password" class="w-full bg-slate-900 border border-slate-700 rounded-xl p-3 text-white focus:outline-none focus:border-gold-500 font-mono">
                        </div>
                        <div class="flex space-x-2 pt-2">
                            <button onclick="toggleAdminPanel()" class="w-1/2 py-2.5 rounded-xl border border-slate-700 hover:bg-slate-900 text-slate-300 font-bold tracking-wide transition-all">Abort Access</button>
                            <button onclick="executeAdminLogin()" class="w-1/2 py-2.5 rounded-xl bg-gradient-to-r from-gold-500 to-gold-600 text-slate-950 font-black tracking-wide hover:opacity-90 transition-all">Verify Access</button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Global Footer System -->
            <footer class="glass mt-12 py-4 px-6 text-center text-[11px] text-slate-400 tracking-wider border-t border-slate-900">
                <p>&copy; 2026 <span class="text-gold-400 font-bold">SHAYAN EXPLORER Architecture Portfolio</span>. All system pipelines fully operational.</p>
            </footer>
        </div>

        <script>
            // Initialize Lucide SVG Vector Asset Rendering Engine
            lucide.createIcons();

            let adminAuthenticated = false;

            // --- Elegant Cosmic Three.js Particle Vector Lattice Background Setup ---
            const canvasElement = document.getElementById('three-canvas');
            const scene = new THREE.Scene();
            const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
            const renderer = new THREE.WebGLRenderer({ canvas: canvasElement, alpha: true, antialias: true });
            
            renderer.setSize(window.innerWidth, window.innerHeight);
            renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

            const particleGeometry = new THREE.BufferGeometry();
            const pointCount = 120;
            const positionArray = new Float32Array(pointCount * 3);

            for(let i=0; i < pointCount * 3; i++) {
                positionArray[i] = (Math.random() - 0.5) * 10;
            }
            particleGeometry.setAttribute('position', new THREE.BufferAttribute(positionArray, 3));

            const particleMaterial = new THREE.PointsMaterial({
                size: 0.035,
                color: 0xD4AF37,
                transparent: true,
                opacity: 0.65
            });

            const particleMesh = new THREE.Points(particleGeometry, particleMaterial);
            scene.add(particleMesh);
            camera.position.z = 3;

            function animationLoop() {
                requestAnimationFrame(animationLoop);
                particleMesh.rotation.y += 0.0008;
                particleMesh.rotation.x += 0.0004;
                renderer.render(scene, camera);
            }
            animationLoop();

            window.addEventListener('resize', () => {
                camera.aspect = window.innerWidth / window.innerHeight;
                camera.updateProjectionMatrix();
                renderer.setSize(window.innerWidth, window.innerHeight);
            });

            // --- INTERACTION ARCHITECTURE LOGIC ---
            function toggleMailbox() {
                const designBox = document.getElementById('mailbox-panel');
                designBox.classList.toggle('hidden');
                document.getElementById('mail-dot').classList.add('hidden');
            }

            function toggleAdminPanel() {
                if (!adminAuthenticated) {
                    document.getElementById('login-modal').classList.toggle('hidden');
                } else {
                    const viewPanel = document.getElementById('admin-view');
                    viewPanel.classList.toggle('hidden');
                }
            }

            async function executeAdminLogin() {
                const user = document.getElementById('login-user').value;
                const pass = document.getElementById('login-pass').value;

                try {
                    const response = await fetch('/api/admin/login', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ username: user, password: pass })
                    });
                    
                    if (response.ok) {
                        adminAuthenticated = true;
                        document.getElementById('login-modal').classList.add('hidden');
                        document.getElementById('admin-view').classList.remove('hidden');
                        fetchAdminDashboardData();
                    } else {
                        alert('Cryptographic matching verification failure.');
                    }
                } catch (err) {
                    console.error(err);
                }
            }

            async function fetchAdminDashboardData() {
                try {
                    const response = await fetch('/api/admin/dashboard-data');
                    const data = await response.json();
                    
                    const tableContainer = document.getElementById('active-keys-table');
                    tableContainer.innerHTML = '';
                    
                    Object.keys(data.keys).forEach(tokenKey => {
                        const info = data.keys[tokenKey];
                        const row = `
                            <tr class="hover:bg-slate-900/50">
                                <td class="py-3 font-semibold text-slate-200">${info.key_name}</td>
                                <td class="py-3"><code class="text-gold-400 font-mono font-bold bg-slate-950 px-2 py-0.5 rounded border border-slate-800">${tokenKey}</code></td>
                                <td class="py-3 font-mono">${info.request_count} / <span class="text-slate-400">${info.daily_limit}</span></td>
                                <td class="py-3 text-slate-400">${info.expires_at.split('T')[0]}</td>
                            </tr>
                        `;
                        tableContainer.innerHTML += row;
                    });
                } catch (e) {
                    console.error("Dashboard synchronization error.", e);
                }
            }

            async function executeGenerateKey() {
                const name = document.getElementById('new-name').value;
                const key = document.getElementById('new-key').value;
                const limit = document.getElementById('new-limit').value;
                const expiryInput = document.getElementById('new-expiry').value;

                if(!name || !key || !expiryInput) return alert('Complete all parameter properties.');

                const payload = {
                    key_name: name,
                    custom_key: key,
                    expires_at: `${expiryInput}T23:59:59`,
                    daily_limit: parseInt(limit),
                    allowed_tools: ["all"]
                };

                const res = await fetch('/api/admin/generate-key', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                if(res.ok) {
                    alert('Token allocation built and active globally.');
                    fetchAdminDashboardData();
                }
            }

            function triggerPurchase(bundleName, amount) {
                alert(`[Simulating Checkout Handshake Verification]\\nConnecting Securely via Razorpay Terminal ID: rzp_live_TCc5USt5FlmfrI\\n\\nProcessing transactional validation routing for ${bundleName} (INR ${amount})...`);
                
                // Emulate Webhook Payment Capture Success Fulfill Action Loop
                setTimeout(() => {
                    const mailboxVault = document.getElementById('mail-contents');
                    const randomGeneratedString = 'exp_' + Math.random().toString(36).substring(2, 10);
                    
                    const generatedMailContent = `
                        <div class="p-2 bg-slate-900/80 rounded border border-gold-500/30 animate-pulse">
                            <p class="font-bold text-gold-400 mb-0.5">🔒 Order Confirmed: ${bundleName}</p>
                            <p>Key payload dispatched into system matrix runtime successfully:</p>
                            <p class="font-mono text-white mt-1 bg-black/60 p-1 rounded select-all text-center border border-slate-800">${randomGeneratedString}</p>
                            <p class="text-[9px] text-slate-400 mt-1">Daily Allotted Allocation Cap: 2,500 operations / 30 day cycle active.</p>
                        </div>
                    `;
                    mailboxVault.innerHTML = generatedMailContent + mailboxVault.innerHTML;
                    document.getElementById('mail-dot').classList.remove('hidden');
                    alert('Transaction Accepted! Check your secure system mailbox vault located at the top right header profile element.');
                }, 1200);
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)
