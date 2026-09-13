# 🤖 Autonomous E-Commerce Supply Chain Restocker Dashboard
### A Resilient Multi-Agent Sandboxed Orchestration Pipeline

An enterprise-grade automation engine built for the **Multi-App AI Agent Hackathon**. This platform bridges real-time storefront demand with wholesale logistics networks by orchestrating independent backend agents across **3 high-fidelity application sandboxes**: **Shopify (Webhooks)**, **Airtable/Google Sheets (Supplier Matrix)**, and **Gmail (via live Google Gemini AI generation)**.

---

## 📺 Product Walkthrough & Demo Video
Click the link below to watch the live 2-minute architectural walk-through and resilience demo:

👉 **[Watch the Live Project Demo on YouTube](YOUR_YOUTUBE_LINK_HERE)**

---

## 🛠️ The Architecture: Multi-App Emulation

The system handles multi-step autonomous actions using a React (Vite) + Tailwind CSS frontend dashboard connected via live, bi-directional **WebSockets** to an asynchronous **FastAPI** Python backend engine.

1. **App 1 — Shopify (Live Inventory Source):** Monitors storefront counts. When a numerical stepper drops stock under a deterministic threshold (< 10 units), it fires a local simulated webhook payload down our event pipeline.
2. **App 2 — Supplier Base (Sheet Registry):** A structured grid matrix detailing global suppliers, wholesale pricing brackets, lead times, and contact profiles. 
3. **App 3 — Gmail (Procurement Communication Outbox):** Once the strategist calculates the optimal financial decision, the **Communications Agent** actively calls the live **Google Gemini API** (`google-genai` engine configured in `backend/.env`) to dynamically construct a tailored, formal enterprise purchase order email, caching it directly in our outgoing outbox grid with a successful `SENT` state.

---

## 🛡️ Built for Production Reliability (Arga & Lemma Alignment)
Addressing the core engineering focus of judges from **Arga Labs** (pre-production environmental sandboxing) and **Lemma AI** (runtime semantic observability), our platform features advanced resilience gates:

* **Deterministic Fault Isolation (Chaos Mode):** Includes an aggressive exception interceptor switch. If data fields are corrupted or missing (e.g., if a supplier's contact email is severed on the dashboard), the agent chain gracefully traps the missing metrics exception, freezes the financial state transaction, and logs a critical halt warning instead of throwing an unhandled `500` script loop crash.
* **Real-Time Telemetry Logging:** Features a scrolling, color-coded terminal monitor that streams exact agent state mutations live over WebSockets, giving developers total visibility over multi-app system traces.

---

## ⚙️ Quickstart Local Installation

### 1. Backend Setup
Navigate to the directory, create your local environment reference slots, and kick off the server:
```bash
cd backend
pip install fastapi uvicorn google-genai
touch .env
```
Add your credentials to your `backend/.env` file:
```env
GEMINI_API_KEY=your_google_ai_studio_key_here
```
Launch the Uvicorn engine:
```bash
uvicorn main:app --reload --port 8000
```

### 2. Frontend Dashboard Setup
In a secondary terminal tab, boot up the visual control interface:
```bash
cd frontend
npm install
npm run dev -- --port 5173
```
Open **`http://localhost:5173`** in your web browser to test the interactive eng
Demo Video : https://www.youtube.com/watch?v=YVYx7T9q9F0
