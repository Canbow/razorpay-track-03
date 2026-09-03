'use client';

import React from 'react';
import { X, CheckCircle, Shield, Bolt } from 'lucide-react';

interface WhatsAppModalProps {
  isOpen: boolean;
  onClose: () => void;
  invoiceId: string;
  amount: number;
  onOpenCheckout?: () => void;
}

export default function WhatsAppModal({
  isOpen,
  onClose,
  invoiceId,
  amount,
  onOpenCheckout,
}: WhatsAppModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-700 w-full max-w-sm rounded-2xl overflow-hidden shadow-2xl relative font-sans animate-in fade-in zoom-in-95 duration-200">
        {/* WhatsApp Header */}
        <div className="bg-[#075E54] p-3 text-white flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="w-9 h-9 rounded-full bg-white/20 flex items-center justify-center font-bold text-white text-base">
              R
            </div>
            <div>
              <div className="font-bold text-xs flex items-center space-x-1">
                <span>Razorpay Payments</span>
                <CheckCircle className="w-3.5 h-3.5 text-cyan-300" />
              </div>
              <div className="text-[10px] text-emerald-100">Official Verified Business</div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-6 h-6 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center text-white transition"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Chat Body */}
        <div className="p-4 bg-[#0B141A] space-y-3 min-h-[260px] flex flex-col justify-end text-xs">
          <div className="text-center">
            <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">
              TODAY, 08:01 AM (TRAI Compliant Delivery)
            </span>
          </div>

          <div className="p-3 rounded-xl rounded-tl-none bg-[#202C33] text-slate-100 space-y-2 border border-slate-800 shadow-md">
            <p>
              Hello Priya! 👋<br />
              Your monthly subscription renewal of{' '}
              <strong className="text-emerald-400 font-mono">
                ₹{amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </strong>{' '}
              for invoice <strong className="font-mono text-cyan-300">{invoiceId}</strong> could not be cleared last night due to bank account balance.
            </p>
            <p className="text-[11px] text-slate-300">
              To avoid service pause, authorize your renewal in 1-tap via your preferred UPI app:
            </p>

            <div className="pt-1 border-t border-slate-700/80">
              <button
                onClick={() => {
                  onClose();
                  if (onOpenCheckout) onOpenCheckout();
                }}
                className="w-full py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs flex items-center justify-center space-x-1.5 transition shadow-sm"
              >
                <Bolt className="w-3.5 h-3.5 text-yellow-300" />
                <span>Pay via UPI Intent in 1-Tap</span>
              </button>
            </div>
            <div className="text-[9px] text-right text-slate-400">08:01 AM ✓✓</div>
          </div>
        </div>

        {/* Footer info note */}
        <div className="p-3 bg-slate-900 border-t border-slate-800 text-[10px] text-center text-slate-400 flex items-center justify-center space-x-1">
          <Shield className="w-3.5 h-3.5 text-emerald-400" />
          <span>Outbound notification queued overnight; dispatched at 08:01 AM IST.</span>
        </div>
      </div>
    </div>
  );
}
