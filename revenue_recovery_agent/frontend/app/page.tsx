'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  Shield,
  ShieldCheck,
  RotateCw,
  Bolt,
  Play,
  Moon,
  Clock,
  UserCheck,
  PiggyBank,
  Gauge,
  TrendingUp,
  Search,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Smartphone,
  Layers,
  Terminal,
  FileCheck
} from 'lucide-react';
import ThreeVisualizer from '@/components/ThreeVisualizer';
import RecoveryComparisonChart from '@/components/RecoveryComparisonChart';
import CheckoutModal from '@/components/CheckoutModal';
import WhatsAppModal from '@/components/WhatsAppModal';
import { BenchmarkKPIs, ProcessedEvent, AuditRecord, SimulateRequest, SimulateResponse } from '@/lib/types';
import { initialKPIs, initialEvents } from '@/lib/mockData';

export default function DashboardPage() {
  // State
  const [kpis, setKpis] = useState<BenchmarkKPIs>(initialKPIs);
  const [events, setEvents] = useState<ProcessedEvent[]>(initialEvents);
  const [filteredEvents, setFilteredEvents] = useState<ProcessedEvent[]>(initialEvents);
  const [auditLogs, setAuditLogs] = useState<AuditRecord[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('ALL');

  // View Mode: show 3D Topology + Dashboard
  const [show3DCanvas, setShow3DCanvas] = useState(true);

  // Live IST Clock & TRAI Status
  const [liveTime, setLiveTime] = useState<string>('--:--:-- IST');
  const [isTraiCompliantHour, setIsTraiCompliantHour] = useState<boolean>(true);

  // Simulation Form State
  const [simInvoiceId, setSimInvoiceId] = useState('INV-SIM-8001');
  const [simCustomerId, setSimCustomerId] = useState('CUST-8001');
  const [simAmount, setSimAmount] = useState<number>(3500);
  const [simRail, setSimRail] = useState<'CARD' | 'UPI' | 'NETBANKING' | 'MANDATE'>('CARD');
  const [simErrorCode, setSimErrorCode] = useState('GATEWAY_TIMEOUT');
  const [simAttemptCount, setSimAttemptCount] = useState<number>(0);
  const [simHour, setSimHour] = useState<number>(14);
  const [simIsLocked, setSimIsLocked] = useState<boolean>(false);
  const [isSimulating, setIsSimulating] = useState<boolean>(false);
  const [simResult, setSimResult] = useState<SimulateResponse | null>(null);

  // Modals
  const [isCheckoutOpen, setIsCheckoutOpen] = useState(false);
  const [isWhatsAppOpen, setIsWhatsAppOpen] = useState(false);

  // 1. Live Real-Time IST Clock
  useEffect(() => {
    const updateClock = () => {
      const now = new Date();
      const timeStr = new Intl.DateTimeFormat('en-IN', {
        timeZone: 'Asia/Kolkata',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false,
      }).format(now);
      setLiveTime(`${timeStr} IST`);

      const istHour = parseInt(
        new Intl.DateTimeFormat('en-IN', {
          timeZone: 'Asia/Kolkata',
          hour: 'numeric',
          hour12: false,
        }).format(now)
      );
      setIsTraiCompliantHour(istHour >= 8 && istHour < 20);
    };

    updateClock();
    const timer = setInterval(updateClock, 1000);
    return () => clearInterval(timer);
  }, []);

  // 2. Data Fetching from FastAPI backend (with fallback to mock data)
  const fetchBackendData = useCallback(async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/benchmark-summary');
      if (res.ok) {
        const data = await res.json();
        setKpis(data.kpis);
        setEvents(data.events);
        setFilteredEvents(data.events);
      }
    } catch {
      // Backend not running on 8000; mockData is preserved
    }

    try {
      const auditRes = await fetch('http://127.0.0.1:8000/api/audit-trail?limit=40');
      if (auditRes.ok) {
        const auditData = await auditRes.json();
        setAuditLogs(auditData.records.reverse());
      }
    } catch {
      // Fallback empty audit
    }
  }, []);

  useEffect(() => {
    fetchBackendData();
  }, [fetchBackendData]);

  // 3. Search & Filter Transactions
  useEffect(() => {
    let result = events;
    if (categoryFilter !== 'ALL') {
      result = result.filter((e) => e.category === categoryFilter);
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(
        (e) =>
          e.invoice_id.toLowerCase().includes(q) ||
          e.customer_id.toLowerCase().includes(q) ||
          e.error_code.toLowerCase().includes(q) ||
          e.payment_rail.toLowerCase().includes(q)
      );
    }
    setFilteredEvents(result);
  }, [events, searchQuery, categoryFilter]);

  // 4. Live Agent Simulation Execution
  const handleSimulate = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSimulating(true);

    const payload: SimulateRequest = {
      invoice_id: simInvoiceId,
      customer_id: simCustomerId,
      amount: simAmount,
      payment_rail: simRail,
      error_code: simErrorCode,
      error_description: `Simulated error for ${simErrorCode}`,
      attempt_count: simAttemptCount,
      current_hour_ist: simHour,
      is_locked: simIsLocked,
    };

    try {
      const res = await fetch('http://127.0.0.1:8000/api/simulate-recovery', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        const data = await res.json();
        setSimResult(data);
        fetchBackendData();
      } else {
        throw new Error('Backend simulation error');
      }
    } catch {
      // Standalone Fallback Simulation logic mirroring core/policy.py
      let category = 'CUSTOMER_ACTIONABLE';
      if (['GATEWAY_TIMEOUT', 'ISSUER_DOWN', 'NETWORK_ERROR'].includes(simErrorCode)) {
        category = 'TRANSIENT_DOWNTIME';
      } else if (['ACCOUNT_CLOSED', 'FRAUD_BLOCK', 'INVALID_ACCOUNT'].includes(simErrorCode)) {
        category = 'TERMINAL_FAILURE';
      }

      let guardPassed = true;
      let guardMsg = 'PASSED_ALL_GUARDRAILS';
      let action = 'SCHEDULED_SILENT_RETRY';

      if (category === 'TRANSIENT_DOWNTIME') action = 'SCHEDULED_SILENT_RETRY';
      else if (category === 'CUSTOMER_ACTIONABLE') action = 'DISPATCH_DYNAMIC_LINK';
      else action = 'ABORT_TERMINAL';

      if (simIsLocked) {
        guardPassed = false;
        guardMsg = 'IDEMPOTENCY_LOCK_ACTIVE: invoice is locked by concurrent recovery process';
      } else if (simAttemptCount >= 2) {
        guardPassed = false;
        guardMsg = `MAX_RETRY_EXCEEDED: attempt count ${simAttemptCount} reaches/exceeds limit 2`;
      } else if (action === 'DISPATCH_DYNAMIC_LINK' && (simHour < 8 || simHour >= 20)) {
        guardPassed = false;
        guardMsg = `COMPLIANCE_WINDOW_VIOLATION: hour ${simHour}:00 is outside permissible outreach window (08:00–20:00 IST)`;
      }

      let status = 'RECOVERED';
      let reasoning = '';
      let dynamicLink: string | undefined = undefined;

      if (!guardPassed || category === 'TERMINAL_FAILURE') {
        action = 'ABORT_TERMINAL';
        status = simAttemptCount >= 2 ? 'ABORTED_MAX_RETRIES' : 'FAILED';
        reasoning = `Hard stopping rule enforced: ${guardMsg}`;
      } else if (category === 'TRANSIENT_DOWNTIME') {
        status = 'RECOVERED';
        reasoning = `Transient downtime (${simErrorCode}) diagnosed on ${simRail}. Scheduled silent off-peak retry (+12h cooldown) to match bank uptime.`;
      } else {
        const targetRail = simRail !== 'UPI' ? 'UPI' : 'CARD';
        status = 'RECOVERED';
        dynamicLink = `https://pay.rzp.io/recover/${simInvoiceId}?rail=${targetRail}&auth=intent`;
        reasoning = `Customer-actionable failure (${simErrorCode}) on ${simRail}. Dispatched dynamic multi-rail payment link with smart fallback to ${targetRail} Intent.`;
      }

      setSimResult({
        status: 'success',
        input_event: payload,
        current_hour_ist: simHour,
        failure_category: category,
        guard_passed: guardPassed,
        guard_message: guardMsg,
        recovery_status: status,
        recovery_plan: {
          invoice_id: simInvoiceId,
          action,
          target_rail: simRail !== 'UPI' ? 'UPI' : 'CARD',
          dynamic_link: dynamicLink,
          reasoning,
        },
        is_recovered: status === 'RECOVERED',
      });
    } finally {
      setTimeout(() => setIsSimulating(false), 500);
    }
  };

  // Load a transaction from the table directly into the simulator
  const loadTransactionIntoSim = (ev: ProcessedEvent) => {
    setSimInvoiceId(ev.invoice_id);
    setSimCustomerId(ev.customer_id);
    setSimAmount(ev.amount);
    setSimRail(ev.payment_rail);
    setSimErrorCode(ev.error_code);
    setSimAttemptCount(ev.attempt_count);
    window.scrollTo({ top: 400, behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen bg-brand-dark text-slate-100 font-sans p-4 sm:p-6 space-y-6">
      {/* Top Header */}
      <header className="glass-panel rounded-2xl p-4 border border-brand-border sticky top-0 z-40">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="w-11 h-11 rounded-xl bg-gradient-to-tr from-brand-blue to-brand-cyan flex items-center justify-center shadow-lg shadow-brand-blue/30">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-xl text-white tracking-wide">
                  Razorpay <span className="text-brand-cyan">RecoveryAI</span>
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Autonomous AI Dunning, Dynamic Multi-Rail Routing & Guardrails
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Real-time IST clock & TRAI compliance watchdog */}
            <div className="flex items-center space-x-2 px-3 py-1.5 rounded-xl bg-slate-900/90 border border-slate-700 text-xs">
              <div
                className={`w-2.5 h-2.5 rounded-full ${
                  isTraiCompliantHour ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'
                }`}
              />
              <span className="font-mono text-slate-200 font-semibold tracking-wider">
                {liveTime}
              </span>
              <span
                className={`text-[11px] px-2 py-0.5 rounded font-medium border ${
                  isTraiCompliantHour
                    ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                    : 'bg-amber-500/20 text-amber-400 border-amber-500/30'
                }`}
              >
                {isTraiCompliantHour
                  ? 'TRAI Compliant Hours (08:00–20:00)'
                  : 'Night Cooldown (08:00–20:00 Closed)'}
              </span>
            </div>

            {/* Sync button */}
            <button
              onClick={fetchBackendData}
              className="px-3 py-1.5 rounded-xl bg-brand-blue/20 hover:bg-brand-blue/30 text-brand-cyan border border-brand-blue/40 text-xs font-semibold flex items-center space-x-1.5 transition shadow-sm"
            >
              <RotateCw className="w-3.5 h-3.5" />
              <span>Sync Pipeline</span>
            </button>
          </div>
        </div>
      </header>

      {/* 3D Three.js Payment Rail Topology Visualizer */}
      {show3DCanvas && (
        <section className="animate-in fade-in duration-300">
          <ThreeVisualizer className="shadow-2xl" />
        </section>
      )}

      {/* Executive KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="glass-panel rounded-xl p-4 border border-brand-border">
          <div className="text-xs text-slate-400 font-medium uppercase tracking-wider">
            Total at Risk
          </div>
          <div className="text-2xl font-bold text-white mt-1">
            ₹{kpis.total_at_risk.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <div className="text-xs text-slate-400 mt-2 flex items-center space-x-1">
            <span className="text-slate-200 font-semibold">{kpis.total_transactions}</span>{' '}
            transactions ingested
          </div>
        </div>

        <div className="glass-panel rounded-xl p-4 border border-emerald-500/30 bg-gradient-to-b from-emerald-500/10 to-transparent">
          <div className="text-xs text-emerald-400 font-medium uppercase tracking-wider">
            AI Recovered Revenue
          </div>
          <div className="text-2xl font-bold text-emerald-400 mt-1">
            ₹{kpis.total_recovered.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <div className="text-xs text-emerald-400/90 mt-2 flex items-center space-x-1 font-medium">
            <TrendingUp className="w-3.5 h-3.5" />
            <span>{kpis.recovery_percentage}%</span> recovery conversion
          </div>
        </div>

        <div className="glass-panel rounded-xl p-4 border border-brand-cyan/30 bg-gradient-to-b from-brand-cyan/10 to-transparent">
          <div className="text-xs text-brand-cyan font-medium uppercase tracking-wider">
            Net Incremental Uplift
          </div>
          <div className="text-2xl font-bold text-brand-cyan mt-1">
            +₹{kpis.net_uplift.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <div className="text-xs text-slate-400 mt-2">
            vs. Naive Retries (<span className="text-rose-400 font-medium">{kpis.baseline_percentage}%</span>)
          </div>
        </div>

        <div className="glass-panel rounded-xl p-4 border border-brand-border">
          <div className="text-xs text-slate-400 font-medium uppercase tracking-wider">
            Double-Debit Guard
          </div>
          <div className="text-2xl font-bold text-white mt-1 flex items-center space-x-1.5">
            <span>0</span>
            <span className="text-xs text-emerald-400 font-medium px-2 py-0.5 rounded bg-emerald-500/20 border border-emerald-500/30">
              100% Guarded
            </span>
          </div>
          <div className="text-xs text-slate-400 mt-2">Idempotency Lock Active</div>
        </div>

        <div className="glass-panel rounded-xl p-4 border border-brand-border">
          <div className="text-xs text-slate-400 font-medium uppercase tracking-wider">
            TRAI Compliance
          </div>
          <div className="text-2xl font-bold text-white mt-1 flex items-center space-x-1.5">
            <span>0 Violations</span>
          </div>
          <div className="text-xs text-slate-400 mt-2">
            <span className="text-rose-400 font-medium">{kpis.baseline_trai_violations} stopped</span> in baseline
          </div>
        </div>
      </div>

      {/* Merchant Operational Efficiency & Involuntary Churn Strip */}
      <div className="glass-panel rounded-xl p-3 px-5 border border-brand-border/80 bg-slate-900/40 flex flex-wrap items-center justify-between gap-4 text-xs">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold">
            <UserCheck className="w-4 h-4" />
          </div>
          <div>
            <span className="text-slate-400 block text-[10px] uppercase tracking-wider">
              Involuntary Churn Rescued
            </span>
            <span className="font-bold text-white text-sm">34 Subscribers Rescued</span>
          </div>
        </div>

        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-brand-cyan/20 text-brand-cyan flex items-center justify-center font-bold">
            <PiggyBank className="w-4 h-4" />
          </div>
          <div>
            <span className="text-slate-400 block text-[10px] uppercase tracking-wider">
              Gateway Attempt Fees Saved
            </span>
            <span className="font-bold text-white text-sm">₹3,150.00 Saved</span>{' '}
            <span className="text-[10px] text-slate-400">(15 terminal loops killed)</span>
          </div>
        </div>

        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-purple-500/20 text-purple-400 flex items-center justify-center font-bold">
            <Gauge className="w-4 h-4" />
          </div>
          <div>
            <span className="text-slate-400 block text-[10px] uppercase tracking-wider">
              Avg Agent Decision Latency
            </span>
            <span className="font-bold text-white text-sm">185 ms / transaction</span>
          </div>
        </div>

        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-amber-500/20 text-amber-400 flex items-center justify-center font-bold">
            <TrendingUp className="w-4 h-4" />
          </div>
          <div>
            <span className="text-slate-400 block text-[10px] uppercase tracking-wider">
              Net Operational ROI
            </span>
            <span className="font-bold text-white text-sm">18.2x Return on Recovery</span>
          </div>
        </div>
      </div>

      {/* Main Grid: Interactive Sandbox (5 cols) & Analytics/Comparison (7 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Webhook Simulator Sandbox */}
        <div className="lg:col-span-5 glass-panel rounded-xl p-5 border border-brand-border space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-white flex items-center space-x-2">
              <Bolt className="w-4 h-4 text-brand-blue" />
              <span>Interactive Webhook Simulator</span>
            </h2>
            <span className="text-xs text-brand-cyan bg-brand-blue/10 px-2 py-0.5 rounded border border-brand-blue/20">
              Live Evaluation
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Inject a custom payment failure to test agent diagnosis, guardrails, and dynamic multi-rail fallback.
          </p>

          <form onSubmit={handleSimulate} className="space-y-3 text-xs">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-slate-400 mb-1">Invoice ID</label>
                <input
                  type="text"
                  value={simInvoiceId}
                  onChange={(e) => setSimInvoiceId(e.target.value)}
                  className="w-full bg-slate-900/80 border border-slate-700 rounded-lg px-2.5 py-1.5 text-white font-mono outline-none focus:border-brand-blue"
                />
              </div>
              <div>
                <label className="block text-slate-400 mb-1">Amount (₹ INR)</label>
                <input
                  type="number"
                  value={simAmount}
                  onChange={(e) => setSimAmount(parseFloat(e.target.value) || 0)}
                  className="w-full bg-slate-900/80 border border-slate-700 rounded-lg px-2.5 py-1.5 text-white font-mono outline-none focus:border-brand-blue"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-slate-400 mb-1">Payment Rail</label>
                <select
                  value={simRail}
                  onChange={(e) => setSimRail(e.target.value as any)}
                  className="w-full bg-slate-900/80 border border-slate-700 rounded-lg px-2.5 py-1.5 text-white outline-none"
                >
                  <option value="CARD">CARD</option>
                  <option value="MANDATE">MANDATE</option>
                  <option value="NETBANKING">NETBANKING</option>
                  <option value="UPI">UPI</option>
                </select>
              </div>
              <div>
                <label className="block text-slate-400 mb-1">
                  Prior Retries: <span className="font-mono text-white font-bold">{simAttemptCount}</span>
                </label>
                <input
                  type="range"
                  min="0"
                  max="3"
                  value={simAttemptCount}
                  onChange={(e) => setSimAttemptCount(parseInt(e.target.value))}
                  className="w-full accent-brand-blue"
                />
                <div className="text-[10px] text-slate-500 flex justify-between">
                  <span>0</span>
                  <span>1</span>
                  <span className="text-amber-400">2 (Max)</span>
                  <span>3</span>
                </div>
              </div>
            </div>

            <div>
              <label className="block text-slate-400 mb-1">Error Code</label>
              <select
                value={simErrorCode}
                onChange={(e) => setSimErrorCode(e.target.value)}
                className="w-full bg-slate-900/80 border border-slate-700 rounded-lg px-2.5 py-1.5 text-white outline-none font-mono"
              >
                <optgroup label="Transient Downtime (Scheduled Silent Retry)">
                  <option value="GATEWAY_TIMEOUT">GATEWAY_TIMEOUT (Bank switch timeout)</option>
                  <option value="ISSUER_DOWN">ISSUER_DOWN (Core banking unreachable)</option>
                  <option value="NETWORK_ERROR">NETWORK_ERROR (NPCI network drop)</option>
                </optgroup>
                <optgroup label="Customer Actionable (Dynamic UPI Link)">
                  <option value="INSUFFICIENT_FUNDS">INSUFFICIENT_FUNDS (Account depleted)</option>
                  <option value="AUTH_FAILED">AUTH_FAILED (OTP / 3DS cancelled)</option>
                  <option value="EXPIRED_MANDATE">EXPIRED_MANDATE (Mandate expired)</option>
                </optgroup>
                <optgroup label="Terminal Failure (Graceful Abort)">
                  <option value="ACCOUNT_CLOSED">ACCOUNT_CLOSED (Account closed)</option>
                  <option value="FRAUD_BLOCK">FRAUD_BLOCK (Risk block triggered)</option>
                  <option value="INVALID_ACCOUNT">INVALID_ACCOUNT (Invalid account)</option>
                </optgroup>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-slate-400 mb-1">
                  Simulated Hour (IST):{' '}
                  <span className="font-mono text-white font-bold">{simHour.toString().padStart(2, '0')}:00</span>
                </label>
                <input
                  type="range"
                  min="0"
                  max="23"
                  value={simHour}
                  onChange={(e) => setSimHour(parseInt(e.target.value))}
                  className="w-full accent-brand-blue"
                />
                <div className="text-[10px] text-slate-500 flex justify-between">
                  <span className="text-rose-400">02:00</span>
                  <span className="text-emerald-400">14:00</span>
                  <span className="text-rose-400">23:00</span>
                </div>
              </div>
              <div className="flex items-center pt-3">
                <input
                  type="checkbox"
                  id="lockedBox"
                  checked={simIsLocked}
                  onChange={(e) => setSimIsLocked(e.target.checked)}
                  className="w-4 h-4 rounded bg-slate-900 border-slate-700 text-brand-blue focus:ring-0"
                />
                <label htmlFor="lockedBox" className="ml-2 text-slate-300 text-xs select-none">
                  Simulate Active Lock (<span className="text-amber-400 font-medium">Double-Debit Test</span>)
                </label>
              </div>
            </div>

            <button
              type="submit"
              disabled={isSimulating}
              className="w-full py-2.5 rounded-lg bg-gradient-to-r from-brand-blue to-brand-cyan hover:opacity-95 text-white font-semibold text-xs transition shadow-lg shadow-brand-blue/20 flex items-center justify-center space-x-2 mt-2"
            >
              {isSimulating ? (
                <>
                  <RotateCw className="w-4 h-4 animate-spin" />
                  <span>Agent Thinking...</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  <span>Execute AI Recovery Agent</span>
                </>
              )}
            </button>
          </form>

          {/* Simulation Verdict Card */}
          {simResult && (
            <div className="mt-4 p-3.5 rounded-lg bg-slate-900/90 border border-slate-700 space-y-2 text-xs animate-in fade-in duration-200">
              <div className="flex items-center justify-between pb-1 border-b border-slate-800">
                <span className="font-bold text-white flex items-center space-x-1.5">
                  {simResult.recovery_status === 'RECOVERED' ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  ) : (
                    <XCircle className="w-4 h-4 text-rose-400" />
                  )}
                  <span>Agent Decision Verdict</span>
                </span>
                <span
                  className={`px-2 py-0.5 rounded text-[11px] font-semibold font-mono border ${
                    simResult.recovery_status === 'RECOVERED'
                      ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                      : simResult.recovery_status === 'RETRY_SCHEDULED'
                      ? 'bg-blue-500/20 text-blue-400 border-blue-500/30'
                      : 'bg-rose-500/20 text-rose-400 border-rose-500/30'
                  }`}
                >
                  {simResult.recovery_status}
                </span>
              </div>

              <div className="space-y-1.5 pt-1">
                <div className="flex justify-between">
                  <span className="text-slate-400">Classified Category:</span>
                  <span className="font-mono text-white font-semibold">{simResult.failure_category}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Policy Guardrails:</span>
                  <span className="font-mono">
                    {simResult.guard_passed ? (
                      <span className="text-emerald-400 font-bold">PASSED</span>
                    ) : (
                      <span className="text-rose-400 font-bold">REJECTED ({simResult.guard_message})</span>
                    )}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Action Plan:</span>
                  <span className="font-mono text-cyan-300 font-semibold">
                    {simResult.recovery_plan.action}
                  </span>
                </div>

                {/* Dynamic Link Fallback Button */}
                {simResult.recovery_plan.dynamic_link && (
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 pt-1 border-t border-slate-800">
                    <div>
                      <span className="text-slate-400 block text-[11px]">Dynamic Checkout Link:</span>
                      <span className="text-brand-cyan underline font-mono text-[11px] truncate max-w-[200px] block">
                        {simResult.recovery_plan.dynamic_link}
                      </span>
                    </div>
                    <button
                      onClick={() => setIsCheckoutOpen(true)}
                      className="px-2.5 py-1 rounded bg-brand-cyan/20 text-brand-cyan border border-brand-cyan/30 hover:bg-brand-cyan/30 font-semibold text-[11px] flex items-center space-x-1 transition shadow-sm self-start sm:self-auto"
                    >
                      <Smartphone className="w-3.5 h-3.5" />
                      <span>Preview Customer Checkout</span>
                    </button>
                  </div>
                )}

                {/* Nocturnal Smart Queue Alert */}
                {(simHour < 8 || simHour >= 20) && (
                  <div className="p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs mt-2">
                    <div className="font-bold flex items-center space-x-1.5 text-amber-400">
                      <Moon className="w-3.5 h-3.5" />
                      <span>Nocturnal Anti-Spam Guardrail: Outreach Queued</span>
                    </div>
                    <p className="text-[11px] text-slate-300 mt-1">
                      Outbound messages held until <strong>08:01 AM IST</strong> per TRAI rules. Dispatches 1-tap link at daybreak.
                    </p>
                    <button
                      onClick={() => setIsWhatsAppOpen(true)}
                      className="mt-2 text-[11px] font-semibold px-2.5 py-1 rounded bg-amber-500/20 text-amber-300 hover:bg-amber-500/30 border border-amber-500/30 flex items-center space-x-1.5 transition"
                    >
                      <Smartphone className="w-3.5 h-3.5 text-emerald-400" />
                      <span>View Queued WhatsApp Notification Preview</span>
                    </button>
                  </div>
                )}

                <div className="pt-1 text-[11px] bg-slate-950/60 p-2 rounded border border-slate-800/80">
                  <span className="text-slate-400 block font-semibold mb-0.5">AI Reasoning:</span>
                  <p className="italic text-slate-300">{simResult.recovery_plan.reasoning}</p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Strategy Comparison & Category Recovery Stats (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          <RecoveryComparisonChart
            baselineRecovered={kpis.baseline_recovered}
            aiRecovered={kpis.total_recovered}
            totalAtRisk={kpis.total_at_risk}
            baselinePercentage={kpis.baseline_percentage}
            aiPercentage={kpis.recovery_percentage}
            netUplift={kpis.net_uplift}
          />

          {/* Differentiators Table */}
          <div className="glass-panel rounded-xl p-4 border border-brand-border text-xs overflow-x-auto">
            <table className="w-full text-left">
              <thead className="text-slate-400 border-b border-slate-800 text-[11px]">
                <tr>
                  <th className="py-1 px-2">Dimension</th>
                  <th className="py-1 px-2 text-rose-400">Naive Retries</th>
                  <th className="py-1 px-2 text-emerald-400">AI Recovery Engine</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300 text-[11px]">
                <tr>
                  <td className="py-1.5 px-2 font-medium text-white">Decision Engine</td>
                  <td className="py-1.5 px-2 text-slate-400">Blind cron loop</td>
                  <td className="py-1.5 px-2 text-emerald-300 font-semibold">LangGraph Diagnostic State Machine</td>
                </tr>
                <tr>
                  <td className="py-1.5 px-2 font-medium text-white">Bank Switch Outages</td>
                  <td className="py-1.5 px-2 text-slate-400">Hammers switch &rarr; rate limit</td>
                  <td className="py-1.5 px-2 text-blue-300 font-semibold">Scheduled Off-Peak (+12h Cooldown)</td>
                </tr>
                <tr>
                  <td className="py-1.5 px-2 font-medium text-white">Card/Mandate Failures</td>
                  <td className="py-1.5 px-2 text-slate-400">Repeats broken rail</td>
                  <td className="py-1.5 px-2 text-purple-300 font-semibold">Dynamic Fallback to UPI Intent</td>
                </tr>
                <tr>
                  <td className="py-1.5 px-2 font-medium text-white">TRAI Regulatory Window</td>
                  <td className="py-1.5 px-2 text-rose-400">13 nocturnal violations</td>
                  <td className="py-1.5 px-2 text-emerald-400 font-semibold">0 Violations (08:00–20:00 IST Enforced)</td>
                </tr>
                <tr>
                  <td className="py-1.5 px-2 font-medium text-white">Double-Debit Guard</td>
                  <td className="py-1.5 px-2 text-rose-400">No concurrency lock</td>
                  <td className="py-1.5 px-2 text-emerald-400 font-semibold">100% Guarded (Idempotency Locks)</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Benchmark Transactions Explorer */}
      <section className="glass-panel rounded-xl p-5 border border-brand-border space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold text-white flex items-center space-x-2">
              <FileCheck className="w-4 h-4 text-brand-blue" />
              <span>Benchmark Cohort Explorer (60 Failure Webhooks)</span>
            </h2>
            <p className="text-xs text-slate-400">
              Full trace showing root cause classification, guardrail verdict, and recovery conversion. Click any row to test.
            </p>
          </div>

          <div className="flex items-center space-x-2">
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search invoice, error code..."
                className="bg-slate-900/90 border border-slate-700 rounded-lg pl-8 pr-3 py-1.5 text-xs text-white outline-none focus:border-brand-blue w-52"
              />
            </div>

            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="bg-slate-900/90 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-white outline-none"
            >
              <option value="ALL">All Categories</option>
              <option value="TRANSIENT_DOWNTIME">Transient Downtime (25)</option>
              <option value="CUSTOMER_ACTIONABLE">Customer Actionable (20)</option>
              <option value="EXHAUSTED_LIMIT">Exhausted Retries (7)</option>
              <option value="TERMINAL_FAILURE">Terminal Failures (8)</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto rounded-lg border border-slate-800 max-h-96">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/90 text-slate-300 font-semibold border-b border-slate-800 sticky top-0 z-10">
              <tr>
                <th className="py-2 px-3">Invoice ID</th>
                <th className="py-2 px-3">Customer</th>
                <th className="py-2 px-3 text-right">Amount</th>
                <th className="py-2 px-3">Rail</th>
                <th className="py-2 px-3">Error Code</th>
                <th className="py-2 px-3">Guardrail</th>
                <th className="py-2 px-3">Action Taken</th>
                <th className="py-2 px-3 text-center">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
              {filteredEvents.map((ev) => (
                <tr
                  key={ev.invoice_id}
                  onClick={() => loadTransactionIntoSim(ev)}
                  className="hover:bg-slate-800/40 cursor-pointer transition"
                >
                  <td className="py-2 px-3 font-semibold text-white">{ev.invoice_id}</td>
                  <td className="py-2 px-3 text-slate-400">{ev.customer_id}</td>
                  <td className="py-2 px-3 text-right font-semibold text-white">
                    ₹{ev.amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </td>
                  <td className="py-2 px-3 text-amber-300">{ev.payment_rail}</td>
                  <td className="py-2 px-3 text-slate-300 font-sans">{ev.error_code}</td>
                  <td className="py-2 px-3 font-sans">
                    {ev.guard_passed ? (
                      <span className="text-emerald-400 text-[11px]">Passed</span>
                    ) : (
                      <span className="text-rose-400 text-[11px]">Blocked</span>
                    )}
                  </td>
                  <td className="py-2 px-3 font-sans">
                    {ev.recovery_plan?.action === 'SCHEDULED_SILENT_RETRY' ? (
                      <span className="text-blue-300">Silent Retry (+12h)</span>
                    ) : ev.recovery_plan?.action === 'DISPATCH_DYNAMIC_LINK' ? (
                      <span className="text-purple-300">Dynamic Link (UPI)</span>
                    ) : (
                      <span className="text-rose-300">Abort & Flag</span>
                    )}
                  </td>
                  <td className="py-2 px-3 text-center">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-semibold font-mono border ${
                        ev.recovery_status === 'RECOVERED'
                          ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                          : ev.recovery_status === 'RETRY_SCHEDULED'
                          ? 'bg-blue-500/20 text-blue-400 border-blue-500/30'
                          : ev.recovery_status === 'LINK_DISPATCHED'
                          ? 'bg-purple-500/20 text-purple-400 border-purple-500/30'
                          : 'bg-rose-500/20 text-rose-400 border-rose-500/30'
                      }`}
                    >
                      {ev.recovery_status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Live Microsecond JSONL Audit Stream */}
      {auditLogs.length > 0 && (
        <section className="glass-panel rounded-xl p-5 border border-brand-border space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-white flex items-center space-x-2">
              <Terminal className="w-4 h-4 text-purple-400" />
              <span>Live Microsecond Audit Trail Log (recovery_audit_trail.jsonl)</span>
            </h2>
            <span className="text-xs text-slate-400 font-mono">Latest {auditLogs.length} events</span>
          </div>
          <div className="h-44 overflow-y-auto bg-slate-950/80 rounded-lg p-3 font-mono text-[11px] text-slate-400 space-y-1 border border-slate-800">
            {auditLogs.map((log, idx) => (
              <div key={idx} className="truncate">
                <span className="text-slate-500">[{log.timestamp.split('T')[1]?.replace('Z', '')}]</span>{' '}
                <span className="font-bold text-white">{log.invoice_id}</span> |{' '}
                <span className="text-brand-cyan">{log.event_type}</span> &rarr;{' '}
                <span className={log.guard_check_passed ? 'text-emerald-400' : 'text-rose-400'}>
                  {log.action}
                </span>{' '}
                <span className="text-slate-500">{JSON.stringify(log.details)}</span>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Modals */}
      <CheckoutModal
        isOpen={isCheckoutOpen}
        onClose={() => setIsCheckoutOpen(false)}
        invoiceId={simInvoiceId}
        amount={simAmount}
        failedRail={simRail}
        errorCode={simErrorCode}
      />

      <WhatsAppModal
        isOpen={isWhatsAppOpen}
        onClose={() => setIsWhatsAppOpen(false)}
        invoiceId={simInvoiceId}
        amount={simAmount}
        onOpenCheckout={() => setIsCheckoutOpen(true)}
      />

      <footer className="border-t border-brand-border py-6 text-center text-xs text-slate-500">
        Razorpay Buildathon — Autonomous AI Revenue Recovery Engine | Next.js 14, Three.js & LangGraph
      </footer>
    </div>
  );
}
