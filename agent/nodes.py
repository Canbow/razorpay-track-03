"""LangGraph nodes executing deterministic 3-way reconciliation and invariant checks."""
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List

from core.models import (
    AuditLogEntry,
    BankStatementEntry,
    InternalOrder,
    RazorpaySettlement,
    ReconciliationResult,
    ReconciliationStatus,
)
from core.rules import (
    check_fee_overcharge,
    quantize_currency,
    verify_accounting_equation,
)
from agent.state import ReconciliationState


def ingest_node(state: ReconciliationState) -> Dict[str, Any]:
    """Ingest raw batches and build O(1) indexed lookup tables."""
    raw_orders = state.get("raw_orders", [])
    raw_settlements = state.get("raw_settlements", [])
    raw_bank_entries = state.get("raw_bank_entries", [])

    indexed_orders: Dict[str, Dict[str, Any]] = {}
    for ord_dict in raw_orders:
        indexed_orders[ord_dict["order_id"]] = ord_dict

    indexed_settlements_by_order: Dict[str, Dict[str, Any]] = {}
    for stl_dict in raw_settlements:
        indexed_settlements_by_order[stl_dict["order_id"]] = stl_dict

    indexed_bank_by_utr: Dict[str, Dict[str, Any]] = {}
    for bnk_dict in raw_bank_entries:
        if bnk_dict.get("utr"):
            indexed_bank_by_utr[bnk_dict["utr"]] = bnk_dict

    audit_entry = AuditLogEntry(
        timestamp=datetime.now(timezone.utc).isoformat(),
        order_id="SYSTEM_INGEST",
        step="ingest_node",
        action_taken="INGEST_AND_INDEX_BATCH",
        math_verified=True,
        details={
            "orders_count": len(indexed_orders),
            "settlements_count": len(indexed_settlements_by_order),
            "bank_entries_count": len(indexed_bank_by_utr),
        },
    ).model_dump()

    return {
        "indexed_orders": indexed_orders,
        "indexed_settlements_by_order": indexed_settlements_by_order,
        "indexed_bank_by_utr": indexed_bank_by_utr,
        "audit_trail": [audit_entry],
    }


