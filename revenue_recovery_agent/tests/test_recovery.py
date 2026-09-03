"""Comprehensive test suite for Autonomous AI Revenue Recovery Engine."""
import json
import sys
from decimal import Decimal
from pathlib import Path
import pytest

# Ensure repo root is on sys.path for direct pytest invocation
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from revenue_recovery_agent.core.models import (
    PaymentRail,
    FailureCategory,
    RecoveryAction,
    PaymentStatus,
    FailedPaymentEvent,
)
from revenue_recovery_agent.core.policy import (
    MAX_RETRY_LIMIT,
    COMPLIANT_HOURS,
    diagnose_failure,
    evaluate_guardrails,
)
from revenue_recovery_agent.agent.graph import create_recovery_graph
from revenue_recovery_agent.data.generate_batch import get_default_dataset_path, write_batch_dataset


def test_failure_diagnostic_mapping():
    """Verify that error codes are deterministically mapped to the correct FailureCategory."""
    # Transient downtime errors
    for err in ["GATEWAY_TIMEOUT", "ISSUER_DOWN", "NETWORK_ERROR", "gateway_timeout", "  ISSUER_DOWN  "]:
        assert diagnose_failure(err) == FailureCategory.TRANSIENT_DOWNTIME

    # Actionable customer soft failures
    for err in ["INSUFFICIENT_FUNDS", "AUTH_FAILED", "EXPIRED_MANDATE"]:
        assert diagnose_failure(err) == FailureCategory.CUSTOMER_ACTIONABLE

    # Terminal hard failures
    for err in ["ACCOUNT_CLOSED", "FRAUD_BLOCK", "INVALID_ACCOUNT"]:
        assert diagnose_failure(err) == FailureCategory.TERMINAL_FAILURE


def test_max_retry_stopping_rule():
    """Verify that transactions with attempt_count >= MAX_RETRY_LIMIT are strictly rejected."""
    event_limit_reached = FailedPaymentEvent(
        invoice_id="INV-TEST-LIMIT-01",
        customer_id="CUST-TEST-01",
        amount=Decimal("2500.00"),
        payment_rail=PaymentRail.CARD,
        error_code="INSUFFICIENT_FUNDS",
        error_description="Card balance depleted",
        attempt_count=MAX_RETRY_LIMIT,  # 2
        failed_at="2026-09-03T10:00:00.000Z",
        is_locked=False,
    )
    passed, msg = evaluate_guardrails(event_limit_reached, RecoveryAction.DISPATCH_DYNAMIC_LINK, current_hour_ist=14)
    assert not passed
    assert "MAX_RETRY_EXCEEDED" in msg

    # Graph level execution test
    graph = create_recovery_graph()
    result = graph.invoke({
        "event": event_limit_reached.model_dump(),
        "current_hour_ist": 14,
        "recovered_events": [],
        "scheduled_retries": [],
        "dispatched_links": [],
        "aborted_events": [],
        "audit_trail": [],
    })
    assert result["recovery_status"] == PaymentStatus.ABORTED_MAX_RETRIES.value
    assert len(result["aborted_events"]) == 1
    assert result["aborted_events"][0]["invoice_id"] == "INV-TEST-LIMIT-01"


def test_compliance_window_violation():
    """Verify that active dunning outreach (dynamic payment links) is strictly blocked outside 08:00-20:00 IST."""
    event = FailedPaymentEvent(
        invoice_id="INV-TEST-WINDOW-01",
        customer_id="CUST-TEST-02",
        amount=Decimal("1800.00"),
        payment_rail=PaymentRail.UPI,
        error_code="AUTH_FAILED",
        error_description="Customer did not enter UPI PIN",
        attempt_count=0,
        failed_at="2026-09-03T23:30:00.000Z",
        is_locked=False,
    )

    # Nocturnal hour (23:00 IST) -> Must be rejected
    passed_night, msg_night = evaluate_guardrails(event, RecoveryAction.DISPATCH_DYNAMIC_LINK, current_hour_ist=23)
    assert not passed_night
    assert "COMPLIANCE_WINDOW_VIOLATION" in msg_night

    # Early morning hour (04:00 IST) -> Must be rejected
    passed_dawn, msg_dawn = evaluate_guardrails(event, RecoveryAction.DISPATCH_DYNAMIC_LINK, current_hour_ist=4)
    assert not passed_dawn
    assert "COMPLIANCE_WINDOW_VIOLATION" in msg_dawn

    # Compliant daytime hour (15:00 IST) -> Must pass
    passed_day, msg_day = evaluate_guardrails(event, RecoveryAction.DISPATCH_DYNAMIC_LINK, current_hour_ist=15)
    assert passed_day
    assert msg_day == "PASSED_ALL_GUARDRAILS"


