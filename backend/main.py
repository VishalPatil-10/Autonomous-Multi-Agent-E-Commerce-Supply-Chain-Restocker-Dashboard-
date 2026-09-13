"""
Autonomous Restocker Dashboard — FastAPI Backend
Multi-agent orchestration chain for inventory monitoring, supplier strategy, and AI-powered procurement.
"""

import os
import json
import asyncio
import traceback
from datetime import datetime, timezone
from typing import Optional
import shlex

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

load_dotenv()

# ─── Gemini API Setup ────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
gemini_model = None

try:
    import google.generativeai as genai
    if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel("gemini-2.0-flash")
except Exception:
    gemini_model = None

# ─── FastAPI App ──────────────────────────────────────────────────
app = FastAPI(title="Autonomous Restocker Dashboard API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Simulated Data Stores ────────────────────────────────────────

inventory_data = [
    {"id": 1, "product": "Leather Boots",       "sku": "LB-001", "stock": 24, "category": "Footwear",     "price": 189.99},
    {"id": 2, "product": "Canvas Backpack",      "sku": "CB-002", "stock": 7,  "category": "Accessories",  "price": 79.99},
    {"id": 3, "product": "Merino Wool Scarf",    "sku": "MW-003", "stock": 42, "category": "Apparel",      "price": 54.99},
    {"id": 4, "product": "Titanium Watch",       "sku": "TW-004", "stock": 3,  "category": "Accessories",  "price": 449.99},
    {"id": 5, "product": "Silk Pocket Square",   "sku": "SP-005", "stock": 15, "category": "Apparel",      "price": 34.99},
    {"id": 6, "product": "Heritage Sunglasses",  "sku": "HS-006", "stock": 9,  "category": "Accessories",  "price": 229.99},
    {"id": 7, "product": "Cashmere Sweater",     "sku": "CS-007", "stock": 5,  "category": "Apparel",      "price": 299.99},
    {"id": 8, "product": "Suede Loafers",        "sku": "SL-008", "stock": 18, "category": "Footwear",     "price": 159.99},
    {"id": 9, "product": "Travel Duffel Bag",    "sku": "TD-009", "stock": 11, "category": "Accessories",  "price": 129.99},
    {"id": 10,"product": "Linen Dress Shirt",    "sku": "LD-010", "stock": 6,  "category": "Apparel",      "price": 89.99},
]

DEFAULT_SUPPLIERS = [
    {"id": 1, "name": "Alpine Leather Co.",     "region": "Italy",      "price_tier": "Premium",   "price_per_unit": 62.50,  "lead_time_days": 14, "email": "orders@alpineleather.it",    "speciality": "Leather goods, Footwear"},
    {"id": 2, "name": "Pacific Textiles Ltd.",  "region": "Vietnam",    "price_tier": "Economy",   "price_per_unit": 18.75,  "lead_time_days": 7,  "email": "supply@pacifictextiles.vn",  "speciality": "Canvas, Backpacks, Bags"},
    {"id": 3, "name": "Nordic Wool Partners",   "region": "Norway",     "price_tier": "Standard",  "price_per_unit": 28.00,  "lead_time_days": 10, "email": "bulk@nordicwool.no",          "speciality": "Wool, Cashmere, Knits"},
    {"id": 4, "name": "Shenzhen Precision MFG", "region": "China",      "price_tier": "Economy",   "price_per_unit": 85.00,  "lead_time_days": 5,  "email": "exports@szprecision.cn",     "speciality": "Watches, Eyewear, Metal"},
    {"id": 5, "name": "Lyon Silk Maison",       "region": "France",     "price_tier": "Luxury",    "price_per_unit": 12.00,  "lead_time_days": 12, "email": "atelier@lyonsilk.fr",        "speciality": "Silk, Pocket squares"},
    {"id": 6, "name": "Mumbai Linen House",     "region": "India",      "price_tier": "Economy",   "price_per_unit": 22.00,  "lead_time_days": 8,  "email": "orders@mumbailinen.in",      "speciality": "Linen, Cotton, Shirts"},
    {"id": 7, "name": "Florence Suede Atelier", "region": "Italy",      "price_tier": "Premium",   "price_per_unit": 55.00,  "lead_time_days": 16, "email": "",                            "speciality": "Suede, Leather, Footwear"},
]

supplier_data = DEFAULT_SUPPLIERS.copy()

MCP_SERVER_COMMAND = os.getenv("MCP_SERVER_COMMAND", "npx")
MCP_SERVER_ARGS = os.getenv("MCP_SERVER_ARGS", "-y @modelcontextprotocol/server-google-sheets")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "your_google_sheet_id_here")

