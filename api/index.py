import secrets
from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)

# Temporary in-memory database for key tracking
# Note: Serverless platforms like Vercel recycle instances. For production,
# you should link this to a persistent database like Vercel KV, Supabase, or MongoDB.
api_keys_db = {}

# Premium OpenAI-inspired UI layout
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Module Dashboard</title>
    <!-- Tailwind CSS for modern layout styling -->
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <!-- Lucide Icons for clean UI components -->
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        body {
            font-family: 'Inter', sans-serif;
            background-color: #0B0B0F;
        }
        .gradient-glow {
            background: radial-gradient(circle at top middle, rgba(124, 58, 237, 0.08) 0%, transparent 60%);
        }
    </style>
</head>
<body class="text-gray-200 min-h-screen relative overflow-x-hidden gradient-glow">

    <!-- Top Navigation Header -->
    <header class="border-b border-gray-800/60 bg-[#0B0B0F]/80 backdrop-blur-md sticky top-0 z-40">
        <div class="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
            <div class="flex items-center space-x-3">
                <div class="h-8 w-8 rounded-lg bg-gradient-to-br from-violet-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-violet-500/20">
                    <i data-lucide="cpu" class="w-4 h-4 text-white"></i>
                </div>
                <span class="font-semibold text-lg tracking-tight bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">AI Module Management</span>
            </div>
            <div class="flex items-center space-x-4">
                <span class="text-xs font-mono text-gray-500 bg-gray-900/80 px-2.5 py-1 rounded-full border border-gray-800">v1.0.0</span>
            </div>
        </div>
    </header>

    <!-- Main Content Area -->
    <main class="max-w-6xl mx-auto px-4 py-10 relative z-10">
        <div class="md:flex md:items-center md:justify-between mb-8">
            <div class="flex-1 min-w-0">
                <h1 class="text-2xl font-bold text-white sm:text-3xl tracking-tight">API Keys</h1>
                <p class="mt-2 text-sm text-gray-400">Create and manage secure authentication keys for your dedicated AI modules.</p>
            </div>
            <div class="mt-4 md:mt-0 flex">
                <button onclick="openCreateModal()" class="inline-flex items-center justify-center px-4 py-2.5 rounded-xl bg-white text-black font-medium text-sm hover:bg-gray-100 transition-all shadow-xl shadow-white/5 active:scale-98 cursor-pointer">
                    <i data-lucide="plus" class="w-4 h-4 mr-2"></i>
                    Create new secret key
                </button>
            </div>
        </div>

        <!-- API Keys Table Container -->
        <div class="bg-[#121218] border border-gray-800/80 rounded-2xl overflow-hidden shadow-2xl">
            <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse">
                    <thead>
                        <tr class="border-b border-gray-800 bg-gray-900/30 text-xs font-semibold uppercase tracking-wider text-gray-400">
                            <th class="px-6 py-4">Name</th>
                            <th class="px-6 py-4">Secret Key</th>
                            <th class="px-6 py-4">Status</th>
                            <th class="px-6 py-4 text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody id="keys-table-body" class="divide-y divide-gray-800/60 text-sm">
                        <!-- Dynamic rows injected via JavaScript -->
                    </tbody>
                </table>
            </div>
            <!-- Empty State Dynamic Element -->
            <div id="empty-state" class="hidden flex flex-col items-center justify-center py-16 px-4 text-center">
                <div class="h-12 w-12 rounded-xl bg-gray-900 flex items-center justify-center border border-gray-800 text-gray-500 mb-4">
                    <i data-lucide="key-round" class="w-5 h-5"></i>
                </div>
                <h3 class="text-sm font-medium text-gray-300">No active keys</h3>
                <p class="text-xs text-gray-500 mt-1">Get started by generating your first unique security token access credential.</p>
            </div>
        </div>
    </main>

    <!-- Modal 1: Request Key Name -->
    <div id="create-modal" class="fixed inset-0 bg-black/70 backdrop-blur-sm hidden items-center justify-center z-50 p-4">
        <div class="bg-[#121218] border border-gray-800 rounded-2xl w-full max-w-md p-6 shadow-2xl scale-95 transition-transform duration-200">
            <h3 class="text-lg font-semibold text-white mb-2">Create secret key</h3>
            <p class="text-xs text-gray-400 mb-5">Assign a recognizable label to easily trace usage metrics later.</p>
            
            <label class="block text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">Key Name</label>
            <input type="text" id="key-name-input" placeholder="e.g., Development Server Token" 
                   class="w-full bg-[#0B0B0F] border border-gray-800 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500 transition-colors">
            
            <div class="flex items-center justify-end space-x-3 mt-6">
                <button onclick="closeCreateModal()" class="px-4 py-2 rounded-xl text-sm font-medium text-gray-400 hover:text-white transition-colors cursor-pointer">Cancel</button>
                <button onclick="submitCreateKey()" class="px-4 py-2 rounded-xl bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium transition-colors shadow-lg shadow-violet-600/25 cursor-pointer">Generate Key</button>
            </div>
        </div>
    </div>

    <!-- Modal 2: One-Time Key Display Reveal -->
    <div id="reveal-modal" class="fixed inset-0 bg-black/70 backdrop-blur-sm hidden items-center justify-center z-50 p-4">
        <div class="bg-[#121218] border border-gray-800 rounded-2xl w-full max-w-lg p-6 shadow-2xl">
            <div class="flex items-center space-x-3 text-amber-400 mb-3">
                <i data-lucide="alert-triangle" class="w-5 h-5"></i>
                <h3 class="text-lg font-semibold text-white">Save your secret key</h3>
            </div>
            <p class="text-xs text-gray-400 mb-4">Please copy this secret key now. For your security, you will not be able to see it again through your account dashboard dashboard interface.</p>
            
            <div class="flex items-center bg-[#0B0B0F] border border-gray-800 rounded-xl p-3 font-mono text-sm text-violet-400 select-all overflow-x-auto relative group">
                <span id="revealed-key-span" class="pr-12 whitespace-nowrap"></span>
                <button onclick="copyKeyToClipboard()" class="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-gray-900 rounded-lg text-gray-400 hover:text-white border border-gray-800 transition-colors cursor-pointer" title="Copy key">
                    <i data-lucide="copy" class="w-4 h-4"></i>
                </button>
            </div>
            
            <div class="flex items-center justify-end mt-6">
                <button onclick="closeRevealModal()" class="px-5 py-2.5 rounded-xl bg-white text-black font-medium text-sm hover:bg-gray-100 transition-colors cursor-pointer">Done</button>
            </div>
        </div>
    </div>

    <!-- Interface Controller Logic -->
    <script>
        // Fetch and draw API rows on initiation
        document.addEventListener("DOMContentLoaded", () => {
            fetchKeys();
        });

        async function fetchKeys() {
            try {
                const res = await fetch('/api/keys');
                const keys = await res.json();
                renderTable(keys);
            } catch (err) {
                console.error("Error communicating with application backend server:", err);
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
                tr.className = "hover:bg-gray-950/40 transition-colors group";

                const isSuspended = k.status === 'Suspended';
                const statusBadge = isSuspended 
                    ? `<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">Suspended</span>`
                    : `<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Active</span>`;

                const toggleIcon = isSuspended ? 'play' : 'pause';
                const toggleTitle = isSuspended ? 'Unsuspend API Key' : 'Suspend API Key';

                tr.innerHTML = `
                    <td class="px-6 py-4.5 font-medium text-white">${escapeHtml(k.name)}</td>
                    <td class="px-6 py-4.5 font-mono text-xs text-gray-500 tracking-wider">${k.key_masked}</td>
                    <td class="px-6 py-4.5">${statusBadge}</td>
                    <td class="px-6 py-4.5 text-right space-x-1 whitespace-nowrap">
                        <button onclick="toggleKeyStatus('${k.id}')" class="p-2 text-gray-400 hover:text-white rounded-lg hover:bg-gray-800/50 transition-all inline-flex items-center cursor-pointer" title="${toggleTitle}">
                            <i data-lucide="${toggleIcon}" class="w-4 h-4"></i>
                        </button>
                        <button onclick="deleteKey('${k.id}')" class="p-2 text-gray-400 hover:text-red-400 rounded-lg hover:bg-red-950/20 transition-all inline-flex items-center cursor-pointer" title="Delete API Key">
                            <i data-lucide="trash-2" class="w-4 h-4"></i>
                        </button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
            lucide.createIcons();
        }

        // Action Handlers
        function openCreateModal() {
            document.getElementById('key-name-input').value = '';
            const modal = document.getElementById('create-modal');
            modal.style.display = 'flex';
        }

        function closeCreateModal() {
            document.getElementById('create-modal').style.display = 'none';
        }

        async function submitCreateKey() {
            const nameInput = document.getElementById('key-name-input').value.trim();
            const name = nameInput ? nameInput : "Default Access Token";

            try {
                const res = await fetch('/api/keys/create', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: name })
                });
                const data = await res.json();
                
                closeCreateModal();
                
                // Show token string via temporary one-time modal reveal layout window
                document.getElementById('revealed-key-span').innerText = data.key_full;
                document.getElementById('reveal-modal').style.display = 'flex';
                
                fetchKeys();
            } catch (err) {
                console.error("Failed to compile new token generation parameters:", err);
            }
        }

        function closeRevealModal() {
            document.getElementById('reveal-modal').style.display = 'none';
        }

        function copyKeyToClipboard() {
            const keyText = document.getElementById('revealed-key-span').innerText;
            navigator.clipboard.writeText(keyText).then(() => {
                alert("Copied to clipboard successfully!");
            });
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
                console.error("Status state update payload drop encountered errors:", err);
            }
        }

        async function deleteKey(id) {
            if (!confirm("Are you completely sure you want to permanently delete this secret key? Immediate systemic traffic refusal will follow.")) return;
            try {
                await fetch('/api/keys/delete', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ id: id })
                });
                fetchKeys();
            } catch (err) {
                console.error("Purge task operations tracking anomaly:", err);
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
    for kid, info in api_keys_db.items():
        data.append({
            "id": kid,
            "name": info["name"],
            # Mimics user custom pattern format mask protection output cleanly
            "key_masked": f"sk_...{info['key'][-4:]}",
            "status": info["status"]
        })
    return jsonify(data)

@app.route('/api/keys/create', methods=['POST'])
def create_key():
    req_data = request.get_json() or {}
    name = req_data.get('name', 'Default Access Token').strip()
    
    # Generates format standard tracking match arrays securely
    token = f"sk_{secrets.token_hex(16)}"
    kid = secrets.token_hex(8)
    
    api_keys_db[kid] = {
        "name": name,
        "key": token,
        "status": "Active"
    }
    
    return jsonify({
        "id": kid,
        "name": name,
        "key_full": token
    })

@app.route('/api/keys/toggle', methods=['POST'])
def toggle_key():
    req_data = request.get_json() or {}
    kid = req_data.get('id')
    if kid in api_keys_db:
        current = api_keys_db[kid]["status"]
        api_keys_db[kid]["status"] = "Suspended" if current == "Active" else "Active"
        return jsonify({"success": True})
    return jsonify({"error": "Key target key reference missing"}), 404

@app.route('/api/keys/delete', methods=['POST'])
def delete_key():
    req_data = request.get_json() or {}
    kid = req_data.get('id')
    if kid in api_keys_db:
        del api_keys_db[kid]
        return jsonify({"success": True})
    return jsonify({"error": "Key target key reference missing"}), 404