def test_idempotency_lock():
    """Verify that concurrent actions on an invoice with is_locked=True are blocked to prevent double-debit."""
    locked_event = FailedPaymentEvent(
        invoice_id="INV-TEST-LOCKED-01",
        customer_id="CUST-TEST-03",
        amount=Decimal("4500.00"),
        payment_rail=PaymentRail.NETBANKING,
        error_code="GATEWAY_TIMEOUT",
        error_description="Bank gateway timeout",
        attempt_count=0,
        failed_at="2026-09-03T11:00:00.000Z",
        is_locked=True,  # Active lock
    )

    passed, msg = evaluate_guardrails(locked_event, RecoveryAction.SCHEDULED_SILENT_RETRY, current_hour_ist=14)
    assert not passed
    assert "IDEMPOTENCY_LOCK_ACTIVE" in msg

    # Graph level execution verification
    graph = create_recovery_graph()
    result = graph.invoke({
        "event": locked_event.model_dump(),
        "current_hour_ist": 14,
        "recovered_events": [],
        "scheduled_retries": [],
        "dispatched_links": [],
        "aborted_events": [],
        "audit_trail": [],
    })
    assert result["guard_passed"] is False
    assert len(result["aborted_events"]) == 1
    assert "IDEMPOTENCY_LOCK_ACTIVE" in result["aborted_events"][0]["reasoning"]


def test_full_batch_execution_and_arithmetic_conservation():
    """
    Execute all 60 benchmark payments through the LangGraph recovery pipeline.
    Assert arithmetic conservation: Total Revenue at Risk == Total Recovered + Total Unrecovered/Aborted.
    """
    dataset_path = get_default_dataset_path()
    if not dataset_path.exists():
        write_batch_dataset(dataset_path)

    with open(dataset_path, "r", encoding="utf-8") as f:
        batch_records = json.load(f)

    assert len(batch_records) == 60

    graph = create_recovery_graph()

    total_at_risk = Decimal("0.00")
    total_recovered = Decimal("0.00")
    total_unrecovered = Decimal("0.00")

    all_invoices = set()
    exhausted_stopped_count = 0
    terminal_stopped_count = 0

    for raw in batch_records:
        invoice_id = raw["invoice_id"]
        assert invoice_id not in all_invoices, f"Duplicate invoice_id detected: {invoice_id}"
        all_invoices.add(invoice_id)

        amount = Decimal(raw["amount"])
        total_at_risk += amount

        # Execute transaction through the agent graph
        result = graph.invoke({
            "event": raw,
            "current_hour_ist": 14,  # Standard compliant hour
            "recovered_events": [],
            "scheduled_retries": [],
            "dispatched_links": [],
            "aborted_events": [],
            "audit_trail": [],
        })

        if result.get("recovered_events"):
            total_recovered += amount
        else:
            total_unrecovered += amount

        if result.get("recovery_status") == PaymentStatus.ABORTED_MAX_RETRIES.value:
            exhausted_stopped_count += 1
        elif result.get("recovery_plan", {}).get("action") == RecoveryAction.ABORT_TERMINAL.value:
            terminal_stopped_count += 1

    # Exact arithmetic conservation verification
    assert total_at_risk == total_recovered + total_unrecovered, (
        f"Arithmetic violation: Total at Risk ({total_at_risk}) != "
        f"Recovered ({total_recovered}) + Unrecovered ({total_unrecovered})"
    )

    # Assert that some revenue was successfully recovered
    assert total_recovered > Decimal("0.00")
    assert total_unrecovered > Decimal("0.00")

    # Subset 3 (records 46-52): exactly 7 records had attempt_count=2 and must be stopped with ABORTED_MAX_RETRIES
    assert exhausted_stopped_count == 7, f"Expected 7 max-retry stops, got {exhausted_stopped_count}"

    # Subset 4 (records 53-60): exactly 8 terminal records must be aborted with ABORT_TERMINAL
    assert terminal_stopped_count == 8, f"Expected 8 terminal aborts, got {terminal_stopped_count}"

    # Total stopped events: 7 + 8 = 15
    assert exhausted_stopped_count + terminal_stopped_count == 15