async def fetch_suppliers_from_mcp(log_func=None):
    global supplier_data
    if GOOGLE_SHEET_ID == "your_google_sheet_id_here" or not GOOGLE_SHEET_ID:
        if log_func:
            await log_func("Agent 2 — Strategist", "⚠️ No valid Google Sheet ID configured. Using fallback supplier data.", "warning")
        return supplier_data

    server_params = StdioServerParameters(
        command=MCP_SERVER_COMMAND,
        args=shlex.split(MCP_SERVER_ARGS),
        env={**os.environ}
    )
    
    try:
        if log_func:
            await log_func("Agent 2 — Strategist", f"🌐 Initiating MCP tool call to Sheets Server (Command: {MCP_SERVER_COMMAND})...")
            await asyncio.sleep(0.3)
            await log_func("Agent 2 — Strategist", f"📊 Executing 'google_sheets_read_range' for Sheet ID: {GOOGLE_SHEET_ID[:10]}...")
            await asyncio.sleep(0.3)

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                result = await session.call_tool(
                    "google_sheets_read_range", 
                    arguments={"spreadsheet_id": GOOGLE_SHEET_ID, "range": "Suppliers!A2:H"}
                )
                
                rows = json.loads(result.content[0].text)
                
                new_suppliers = []
                for row in rows:
                    if len(row) >= 8:
                        new_suppliers.append({
                            "id": int(row[0]),
                            "name": row[1],
                            "region": row[2],
                            "price_tier": row[3],
                            "price_per_unit": float(row[4]),
                            "lead_time_days": int(row[5]),
                            "email": row[6],
                            "speciality": row[7]
                        })
                if new_suppliers:
                    supplier_data = new_suppliers
                    if log_func:
                        await log_func("Agent 2 — Strategist", f"✅ Successfully synced {len(new_suppliers)} suppliers via MCP protocol.")
                        
    except Exception as e:
        if log_func:
            await log_func("Agent 2 — Strategist", f"❌ MCP tool call failed: {str(e)[:100]}. Falling back to local cache.", "error")
            
    return supplier_data

email_outbox = []

# ─── Chaos Mode State ────────────────────────────────────────────
chaos_mode_active = False

# ─── WebSocket Connection Manager ────────────────────────────────
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()


# ─── Helper: Broadcast Telemetry Log ──────────────────────────────
async def emit_log(agent: str, message: str, level: str = "info"):
    """Send a telemetry log entry to all connected WebSocket clients."""
    timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S.%f")[:-3]
    log_entry = {
        "type": "telemetry",
        "agent": agent,
        "message": message,
        "level": level,
        "timestamp": timestamp,
    }
    await manager.broadcast(log_entry)
    await asyncio.sleep(0.15)  # pacing for visual streaming effect


# ─── Models ───────────────────────────────────────────────────────
class StockUpdateRequest(BaseModel):
    product_id: int
    new_stock: int

class ChaosToggleRequest(BaseModel):
    enabled: bool


# ─── REST Endpoints ──────────────────────────────────────────────

@app.get("/api/inventory")
async def get_inventory():
    return inventory_data

@app.get("/api/suppliers")
async def get_suppliers():
    return await fetch_suppliers_from_mcp()

@app.get("/api/emails")
async def get_emails():
    return email_outbox

@app.post("/api/inventory/update")
async def update_stock(req: StockUpdateRequest):
    global chaos_mode_active
    for item in inventory_data:
        if item["id"] == req.product_id:
            old_stock = item["stock"]
            item["stock"] = max(0, req.new_stock)

            # Broadcast inventory update
            await manager.broadcast({
                "type": "inventory_update",
                "data": inventory_data
            })

            # If stock dropped below threshold, trigger agent chain
            if item["stock"] < 10 and item["stock"] < old_stock:
                asyncio.create_task(
                    run_agent_chain(item, chaos_mode_active)
                )

            return {"status": "ok", "product": item}
    return {"status": "error", "message": "Product not found"}

@app.post("/api/chaos")
async def toggle_chaos(req: ChaosToggleRequest):
    global chaos_mode_active
    chaos_mode_active = req.enabled
    await emit_log("SYSTEM", f"⚡ Chaos Mode {'ACTIVATED' if req.enabled else 'DEACTIVATED'}", "warning" if req.enabled else "info")
    return {"status": "ok", "chaos_mode": chaos_mode_active}

