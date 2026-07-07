import os
import uuid
import json
import httpx
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, Request, Form, HTTPException, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse

app = FastAPI(title="SHAYAN_EXPLORER Premium Gateway Platform")

# --- CENTRAL PLATFORM SPECIFICATIONS ---
DEVELOPER_NAME = "SHAYAN_EXPLORER"
CREDIT_TAG = "by @vernexzzz"
CHANNEL_URL = "https://t.me/shayan_explorer_channel"

UPSTREAM_API_BASE = "https://ft-osint-api.duckdns.org/api"
UPSTREAM_MASTER_KEY = "vernex-6a9dc4fdd5923c40b0aba27bf1e39e3f"

ADMIN_USER = "vernex"
ADMIN_PASS = "vernex@16vx"
SESSION_TOKEN = "vx_session_secure_token_2026"

# Integrated Tools Registry
AVAILABLE_TOOLS = [
    "adv", "paytm", "imei", "calltracer", "upi", "ifsc", "number", "pincode", "ip", 
    "challan", "ff", "bgmi", "snap", "email", "vehicle", "git", "insta", "tg", 
    "tgidinfo", "numleak", "pk", "name", "aadhar", "numtoupi", "pan", "veh2num", 
    "adharfamily", "bomber"
]

API_KEYS_DB = {
    "VERNEX-PREMIUM-MASTER": {
        "name": "Global Live Stream Feed",
        "limit": 10000,
        "used": 0,
        "expiry": "Lifetime",
        "tools": ["all"],
        "status": "Active"
    }
}
REQUEST_LOGS = []

def is_authenticated(session: Optional[str] = Cookie(None)) -> bool:
    return session == SESSION_TOKEN

# --- GATEWAY PROXY WITH DYNAMIC CONTENT INTERCEPTION ---
@app.get("/api/{tool_name}")
async def proxy_gateway(tool_name: str, request: Request):
    params = dict(request.query_params)
    client_key = params.get("key")
    
    if not client_key or client_key not in API_KEYS_DB:
        return JSONResponse(status_code=403, content={"status": "failed", "error": "Unauthorized Access. Invalid API Key."})
        
    key_profile = API_KEYS_DB[client_key]
    if key_profile["status"] == "Suspended":
        return JSONResponse(status_code=403, content={"status": "failed", "error": "This access profile has been suspended."})
        
    if key_profile["expiry"] != "Lifetime":
        try:
            expiry_dt = datetime.fromisoformat(key_profile["expiry"])
            if datetime.now() > expiry_dt:
                key_profile["status"] = "Suspended"
                return JSONResponse(status_code=403, content={"status": "failed", "error": "Key has expired."})
        except Exception:
            return JSONResponse(status_code=500, content={"status": "failed", "error": "Key validation error."})

    if key_profile["used"] >= key_profile["limit"]:
        return JSONResponse(status_code=429, content={"status": "failed", "error": "Usage threshold capacity exhausted for today."})

    if "all" not in key_profile["tools"] and tool_name not in key_profile["tools"]:
        return JSONResponse(status_code=403, content={"status": "failed", "error": f"Token lacks clearance for route: [{tool_name}]."})

    parsed_queries = ", ".join([f"{k}={v}" for k, v in params.items() if k != "key"])
    key_profile["used"] += 1
    REQUEST_LOGS.append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "key": client_key,
        "tool": tool_name,
        "query": parsed_queries if parsed_queries else "Direct Root Probe"
    })

    # Swap out user key with master key for upstream request
    params["key"] = UPSTREAM_MASTER_KEY
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{UPSTREAM_API_BASE}/{tool_name}", params=params, timeout=15.0)
            raw_content = response.text
            
            # --- STRIP OLD BRANDING & INJECT NEW CREDIT TAGS ---
            raw_content = raw_content.replace("@ftgamer2", CREDIT_TAG)
            raw_content = raw_content.replace("https://t.me/lynx_api", CHANNEL_URL)
            raw_content = raw_content.replace("@bronex_ultra", CREDIT_TAG)
            raw_content = raw_content.replace("@@bornex_ultra", CREDIT_TAG)
            
            try:
                sanitized_json = json.loads(raw_content)
                return JSONResponse(content=sanitized_json, status_code=response.status_code)
            except Exception:
                return HTMLResponse(content=raw_content, status_code=response.status_code)
                
        except Exception:
            return JSONResponse(status_code=502, content={"status": "failed", "error": "Upstream proxy interface pipeline timeout."})

