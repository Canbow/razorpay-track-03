"""LangGraph nodes for diagnosis, deterministic guardrails, and autonomous recovery execution."""
import hashlib
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional

from revenue_recovery_agent.core.models import (
    PaymentRail,
    FailureCategory,
    RecoveryAction,
    PaymentStatus,
    FailedPaymentEvent,
    RecoveryPlan,
)
from revenue_recovery_agent.core.policy import (
    MAX_RETRY_LIMIT,
    diagnose_failure,
    evaluate_guardrails,
)
from revenue_recovery_agent.audit.logger import AuditLogger

# Shared default audit logger instance
audit_logger = AuditLogger()


def simulate_recovery_conversion(invoice_id: str, action: RecoveryAction) -> bool:
    """
    Realistic Mock Recovery Simulator.
    Deterministic pseudo-random conversion based on invoice_id:
    - 85% recovery rate on transient downtime when retried.
    - 60% recovery rate on customer actionable dynamic payment links.
    - 0% recovery rate on terminal / exhausted attempts.
    """
    if action == RecoveryAction.ABORT_TERMINAL:
        return False

    # Seeded pseudo-random hash in [0, 99]
    h = int(hashlib.sha256(f"recover_seed_{invoice_id}".encode()).hexdigest(), 16) % 100
    if action == RecoveryAction.SCHEDULED_SILENT_RETRY:
        return h < 85
    elif action == RecoveryAction.DISPATCH_DYNAMIC_LINK:
        return h < 60
    return False


def diagnose_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates incoming error code and classifies failure root cause into:
    TRANSIENT_DOWNTIME, CUSTOMER_ACTIONABLE, or TERMINAL_FAILURE.
    """
    raw_event = state["event"]
    event = FailedPaymentEvent.model_validate(raw_event)
    category = diagnose_failure(event.error_code)

    audit_logger.log_event(
        invoice_id=event.invoice_id,
        event_type="DIAGNOSIS",
        action="DIAGNOSE_FAILURE",
        guard_check_passed=True,
        details={
            "error_code": event.error_code,
            "classified_category": category.value,
            "payment_rail": event.payment_rail.value,
        },
    )

    return {
        "failure_category": category.value,
    }


def policy_guard_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enforces deterministic stopping rules, TRAI/RBI communication hours,
    and checks idempotency locks to eliminate double-debit race conditions.
    """
    raw_event = state["event"]
    event = FailedPaymentEvent.model_validate(raw_event)
    category_str = state.get("failure_category", FailureCategory.CUSTOMER_ACTIONABLE.value)
    category = FailureCategory(category_str)

    # Determine proposed recovery action based on diagnosed failure category
    if category == FailureCategory.TRANSIENT_DOWNTIME:
        proposed_action = RecoveryAction.SCHEDULED_SILENT_RETRY
    elif category == FailureCategory.CUSTOMER_ACTIONABLE:
        proposed_action = RecoveryAction.DISPATCH_DYNAMIC_LINK
    else:
        proposed_action = RecoveryAction.ABORT_TERMINAL

    current_hour_ist = state.get("current_hour_ist", 14)  # Default: 14:00 (2 PM IST)
    guard_passed, guard_msg = evaluate_guardrails(event, proposed_action, current_hour_ist)

    audit_logger.log_event(
        invoice_id=event.invoice_id,
        event_type="GUARD_EVALUATION",
        action=proposed_action.value,
        guard_check_passed=guard_passed,
        details={
            "attempt_count": event.attempt_count,
            "is_locked": event.is_locked,
            "current_hour_ist": current_hour_ist,
            "guard_message": guard_msg,
        },
    )

    return {
        "guard_passed": guard_passed,
        "guard_message": guard_msg,
    }