def match_exact_node(state: ReconciliationState) -> Dict[str, Any]:
    """
    Evaluate 3-way matching rules, check MDR overcharges, and enforce accounting invariants.
    """
    indexed_orders = state.get("indexed_orders", {})
    indexed_settlements = state.get("indexed_settlements_by_order", {})
    indexed_bank = state.get("indexed_bank_by_utr", {})

    reconciled_records: List[Dict[str, Any]] = []
    exceptions_list: List[Dict[str, Any]] = []
    audit_trail: List[Dict[str, Any]] = []

    for order_id, ord_dict in indexed_orders.items():
        order = InternalOrder(**ord_dict)
        now_ts = datetime.now(timezone.utc).isoformat()

        # Step 1: Check if Gateway Settlement exists
        settlement_dict = indexed_settlements.get(order_id)
        if not settlement_dict:
            res = ReconciliationResult(
                order_id=order_id,
                status=ReconciliationStatus.MISSING_GATEWAY_RECORD,
                order_amount=order.amount,
                gross_amount=None,
                net_settlement=None,
                bank_credit=None,
                discrepancy_reason="Order marked PAID in database, but missing in Razorpay settlement dump.",
                action_required="Initiate gateway payment verification API inquiry / check capture status.",
            )
            audit = AuditLogEntry(
                timestamp=now_ts,
                order_id=order_id,
                step="match_exact_node",
                action_taken="FLAG_MISSING_GATEWAY_RECORD",
                math_verified=False,
                details={
                    "order_amount": str(order.amount),
                    "status": "MISSING_GATEWAY_RECORD",
                },
            )
            res.audit_events.append(audit)
            exceptions_list.append(res.model_dump())
            audit_trail.append(audit.model_dump())
            continue

        settlement = RazorpaySettlement(**settlement_dict)

        # Step 2: Check if Bank Statement Entry exists for the settlement UTR
        utr = settlement.utr
        bank_dict = indexed_bank.get(utr) if utr else None
        if not bank_dict:
            res = ReconciliationResult(
                order_id=order_id,
                status=ReconciliationStatus.UNSETTLED_BY_BANK,
                order_amount=order.amount,
                gross_amount=settlement.gross_amount,
                net_settlement=settlement.net_amount,
                bank_credit=None,
                fee_charged=settlement.fee + settlement.tax_on_fee,
                utr=utr,
                discrepancy_reason=f"Settled by gateway with UTR {utr}, but missing in bank statement credits.",
                action_required=f"Query bank via UTR {utr} or trigger payout inquiry ticket with Razorpay.",
            )
            audit = AuditLogEntry(
                timestamp=now_ts,
                order_id=order_id,
                step="match_exact_node",
                action_taken="FLAG_UNSETTLED_IN_BANK",
                math_verified=False,
                details={
                    "order_amount": str(order.amount),
                    "net_settlement": str(settlement.net_amount),
                    "utr": utr,
                    "status": "UNSETTLED_BY_BANK",
                },
            )
            res.audit_events.append(audit)
            exceptions_list.append(res.model_dump())
            audit_trail.append(audit.model_dump())
            continue

        bank_entry = BankStatementEntry(**bank_dict)

        # Step 3: Verify Accounting Equation
        eq_valid, eq_msg = verify_accounting_equation(order, settlement, bank_entry)
        if not eq_valid:
            res = ReconciliationResult(
                order_id=order_id,
                status=ReconciliationStatus.UNRESOLVED_EXCEPTION,
                order_amount=order.amount,
                gross_amount=settlement.gross_amount,
                net_settlement=settlement.net_amount,
                bank_credit=bank_entry.credit_amount,
                fee_charged=settlement.fee + settlement.tax_on_fee,
                utr=utr,
                discrepancy_reason=eq_msg,
                action_required="Escalate to finance engineering for accounting equation breach.",
            )
            audit = AuditLogEntry(
                timestamp=now_ts,
                order_id=order_id,
                step="match_exact_node",
                action_taken="FLAG_ACCOUNTING_EQUATION_BREACH",
                math_verified=False,
                details={
                    "reason": eq_msg,
                    "order_amount": str(order.amount),
                    "gross_amount": str(settlement.gross_amount),
                    "net_amount": str(settlement.net_amount),
                    "bank_credit": str(bank_entry.credit_amount),
                },
            )
            res.audit_events.append(audit)
            exceptions_list.append(res.model_dump())
            audit_trail.append(audit.model_dump())
            continue

        # Step 4: Check Fee Overcharge (MDR + GST verification)
        is_overcharged, fee_delta, expected_total, actual_total = check_fee_overcharge(settlement)
        if is_overcharged:
            res = ReconciliationResult(
                order_id=order_id,
                status=ReconciliationStatus.FEE_DISCREPANCY,
                order_amount=order.amount,
                gross_amount=settlement.gross_amount,
                net_settlement=settlement.net_amount,
                bank_credit=bank_entry.credit_amount,
                fee_charged=actual_total,
                expected_fee=expected_total,
                fee_delta=fee_delta,
                utr=utr,
                discrepancy_reason=(
                    f"Gateway Fee Overcharge: Charged INR {actual_total} vs contracted INR {expected_total} "
                    f"(Overcharge Delta: INR {fee_delta})"
                ),
                action_required=f"Auto-draft dispute ticket to Razorpay for MDR fee reversal of INR {fee_delta}.",
            )
            audit = AuditLogEntry(
                timestamp=now_ts,
                order_id=order_id,
                step="match_exact_node",
                action_taken="FLAG_FEE_OVERCHARGE_DISCREPANCY",
                math_verified=True,
                details={
                    "expected_fee": str(expected_total),
                    "actual_fee": str(actual_total),
                    "fee_delta": str(fee_delta),
                    "status": "FEE_DISCREPANCY",
                },
            )
            res.audit_events.append(audit)
            exceptions_list.append(res.model_dump())
            audit_trail.append(audit.model_dump())
            continue

        # Step 5: Clean Exact 3-Way Match
        res = ReconciliationResult(
            order_id=order_id,
            status=ReconciliationStatus.FULLY_RECONCILED,
            order_amount=order.amount,
            gross_amount=settlement.gross_amount,
            net_settlement=settlement.net_amount,
            bank_credit=bank_entry.credit_amount,
            fee_charged=actual_total,
            expected_fee=expected_total,
            fee_delta=Decimal("0.00"),
            utr=utr,
            discrepancy_reason=None,
            action_required="None. Balanced & verified 3-way match.",
        )
        audit = AuditLogEntry(
            timestamp=now_ts,
            order_id=order_id,
            step="match_exact_node",
            action_taken="APPROVE_3WAY_MATCH",
            math_verified=True,
            details={
                "order_amount": str(order.amount),
                "net_settled": str(settlement.net_amount),
                "bank_credit": str(bank_entry.credit_amount),
                "fee_verified": str(actual_total),
            },
        )
        res.audit_events.append(audit)
        reconciled_records.append(res.model_dump())
        audit_trail.append(audit.model_dump())

    return {
        "reconciled_records": reconciled_records,
        "exceptions_list": exceptions_list,
        "audit_trail": audit_trail,
    }