# --- USER PORTAL INTERFACES ---
@app.get("/", response_class=HTMLResponse)
@app.get("/login", response_class=HTMLResponse)
async def login_portal(session: Optional[str] = Cookie(None)):
    if session == SESSION_TOKEN:
        return RedirectResponse(url="/admin", status_code=303)
        
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Identity Verification Matrix</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-[#020203] text-zinc-100 flex items-center justify-center min-h-screen p-4">
        <div class="w-full max-w-md bg-[#070709] border border-zinc-800/60 p-8 rounded-[32px] relative overflow-hidden">
            <div class="text-center mb-8">
                <h1 class="text-3xl font-black uppercase tracking-widest text-transparent bg-clip-text bg-gradient-to-r from-purple-500 to-pink-500">{DEVELOPER_NAME}</h1>
                <p class="text-[10px] font-mono text-zinc-500 tracking-widest uppercase mt-2">Centralized Access Gatehouse</p>
            </div>
            <form action="/login" method="POST" class="space-y-5">
                <div>
                    <label class="block text-[10px] font-mono uppercase tracking-widest text-zinc-400 mb-2">OPERATOR_ID</label>
                    <input type="text" name="username" required class="w-full bg-[#0c0c0e] border border-zinc-800 rounded-xl px-4 py-3 text-sm outline-none font-mono text-purple-300">
                </div>
                <div>
                    <label class="block text-[10px] font-mono uppercase tracking-widest text-zinc-400 mb-2">CYPHER_KEY</label>
                    <input type="password" name="password" required class="w-full bg-[#0c0c0e] border border-zinc-800 rounded-xl px-4 py-3 text-sm outline-none font-mono text-pink-300">
                </div>
                <button type="submit" class="w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white text-xs font-mono font-bold uppercase tracking-widest py-4 rounded-xl transition duration-300">INITIALIZE_HANDSHAKE</button>
            </form>
        </div>
    </body>
    </html>
    """

@app.post("/login")
async def process_login(username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USER and password == ADMIN_PASS:
        response = RedirectResponse(url="/admin", status_code=303)
        response.set_cookie(key="session", value=SESSION_TOKEN, httponly=True, samesite="lax")
        return response
    return RedirectResponse(url="/login?error=failed_handshake", status_code=303)

@app.get("/logout")
async def logout_action():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("session")
    return response

@app.get("/admin", response_class=HTMLResponse)
async def administration_dashboard(session: Optional[str] = Cookie(None)):
    if not is_authenticated(session):
        return RedirectResponse(url="/login", status_code=303)
        
    tool_options_html = "".join([f"""
    <label class="flex items-center space-x-3 bg-[#0c0c0e] border border-zinc-900 p-3 rounded-xl cursor-pointer hover:border-zinc-800 transition">
        <input type="checkbox" name="tools" value="{t}" class="rounded border-zinc-800 bg-zinc-900 text-purple-600 focus:ring-purple-500">
        <span class="text-xs font-mono text-zinc-400 uppercase">{t}</span>
    </label>
    """ for t in AVAILABLE_TOOLS])

    key_rows = []
    for k, v in API_KEYS_DB.items():
        status_color = "text-emerald-400 bg-emerald-500/10 border-emerald-500/20" if v["status"] == "Active" else "text-amber-400 bg-amber-500/10 border-amber-500/20"
        tool_badges = " ".join([f'<span class="bg-zinc-900 text-zinc-400 border border-zinc-800 text-[10px] px-2 py-0.5 rounded font-mono uppercase">{t}</span>' for t in v["tools"]])
        
        row = f"""
        <tr class="border-b border-zinc-900/60 bg-[#050507]/40 hover:bg-[#09090b]/80 transition">
            <td class="p-4 font-semibold text-xs max-w-[130px] truncate">{v['name']}</td>
            <td class="p-4 font-mono text-xs text-purple-400 select-all font-bold tracking-wider">{k}</td>
            <td class="p-4 text-xs font-mono text-zinc-300 countdown-container" id="expiry-row-{k}" data-expiry="{v['expiry']}" data-key="{k}">Evaluating...</td>
            <td class="p-4 text-xs font-mono"><span class="text-pink-400 font-bold">{v['used']}</span> / {v['limit']}</td>
            <td class="p-4"><span id="status-badge-{k}" class="px-2.5 py-0.5 text-[10px] font-mono font-bold rounded-full border {status_color}">{v['status']}</span></td>
            <td class="p-4 max-w-[220px]"><div class="flex flex-wrap gap-1">{tool_badges}</div></td>
            <td class="p-4 text-right">
                <div class="inline-flex gap-1.5">
                    <button onclick="triggerEditModal('{k}', '{v['name']}', {v['limit']}, '{','.join(v['tools'])}')" class="bg-purple-600/10 hover:bg-purple-600 border border-purple-500/20 px-2 py-1 text-[10px] font-mono rounded text-purple-400 transition">EDIT</button>
                    <a href="/admin/reset/{k}" class="bg-pink-600/10 hover:bg-pink-600 border border-pink-500/20 px-2 py-1 text-[10px] font-mono rounded text-pink-400 transition">RESET</a>
                    <a href="/admin/toggle/{k}" class="bg-amber-600/10 hover:bg-amber-600 border border-amber-500/20 px-2 py-1 text-[10px] font-mono rounded text-amber-400 transition">TOGGLE</a>
                    <a href="/admin/delete/{k}" onclick="return confirm('Delete token?')" class="bg-red-600/10 hover:bg-red-600 border border-red-500/20 px-2 py-1 text-[10px] font-mono rounded text-red-400 transition">DEL</a>
                </div>
            </td>
        </tr>
        """
        key_rows.append(row)

    log_rows = []
    for log in reversed(REQUEST_LOGS):
        log_rows.append(f"""
        <tr class="border-b border-zinc-900/40 text-xs font-mono hover:bg-[#050507] transition">
            <td class="p-3 text-zinc-500 commit-time">{log['time']}</td>
            <td class="p-3 text-purple-400 select-all">{log['key']}</td>
            <td class="p-3 text-pink-400 font-bold uppercase">{log['tool']}</td>
            <td class="p-3 text-zinc-300 max-w-sm truncate select-all" title="{log['query']}">{log['query']}</td>
        </tr>
        """)
    
    logs_table_body = "".join(log_rows) if log_rows else '<tr><td colspan="4" class="p-8 text-center text-zinc-600 font-mono text-xs">No execution logs found...</td></tr>'

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Control Terminal Workspace</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-[#010102] text-zinc-100 min-h-screen">
        <nav class="border-b border-zinc-900 bg-[#040406]/90 sticky top-0 z-40 backdrop-blur px-4 py-4 md:px-8 flex justify-between items-center">
            <div class="flex items-center gap-3">
                <span class="text-xl font-black tracking-widest text-transparent bg-clip-text bg-gradient-to-r from-purple-500 to-pink-500 uppercase">{DEVELOPER_NAME}</span>
                <span class="text-[9px] font-mono text-zinc-500 bg-zinc-900 border border-zinc-800 px-2 py-0.5 rounded uppercase tracking-wider">{CREDIT_TAG}</span>
            </div>
            <div class="flex items-center space-x-2">
                <button onclick="revealEndpointsModal()" class="border border-purple-500/30 hover:border-purple-500 bg-purple-950/20 text-purple-400 text-xs font-mono py-1.5 px-4 rounded-xl transition">VIEW_SYSTEM_APIS</button>
                <a href="/logout" class="border border-zinc-800 text-zinc-500 hover:text-red-400 text-xs font-mono py-1.5 px-4 rounded-xl transition">LOGOUT</a>
            </div>
        </nav>

        <div class="max-w-7xl mx-auto p-4 md:p-8 space-y-8">
            <section class="bg-[#060608] border border-zinc-900 rounded-3xl p-6">
                <h2 class="text-sm font-mono uppercase tracking-widest text-purple-400 mb-6">Provision Key Parameters</h2>
                <form action="/admin/create" method="POST" class="space-y-6">
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        <div>
                            <label class="block text-[10px] font-mono uppercase tracking-wider text-zinc-500 mb-2">Target Owner Name</label>
                            <input type="text" name="name" required class="w-full bg-[#0b0b0d] border border-zinc-800 rounded-xl px-4 py-2.5 text-xs font-mono">
                        </div>
                        <div>
                            <label class="block text-[10px] font-mono uppercase tracking-wider text-zinc-500 mb-2">Custom Access Key Text</label>
                            <input type="text" name="custom_key" class="w-full bg-[#0b0b0d] border border-zinc-800 rounded-xl px-4 py-2.5 text-xs font-mono">
                        </div>
                        <div>
                            <label class="block text-[10px] font-mono uppercase tracking-wider text-zinc-500 mb-2">Daily Quota Limit</label>
                            <input type="number" name="limit" required class="w-full bg-[#0b0b0d] border border-zinc-800 rounded-xl px-4 py-2.5 text-xs font-mono">
                        </div>
                        <div>
                            <label class="block text-[10px] font-mono uppercase tracking-wider text-zinc-500 mb-2">Lifespan Plan</label>
                            <div class="flex items-center space-x-3 bg-[#0b0b0d] border border-zinc-800 h-[38px] rounded-xl px-4">
                                <input type="checkbox" id="lifetime_toggle" name="lifetime" value="true" onchange="adjustExpiryConstraintState(this)">
                                <label for="lifetime_toggle" class="text-xs font-mono text-zinc-400 select-none cursor-pointer">LIFETIME ACCESS TIER</label>
                            </div>
                        </div>
                    </div>

                    <div id="expiry_date_container">
                        <label class="block text-[10px] font-mono uppercase tracking-wider text-zinc-500 mb-2">Expiration Clock</label>
                        <input type="datetime-local" id="expiry_input" name="expiry" class="bg-[#0b0b0d] border border-zinc-800 rounded-xl px-4 py-2.5 text-xs font-mono w-full md:w-1/4">
                    </div>

                    <div>
                        <div class="flex justify-between items-center mb-3">
                            <label class="block text-[10px] font-mono uppercase tracking-wider text-zinc-500">Route Authorization Privileges</label>
                            <button type="button" onclick="bulkToggleExecutionModules()" class="text-[10px] font-mono uppercase text-pink-400 hover:underline">Select All Internal Routes</button>
                        </div>
                        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-2" id="tools_checkbox_grid">
                            {tool_options_html}
                        </div>
                    </div>

                    <div class="flex justify-end pt-2">
                        <button type="submit" class="w-full md:w-auto bg-gradient-to-r from-purple-600 to-pink-600 text-white text-xs font-mono font-bold uppercase tracking-widest py-3 px-8 rounded-xl">PROVISION_KEY</button>
                    </div>
                </form>
            </section>

            <section class="bg-[#060608] border border-zinc-900 rounded-3xl p-6 overflow-hidden">
                <h2 class="text-sm font-mono uppercase tracking-widest text-pink-400 mb-6">Live Client Registries</h2>
                <div class="overflow-x-auto w-full">
                    <table class="w-full text-left border-collapse">
                        <thead>
                            <tr class="border-b border-zinc-900 text-[10px] font-mono text-zinc-500 uppercase tracking-wider">
                                <th class="p-4">Owner Profile</th>
                                <th class="p-4">Authorization Token</th>
                                <th class="p-4">Live Expiry Stream</th>
                                <th class="p-4">Usage Counter</th>
                                <th class="p-4">Status</th>
                                <th class="p-4">Route Scopes</th>
                                <th class="p-4 text-right">Interventions</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-zinc-900/60">
                            {"".join(key_rows)}
                        </tbody>
                    </table>
                </div>
            </section>

            <section class="bg-[#060608] border border-zinc-900 rounded-3xl p-6">
                <h2 class="text-sm font-mono uppercase tracking-widest text-amber-400 mb-6">Core Traffic Log Feed</h2>
                <div class="overflow-x-auto w-full max-h-96">
                    <table class="w-full text-left border-collapse">
                        <thead>
                            <tr class="border-b border-zinc-900 text-[10px] font-mono text-zinc-500 uppercase tracking-wider">
                                <th class="p-3">Time Stamp</th>
                                <th class="p-3">Executing Token Key</th>
                                <th class="p-3">Endpoint Route Call</th>
                                <th class="p-3">Query Data Context Parameters</th>
                            </tr>
                        </thead>
                        <tbody>
                            {logs_table_body}
                        </tbody>
                    </table>
                </div>
            </section>
        </div>

        <!-- ENDPOINTS MODAL WITH SECURE BASE PLACEHOLDERS -->
        <div id="endpoints_modal" class="hidden fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div class="bg-[#060608] border border-zinc-800 w-full max-w-3xl rounded-3xl p-6 relative max-h-[85vh] flex flex-col">
                <div class="flex justify-between items-center mb-6">
                    <h3 class="text-sm font-mono uppercase tracking-widest text-purple-400">Available System API Paths</h3>
                    <button onclick="dismissEndpointsModal()" class="text-zinc-500 hover:text-white font-mono text-xs border border-zinc-800 px-3 py-1 rounded-xl">&times; CLOSE</button>
                </div>
                <div class="overflow-y-auto space-y-2 flex-1 p-1 bg-[#010102] rounded-2xl" id="endpoints_render_view"></div>
            </div>
        </div>

        <!-- EDIT MODULE FORM MODAL -->
        <div id="edit_modal" class="hidden fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div class="bg-[#060608] border border-zinc-800 w-full max-w-xl rounded-3xl p-6 relative">
                <h3 class="text-sm font-mono uppercase tracking-widest text-purple-400 mb-6">Modify Gateway Authorization Profiles</h3>
                <form action="/admin/edit" method="POST" class="space-y-4">
                    <input type="hidden" name="key" id="edit_key_id">
                    <div>
                        <label class="block text-[10px] font-mono uppercase tracking-wider text-zinc-500 mb-1">Update Owner Identity Name</label>
                        <input type="text" name="name" id="edit_name" required class="w-full bg-[#0b0b0d] border border-zinc-800 rounded-xl px-4 py-2 text-xs text-zinc-200 outline-none font-mono">
                    </div>
                    <div>
                        <label class="block text-[10px] font-mono uppercase tracking-wider text-zinc-500 mb-1">Recalibrate Limit</label>
                        <input type="number" name="limit" id="edit_limit" required class="w-full bg-[#0b0b0d] border border-zinc-800 rounded-xl px-4 py-2 text-xs text-zinc-200 outline-none font-mono">
                    </div>
                    <div>
                        <label class="block text-[10px] font-mono uppercase tracking-wider text-zinc-500 mb-2">Adjust Tool Clearances</label>
                        <div class="grid grid-cols-2 sm:grid-cols-3 gap-2 max-h-40 overflow-y-auto p-2 bg-[#0b0b0d] border border-zinc-800 rounded-xl">
                            {"".join([f'<div><label class="flex items-center space-x-2 text-xs font-mono text-zinc-500 cursor-pointer"><input type="checkbox" name="tools" value="{t}" id="modal_tool_{t}" class="rounded border-zinc-800 bg-zinc-900 text-purple-600"> <span class="uppercase">{t}</span></label></div>' for t in AVAILABLE_TOOLS])}
                        </div>
                    </div>
                    <div class="flex justify-end space-x-2 pt-4">
                        <button type="button" onclick="closeEditModal()" class="border border-zinc-800 px-4 py-2 rounded-xl text-xs font-mono text-zinc-500">Cancel</button>
                        <button type="submit" class="bg-gradient-to-r from-purple-600 to-pink-600 text-white px-4 py-2 rounded-xl text-xs font-mono font-bold uppercase">Save Changes</button>
                    </div>
                </form>
            </div>
        </div>

        <script>
            function adjustExpiryConstraintState(checkbox) {{
                const container = document.getElementById('expiry_date_container');
                const input = document.getElementById('expiry_input');
                if (checkbox.checked) {{
                    container.style.opacity = '0.2';
                    input.disabled = true;
                    input.required = false;
                    input.value = '';
                }} else {{
                    container.style.opacity = '1';
                    input.disabled = false;
                    input.required = true;
                }}
            }}
            
            function bulkToggleExecutionModules() {{
                const checkboxes = document.querySelectorAll('#tools_checkbox_grid input[type="checkbox"]');
                const currentStatus = Array.from(checkboxes).every(cb => cb.checked);
                checkboxes.forEach(cb => cb.checked = !currentStatus);
            }}

            function triggerEditModal(key, name, limit, tools) {{
                document.getElementById('edit_key_id').value = key;
                document.getElementById('edit_name').value = name;
                document.getElementById('edit_limit').value = limit;
                
                const toolArray = tools.split(',');
                document.querySelectorAll('#edit_modal input[type="checkbox"]').forEach(cb => cb.checked = false);
                toolArray.forEach(t => {{
                    const checkbox = document.getElementById('modal_tool_' + t);
                    if(checkbox) checkbox.checked = true;
                }});
                
                document.getElementById('edit_modal').classList.remove('hidden');
            }}

            function closeEditModal() {{
                document.getElementById('edit_modal').classList.add('hidden');
            }}

            function revealEndpointsModal() {{
                const deploymentHostOrigin = window.location.origin;
                const renderTargetNode = document.getElementById('endpoints_render_view');
                renderTargetNode.innerHTML = '';
                
                const toolsListArray = {AVAILABLE_TOOLS};
                
                // Meticulous mapping profiles to safeguard identifiers via strict Redaction policy
                const routeBlueprints = {{
                    "pk": "num=0000000000",
                    "name": "name=abhiraaj",
                    "aadhar": "num=[Aadhaar Redacted]",
                    "upi": "upi=example@ybl",
                    "numtoupi": "num=8945996482",
                    "pan": "pan=AXDPR2606K",
                    "vehicle": "vehicle=KA01AB1234",
                    "veh2num": "vehicle=KL41V3504",
                    "adharfamily": "num=[Aadhaar Redacted]",
                    "bomber": "number=9876543210&counter=100"
                }};

                toolsListArray.forEach(t => {{
                    const structuralParameters = routeBlueprints[t] || "query=example_data";
                    const fullyFormedPath = `${{deploymentHostOrigin}}/api/${{t}}?key=YOUR_KEY&${{structuralParameters}}`;
                    
                    renderTargetNode.innerHTML += `
                        <div class="p-3 border border-zinc-900 bg-[#060608] rounded-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-3 font-mono text-xs">
                            <span class="text-purple-400 font-extrabold uppercase tracking-wide px-2 py-0.5 bg-purple-500/10 rounded border border-purple-500/20 min-w-[110px] text-center">${{t}}</span>
                            <div class="flex items-center gap-2 w-full md:w-auto flex-1">
                                <input type="text" readonly value="${{fullyFormedPath}}" class="bg-[#010102] border border-zinc-800 text-zinc-400 px-3 py-1.5 rounded-lg text-[11px] w-full outline-none font-mono">
                                <button onclick="navigator.clipboard.writeText('${{fullyFormedPath}}'); alert('Copied.')" class="bg-zinc-950 border border-zinc-800 px-3 py-1.5 rounded-lg text-zinc-300 font-sans text-xs shrink-0">Copy</button>
                            </div>
                        </div>
                    `;
                }});
                document.getElementById('endpoints_modal').classList.remove('hidden');
            }}

            function dismissEndpointsModal() {{
                document.getElementById('endpoints_modal').classList.add('hidden');
            }}

            function runChronosTrackingEngine() {{
                const activeRegistryRows = document.querySelectorAll('.countdown-container');
                
                setInterval(() => {{
                    activeRegistryRows.forEach(rowNode => {{
                        const rawExpiryString = rowNode.getAttribute('data-expiry');
                        const keyUniqueToken = rowNode.getAttribute('data-key');
                        
                        if (rawExpiryString === 'Lifetime') {{
                            rowNode.innerHTML = '<span class="text-fuchsia-400 font-bold uppercase tracking-widest text-[10px]">LIFETIME PRIVILEGE</span>';
                            return;
                        }}
                        
                        const targetMillisecondEpoch = new Date(rawExpiryString).getTime();
                        const currentMillisecondEpoch = new Date().getTime();
                        const trackingTimeDelta = targetMillisecondEpoch - currentMillisecondEpoch;
                        const targetStatusBadge = document.getElementById('status-badge-' + keyUniqueToken);
                        
                        if (trackingTimeDelta <= 0) {{
                            rowNode.innerHTML = '<span class="text-red-500 font-black tracking-widest text-[10px] uppercase">EXPIRED</span>';
                            if (targetStatusBadge && !targetStatusBadge.classList.contains('border-red-500/20')) {{
                                targetStatusBadge.innerText = 'Suspended';
                                targetStatusBadge.className = 'px-2.5 py-0.5 text-[10px] font-mono font-bold rounded-full border text-red-400 bg-red-500/10 border-red-500/20';
                            }}
                            return;
                        }}
                        
                        const parseHours = Math.floor(trackingTimeDelta / (1000 * 60 * 60));
                        const parseMinutes = Math.floor((trackingTimeDelta % (1000 * 60 * 60)) / (1000 * 60));
                        const parseSeconds = Math.floor((trackingTimeDelta % (1000 * 60)) / 1000);
                        
                        rowNode.innerHTML = `<span class="text-zinc-400 font-mono">${{parseHours}}H ${{parseMinutes}}M ${{parseSeconds}}S</span>`;
                    }});
                }, 1000);
            }}
            
            window.addEventListener('DOMContentLoaded', runChronosTrackingEngine);
        </script>
    </body>
    </html>
    """

@app.post("/admin/create")
async def process_key_generation(
    name: str = Form(...),
    custom_key: Optional[str] = Form(None),
    limit: int = Form(...),
    lifetime: Optional[str] = Form(None),
    expiry: Optional[str] = Form(None),
    tools: List[str] = Form(default=[]),
    session: Optional[str] = Cookie(None)
):
    if not is_authenticated(session):
        raise HTTPException(status_code=401)
        
    generated_token = custom_key.strip() if custom_key and custom_key.strip() else f"VX-{uuid.uuid4().hex.upper()[:12]}"
    expiration_strategy = "Lifetime" if lifetime == "true" else (expiry if expiry else "Lifetime")
    scope_clearances = tools if tools else ["all"]

    API_KEYS_DB[generated_token] = {
        "name": name,
        "limit": limit,
        "used": 0,
        "expiry": expiration_strategy,
        "tools": scope_clearances,
        "status": "Active"
    }
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/admin/edit")
async def process_key_modification(
    key: str = Form(...),
    name: str = Form(...),
    limit: int = Form(...),
    tools: List[str] = Form(default=[]),
    session: Optional[str] = Cookie(None)
):
    if not is_authenticated(session):
        raise HTTPException(status_code=401)
        
    if key in API_KEYS_DB:
        API_KEYS_DB[key]["name"] = name
        API_KEYS_DB[key]["limit"] = limit
        API_KEYS_DB[key]["tools"] = tools if tools else ["all"]
        
    return RedirectResponse(url="/admin", status_code=303)

@app.get("/admin/reset/{key}")
async def clear_usage_counters(key: str, session: Optional[str] = Cookie(None)):
    if not is_authenticated(session):
        raise HTTPException(status_code=401)
    if key in API_KEYS_DB:
        API_KEYS_DB[key]["used"] = 0
    return RedirectResponse(url="/admin", status_code=303)

@app.get("/admin/toggle/{key}")
async def process_suspension_toggle(key: str, session: Optional[str] = Cookie(None)):
    if not is_authenticated(session):
        raise HTTPException(status_code=401)
    if key in API_KEYS_DB:
        current_state = API_KEYS_DB[key]["status"]
        API_KEYS_DB[key]["status"] = "Suspended" if current_state == "Active" else "Active"
    return RedirectResponse(url="/admin", status_code=303)

@app.get("/admin/delete/{key}")
async def execute_key_destruction(key: str, session: Optional[str] = Cookie(None)):
    if not is_authenticated(session):
        raise HTTPException(status_code=401)
    if key in API_KEYS_DB:
        del API_KEYS_DB[key]
    return RedirectResponse(url="/admin", status_code=303)





