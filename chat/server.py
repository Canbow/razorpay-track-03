"""FastAPI Web Server & Modern Dashboard for AI Finance Controller Copilot."""
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from chat.controller import FinanceControllerAgent
from data.csv_adapter import export_sample_csvs, load_csv_dataset

app = FastAPI(
    title="AI Finance Controller Copilot",
    description="Agentic 3-Way Financial Reconciliation & Dispute Copilot for Razorpay Track 04",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = FinanceControllerAgent()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    intent: str
    data: Optional[Any] = None


@app.get("/api/metrics")
async def get_metrics():
    """Return executive KPI summary."""
    return agent.get_financial_summary()


@app.get("/api/discrepancies")
async def get_discrepancies(status: Optional[str] = None):
    """Return filtered exception records."""
    return agent.filter_discrepancies(status_filter=status)


@app.get("/api/order/{order_id}")
async def get_order_details(order_id: str):
    """Deep dive inspection of a single order."""
    res = agent.inspect_order(order_id)
    if not res.get("found"):
        raise HTTPException(status_code=404, detail=res.get("error"))
    return res


@app.get("/api/dispute-claim")
async def get_dispute_claim():
    """Generate official Razorpay refund claim letter."""
    return agent.generate_razorpay_dispute_letter()


@app.get("/api/bank-inquiry")
async def get_bank_inquiry():
    """Generate Bank UTR tracing inquiry."""
    return agent.generate_bank_inquiry_sheet()


@app.post("/api/chat", response_model=ChatResponse)
async def handle_chat(payload: ChatRequest):
    """Natural language conversational endpoint."""
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
    res = agent.chat(payload.message)
    return ChatResponse(
        reply=res.get("reply", ""),
        intent=res.get("intent", "general"),
        data=res.get("data"),
    )


@app.post("/api/reconcile")
async def trigger_reconciliation(file: Optional[UploadFile] = File(None)):
    """Trigger or upload a new JSON dataset batch for reconciliation."""
    if file:
        content = await file.read()
        try:
            dataset = json.loads(content.decode("utf-8"))
            agent.refresh_reconciliation(dataset=dataset)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON file: {e}")
    else:
        agent.refresh_reconciliation()

    return {
        "status": "success",
        "message": "3-way reconciliation pipeline completed successfully.",
        "summary": agent.get_financial_summary(),
    }


@app.post("/api/reconcile-csv")
async def trigger_csv_reconciliation(
    orders_file: UploadFile = File(...),
    settlements_file: UploadFile = File(...),
    bank_file: UploadFile = File(...),
):
    """Reconcile 3 uploaded CSV files directly."""
    try:
        orders_bytes = await orders_file.read()
        settlements_bytes = await settlements_file.read()
        bank_bytes = await bank_file.read()

        agent.reconcile_csv_sources(orders_bytes, settlements_bytes, bank_bytes)
        return {
            "status": "success",
            "message": "CSV 3-Way Reconciliation completed successfully.",
            "summary": agent.get_financial_summary(),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process CSV files: {str(e)}")


@app.post("/api/export-sample-csvs")
async def export_sample_csv_endpoint():
    """Export sample CSV files for demonstration."""
    paths = export_sample_csvs()
    return {
        "status": "success",
        "message": "Sample CSV files generated in data/samples/",
        "files": {k: str(v) for k, v in paths.items()},
    }


@app.get("/api/audit-trail")
async def get_audit_trail():
    """Stream live audit trail entries."""
    audit_file = agent.audit_path
    if not audit_file.exists():
        return []
    entries = []
    with open(audit_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line.strip()))
    return entries


@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """Serve the complete Single-Page Application Dashboard with Copilot Chat."""
    return HTMLResponse(content=INDEX_HTML)


INDEX_HTML = """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>AI Finance Controller Copilot | 3-Way Reconciliation</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <script src="https://unpkg.com/lucide@latest"></script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            brand: {
              50: '#eef2ff',
              500: '#6366f1',
              600: '#4f46e5',
              700: '#4338ca',
            }
          }
        }
      }
    }
  </script>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');
    body { font-family: 'Inter', sans-serif; }
    code, pre { font-family: 'JetBrains Mono', monospace; }
    .prose table { width: 100%; border-collapse: collapse; margin: 1rem 0; font-size: 0.875rem; }
    .prose th, .prose td { border: 1px solid #374151; padding: 0.5rem 0.75rem; text-align: left; }
    .prose th { background-color: #1f2937; color: #93c5fd; font-weight: 600; }
    .prose tr:nth-child(even) { background-color: #111827; }
    .prose code { background: #1f2937; color: #38bdf8; padding: 0.15rem 0.4rem; border-radius: 0.25rem; font-size: 0.85em; }
    .prose h1, .prose h2, .prose h3 { color: #f3f4f6; font-weight: 700; margin-top: 1rem; margin-bottom: 0.5rem; }
    .custom-scroll::-webkit-scrollbar { width: 6px; height: 6px; }
    .custom-scroll::-webkit-scrollbar-track { background: #111827; }
    .custom-scroll::-webkit-scrollbar-thumb { background: #374151; border-radius: 4px; }
  </style>
</head>
<body class="bg-gray-950 text-gray-100 flex flex-col h-screen overflow-hidden">

  <!-- Header -->
  <header class="bg-gray-900/80 backdrop-blur border-b border-gray-800 px-6 py-3.5 flex items-center justify-between shrink-0">
    <div class="flex items-center gap-3">
      <div class="p-2 bg-indigo-600/20 text-indigo-400 rounded-xl border border-indigo-500/30">
        <i data-lucide="shield-check" class="w-6 h-6"></i>
      </div>
      <div>
        <div class="flex items-center gap-2">
          <h1 class="text-lg font-bold text-white tracking-tight">AI Finance Controller</h1>
          <span class="text-xs bg-indigo-500/20 text-indigo-300 font-semibold px-2 py-0.5 rounded-full border border-indigo-500/30">Track 04</span>
          <span class="text-xs bg-emerald-500/20 text-emerald-400 font-medium px-2 py-0.5 rounded-full flex items-center gap-1 border border-emerald-500/30">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span> Zero Float Invariants Active
          </span>
          <span class="text-xs bg-blue-500/20 text-blue-300 font-medium px-2 py-0.5 rounded-full flex items-center gap-1 border border-blue-500/30">
            <i data-lucide="file-spreadsheet" class="w-3 h-3"></i> CSV Ingestion Ready
          </span>
        </div>
        <p class="text-xs text-gray-400">Deterministic 3-Way Reconciliation & Automated Dispute Copilot</p>
      </div>
    </div>
    <div class="flex items-center gap-3">
      <button onclick="switchTab('csv')" class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-300 rounded-lg border border-indigo-500/30 transition">
        <i data-lucide="upload-cloud" class="w-4 h-4"></i> Upload CSV Feeds
      </button>
      <button onclick="triggerRecon()" id="refreshBtn" class="flex items-center gap-2 px-3.5 py-1.5 text-xs font-semibold bg-gray-800 hover:bg-gray-700 text-gray-200 rounded-lg border border-gray-700 transition">
        <i data-lucide="refresh-cw" class="w-4 h-4"></i> Re-Run Benchmark
      </button>
      <a href="/api/metrics" target="_blank" class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-400 hover:text-gray-200 bg-gray-900 rounded-lg border border-gray-800">
        <i data-lucide="code" class="w-3.5 h-3.5"></i> API Docs
      </a>
    </div>
  </header>

  <!-- KPI Banner -->
  <section class="bg-gray-900/40 border-b border-gray-800/80 px-6 py-3.5 shrink-0 grid grid-cols-2 md:grid-cols-5 gap-3.5 text-sm">
    <div class="bg-gray-900/90 border border-gray-800 rounded-xl p-3">
      <div class="text-xs text-gray-400 font-medium flex items-center justify-between">
        <span>3-Way Match Rate</span>
        <i data-lucide="check-circle" class="w-4 h-4 text-emerald-400"></i>
      </div>
      <div class="text-xl font-bold text-emerald-400 mt-1" id="statMatchRate">--%</div>
      <div class="text-[11px] text-gray-400 mt-0.5" id="statMatchCount">-- clean matches</div>
    </div>

    <div class="bg-gray-900/90 border border-gray-800 rounded-xl p-3">
      <div class="text-xs text-gray-400 font-medium flex items-center justify-between">
        <span>Total Processed Volume</span>
        <i data-lucide="credit-card" class="w-4 h-4 text-indigo-400"></i>
      </div>
      <div class="text-xl font-bold text-indigo-300 mt-1" id="statTotalVolume">₹--</div>
      <div class="text-[11px] text-gray-400 mt-0.5" id="statTotalRecords">-- transactions</div>
    </div>

    <div class="bg-gray-900/90 border border-gray-800 rounded-xl p-3">
      <div class="text-xs text-gray-400 font-medium flex items-center justify-between">
        <span>MDR Fee Leakage</span>
        <i data-lucide="alert-triangle" class="w-4 h-4 text-amber-400"></i>
      </div>
      <div class="text-xl font-bold text-amber-400 mt-1" id="statFeeLeakage">₹--</div>
      <div class="text-[11px] text-amber-300/80 mt-0.5">Overcharged Orders</div>
    </div>

    <div class="bg-gray-900/90 border border-gray-800 rounded-xl p-3">
      <div class="text-xs text-gray-400 font-medium flex items-center justify-between">
        <span>Total Amount at Risk</span>
        <i data-lucide="alert-octagon" class="w-4 h-4 text-rose-400"></i>
      </div>
      <div class="text-xl font-bold text-rose-400 mt-1" id="statAmountRisk">₹--</div>
      <div class="text-[11px] text-rose-300/80 mt-0.5">Unsettled/Missing</div>
    </div>

    <div class="bg-gray-900/90 border border-gray-800 rounded-xl p-3">
      <div class="text-xs text-gray-400 font-medium flex items-center justify-between">
        <span>Exception Rate</span>
        <i data-lucide="activity" class="w-4 h-4 text-cyan-400"></i>
      </div>
      <div class="text-xl font-bold text-cyan-400 mt-1" id="statExceptionRate">--%</div>
      <div class="text-[11px] text-gray-400 mt-0.5" id="statExceptionCount">-- Anomalies</div>
    </div>
  </section>

  <!-- Main Layout -->
  <main class="flex-1 flex overflow-hidden">
    
    <!-- Left Navigation / Tabs & Explorer -->
    <aside class="w-80 bg-gray-900/60 border-r border-gray-800 flex flex-col shrink-0">
      <div class="p-3.5 border-b border-gray-800 grid grid-cols-2 gap-2">
        <button onclick="switchTab('chat')" id="tabBtnChat" class="py-1.5 px-2.5 text-xs font-semibold rounded-lg bg-indigo-600 text-white flex items-center justify-center gap-1.5 transition">
          <i data-lucide="message-square" class="w-3.5 h-3.5"></i> Copilot Chat
        </button>
        <button onclick="switchTab('exceptions')" id="tabBtnExceptions" class="py-1.5 px-2.5 text-xs font-semibold rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-300 flex items-center justify-center gap-1.5 transition">
          <i data-lucide="list-filter" class="w-3.5 h-3.5"></i> Exceptions
        </button>
        <button onclick="switchTab('dispute')" id="tabBtnDispute" class="py-1.5 px-2.5 text-xs font-semibold rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-300 flex items-center justify-center gap-1.5 transition">
          <i data-lucide="file-text" class="w-3.5 h-3.5"></i> Dispute
        </button>
        <button onclick="switchTab('csv')" id="tabBtnCsv" class="py-1.5 px-2.5 text-xs font-semibold rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-300 flex items-center justify-center gap-1.5 transition">
          <i data-lucide="file-spreadsheet" class="w-3.5 h-3.5"></i> Ingest CSV
        </button>
      </div>

      <!-- Quick Action Pills -->
      <div class="p-3.5 border-b border-gray-800">
        <span class="text-[11px] uppercase tracking-wider text-gray-400 font-semibold block mb-2">Prompt Suggestions</span>
        <div class="flex flex-col gap-1.5 text-xs">
          <button onclick="sendQuickPrompt('What is our reconciliation status and total fee leakage today?')" class="text-left px-2.5 py-1.5 bg-gray-800/80 hover:bg-indigo-600/30 text-gray-300 hover:text-white rounded-md border border-gray-700/60 transition">
            📊 Executive status & fee leakage
          </button>
          <button onclick="sendQuickPrompt('Show me all fee overcharge discrepancies from Razorpay')" class="text-left px-2.5 py-1.5 bg-gray-800/80 hover:bg-indigo-600/30 text-gray-300 hover:text-white rounded-md border border-gray-700/60 transition">
            ⚠️ List 3% MDR fee overcharges
          </button>
          <button onclick="sendQuickPrompt('Inspect order ORD_1041')" class="text-left px-2.5 py-1.5 bg-gray-800/80 hover:bg-indigo-600/30 text-gray-300 hover:text-white rounded-md border border-gray-700/60 transition">
            🔍 Deep-dive order ORD_1041
          </button>
          <button onclick="sendQuickPrompt('Generate Razorpay dispute claim letter for MDR overcharges')" class="text-left px-2.5 py-1.5 bg-gray-800/80 hover:bg-indigo-600/30 text-gray-300 hover:text-white rounded-md border border-gray-700/60 transition">
            📝 Draft Razorpay refund dispute letter
          </button>
          <button onclick="sendQuickPrompt('Generate Bank UTR inquiry sheet for unsettled payout funds')" class="text-left px-2.5 py-1.5 bg-gray-800/80 hover:bg-indigo-600/30 text-gray-300 hover:text-white rounded-md border border-gray-700/60 transition">
            🏦 Draft Bank UTR tracing inquiry
          </button>
          <button onclick="sendQuickPrompt('Explain deterministic 3-way accounting rules and zero-float formulas')" class="text-left px-2.5 py-1.5 bg-gray-800/80 hover:bg-indigo-600/30 text-gray-300 hover:text-white rounded-md border border-gray-700/60 transition">
            ⚙️ Explain accounting equations
          </button>
        </div>
      </div>

      <!-- Quick Exception Filter Sidebar -->
      <div class="flex-1 overflow-y-auto p-3.5 custom-scroll text-xs">
        <span class="text-[11px] uppercase tracking-wider text-gray-400 font-semibold block mb-2">Flagged Exceptions</span>
        <div id="quickExceptionList" class="flex flex-col gap-1.5">
          <!-- Populated by JS -->
        </div>
      </div>
    </aside>

    <!-- Center Workspace -->
    <div class="flex-1 flex flex-col overflow-hidden bg-gray-950">
      
      <!-- TAB 1: Chat Pane -->
      <div id="tabChat" class="flex-1 flex flex-col overflow-hidden">
        <!-- Messages Area -->
        <div id="chatMessages" class="flex-1 overflow-y-auto p-6 space-y-4 custom-scroll">
          <!-- Welcome Message -->
          <div class="flex gap-3">
            <div class="w-8 h-8 rounded-lg bg-indigo-600/30 border border-indigo-500/40 text-indigo-400 flex items-center justify-center shrink-0">
              <i data-lucide="bot" class="w-4 h-4"></i>
            </div>
            <div class="bg-gray-900 border border-gray-800 rounded-2xl rounded-tl-none p-4 max-w-3xl text-sm prose prose-invert">
              <p class="font-semibold text-indigo-300 mb-1">AI Finance Controller Copilot Initialized</p>
              <p class="text-gray-300">
                I continuously audit 3-way financial ledgers across <strong>Internal Orders</strong>, <strong>Razorpay Settlement Dumps</strong>, and <strong>Bank Account Credits</strong>.
              </p>
              <p class="text-xs text-gray-400 mt-2">
                📁 <em>Tip: You can now drop in real CSV feeds anytime via the <strong>"Ingest CSV"</strong> tab or CLI!</em>
              </p>
            </div>
          </div>
        </div>

        <!-- Input Area -->
        <div class="p-4 bg-gray-900/60 border-t border-gray-800 shrink-0">
          <form onsubmit="handleChatSubmit(event)" class="flex gap-2">
            <input 
              type="text" 
              id="chatInput" 
              placeholder="Ask the AI Finance Controller (e.g., 'Inspect ORD_1041', 'Generate dispute claim', 'What is our fee leakage?')..." 
              class="flex-1 bg-gray-950 border border-gray-700 focus:border-indigo-500 rounded-xl px-4 py-2.5 text-sm text-gray-100 placeholder-gray-500 outline-none transition"
              autocomplete="off"
            />
            <button 
              type="submit" 
              id="sendBtn" 
              class="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm rounded-xl flex items-center gap-2 transition disabled:opacity-50"
            >
              <span>Send</span>
              <i data-lucide="send" class="w-4 h-4"></i>
            </button>
          </form>
        </div>
      </div>

      <!-- TAB 2: Exceptions Table Pane -->
      <div id="tabExceptions" class="hidden flex-1 flex flex-col overflow-hidden p-6">
        <div class="flex items-center justify-between mb-4">
          <div>
            <h2 class="text-lg font-bold text-white">Reconciliation Exceptions & Anomalies</h2>
            <p class="text-xs text-gray-400">All flagged 3-way discrepancies requiring financial review and dispute action.</p>
          </div>
          <div class="flex gap-2">
            <select id="statusFilterSelect" onchange="applyExceptionFilter()" class="bg-gray-900 border border-gray-700 text-xs rounded-lg px-3 py-1.5 text-gray-200 outline-none">
              <option value="">All Exception Types</option>
              <option value="FEE_DISCREPANCY">Fee Discrepancy (3% MDR)</option>
              <option value="UNSETTLED_BY_BANK">Unsettled by Bank</option>
              <option value="MISSING_GATEWAY_RECORD">Missing Gateway Record</option>
            </select>
          </div>
        </div>

        <div class="flex-1 overflow-auto border border-gray-800 rounded-xl bg-gray-900/70 custom-scroll">
          <table class="w-full text-left text-xs border-collapse">
            <thead class="bg-gray-800/90 text-gray-300 font-semibold sticky top-0 border-b border-gray-700">
              <tr>
                <th class="p-3">Order ID</th>
                <th class="p-3">Exception Status</th>
                <th class="p-3">Order Amount</th>
                <th class="p-3">Gateway Net</th>
                <th class="p-3">Bank Credit</th>
                <th class="p-3">MDR Delta</th>
                <th class="p-3">Discrepancy Reason</th>
                <th class="p-3">Action Required</th>
                <th class="p-3 text-right">Inspect</th>
              </tr>
            </thead>
            <tbody id="exceptionsTableBody" class="divide-y divide-gray-800">
              <!-- Populated by JS -->
            </tbody>
          </table>
        </div>
      </div>

      <!-- TAB 3: Dispute Letter Pane -->
      <div id="tabDispute" class="hidden flex-1 flex flex-col overflow-hidden p-6">
        <div class="flex items-center justify-between mb-4">
          <div>
            <h2 class="text-lg font-bold text-white">Automated Merchant Dispute Claim Package</h2>
            <p class="text-xs text-gray-400">Formally drafted for Razorpay Merchant Operations with itemized mathematical proofs.</p>
          </div>
          <button onclick="copyDisputeLetter()" class="flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold transition">
            <i data-lucide="copy" class="w-4 h-4"></i> Copy Dispute Markdown
          </button>
        </div>

        <div class="flex-1 overflow-y-auto p-6 bg-gray-900/90 border border-gray-800 rounded-xl prose prose-invert max-w-none custom-scroll" id="disputeLetterContent">
          <!-- Populated by JS -->
        </div>
      </div>

      <!-- TAB 4: Real CSV Ingestion Pane -->
      <div id="tabCsv" class="hidden flex-1 flex flex-col overflow-y-auto p-6 custom-scroll">
        <div class="flex items-center justify-between mb-6">
          <div>
            <h2 class="text-lg font-bold text-white flex items-center gap-2">
              <i data-lucide="file-spreadsheet" class="w-5 h-5 text-indigo-400"></i> Real CSV Ingestion Adapter
            </h2>
            <p class="text-xs text-gray-400">Upload CSV exports from your OMS, Razorpay dashboard, and Bank statements for instant 3-way reconciliation.</p>
          </div>
          <button onclick="exportAndLoadSampleCSVs()" id="sampleCsvBtn" class="flex items-center gap-2 px-3.5 py-2 bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-300 rounded-lg text-xs font-semibold border border-indigo-500/30 transition">
            <i data-lucide="download" class="w-4 h-4"></i> Generate & Load Sample CSVs
          </button>
        </div>

        <form onsubmit="handleCsvUpload(event)" class="space-y-4 max-w-2xl bg-gray-900/90 border border-gray-800 rounded-2xl p-6 shadow-xl">
          <div>
            <label class="block text-xs font-semibold text-gray-300 mb-1.5">1. Internal Orders CSV (OMS)</label>
            <input type="file" id="ordersCsvInput" accept=".csv" required class="block w-full text-xs text-gray-400 file:mr-3 file:py-2 file:px-3.5 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-indigo-600/20 file:text-indigo-300 hover:file:bg-indigo-600/30 bg-gray-950 border border-gray-800 rounded-xl p-2 cursor-pointer" />
            <p class="text-[11px] text-gray-500 mt-1">Headers recognized: <code>Order ID</code>, <code>Amount</code>, <code>Tax Amount</code>, <code>Customer ID</code>, <code>Status</code>, <code>Created At</code></p>
          </div>

          <div>
            <label class="block text-xs font-semibold text-gray-300 mb-1.5">2. Razorpay Settlements CSV (Gateway Dump)</label>
            <input type="file" id="settlementsCsvInput" accept=".csv" required class="block w-full text-xs text-gray-400 file:mr-3 file:py-2 file:px-3.5 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-indigo-600/20 file:text-indigo-300 hover:file:bg-indigo-600/30 bg-gray-950 border border-gray-800 rounded-xl p-2 cursor-pointer" />
            <p class="text-[11px] text-gray-500 mt-1">Headers recognized: <code>Payment ID</code>, <code>Order ID</code>, <code>Gross Amount</code>, <code>MDR Fee</code>, <code>Tax on Fee</code>, <code>Net Amount</code>, <code>UTR</code></p>
          </div>

          <div>
            <label class="block text-xs font-semibold text-gray-300 mb-1.5">3. Bank Statement Credits CSV (Bank Feed)</label>
            <input type="file" id="bankCsvInput" accept=".csv" required class="block w-full text-xs text-gray-400 file:mr-3 file:py-2 file:px-3.5 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-indigo-600/20 file:text-indigo-300 hover:file:bg-indigo-600/30 bg-gray-950 border border-gray-800 rounded-xl p-2 cursor-pointer" />
            <p class="text-[11px] text-gray-500 mt-1">Headers recognized: <code>Bank Ref</code>, <code>UTR</code>, <code>Credit Amount</code>, <code>Value Date</code>, <code>Description</code></p>
          </div>

          <div class="pt-2 flex items-center justify-between">
            <span class="text-xs text-gray-400">Automated trimming & zero-float Decimal normalization active.</span>
            <button type="submit" id="csvSubmitBtn" class="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-xl flex items-center gap-2 transition">
              <i data-lucide="play" class="w-4 h-4"></i> Run 3-Way CSV Reconciliation
            </button>
          </div>
        </form>

        <div class="mt-8 p-4 bg-gray-900/50 border border-gray-800 rounded-xl max-w-2xl text-xs space-y-2 text-gray-300">
          <div class="font-bold text-white flex items-center gap-1.5">
            <i data-lucide="terminal" class="w-4 h-4 text-indigo-400"></i> CLI Direct Ingestion Command:
          </div>
          <p class="text-gray-400">You can also run CSV reconciliation directly from your terminal:</p>
          <pre class="bg-gray-950 p-2.5 rounded-lg text-emerald-400 font-mono text-[11px] border border-gray-800 overflow-x-auto">python run_reconciliation.py --orders orders.csv --settlements razorpay.csv --bank bank.csv</pre>
        </div>
      </div>

    </div>
  </main>

  <script>
    let currentTab = 'chat';
    let cachedMetrics = null;

    async function loadMetrics() {
      try {
        const res = await fetch('/api/metrics');
        const data = await res.json();
        cachedMetrics = data;

        document.getElementById('statMatchRate').textContent = data.match_rate;
        document.getElementById('statMatchCount').textContent = `${data.fully_reconciled} clean matches`;
        document.getElementById('statTotalVolume').textContent = data.total_volume_processed;
        document.getElementById('statTotalRecords').textContent = `${data.total_transactions} transactions`;
        document.getElementById('statFeeLeakage').textContent = data.recoverable_fee_overcharge;
        document.getElementById('statAmountRisk').textContent = data.total_amount_at_risk;
        document.getElementById('statExceptionRate').textContent = data.exception_rate;
        document.getElementById('statExceptionCount').textContent = `${data.total_exceptions} anomalies`;
      } catch (e) {
        console.error("Failed to load metrics", e);
      }
    }

    async function loadExceptions(filter = '') {
      try {
        const url = filter ? `/api/discrepancies?status=${encodeURIComponent(filter)}` : '/api/discrepancies';
        const res = await fetch(url);
        const data = await res.json();

        const tbody = document.getElementById('exceptionsTableBody');
        tbody.innerHTML = '';

        const quickList = document.getElementById('quickExceptionList');
        if (!filter) quickList.innerHTML = '';

        data.forEach(exc => {
          let badgeColor = 'bg-amber-500/20 text-amber-400 border-amber-500/30';
          if (exc.status.includes('UNSETTLED')) badgeColor = 'bg-orange-500/20 text-orange-400 border-orange-500/30';
          if (exc.status.includes('MISSING')) badgeColor = 'bg-rose-500/20 text-rose-400 border-rose-500/30';

          const tr = document.createElement('tr');
          tr.className = 'hover:bg-gray-800/50 transition';
          tr.innerHTML = `
            <td class="p-3 font-mono font-medium text-indigo-300">${exc.order_id}</td>
            <td class="p-3">
              <span class="px-2 py-0.5 rounded-full text-[11px] font-semibold border ${badgeColor}">
                ${exc.status}
              </span>
            </td>
            <td class="p-3 font-mono text-gray-200">${exc.order_amount}</td>
            <td class="p-3 font-mono text-gray-400">${exc.net_settlement}</td>
            <td class="p-3 font-mono text-gray-400">${exc.bank_credit}</td>
            <td class="p-3 font-mono font-bold ${exc.fee_delta !== 'N/A' ? 'text-amber-400' : 'text-gray-500'}">${exc.fee_delta}</td>
            <td class="p-3 text-gray-300 max-w-xs truncate" title="${exc.reason}">${exc.reason}</td>
            <td class="p-3 text-gray-400 max-w-xs truncate" title="${exc.action}">${exc.action}</td>
            <td class="p-3 text-right">
              <button onclick="inspectFromTable('${exc.order_id}')" class="px-2 py-1 bg-gray-800 hover:bg-indigo-600 text-gray-300 hover:text-white rounded text-[11px] transition">
                Deep Dive
              </button>
            </td>
          `;
          tbody.appendChild(tr);

          if (!filter) {
            const btn = document.createElement('button');
            btn.onclick = () => inspectFromTable(exc.order_id);
            btn.className = 'text-left p-2 rounded-lg bg-gray-900 border border-gray-800 hover:border-indigo-500/50 flex items-center justify-between group transition';
            btn.innerHTML = `
              <div>
                <span class="font-mono font-bold text-gray-200 group-hover:text-indigo-300">${exc.order_id}</span>
                <span class="block text-[10px] text-gray-500">${exc.order_amount}</span>
              </div>
              <span class="text-[10px] px-1.5 py-0.5 rounded border ${badgeColor}">
                ${exc.status.replace('ReconciliationStatus.', '').substring(0, 10)}
              </span>
            `;
            quickList.appendChild(btn);
          }
        });
      } catch (e) {
        console.error("Failed to load exceptions", e);
      }
    }

    async function loadDispute() {
      try {
        const res = await fetch('/api/dispute-claim');
        const data = await res.json();
        document.getElementById('disputeLetterContent').innerHTML = marked.parse(data.dispute_letter_markdown);
      } catch (e) {
        console.error("Failed to load dispute", e);
      }
    }

    function switchTab(tab) {
      currentTab = tab;
      document.getElementById('tabChat').classList.toggle('hidden', tab !== 'chat');
      document.getElementById('tabExceptions').classList.toggle('hidden', tab !== 'exceptions');
      document.getElementById('tabDispute').classList.toggle('hidden', tab !== 'dispute');
      document.getElementById('tabCsv').classList.toggle('hidden', tab !== 'csv');

      const setBtnClass = (id, active) => {
        const el = document.getElementById(id);
        if (!el) return;
        el.className = active
          ? 'py-1.5 px-2.5 text-xs font-semibold rounded-lg bg-indigo-600 text-white flex items-center justify-center gap-1.5 transition'
          : 'py-1.5 px-2.5 text-xs font-semibold rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-300 flex items-center justify-center gap-1.5 transition';
      };

      setBtnClass('tabBtnChat', tab === 'chat');
      setBtnClass('tabBtnExceptions', tab === 'exceptions');
      setBtnClass('tabBtnDispute', tab === 'dispute');
      setBtnClass('tabBtnCsv', tab === 'csv');

      lucide.createIcons();
    }

    function applyExceptionFilter() {
      const select = document.getElementById('statusFilterSelect');
      loadExceptions(select.value);
    }

    function inspectFromTable(orderId) {
      switchTab('chat');
      sendQuickPrompt(`Inspect order ${orderId}`);
    }

    async function sendQuickPrompt(promptText) {
      document.getElementById('chatInput').value = promptText;
      await handleChatSubmit(new Event('submit'));
    }

    async function handleChatSubmit(e) {
      e.preventDefault();
      const input = document.getElementById('chatInput');
      const text = input.value.trim();
      if (!text) return;

      input.value = '';
      appendUserMessage(text);

      const loadingId = appendLoadingIndicator();
      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: text })
        });
        const data = await res.json();
        removeLoadingIndicator(loadingId);
        appendAssistantMessage(data.reply);
      } catch (err) {
        removeLoadingIndicator(loadingId);
        appendAssistantMessage(`❌ Error: ${err.message}`);
      }
    }

    function appendUserMessage(text) {
      const container = document.getElementById('chatMessages');
      const div = document.createElement('div');
      div.className = 'flex gap-3 justify-end';
      div.innerHTML = `
        <div class="bg-indigo-600 text-white rounded-2xl rounded-tr-none px-4 py-3 max-w-2xl text-sm shadow-md">
          <p>${escapeHtml(text)}</p>
        </div>
        <div class="w-8 h-8 rounded-lg bg-indigo-500/20 border border-indigo-500/30 text-indigo-300 flex items-center justify-center shrink-0">
          <i data-lucide="user" class="w-4 h-4"></i>
        </div>
      `;
      container.appendChild(div);
      lucide.createIcons();
      container.scrollTop = container.scrollHeight;
    }

    function appendAssistantMessage(markdown) {
      const container = document.getElementById('chatMessages');
      const div = document.createElement('div');
      div.className = 'flex gap-3';
      div.innerHTML = `
        <div class="w-8 h-8 rounded-lg bg-indigo-600/30 border border-indigo-500/40 text-indigo-400 flex items-center justify-center shrink-0">
          <i data-lucide="bot" class="w-4 h-4"></i>
        </div>
        <div class="bg-gray-900 border border-gray-800 rounded-2xl rounded-tl-none p-4 max-w-3xl text-sm prose prose-invert shadow-md">
          ${marked.parse(markdown)}
        </div>
      `;
      container.appendChild(div);
      lucide.createIcons();
      container.scrollTop = container.scrollHeight;
    }

    function appendLoadingIndicator() {
      const container = document.getElementById('chatMessages');
      const id = 'loader_' + Date.now();
      const div = document.createElement('div');
      div.id = id;
      div.className = 'flex gap-3';
      div.innerHTML = `
        <div class="w-8 h-8 rounded-lg bg-indigo-600/30 border border-indigo-500/40 text-indigo-400 flex items-center justify-center shrink-0 animate-pulse">
          <i data-lucide="bot" class="w-4 h-4"></i>
        </div>
        <div class="bg-gray-900 border border-gray-800 rounded-2xl rounded-tl-none p-3 text-xs text-gray-400 flex items-center gap-2">
          <div class="w-2 h-2 rounded-full bg-indigo-400 animate-bounce"></div>
          <div class="w-2 h-2 rounded-full bg-indigo-400 animate-bounce [animation-delay:0.2s]"></div>
          <div class="w-2 h-2 rounded-full bg-indigo-400 animate-bounce [animation-delay:0.4s]"></div>
          <span>Verifying ledgers & computing invariants...</span>
        </div>
      `;
      container.appendChild(div);
      lucide.createIcons();
      container.scrollTop = container.scrollHeight;
      return id;
    }

    function removeLoadingIndicator(id) {
      const el = document.getElementById(id);
      if (el) el.remove();
    }

    async function triggerRecon() {
      const btn = document.getElementById('refreshBtn');
      btn.disabled = true;
      btn.innerHTML = `<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i> Running...`;
      lucide.createIcons();

      try {
        await fetch('/api/reconcile', { method: 'POST' });
        await loadMetrics();
        await loadExceptions();
        await loadDispute();
        appendAssistantMessage("✅ **3-Way Reconciliation Pipeline Re-executed Successfully!** All metrics and dispute tables are synchronized.");
      } catch (e) {
        alert("Reconciliation failed: " + e.message);
      } finally {
        btn.disabled = false;
        btn.innerHTML = `<i data-lucide="refresh-cw" class="w-4 h-4"></i> Re-Run Benchmark`;
        lucide.createIcons();
      }
    }

    async function handleCsvUpload(e) {
      e.preventDefault();
      const ordersFile = document.getElementById('ordersCsvInput').files[0];
      const settlementsFile = document.getElementById('settlementsCsvInput').files[0];
      const bankFile = document.getElementById('bankCsvInput').files[0];

      if (!ordersFile || !settlementsFile || !bankFile) {
        alert("Please select all 3 CSV files (Orders, Settlements, Bank).");
        return;
      }

      const btn = document.getElementById('csvSubmitBtn');
      btn.disabled = true;
      btn.innerHTML = `<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i> Processing CSVs...`;
      lucide.createIcons();

      const formData = new FormData();
      formData.append('orders_file', ordersFile);
      formData.append('settlements_file', settlementsFile);
      formData.append('bank_file', bankFile);

      try {
        const res = await fetch('/api/reconcile-csv', {
          method: 'POST',
          body: formData,
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'CSV Reconciliation failed');

        await loadMetrics();
        await loadExceptions();
        await loadDispute();
        switchTab('chat');
        appendAssistantMessage(`✅ **CSV Ingestion & Reconciliation Complete!**\n\n- Successfully parsed and verified \`${ordersFile.name}\`, \`${settlementsFile.name}\`, and \`${bankFile.name}\`.\n- Match rate: **${data.summary.match_rate}** (${data.summary.fully_reconciled} clean matches).\n- Exceptions flagged: **${data.summary.total_exceptions}**.\n- Total Recoverable Overcharges: **${data.summary.recoverable_fee_overcharge}**.`);
      } catch (err) {
        alert(`Error: ${err.message}`);
      } finally {
        btn.disabled = false;
        btn.innerHTML = `<i data-lucide="play" class="w-4 h-4"></i> Run 3-Way CSV Reconciliation`;
        lucide.createIcons();
      }
    }

    async function exportAndLoadSampleCSVs() {
      const btn = document.getElementById('sampleCsvBtn');
      btn.disabled = true;
      btn.innerHTML = `<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i> Generating...`;
      lucide.createIcons();

      try {
        const res = await fetch('/api/export-sample-csvs', { method: 'POST' });
        const data = await res.json();
        alert(`✅ Sample CSV files generated in: data/samples/\n\n- sample_orders.csv\n- sample_razorpay.csv\n- sample_bank.csv`);
      } catch (err) {
        alert(`Error: ${err.message}`);
      } finally {
        btn.disabled = false;
        btn.innerHTML = `<i data-lucide="download" class="w-4 h-4"></i> Generate & Load Sample CSVs`;
        lucide.createIcons();
      }
    }

    async function copyDisputeLetter() {
      const res = await fetch('/api/dispute-claim');
      const data = await res.json();
      navigator.clipboard.writeText(data.dispute_letter_markdown);
      alert("✅ Dispute claim markdown copied to clipboard!");
    }

    function escapeHtml(text) {
      return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }

    // Initialize
    window.addEventListener('DOMContentLoaded', () => {
      lucide.createIcons();
      loadMetrics();
      loadExceptions();
      loadDispute();
    });
  </script>
</body>
</html>
"""
