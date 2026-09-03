'use client';

import React from 'react';
import { TrendingUp, ArrowUpRight, ShieldCheck, AlertCircle } from 'lucide-react';

interface RecoveryComparisonChartProps {
  baselineRecovered: number;
  aiRecovered: number;
  totalAtRisk: number;
  baselinePercentage: number;
  aiPercentage: number;
  netUplift: number;
}

export default function RecoveryComparisonChart({
  baselineRecovered = 16700,
  aiRecovered = 162300,
  totalAtRisk = 262800,
  baselinePercentage = 6.4,
  aiPercentage = 61.8,
  netUplift = 145600,
}: RecoveryComparisonChartProps) {
  // Max scale for vertical bars
  const maxScale = Math.max(aiRecovered * 1.15, 180000);
  const baselineHeightPct = Math.max(8, (baselineRecovered / maxScale) * 100);
  const aiHeightPct = (aiRecovered / maxScale) * 100;

  return (
    <div className="space-y-4">
      {/* Visual Comparative 2D Bar Graph */}
      <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800">
        <div className="flex items-center justify-between mb-4">
          <div>
            <span className="text-xs font-bold text-white uppercase tracking-wider flex items-center space-x-1.5">
              <TrendingUp className="w-4 h-4 text-emerald-400" />
              <span>2D Financial Recovery Comparison</span>
            </span>
            <span className="text-[11px] text-slate-400">
              Recovered Capital: Naive Dunning vs. Autonomous AI Engine
            </span>
          </div>
          <div className="flex items-center space-x-1 text-xs font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1 rounded-lg">
            <ArrowUpRight className="w-3.5 h-3.5" />
            <span>+₹{netUplift.toLocaleString('en-IN', { minimumFractionDigits: 2 })} Uplift</span>
          </div>
        </div>

        {/* 2D Bar Columns */}
        <div className="h-52 w-full flex items-end justify-around gap-6 pt-6 pb-2 px-4 border-b border-slate-800 relative">
          {/* Y-axis grid guide lines */}
          <div className="absolute inset-0 flex flex-col justify-between pointer-events-none opacity-20">
            <div className="border-b border-dashed border-slate-500 w-full" />
            <div className="border-b border-dashed border-slate-500 w-full" />
            <div className="border-b border-dashed border-slate-500 w-full" />
          </div>

          {/* Bar 1: Baseline Naive Retries */}
          <div className="flex-1 max-w-[140px] flex flex-col items-center h-full justify-end z-10">
            <div className="text-[11px] font-mono font-bold text-rose-400 mb-1.5 text-center">
              ₹{baselineRecovered.toLocaleString('en-IN')}
              <span className="block text-[10px] text-rose-400/80 font-sans">({baselinePercentage}%)</span>
            </div>
            <div
              style={{ height: `${baselineHeightPct}%` }}
              className="w-full rounded-t-lg bg-gradient-to-t from-rose-600/60 to-rose-500 border border-rose-500/80 transition-all duration-700 hover:brightness-125 shadow-lg shadow-rose-600/20 relative group"
            >
              <div className="opacity-0 group-hover:opacity-100 absolute -top-8 left-1/2 -translate-x-1/2 bg-slate-900 text-white text-[10px] px-2 py-0.5 rounded border border-slate-700 whitespace-nowrap transition pointer-events-none">
                13 TRAI Violations
              </div>
            </div>
            <span className="text-[11px] font-semibold text-slate-400 mt-2 text-center">
              Naive Retries
            </span>
          </div>

          {/* Bar 2: Autonomous AI Recovery Agent */}
          <div className="flex-1 max-w-[140px] flex flex-col items-center h-full justify-end z-10">
            <div className="text-[11px] font-mono font-bold text-emerald-400 mb-1.5 text-center">
              ₹{aiRecovered.toLocaleString('en-IN')}
              <span className="block text-[10px] text-emerald-400/80 font-sans">({aiPercentage}%)</span>
            </div>
            <div
              style={{ height: `${aiHeightPct}%` }}
              className="w-full rounded-t-lg bg-gradient-to-t from-emerald-600/70 to-emerald-400 border border-emerald-400 transition-all duration-700 hover:brightness-125 shadow-xl shadow-emerald-500/30 relative group"
            >
              <div className="opacity-0 group-hover:opacity-100 absolute -top-8 left-1/2 -translate-x-1/2 bg-slate-900 text-white text-[10px] px-2 py-0.5 rounded border border-slate-700 whitespace-nowrap transition pointer-events-none">
                0 Violations | 0 Double Debits
              </div>
            </div>
            <span className="text-[11px] font-semibold text-emerald-400 mt-2 text-center flex items-center space-x-1">
              <span>AI Engine</span>
              <ShieldCheck className="w-3 h-3" />
            </span>
          </div>
        </div>

        {/* Legend */}
        <div className="flex items-center justify-between text-[11px] text-slate-400 pt-3">
          <div className="flex items-center space-x-4">
            <span className="flex items-center space-x-1.5">
              <span className="w-2.5 h-2.5 rounded-sm bg-rose-500" />
              <span>Naive Blind Retries (6.4%)</span>
            </span>
            <span className="flex items-center space-x-1.5">
              <span className="w-2.5 h-2.5 rounded-sm bg-emerald-400" />
              <span className="text-emerald-300 font-medium">Autonomous AI Agent (61.8%)</span>
            </span>
          </div>
          <span className="font-mono text-slate-300">Cohort: 60 Invoices</span>
        </div>
      </div>

      {/* 2D Horizontal Visual Category Progress Graphs */}
      <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-3">
        <span className="text-xs font-bold text-white uppercase tracking-wider block">
          Recovery Rate by Failure Cohort
        </span>

        {/* Cohort 1: Transient */}
        <div className="space-y-1">
          <div className="flex justify-between text-xs">
            <span className="text-slate-300">Transient Outages (Bank CBS / Switch Timeout)</span>
            <span className="font-mono font-bold text-emerald-400">89.8% (₹93,700)</span>
          </div>
          <div className="w-full h-2.5 rounded-full bg-slate-900 overflow-hidden border border-slate-800">
            <div className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-teal-400 transition-all duration-700" style={{ width: '89.8%' }} />
          </div>
          <span className="text-[10px] text-slate-500">25 Invoices &bull; Scheduled Silent Retry (+12h Cooldown)</span>
        </div>

        {/* Cohort 2: Customer Actionable */}
        <div className="space-y-1 pt-1">
          <div className="flex justify-between text-xs">
            <span className="text-slate-300">Customer Actionable (Card Depleted / Mandate Expired)</span>
            <span className="font-mono font-bold text-purple-400">59.0% (₹68,600)</span>
          </div>
          <div className="w-full h-2.5 rounded-full bg-slate-900 overflow-hidden border border-slate-800">
            <div className="h-full rounded-full bg-gradient-to-r from-purple-500 to-indigo-400 transition-all duration-700" style={{ width: '59.0%' }} />
          </div>
          <span className="text-[10px] text-slate-500">20 Invoices &bull; Dynamic Multi-Rail Link (UPI Intent Fallback)</span>
        </div>

        {/* Cohort 3: Exhausted Limits */}
        <div className="space-y-1 pt-1">
          <div className="flex justify-between text-xs">
            <span className="text-slate-300">Exhausted Retries (Attempt Count &ge; 2)</span>
            <span className="font-mono font-bold text-amber-400">0.0% (100% Guarded)</span>
          </div>
          <div className="w-full h-2.5 rounded-full bg-slate-900 overflow-hidden border border-slate-800">
            <div className="h-full rounded-full bg-amber-500 transition-all duration-700" style={{ width: '0%' }} />
          </div>
          <span className="text-[10px] text-slate-500">7 Invoices &bull; Hard Stopping Rule Enforced (0 Gateway Fees Burned)</span>
        </div>

        {/* Cohort 4: Terminal */}
        <div className="space-y-1 pt-1">
          <div className="flex justify-between text-xs">
            <span className="text-slate-300">Terminal Failures (Account Closed / Fraud)</span>
            <span className="font-mono font-bold text-rose-400">0.0% (100% Dropped)</span>
          </div>
          <div className="w-full h-2.5 rounded-full bg-slate-900 overflow-hidden border border-slate-800">
            <div className="h-full rounded-full bg-rose-500 transition-all duration-700" style={{ width: '0%' }} />
          </div>
          <span className="text-[10px] text-slate-500">8 Invoices &bull; Graceful Abort (Zero Risk Score Penalty)</span>
        </div>
      </div>
    </div>
  );
}
