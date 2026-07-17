import os
import secrets
import urllib.request
import json
from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)

# Temporary in-memory database
# Pre-seeded with your custom website key so it works instantly without manual creation!
api_keys_db = {
    "seeded_primary": {
        "name": "InceptionLabs Default Token",
        "key": "sk_e69e68f3c0701acec67b5b34b8508d75",
        "status": "Active",
        "requests": 0
    }
}

# MASTER INCEPTIONLABS KEY: Pre-configured with the production authorization token you provided
MASTER_INCEPTION_KEY = os.environ.get("INCEPTION_API_KEY", "sk_40c87e7f2e5c3ef0978568bf78d71e62")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Angel AI Module Control Panel</title>
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        body {
            font-family: 'Inter', sans-serif;
            background-color: #09090D;
        }
        .gradient-glow {
            background: radial-gradient(circle at top center, rgba(139, 92, 246, 0.05) 0%, transparent 65%);
        }
    </style>
</head>
<body class="text-gray-200 min-h-screen relative overflow-x-hidden gradient-glow">

    <!-- Top Navigation Header -->
    <header class="border-b border-gray-800/70 bg-[#09090D]/90 backdrop-blur-md sticky top-0 z-40">
        <div class="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
            <div class="flex items-center space-x-3">
                <!-- 3-Line Hamburger Menu Button -->
                <button onclick="toggleSidebar()" class="p-2 -ml-2 text-gray-400 hover:text-white rounded-lg hover:bg-gray-800/50 transition-colors cursor-pointer" title="Open Menu">
                    <i data-lucide="menu" class="w-6 h-6"></i>
                </button>
                
                <!-- Angel Logo Frame Integration -->
                <div class="h-9 w-9 rounded-xl overflow-hidden bg-gray-900 border border-gray-800 flex items-center justify-center shadow-md">
                    <img src="/static/logo.png" onerror="this.src='https://placehold.co/100x100/121218/7c3aed?text=Angel';this.onerror=null;" alt="Angel Logo" class="w-full h-full object-cover">
                </div>
                <span class="font-semibold text-base tracking-tight bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">Angel AI Dashboard</span>
            </div>
            <div class="flex items-center space-x-3">
                <span class="text-[10px] font-mono tracking-widest uppercase text-violet-400 bg-violet-500/10 px-2.5 py-1 rounded-full border border-violet-500/20">Inception Proxy Active</span>
            </div>
        </div>
    </header>

    <!-- Slide-out Navigation Drawer Dashboard Panel -->
    <div id="sidebar-drawer" class="fixed inset-y-0 left-0 w-72 bg-[#0C0C12] border-r border-gray-800/80 z-50 transform -translate-x-full transition-transform duration-300 ease-in-out shadow-2xl flex flex-col">
        <div class="h-16 px-6 border-b border-gray-800/60 flex items-center justify-between">
            <div class="flex items-center space-x-2 text-white font-medium">
                <i data-lucide="layout-dashboard" class="w-4 h-4 text-violet-400"></i>
                <span>Navigation Dashboard</span>
            </div>
            <button onclick="toggleSidebar()" class="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 transition-colors cursor-pointer">
                <i data-lucide="x" class="w-4 h-4"></i>
            </button>
        </div>
        <div class="p-4 flex-1 space-y-1">
            <a href="#" onclick="toggleSidebar()" class="flex items-center space-x-3 px-4 py-3 bg-violet-600/10 text-violet-400 font-medium rounded-xl border border-violet-500/10 transition-all">
                <i data-lucide="key-round" class="w-4 h-4"></i>
                <span class="text-sm">API Key Manager</span>
            </a>
            <div class="pt-4 px-4 text-[11px] font-semibold uppercase tracking-wider text-gray-500">System Integration URL</div>
            <div class="mx-2 mt-2 p-3 bg-gray-950/60 border border-gray-800/60 rounded-xl font-mono text-[11px] text-gray-400 break-all select-all">
                https://YOUR-VERCEL-DOMAIN.vercel.app/v1
            </div>
        </div>
        <div class="p-4 border-t border-gray-800/60 text-center text-xs text-gray-500 font-mono">
            shayan_explorer v1.2
        </div>
    </div>
    <!-- Sidebar Overlay Darkener Background -->
    <div id="sidebar-overlay" onclick="toggleSidebar()" class="fixed inset-0 bg-black/60 backdrop-blur-xs hidden z-40"></div>

    <!-- Main Table Container Layout -->
    <main class="max-w-6xl mx-auto px-4 py-10 relative z-10">
        <div class="sm:flex sm:items-center sm:justify-between mb-8">
            <div class="flex-1 min-w-0">
                <h1 class="text-2xl font-bold text-white sm:text-3xl tracking-tight">API Infrastructure</h1>
                <p class="mt-2 text-sm text-gray-400">Deploy custom keys to connect clients safely. Requests route transparently through the core engine.</p>
            </div>
            <div class="mt-4 sm:mt-0 flex">
                <button onclick="openCreateModal()" class="w-full sm:w-auto inline-flex items-center justify-center px-4 py-2.5 rounded-xl bg-white text-black font-medium text-sm hover:bg-gray-100 transition-all active:scale-98 cursor-pointer shadow-lg shadow-white/5">
                    <i data-lucide="plus" class="w-4 h-4 mr-2"></i>
                    Create new secret key
                </button>
            </div>
        </div>

        <!-- System Overview Counters Panel -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <div class="bg-[#111116] border border-gray-800/80 rounded-xl p-5 flex items-center justify-between">
                <div>
                    <p class="text-xs font-semibold text-gray-500 uppercase tracking-wider">Total Active Tokens</p>
                    <h3 id="stat-total-keys" class="text-2xl font-bold text-white mt-1">1</h3>
                </div>
                <div class="p-3 bg-violet-500/10 rounded-xl text-violet-400"><i data-lucide="shield-check" class="w-5 h-5"></i></div>
            </div>
            <div class="bg-[#111116] border border-gray-800/80 rounded-xl p-5 flex items-center justify-between">
                <div>
                    <p class="text-xs font-semibold text-gray-500 uppercase tracking-wider">Accumulated AI Module Requests</p>
                    <h3 id="stat-total-requests" class="text-2xl font-bold text-emerald-400 mt-1">0</h3>
                </div>
                <div class="p-3 bg-emerald-500/10 rounded-xl text-emerald-400"><i data-lucide="activity" class="w-5 h-5"></i></div>
            </div>
        </div>

        <!-- API Management Workspace Table -->
        <div class="bg-[#111116] border border-gray-800/80 rounded-2xl overflow-hidden shadow-2xl">
            <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse">
                    <thead>
                        <tr class="border-b border-gray-800 bg-gray-900/20 text-xs font-semibold uppercase tracking-wider text-gray-400">
                            <th class="px-6 py-4">Name</th>
                            <th class="px-6 py-4">Secret Key String</th>
                            <th class="px-6 py-4">Traffic Count</th>
                            <th class="px-6 py-4">Status</th>
                            <th class="px-6 py-4 text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody id="keys-table-body" class="divide-y divide-gray-800/50 text-sm"></tbody>
                </table>
            </div>
            <div id="empty-state" class="hidden flex flex-col items-center justify-center py-16 px-4 text-center">
                <div class="h-12 w-12 rounded-xl bg-gray-900 flex items-center justify-center border border-gray-800 text-gray-500 mb-4">
                    <i data-lucide="key-round" class="w-5 h-5"></i>
                </div>
                <h3 class="text-sm font-medium text-gray-300">No security keys found</h3>
                <p class="text-xs text-gray-500 mt-1">Generate an authorization token first to open processing channels.</p>
            </div>
        </div>
    </main>

    <!-- Create Modal Wrapper Panel -->
    <div id="create-modal" class="fixed inset-0 bg-black/80 backdrop-blur-sm hidden items-center justify-center z-50 p-4">
        <div class="bg-[#111116] border border-gray-800 rounded-2xl w-full max-w-md p-6 shadow-2xl">
            <h3 class="text-lg font-semibold text-white mb-1">Generate AI Token Access</h3>
            <p class="text-xs text-gray-400 mb-5">Input a reference label below to authorize a workspace module instance.</p>
            
            <label class="block text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-2">Key Label Identifier</label>
            <input type="text" id="key-name-input" placeholder="e.g., Main Production Client" 
                   class="w-full bg-[#09090D] border border-gray-800 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500 transition-all">
            
            <div class="flex items-center justify-end space-x-3 mt-6">
                <button onclick="closeCreateModal()" class="px-4 py-2 rounded-xl text-sm font-medium text-gray-400 hover:text-white transition-colors cursor-pointer">Cancel</button>
                <button onclick="submitCreateKey()" class="px-4 py-2 rounded-xl bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium transition-colors cursor-pointer shadow-lg shadow-violet-600/20">Create Token</button>
            </div>
        </div>
    </div>

    <!-- Hidden Display Security Key One-Time Window -->
    <div id="reveal-modal" class="fixed inset-0 bg-black/80 backdrop-blur-sm hidden items-center justify-center z-50 p-4">
        <div class="bg-[#111116] border border-gray-800 rounded-2xl w-full max-w-md p-6 shadow-2xl">
            <div class="flex items-center space-x-2.5 text-amber-400 mb-3">
                <i data-lucide="alert-triangle" class="w-5 h-5"></i>
                <h3 class="text-base font-semibold text-white">Save Secret Credential</h3>
            </div>
            <p class="text-xs text-gray-400 mb-4">Copy this security token key instantly. For secure protection architecture, you cannot review it again after dismissing this screen window.</p>
            
            <div class="flex items-center bg-[#09090D] border border-gray-800 rounded-xl p-3 font-mono text-xs text-violet-400 relative overflow-x-auto select-all">
                <span id="revealed-key-span" class="pr-12 whitespace-nowrap"></span>
                <button onclick="copyKeyToClipboard()" class="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-gray-900 rounded-lg text-gray-400 hover:text-white border border-gray-800 transition-colors cursor-pointer">
                    <i data-lucide="copy" class="w-3.5 h-3.5"></i>
                </button>
            </div>
            <div class="flex items-center justify-end mt-6">
                <button onclick="closeRevealModal()" class="px-5 py-2 rounded-xl bg-white text-black font-medium text-sm hover:bg-gray-100 transition-colors cursor-pointer">I Saved the Key</button>
            </div>
        </div>
    </div>

    <script>
        document.addEventListener("DOMContentLoaded", () => fetchKeys());

        function toggleSidebar() {
            const drawer = document.getElementById('sidebar-drawer');
            const overlay = document.getElementById('sidebar-overlay');
            drawer.classList.toggle('-translate-x-full');
            overlay.classList.toggle('hidden');
        }

        async function fetchKeys() {
            try {
                const res = await fetch('/api/keys');
                const data = await res.json();
                renderTable(data.keys);
                
                document.getElementById('stat-total-keys').innerText = data.keys.length;
                document.getElementById('stat-total-requests').innerText = data.total_global_requests;
            } catch (err) {
                console.error("Dashboard synchronization error:", err);
            }
        }

        function renderTable(keys) {
            const tbody = document.getElementById('keys-table-body');
            const emptyState = document.getElementById('empty-state');
            tbody.innerHTML = '';

            if (keys.length === 0) {
                emptyState.classList.remove('hidden');
                return;
            } else {
                emptyState.classList.add('hidden');
            }

            keys.forEach(k => {
                const tr = document.createElement('tr');
                tr.className = "hover:bg-gray-900/30 transition-colors group";

                const isSuspended = k.status === 'Suspended';
                const statusBadge = isSuspended 
                    ? `<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">Suspended</span>`
                    : `<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Active</span>`;

                const toggleIcon = isSuspended ? 'play' : 'pause';
                const toggleTitle = isSuspended ? 'Activate Key' : 'Suspend Key Operations';

                tr.innerHTML = `
                    <td class="px-6 py-4 font-medium text-white">${escapeHtml(k.name)}</td>
                    <td class="px-6 py-4 font-mono text-xs text-gray-500 tracking-wider">${k.key_masked}</td>
                    <td class="px-6 py-4 font-mono text-xs text-gray-400">${k.requests} reqs</td>
                    <td class="px-6 py-4">${statusBadge}</td>
                    <td class="px-6 py-4 text-right space-x-1 whitespace-nowrap">
                        <button onclick="toggleKeyStatus('${k.id}')" class="p-2 text-gray-400 hover:text-white rounded-lg hover:bg-gray-800/40 transition-all cursor-pointer" title="${toggleTitle}">
                            <i data-lucide="${toggleIcon}" class="w-4 h-4"></i>
                        </button>
                        <button onclick="deleteKey('${k.id}')" class="p-2 text-gray-400 hover:text-red-400 rounded-lg hover:bg-red-950/20 transition-all cursor-pointer" title="Permanently Delete Key">
                            <i data-lucide="trash-2" class="w-4 h-4"></i>
                        </button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
            lucide.createIcons();
        }

        function openCreateModal() {
            document.getElementById('key-name-input').value = '';
            document.getElementById('create-modal').style.display = 'flex';
        }

        function closeCreateModal() {
            document.getElementById('create-modal').style.display = 'none';
        }

        async function submitCreateKey() {
            const nameInput = document.getElementById('key-name-input').value.trim();
            const name = nameInput ? nameInput : "Custom Generated Key Instance";

            try {
                const res = await fetch('/api/keys/create', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: name })
                });
                const data = await res.json();
                
                closeCreateModal();
                document.getElementById('revealed-key-span').innerText = data.key_full;
                document.getElementById('reveal-modal').style.display = 'flex';
                
                fetchKeys();
            } catch (err) {
                console.error("Communication failure creating key:", err);
            }
        }

        function closeRevealModal() {
            document.getElementById('reveal-modal').style.display = 'none';
        }

        function copyKeyToClipboard() {
            const text = document.getElementById('revealed-key-span').innerText;
            navigator.clipboard.writeText(text).then(() => alert("Copied token cleanly to clipboard."));
        }

        async function toggleKeyStatus(id) {
            try {
                await fetch('/api/keys/toggle', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ id: id })
                });
                fetchKeys();
            } catch (err) {
                console.error("Status state update failed:", err);
            }
        }

        async function deleteKey(id) {
            if (!confirm("Are you entirely sure you want to permanently delete this key?")) return;
            try {
                await fetch('/api/keys/delete', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ id: id })
                });
                fetchKeys();
            } catch (err) {
                console.error("Purging instruction failure:", err);
            }
        }

        function escapeHtml(str) {
            return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/keys', methods=['GET'])
def get_keys():
    data = []
    global_total = 0
    for kid, info in api_keys_db.items():
        global_total += info.get("requests", 0)
        data.append({
            "id": kid,
            "name": info["name"],
            "key_masked": f"sk_...{info['key'][-4:]}",
            "status": info["status"],
            "requests": info.get("requests", 0)
        })
    return jsonify({"keys": data, "total_global_requests": global_total})

@app.route('/api/keys/create', methods=['POST'])
def create_key():
    req_data = request.get_json() or {}
    name = req_data.get('name', 'AI Module Link').strip()
    
    token = f"sk_{secrets.token_hex(16)}"
    kid = secrets.token_hex(8)
    
    api_keys_db[kid] = {
        "name": name,
        "key": token,
        "status": "Active",
        "requests": 0
    }
    return jsonify({"id": kid, "name": name, "key_full": token})

@app.route('/api/keys/toggle', methods=['POST'])
def toggle_key():
    req_data = request.get_json() or {}
    kid = req_data.get('id')
    if kid in api_keys_db:
        current = api_keys_db[kid]["status"]
        api_keys_db[kid]["status"] = "Suspended" if current == "Active" else "Active"
        return jsonify({"success": True})
    return jsonify({"error": "Key ID not found"}), 404

@app.route('/api/keys/delete', methods=['POST'])
def delete_key():
    req_data = request.get_json() or {}
    kid = req_data.get('id')
    if kid in api_keys_db:
        del api_keys_db[kid]
        return jsonify({"success": True})
    return jsonify({"error": "Key ID not found"}), 404


# ==========================================
# ULTRA-FAST INCEPTIONLABS AI PROXY ENGINE
# ==========================================
@app.route('/v1/chat/completions', methods=['POST'])
def ai_proxy_completions():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": {"message": "Missing Authorization header payload structure.", "type": "invalid_request_error"}}), 401
    
    user_provided_key = auth_header.replace("Bearer ", "").strip()
    
    # Fast DB Check
    found_key_id = None
    for kid, info in api_keys_db.items():
        if info["key"] == user_provided_key:
            found_key_id = kid
            break
            
    if not found_key_id:
        return jsonify({"error": {"message": "Incorrect API key provided.", "type": "invalid_api_key"}}), 401
    
    if api_keys_db[found_key_id]["status"] == "Suspended":
        return jsonify({"error": {"message": "This custom API key has been Suspended.", "type": "access_denied_error"}}), 403

    # Analytics update
    api_keys_db[found_key_id]["requests"] += 1
    
    # Ultra-Fast Raw Streaming Delivery straight to InceptionLabs
    try:
        req_payload = request.get_data()
        inception_url = "https://api.inceptionlabs.ai/v1/chat/completions"
        
        proxy_request = urllib.request.Request(
            inception_url,
            data=req_payload,
            headers={
                "Authorization": f"Bearer {MASTER_INCEPTION_KEY}",
                "Content-Type": "application/json"
            },
            method="POST"
        )
        
        with urllib.request.urlopen(proxy_request) as response:
            res_data = response.read()
            return (res_data, response.status, {"Content-Type": "application/json"})
            
    except Exception as e:
        return jsonify({"error": {"message": f"InceptionLabs upstream processing anomaly: {str(e)}", "type": "api_error"}}), 500