def execution_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes optimal recovery action, invokes mock recovery simulator,
    and records updates to state reducers.
    """
    raw_event = state["event"]
    event = FailedPaymentEvent.model_validate(raw_event)
    category_str = state.get("failure_category", FailureCategory.CUSTOMER_ACTIONABLE.value)
    category = FailureCategory(category_str)
    guard_passed = state.get("guard_passed", True)
    guard_msg = state.get("guard_message", "")

    recovered_events = []
    scheduled_retries = []
    dispatched_links = []
    aborted_events = []

    # Case 1: Hard stopping rule / Guardrail rejection / Terminal failure
    if not guard_passed or category == FailureCategory.TERMINAL_FAILURE:
        if event.attempt_count >= MAX_RETRY_LIMIT:
            recovery_status = PaymentStatus.ABORTED_MAX_RETRIES.value
            reasoning = f"Hard stopping rule enforced: {guard_msg}"
        elif event.is_locked:
            recovery_status = PaymentStatus.FAILED.value
            reasoning = f"Execution blocked: {guard_msg}"
        elif "COMPLIANCE_WINDOW_VIOLATION" in guard_msg:
            recovery_status = PaymentStatus.FAILED.value
            reasoning = f"Customer contact blocked: {guard_msg}"
        else:
            recovery_status = PaymentStatus.FAILED.value
            reasoning = f"Terminal failure detected for {event.error_code}. Aborting dunning sequence."

        plan = RecoveryPlan(
            invoice_id=event.invoice_id,
            action=RecoveryAction.ABORT_TERMINAL,
            target_rail=None,
            scheduled_at=None,
            dynamic_link=None,
            reasoning=reasoning,
        )

        record = {
            "invoice_id": event.invoice_id,
            "customer_id": event.customer_id,
            "amount": str(event.amount),
            "payment_rail": event.payment_rail.value,
            "status": recovery_status,
            "action": RecoveryAction.ABORT_TERMINAL.value,
            "reasoning": reasoning,
            "is_recovered": False,
        }
        aborted_events.append(record)

        audit_logger.log_event(
            invoice_id=event.invoice_id,
            event_type="RECOVERY_ABORTED",
            action=RecoveryAction.ABORT_TERMINAL.value,
            guard_check_passed=guard_passed,
            details={
                "status": recovery_status,
                "amount": float(event.amount),
                "reasoning": reasoning,
            },
        )

        return {
            "recovery_plan": plan.model_dump(),
            "recovery_status": recovery_status,
            "recovered_events": recovered_events,
            "scheduled_retries": scheduled_retries,
            "dispatched_links": dispatched_links,
            "aborted_events": aborted_events,
            "audit_trail": [record],
        }

    # Case 2: Transient downtime -> Scheduled Silent Retry (+12h cooldown)
    if category == FailureCategory.TRANSIENT_DOWNTIME:
        scheduled_time = (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat()
        reasoning = (
            f"Transient downtime ({event.error_code}) diagnosed on {event.payment_rail.value}. "
            f"Scheduling silent off-peak retry (+12h cooldown) to bypass issuer outage without disturbing customer."
        )
        plan = RecoveryPlan(
            invoice_id=event.invoice_id,
            action=RecoveryAction.SCHEDULED_SILENT_RETRY,
            target_rail=event.payment_rail,
            scheduled_at=scheduled_time,
            dynamic_link=None,
            reasoning=reasoning,
        )

        is_recovered = simulate_recovery_conversion(event.invoice_id, RecoveryAction.SCHEDULED_SILENT_RETRY)
        recovery_status = PaymentStatus.RECOVERED.value if is_recovered else PaymentStatus.RETRY_SCHEDULED.value

        record = {
            "invoice_id": event.invoice_id,
            "customer_id": event.customer_id,
            "amount": str(event.amount),
            "payment_rail": event.payment_rail.value,
            "status": recovery_status,
            "action": RecoveryAction.SCHEDULED_SILENT_RETRY.value,
            "scheduled_at": scheduled_time,
            "reasoning": reasoning,
            "is_recovered": is_recovered,
        }

        scheduled_retries.append(record)
        if is_recovered:
            recovered_events.append(record)

        audit_logger.log_event(
            invoice_id=event.invoice_id,
            event_type="RECOVERY_EXECUTION",
            action=RecoveryAction.SCHEDULED_SILENT_RETRY.value,
            guard_check_passed=True,
            details={
                "status": recovery_status,
                "is_recovered": is_recovered,
                "amount": float(event.amount),
                "scheduled_at": scheduled_time,
            },
        )

        return {
            "recovery_plan": plan.model_dump(),
            "recovery_status": recovery_status,
            "recovered_events": recovered_events,
            "scheduled_retries": scheduled_retries,
            "dispatched_links": dispatched_links,
            "aborted_events": aborted_events,
            "audit_trail": [record],
        }

    # Case 3: Customer Actionable -> Dispatch Dynamic Multi-Rail Recovery Link
    target_rail = PaymentRail.UPI if event.payment_rail != PaymentRail.UPI else PaymentRail.CARD
    dynamic_link = f"https://pay.rzp.io/recover/{event.invoice_id}?rail={target_rail.value}&auth=intent"
    reasoning = (
        f"Customer-actionable failure ({event.error_code}) on {event.payment_rail.value}. "
        f"Generated dynamic multi-rail payment link with smart fallback to {target_rail.value} Intent."
    )
    plan = RecoveryPlan(
        invoice_id=event.invoice_id,
        action=RecoveryAction.DISPATCH_DYNAMIC_LINK,
        target_rail=target_rail,
        scheduled_at=None,
        dynamic_link=dynamic_link,
        reasoning=reasoning,
    )

    is_recovered = simulate_recovery_conversion(event.invoice_id, RecoveryAction.DISPATCH_DYNAMIC_LINK)
    recovery_status = PaymentStatus.RECOVERED.value if is_recovered else PaymentStatus.LINK_DISPATCHED.value

    record = {
        "invoice_id": event.invoice_id,
        "customer_id": event.customer_id,
        "amount": str(event.amount),
        "payment_rail": event.payment_rail.value,
        "target_rail": target_rail.value,
        "status": recovery_status,
        "action": RecoveryAction.DISPATCH_DYNAMIC_LINK.value,
        "dynamic_link": dynamic_link,
        "reasoning": reasoning,
        "is_recovered": is_recovered,
    }

    dispatched_links.append(record)
    if is_recovered:
        recovered_events.append(record)

    audit_logger.log_event(
        invoice_id=event.invoice_id,
        event_type="RECOVERY_EXECUTION",
        action=RecoveryAction.DISPATCH_DYNAMIC_LINK.value,
        guard_check_passed=True,
        details={
            "status": recovery_status,
            "is_recovered": is_recovered,
            "amount": float(event.amount),
            "dynamic_link": dynamic_link,
            "fallback_rail": target_rail.value,
        },
    )

    return {
        "recovery_plan": plan.model_dump(),
        "recovery_status": recovery_status,
        "recovered_events": recovered_events,
        "scheduled_retries": scheduled_retries,
        "dispatched_links": dispatched_links,
        "aborted_events": aborted_events,
        "audit_trail": [record],
    }