def synthesize_metrics_node(state: ReconciliationState) -> Dict[str, Any]:
    """Aggregate KPI metrics, risk exposure, and summary statistics."""
    reconciled = state.get("reconciled_records", [])
    exceptions = state.get("exceptions_list", [])

    total_records = len(reconciled) + len(exceptions)
    match_rate = (len(reconciled) / total_records * 100.0) if total_records > 0 else 0.0
    exception_rate = (len(exceptions) / total_records * 100.0) if total_records > 0 else 0.0

    total_volume = Decimal("0.00")
    total_amount_at_risk = Decimal("0.00")
    total_fee_overcharge = Decimal("0.00")

    status_counts: Dict[str, int] = {
        ReconciliationStatus.FULLY_RECONCILED.value: len(reconciled),
        ReconciliationStatus.FEE_DISCREPANCY.value: 0,
        ReconciliationStatus.UNSETTLED_BY_BANK.value: 0,
        ReconciliationStatus.MISSING_GATEWAY_RECORD.value: 0,
        ReconciliationStatus.UNRESOLVED_EXCEPTION.value: 0,
    }

    for rec in reconciled:
        amt = Decimal(str(rec.get("order_amount") or 0))
        total_volume += amt

    for exc in exceptions:
        amt = Decimal(str(exc.get("order_amount") or 0))
        total_volume += amt
        st = exc.get("status")
        if st in status_counts:
            status_counts[st] += 1

        if st in (ReconciliationStatus.UNSETTLED_BY_BANK.value, ReconciliationStatus.MISSING_GATEWAY_RECORD.value, ReconciliationStatus.UNRESOLVED_EXCEPTION.value):
            total_amount_at_risk += amt
        elif st == ReconciliationStatus.FEE_DISCREPANCY.value:
            delta = Decimal(str(exc.get("fee_delta") or 0))
            total_fee_overcharge += delta

    summary_metrics = {
        "total_records": total_records,
        "total_reconciled": len(reconciled),
        "total_exceptions": len(exceptions),
        "match_rate_pct": round(match_rate, 2),
        "exception_rate_pct": round(exception_rate, 2),
        "total_volume_processed": str(quantize_currency(total_volume)),
        "total_amount_at_risk": str(quantize_currency(total_amount_at_risk)),
        "total_fee_overcharges_recoverable": str(quantize_currency(total_fee_overcharge)),
        "status_breakdown": status_counts,
    }

    summary_audit = AuditLogEntry(
        timestamp=datetime.now(timezone.utc).isoformat(),
        order_id="SYSTEM_SUMMARY",
        step="synthesize_metrics_node",
        action_taken="AGGREGATE_METRICS",
        math_verified=True,
        details=summary_metrics,
    ).model_dump()

    return {
        "summary_metrics": summary_metrics,
        "audit_trail": [summary_audit],
    }
