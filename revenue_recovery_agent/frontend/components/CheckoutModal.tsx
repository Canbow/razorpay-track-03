'use client';

import React, { useState } from 'react';
import { X, Check, Bolt, Lock, AlertTriangle, QrCode, Smartphone, Wallet } from 'lucide-react';

interface CheckoutModalProps {
  isOpen: boolean;
  onClose: () => void;
  invoiceId: string;
  amount: number;
  failedRail: string;
  errorCode: string;
  onPaymentSuccess?: () => void;
}

export default function CheckoutModal({
  isOpen,
  onClose,
  invoiceId,
  amount,
  failedRail,
  errorCode,
  onPaymentSuccess,
}: CheckoutModalProps) {
  const [isPaid, setIsPaid] = useState(false);

  if (!isOpen) return null;

  const handlePay = () => {
    setIsPaid(true);
    if (onPaymentSuccess) {
      onPaymentSuccess();
    }
  };

  const handleResetAndClose = () => {
    setIsPaid(false);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-700 w-full max-w-md rounded-2xl overflow-hidden shadow-2xl relative animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-700 to-cyan-600 p-4 text-white flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-white/20 flex items-center justify-center font-bold">
              <Bolt className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="font-bold text-sm">Razorpay Recovery Checkout</div>
              <div className="text-[11px] text-blue-100">Acme Cloud SaaS Subscriptions</div>
            </div>
          </div>
          <button
            onClick={handleResetAndClose}
            className="w-7 h-7 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center text-white transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        {!isPaid ? (
          <div className="p-5 space-y-4 text-xs">
            {/* Invoice Reference */}
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div>
                <span className="text-slate-400 block text-[11px]">Invoice Reference</span>
                <span className="font-mono font-bold text-white text-sm">{invoiceId}</span>
              </div>
              <div className="text-right">
                <span className="text-slate-400 block text-[11px]">Total Due</span>
                <span className="font-mono font-bold text-emerald-400 text-lg">
                  ₹{amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                </span>
              </div>
            </div>

            {/* Failure notice */}
            <div className="p-2.5 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300">
              <div className="font-semibold flex items-center space-x-1.5 text-[11px]">
                <AlertTriangle className="w-3.5 h-3.5" />
                <span>Earlier Attempt Failed</span>
              </div>
              <p className="text-[11px] text-slate-300 mt-0.5">
                Your prior debit on <strong className="text-white">{failedRail}</strong> failed ({errorCode}).
              </p>
            </div>

            {/* AI Dynamic Multi-Rail Recommendation */}
            <div className="p-3 rounded-xl bg-brand-blue/10 border border-brand-cyan/30 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-brand-cyan flex items-center space-x-1.5 text-xs">
                  <Bolt className="w-3.5 h-3.5 text-amber-400" />
                  <span>AI Recommended Smart Fallback</span>
                </span>
                <span className="text-[10px] bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded font-mono">
                  1-TAP INTENT
                </span>
              </div>
              <p className="text-slate-300 text-[11px]">
                To bypass bank limits and keep your subscription active, authorize instantly via <strong>UPI Intent</strong>:
              </p>

              {/* UPI Options */}
              <div className="grid grid-cols-4 gap-2 pt-1">
                <button
                  type="button"
                  onClick={handlePay}
                  className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 flex flex-col items-center justify-center text-[10px] text-slate-300 transition hover:border-brand-cyan"
                >
                  <Smartphone className="w-4 h-4 text-blue-400 mb-1" />
                  <span>GPay</span>
                </button>
                <button
                  type="button"
                  onClick={handlePay}
                  className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 flex flex-col items-center justify-center text-[10px] text-slate-300 transition hover:border-brand-cyan"
                >
                  <Smartphone className="w-4 h-4 text-purple-400 mb-1" />
                  <span>PhonePe</span>
                </button>
                <button
                  type="button"
                  onClick={handlePay}
                  className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 flex flex-col items-center justify-center text-[10px] text-slate-300 transition hover:border-brand-cyan"
                >
                  <Wallet className="w-4 h-4 text-cyan-400 mb-1" />
                  <span>Paytm</span>
                </button>
                <button
                  type="button"
                  onClick={handlePay}
                  className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 flex flex-col items-center justify-center text-[10px] text-slate-300 transition hover:border-brand-cyan"
                >
                  <QrCode className="w-4 h-4 text-emerald-400 mb-1" />
                  <span>Scan QR</span>
                </button>
              </div>
            </div>

            {/* Pay Button */}
            <button
              onClick={handlePay}
              className="w-full py-3 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 hover:opacity-95 text-white font-bold text-xs tracking-wide transition shadow-lg shadow-emerald-500/20 flex items-center justify-center space-x-2"
            >
              <Check className="w-4 h-4" />
              <span>Complete Recovery via UPI Intent</span>
            </button>

            <div className="text-[10px] text-center text-slate-500 flex items-center justify-center space-x-1.5">
              <Lock className="w-3 h-3" />
              <span>Secured by Razorpay 256-bit PCI-DSS Compliance</span>
            </div>
          </div>
        ) : (
          /* Payment Cleared Success State */
          <div className="p-8 text-center space-y-4">
            <div className="w-16 h-16 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center justify-center text-3xl mx-auto animate-bounce">
              <Check className="w-8 h-8" />
            </div>
            <div>
              <h3 className="font-bold text-lg text-white">Payment Recovered Successfully!</h3>
              <p className="text-xs text-slate-300 mt-1">
                Transaction reconciled via UPI Intent. Subscription kept active with zero disruption.
              </p>
            </div>
            <div className="p-3 bg-slate-950/80 rounded-lg border border-slate-800 text-left font-mono text-[11px] text-slate-400 space-y-1">
              <div className="flex justify-between">
                <span>Recovery Status:</span>
                <span className="text-emerald-400 font-bold">RECOVERED</span>
              </div>
              <div className="flex justify-between">
                <span>Settlement Rail:</span>
                <span className="text-brand-cyan">UPI (NPCI Intent)</span>
              </div>
              <div className="flex justify-between">
                <span>Bank Payout UTR:</span>
                <span className="text-slate-200 font-mono">UTR-99281746201</span>
              </div>
            </div>
            <button
              onClick={handleResetAndClose}
              className="w-full py-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-semibold text-xs transition"
            >
              Return to Dashboard
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
