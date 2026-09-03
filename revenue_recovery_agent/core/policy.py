"""Deterministic guardrails, regulatory compliance rules, and diagnostic classification."""
from typing import Tuple
from revenue_recovery_agent.core.models import (
    FailureCategory,
    FailedPaymentEvent,
    RecoveryAction,
)

# Business and Regulatory Policy Constants
MAX_RETRY_LIMIT: int = 2  # Hard stop after 2 recovery attempts
COMPLIANT_HOURS: Tuple[int, int] = (8, 20)  # Customer contact allowed only 08:00–20:00 IST (TRAI/RBI norms)
MIN_COOLDOWN_HOURS: int = 12  # Minimum cooldown period between silent retries

# Canonical Error Code Mappings
TRANSIENT_ERRORS = {
    "GATEWAY_TIMEOUT",
    "ISSUER_DOWN",
    "NETWORK_ERROR",
    "BANK_PROCESSING_ERROR",
    "SWITCHING_CENTER_ERROR",
}

CUSTOMER_ACTIONABLE_ERRORS = {
    "INSUFFICIENT_FUNDS",
    "AUTH_FAILED",
    "EXPIRED_MANDATE",
    "INSUFFICIENT_LIMIT",
    "CARD_EXPIRED",
    "OTP_TIMEOUT",
}

TERMINAL_ERRORS = {
    "ACCOUNT_CLOSED",
    "FRAUD_BLOCK",
    "INVALID_ACCOUNT",
    "STOLEN_CARD",
    "ACCOUNT_BLOCKED",
}


def diagnose_failure(error_code: str) -> FailureCategory:
    """
    Classify failure error code into standard FailureCategory.
    
    Rules:
    - GATEWAY_TIMEOUT, ISSUER_DOWN, NETWORK_ERROR -> TRANSIENT_DOWNTIME
    - INSUFFICIENT_FUNDS, AUTH_FAILED, EXPIRED_MANDATE -> CUSTOMER_ACTIONABLE
    - ACCOUNT_CLOSED, FRAUD_BLOCK, INVALID_ACCOUNT -> TERMINAL_FAILURE
    """
    normalized = error_code.strip().upper()

    if normalized in TRANSIENT_ERRORS:
        return FailureCategory.TRANSIENT_DOWNTIME
    elif normalized in CUSTOMER_ACTIONABLE_ERRORS:
        return FailureCategory.CUSTOMER_ACTIONABLE
    elif normalized in TERMINAL_ERRORS:
        return FailureCategory.TERMINAL_FAILURE
    else:
        # Default safety classification
        if "TIMEOUT" in normalized or "DOWN" in normalized or "NETWORK" in normalized:
            return FailureCategory.TRANSIENT_DOWNTIME
        elif "FRAUD" in normalized or "CLOSED" in normalized or "INVALID" in normalized:
            return FailureCategory.TERMINAL_FAILURE
        return FailureCategory.CUSTOMER_ACTIONABLE


def evaluate_guardrails(
    event: FailedPaymentEvent,
    proposed_action: RecoveryAction,
    current_hour_ist: int,
) -> Tuple[bool, str]:
    """
    Evaluate deterministic guardrails and regulatory compliance rules.
    
    Enforces:
    1. Idempotency Lock: Rejects duplicate concurrent actions if event.is_locked is True.
    2. Max Retry Stopping Rule: Rejects any retry/recovery if attempt_count >= MAX_RETRY_LIMIT.
    3. Regulatory Contact Window: If action is DISPATCH_DYNAMIC_LINK, requires current_hour_ist
       to be strictly within COMPLIANT_HOURS (08:00 - 20:00 IST).
    """
    # 1. Idempotency Lock Check
    if event.is_locked:
        return False, f"IDEMPOTENCY_LOCK_ACTIVE: invoice {event.invoice_id} is locked by concurrent recovery process"

    # 2. Max Retry Stopping Rule
    if event.attempt_count >= MAX_RETRY_LIMIT:
        return False, f"MAX_RETRY_EXCEEDED: attempt count {event.attempt_count} reaches/exceeds limit {MAX_RETRY_LIMIT}"

    # 3. Regulatory Communication Window Guardrail (TRAI / RBI)
    if proposed_action == RecoveryAction.DISPATCH_DYNAMIC_LINK:
        start_hour, end_hour = COMPLIANT_HOURS
        if not (start_hour <= current_hour_ist < end_hour):
            return False, (
                f"COMPLIANCE_WINDOW_VIOLATION: current hour {current_hour_ist:02d}:00 IST "
                f"is outside permissible customer outreach window ({start_hour:02d}:00-{end_hour:02d}:00 IST)"
            )

    return True, "PASSED_ALL_GUARDRAILS"