@app.post("/api/suppliers/sever/{supplier_id}")
async def sever_supplier(supplier_id: int):
    """Sever supplier contact info — removes email for error testing."""
    for supplier in supplier_data:
        if supplier["id"] == supplier_id:
            old_email = supplier["email"]
            supplier["email"] = ""
            await emit_log("SYSTEM", f"🔴 SEVERED contact for {supplier['name']} (was: {old_email})", "warning")
            await manager.broadcast({"type": "supplier_update", "data": supplier_data})
            return {"status": "ok", "supplier": supplier}
    return {"status": "error", "message": "Supplier not found"}

@app.post("/api/suppliers/restore/{supplier_id}")
async def restore_supplier(supplier_id: int):
    """Restore supplier contact information."""
    original_emails = {
        1: "orders@alpineleather.it",
        2: "supply@pacifictextiles.vn",
        3: "bulk@nordicwool.no",
        4: "exports@szprecision.cn",
        5: "atelier@lyonsilk.fr",
        6: "orders@mumbailinen.in",
        7: "dispatch@florencesuede.it",
    }
    for supplier in supplier_data:
        if supplier["id"] == supplier_id:
            supplier["email"] = original_emails.get(supplier_id, "restored@example.com")
            await emit_log("SYSTEM", f"🟢 RESTORED contact for {supplier['name']}: {supplier['email']}", "info")
            await manager.broadcast({"type": "supplier_update", "data": supplier_data})
            return {"status": "ok", "supplier": supplier}
    return {"status": "error", "message": "Supplier not found"}


# ─── WebSocket Endpoint ──────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send initial state
        await websocket.send_json({"type": "inventory_update", "data": inventory_data})
        await websocket.send_json({"type": "supplier_update", "data": supplier_data})
        await websocket.send_json({"type": "email_update", "data": email_outbox})
        while True:
            data = await websocket.receive_text()
            # Handle incoming WebSocket messages if needed
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ─── Multi-Agent Orchestration Chain ─────────────────────────────

# SKU to category mapping for supplier matching
SKU_CATEGORY_MAP = {
    "LB-001": ["Leather", "Footwear"],
    "CB-002": ["Canvas", "Backpacks", "Bags"],
    "MW-003": ["Wool", "Knits"],
    "TW-004": ["Watches", "Metal"],
    "SP-005": ["Silk", "Pocket squares"],
    "HS-006": ["Eyewear", "Metal"],
    "CS-007": ["Cashmere", "Knits"],
    "SL-008": ["Suede", "Footwear", "Leather"],
    "TD-009": ["Bags", "Canvas"],
    "LD-010": ["Linen", "Shirts", "Cotton"],
}


async def run_agent_chain(product: dict, chaos_mode: bool):
    """Execute the three-agent orchestration chain."""
    sku = product["sku"]
    product_name = product["product"]
    current_stock = product["stock"]

    try:
        # ══════════════════════════════════════════════════════════
        # AGENT 1 — AUDITOR
        # ══════════════════════════════════════════════════════════
        await emit_log("Agent 1 — Auditor", f"🔍 Initiating stock audit scan for all inventory items...")
        await asyncio.sleep(0.3)

        await emit_log("Agent 1 — Auditor", f"📊 Scanning {product_name} (SKU: {sku})... current stock at {current_stock} units")
        await asyncio.sleep(0.2)

        await emit_log("Agent 1 — Auditor", f"⚠️ ALERT: {product_name} stock ({current_stock} units) is BELOW reorder threshold of 10 units!", "warning")
        await asyncio.sleep(0.2)

        await emit_log("Agent 1 — Auditor", f"📋 Generating restock requisition ticket #RST-{datetime.now().strftime('%Y%m%d%H%M%S')}")
        await asyncio.sleep(0.2)

        await emit_log("Agent 1 — Auditor", f"➡️ Forwarding SKU {sku} to Agent 2 (Strategist) for vendor correlation...")
        await asyncio.sleep(0.3)

        # ══════════════════════════════════════════════════════════
        # AGENT 2 — STRATEGIST
        # ══════════════════════════════════════════════════════════
        await emit_log("Agent 2 — Strategist", f"📥 Received restock request for {product_name} (SKU: {sku})")
        await asyncio.sleep(0.3)

        keywords = SKU_CATEGORY_MAP.get(sku, [product_name.split()[0]])
        await emit_log("Agent 2 — Strategist", f"🔎 Mapping SKU {sku} to product categories: {keywords}")
        await asyncio.sleep(0.2)

        live_suppliers = await fetch_suppliers_from_mcp(emit_log)

        await emit_log("Agent 2 — Strategist", f"📑 Loading supplier grid matrix ({len(live_suppliers)} vendors)...")
        await asyncio.sleep(0.3)

        # Score suppliers
        candidates = []
        for supplier in live_suppliers:
            speciality_lower = supplier["speciality"].lower()
            match_score = sum(1 for kw in keywords if kw.lower() in speciality_lower)
            if match_score > 0:
                # Weight: 40% category match, 35% lead time (lower=better), 25% cost (lower=better)
                lead_time_score = max(0, 20 - supplier["lead_time_days"]) / 20
                cost_score = max(0, 100 - supplier["price_per_unit"]) / 100
                total_score = (match_score * 0.4) + (lead_time_score * 0.35) + (cost_score * 0.25)
                candidates.append((supplier, total_score, match_score))
                await emit_log("Agent 2 — Strategist",
                    f"  ├─ {supplier['name']} | Match: {match_score} | Lead: {supplier['lead_time_days']}d | "
                    f"Cost: ${supplier['price_per_unit']}/unit | Score: {total_score:.3f}")
                await asyncio.sleep(0.15)

        if not candidates:
            await emit_log("Agent 2 — Strategist", f"❌ No matching suppliers found for SKU {sku}. Manual intervention required.", "error")
            return

        candidates.sort(key=lambda x: x[1], reverse=True)
        best_supplier = candidates[0][0]
        best_score = candidates[0][1]

        await emit_log("Agent 2 — Strategist", f"🏆 Optimal vendor selected: {best_supplier['name']} (Score: {best_score:.3f})")
        await asyncio.sleep(0.2)

        reorder_qty = max(20, (10 - current_stock) + 15)  # Reorder to comfortable level
        total_cost = reorder_qty * best_supplier["price_per_unit"]

        await emit_log("Agent 2 — Strategist",
            f"📦 Recommended reorder: {reorder_qty} units × ${best_supplier['price_per_unit']}/unit = ${total_cost:.2f} total")
        await asyncio.sleep(0.2)

        await emit_log("Agent 2 — Strategist",
            f"🚚 Estimated delivery: {best_supplier['lead_time_days']} business days from {best_supplier['region']}")
        await asyncio.sleep(0.2)

        # ── Chaos Mode Check ──
        if chaos_mode:
            await emit_log("Agent 2 — Strategist", f"⚡ Chaos Mode active — injecting supplier data fault...", "warning")
            await asyncio.sleep(0.3)
            # Force pick supplier with missing email
            severed = [s for s in live_suppliers if s["email"] == ""]
            if severed:
                best_supplier = severed[0]
                await emit_log("Agent 2 — Strategist", f"⚡ Overriding to {best_supplier['name']} (email SEVERED)", "warning")
            else:
                # Artificially clear email
                best_supplier = {**best_supplier, "email": ""}
                await emit_log("Agent 2 — Strategist", f"⚡ Artificially clearing vendor email for chaos test", "warning")

        await emit_log("Agent 2 — Strategist",
            f"➡️ Forwarding procurement brief to Agent 3 (Comms) — Vendor: {best_supplier['name']}")
        await asyncio.sleep(0.3)

        # ══════════════════════════════════════════════════════════
        # AGENT 3 — COMMS (Gemini-powered email generation)
        # ══════════════════════════════════════════════════════════
        await emit_log("Agent 3 — Comms", f"📥 Received procurement brief for {product_name}")
        await asyncio.sleep(0.2)

        await emit_log("Agent 3 — Comms", f"📧 Preparing purchase order email to {best_supplier['name']}...")
        await asyncio.sleep(0.2)

        # Check for missing email (Chaos Mode trigger)
        if not best_supplier["email"]:
            await emit_log("Agent 3 — Comms",
                f"🚨 CRITICAL: Vendor {best_supplier['name']} has NO contact email on file!", "error")
            await asyncio.sleep(0.2)
            await emit_log("Agent 3 — Comms",
                f"🛑 HALTING agent chain — cannot dispatch PO without valid recipient address", "error")
            await asyncio.sleep(0.2)
            await emit_log("Agent 3 — Comms",
                f"💾 Preserving state: SKU={sku}, Vendor={best_supplier['name']}, Qty={reorder_qty}", "warning")
            await asyncio.sleep(0.2)
            await emit_log("Agent 3 — Comms",
                f"⚠️ ACTION REQUIRED: Admin must update supplier contact info and re-trigger restock", "warning")

            # Log the failed email to outbox
            failed_email = {
                "id": len(email_outbox) + 1,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "to": "⚠️ MISSING — NO EMAIL ON FILE",
                "supplier": best_supplier["name"],
                "subject": f"[FAILED] PO for {product_name} (SKU: {sku})",
                "body": f"DISPATCH HALTED: No valid email for {best_supplier['name']}. "
                        f"Reorder of {reorder_qty}x {product_name} requires manual intervention.",
                "status": "FAILED",
                "sku": sku,
                "quantity": reorder_qty,
            }
            email_outbox.insert(0, failed_email)
            await manager.broadcast({"type": "email_update", "data": email_outbox})
            return

        await emit_log("Agent 3 — Comms", f"✅ Vendor email verified: {best_supplier['email']}")
        await asyncio.sleep(0.2)

        # Generate email with Gemini or fallback template
        po_number = f"PO-{datetime.now().strftime('%Y%m%d')}-{sku}"
        email_body = None

        if gemini_model:
            await emit_log("Agent 3 — Comms", f"🤖 Connecting to Gemini AI for contextual email generation...")
            await asyncio.sleep(0.3)
            try:
                prompt = f"""Write a formal enterprise procurement email for a purchase order with these details:
- From: Autonomous Restocker System, Premium Goods Inc.
- To: {best_supplier['name']} ({best_supplier['region']})
- Recipient Email: {best_supplier['email']}
- Product: {product_name} (SKU: {sku})
- Quantity: {reorder_qty} units
- Unit Price: ${best_supplier['price_per_unit']}
- Total Value: ${total_cost:.2f}
- Expected Lead Time: {best_supplier['lead_time_days']} business days
- PO Number: {po_number}
- Urgency: HIGH (stock critically low at {current_stock} units)

Write a professional, concise email body only (no subject line). Include PO number reference, delivery address placeholder, payment terms (Net 30), and quality requirements."""

                response = await asyncio.to_thread(
                    gemini_model.generate_content, prompt
                )
                email_body = response.text
                await emit_log("Agent 3 — Comms", f"🤖 Gemini AI generated contextual procurement email ✓")
            except Exception as e:
                await emit_log("Agent 3 — Comms", f"⚠️ Gemini API fallback: {str(e)[:80]}. Using template.", "warning")

        if not email_body:
            await emit_log("Agent 3 — Comms", f"📝 Generating procurement email from template engine...")
            await asyncio.sleep(0.3)
            email_body = f"""Dear {best_supplier['name']} Procurement Team,

We are writing to place an urgent purchase order for the following items:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PURCHASE ORDER: {po_number}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Product:        {product_name}
SKU:            {sku}
Quantity:       {reorder_qty} units
Unit Price:     ${best_supplier['price_per_unit']:.2f}
Total Value:    ${total_cost:.2f}
Priority:       HIGH — Current stock at {current_stock} units (critical)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Requested Delivery: Within {best_supplier['lead_time_days']} business days
Ship To: Premium Goods Inc., 1200 Commerce Blvd, Suite 400, Austin, TX 78701
Payment Terms: Net 30

Please confirm receipt of this order and provide an estimated shipping date at your earliest convenience. This is an automated restock triggered by our inventory management system.

Best regards,
Autonomous Restocker System
Premium Goods Inc.
procurement@premiumgoods.com"""

        await emit_log("Agent 3 — Comms", f"✉️ Email composed — Subject: Purchase Order {po_number}")
        await asyncio.sleep(0.2)

        # Store email in outbox
        email_entry = {
            "id": len(email_outbox) + 1,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "to": best_supplier["email"],
            "supplier": best_supplier["name"],
            "subject": f"Purchase Order {po_number} — {product_name} ({reorder_qty} units)",
            "body": email_body,
            "status": "SENT",
            "sku": sku,
            "quantity": reorder_qty,
            "total_cost": total_cost,
        }
        email_outbox.insert(0, email_entry)

        await manager.broadcast({"type": "email_update", "data": email_outbox})

        await emit_log("Agent 3 — Comms", f"📤 Purchase order dispatched to {best_supplier['email']}")
        await asyncio.sleep(0.2)

        await emit_log("Agent 3 — Comms", f"✅ Agent chain complete — PO {po_number} logged to outbox")
        await emit_log("SYSTEM", f"━━━ Restock cycle for {product_name} finished successfully ━━━", "success")

    except Exception as e:
        error_trace = traceback.format_exc()
        await emit_log("SYSTEM", f"🚨 UNHANDLED EXCEPTION in agent chain: {str(e)}", "error")
        await emit_log("SYSTEM", f"💾 State preserved. Admin review required. Trace:\n{error_trace[:200]}", "error")


# ─── Root Health Check ────────────────────────────────────────────
@app.get("/")
async def health_check():
    return {
        "status": "operational",
        "service": "Autonomous Restocker Dashboard API",
        "version": "1.0.0",
        "gemini_connected": gemini_model is not None,
    }
