"""Comprehensive test suite for AI Finance Controller 3-Way Reconciliation."""
import json
from decimal import Decimal
from pathlib import Path
import pytest

from core.models import (
    BankStatementEntry,
    InternalOrder,
    RazorpaySettlement,
    ReconciliationStatus,
)
from core.rules import (
    CONTRACTED_MDR_RATE,
    GST_RATE,
    calculate_expected_fee,
    check_fee_overcharge,
    quantize_currency,
    verify_accounting_equation,
)
from agent.graph import get_compiled_graph
from data.generate_batch import generate_dataset


@pytest.fixture
def sample_clean_triplet():
    """Valid 3-way matching dataset triplet."""
    gross = Decimal("10000.00")
    expected_mdr = Decimal("200.00")      # 2% of 10,000
    expected_gst = Decimal("36.00")       # 18% of 200
    net = Decimal("9764.00")              # 10,000 - 236
    utr = "UTR20260901CLEAN1001"

    order = InternalOrder(
        order_id="ORD_1001",
        amount=gross,
        tax_amount=Decimal("1800.00"),
        customer_id="CUST_001",
        status="PAID",
        created_at="2026-09-01T10:00:00Z",
    )
    settlement = RazorpaySettlement(
        payment_id="pay_clean_1001",
        order_id="ORD_1001",
        gross_amount=gross,
        fee=expected_mdr,
        tax_on_fee=expected_gst,
        net_amount=net,
        utr=utr,
        settled_at="2026-09-01T11:00:00Z",
    )
    bank_entry = BankStatementEntry(
        bank_ref="BNK_1001",
        utr=utr,
        credit_amount=net,
        value_date="2026-09-01",
        description="ACH CR RAZORPAY SETTLEMENT",
    )
    return order, settlement, bank_entry


def test_clean_3way_match(sample_clean_triplet):
    """Test standard clean match satisfies accounting equation and fee verification."""
    order, settlement, bank_entry = sample_clean_triplet

    # Verify accounting equation
    valid, msg = verify_accounting_equation(order, settlement, bank_entry)
    assert valid is True
    assert "balanced" in msg

    # Verify fee check (2% contracted)
    is_overcharged, delta, expected, actual = check_fee_overcharge(settlement)
    assert is_overcharged is False
    assert delta == Decimal("0.00")
    assert actual == Decimal("236.00")
    assert expected == Decimal("236.00")


def test_fee_overcharge_detection_with_exact_delta():
    """Test gateway charging 3% MDR instead of 2% produces exact delta."""
    gross = Decimal("50000.00")
    # Expected at 2% MDR:
    # MDR = 1000.00, GST = 180.00, Total Expected = 1180.00
    # Overcharged at 3% MDR:
    # MDR = 1500.00, GST = 270.00, Total Actual = 1770.00
    # Expected delta = 1770.00 - 1180.00 = 590.00
    fee_charged = Decimal("1500.00")
    gst_charged = Decimal("270.00")
    net_amount = gross - fee_charged - gst_charged

    settlement = RazorpaySettlement(
        payment_id="pay_overcharge_1041",
        order_id="ORD_1041",
        gross_amount=gross,
        fee=fee_charged,
        tax_on_fee=gst_charged,
        net_amount=net_amount,
        utr="UTR20260901OVER1041",
        settled_at="2026-09-01T12:00:00Z",
    )

    is_overcharged, delta, expected_total, actual_total = check_fee_overcharge(settlement)
    assert is_overcharged is True
    assert expected_total == Decimal("1180.00")
    assert actual_total == Decimal("1770.00")
    assert delta == Decimal("590.00")


def test_missing_gateway_record_exception():
    """Test pipeline detects internal order with no gateway settlement record."""
    graph = get_compiled_graph()
    order = {
        "order_id": "ORD_GHOST_1",
        "amount": "2500.00",
        "tax_amount": "450.00",
        "customer_id": "CUST_999",
        "status": "PAID",
        "created_at": "2026-09-01T10:00:00Z",
    }
    initial_state = {
        "raw_orders": [order],
        "raw_settlements": [],  # Missing in Razorpay
        "raw_bank_entries": [],
        "indexed_orders": {},
        "indexed_settlements_by_order": {},
        "indexed_bank_by_utr": {},
        "reconciled_records": [],
        "exceptions_list": [],
        "audit_trail": [],
        "summary_metrics": {},
    }
    final_state = graph.invoke(initial_state)

    exceptions = final_state["exceptions_list"]
    assert len(exceptions) == 1
    assert exceptions[0]["order_id"] == "ORD_GHOST_1"
    assert exceptions[0]["status"] == ReconciliationStatus.MISSING_GATEWAY_RECORD.value
    assert len(final_state["reconciled_records"]) == 0


def test_missing_bank_entry_exception():
    """Test pipeline detects gateway settlement with UTR missing from bank statement."""
    graph = get_compiled_graph()
    order = {
        "order_id": "ORD_BANK_UNSETTLED_1",
        "amount": "10000.00",
        "tax_amount": "1800.00",
        "customer_id": "CUST_888",
        "status": "PAID",
        "created_at": "2026-09-01T10:00:00Z",
    }
    settlement = {
        "payment_id": "pay_unsettled_1",
        "order_id": "ORD_BANK_UNSETTLED_1",
        "gross_amount": "10000.00",
        "fee": "200.00",
        "tax_on_fee": "36.00",
        "net_amount": "9764.00",
        "utr": "UTR_UNSETTLED_9999",
        "settled_at": "2026-09-01T11:00:00Z",
    }
    initial_state = {
        "raw_orders": [order],
        "raw_settlements": [settlement],
        "raw_bank_entries": [],  # Missing in bank
        "indexed_orders": {},
        "indexed_settlements_by_order": {},
        "indexed_bank_by_utr": {},
        "reconciled_records": [],
        "exceptions_list": [],
        "audit_trail": [],
        "summary_metrics": {},
    }
    final_state = graph.invoke(initial_state)

    exceptions = final_state["exceptions_list"]
    assert len(exceptions) == 1
    assert exceptions[0]["order_id"] == "ORD_BANK_UNSETTLED_1"
    assert exceptions[0]["status"] == ReconciliationStatus.UNSETTLED_BY_BANK.value
    assert exceptions[0]["utr"] == "UTR_UNSETTLED_9999"


def test_decimal_precision_and_invariants():
    """Verify precision invariance without IEEE-754 floating point distortion."""
    d1 = Decimal("0.1")
    d2 = Decimal("0.2")
    assert d1 + d2 == Decimal("0.3")

    amount = Decimal("7850.55")
    mdr, gst, total = calculate_expected_fee(amount)
    assert mdr == Decimal("157.01")
    assert gst == Decimal("28.26")
    assert total == Decimal("185.27")


def test_accounting_equation_mismatch():
    """Test accounting equation failure when gateway net amount does not match bank credit."""
    order = InternalOrder(
        order_id="ORD_MISMATCH",
        amount=Decimal("5000.00"),
        tax_amount=Decimal("900.00"),
        customer_id="CUST_001",
        status="PAID",
        created_at="2026-09-01T10:00:00Z",
    )
    settlement = RazorpaySettlement(
        payment_id="pay_mismatch",
        order_id="ORD_MISMATCH",
        gross_amount=Decimal("5000.00"),
        fee=Decimal("100.00"),
        tax_on_fee=Decimal("18.00"),
        net_amount=Decimal("4882.00"),
        utr="UTR_MISMATCH_01",
        settled_at="2026-09-01T11:00:00Z",
    )
    bank_entry = BankStatementEntry(
        bank_ref="BNK_MISMATCH",
        utr="UTR_MISMATCH_01",
        credit_amount=Decimal("4800.00"),  # Mismatch!
        value_date="2026-09-01",
        description="ACH CR RAZORPAY",
    )

    valid, reason = verify_accounting_equation(order, settlement, bank_entry)
    assert valid is False
    assert "Bank Settlement Mismatch" in reason


def test_full_graph_execution_60_batch(tmp_path):
    """Test full 60-record dataset execution against exact classification invariants."""
    test_data_path = tmp_path / "test_dataset_60.json"
    dataset = generate_dataset(test_data_path)

    initial_state = {
        "raw_orders": dataset["internal_orders"],
        "raw_settlements": dataset["razorpay_settlements"],
        "raw_bank_entries": dataset["bank_statement_entries"],
        "indexed_orders": {},
        "indexed_settlements_by_order": {},
        "indexed_bank_by_utr": {},
        "reconciled_records": [],
        "exceptions_list": [],
        "audit_trail": [],
        "summary_metrics": {},
    }

    graph = get_compiled_graph()
    final_state = graph.invoke(initial_state)

    reconciled = final_state["reconciled_records"]
    exceptions = final_state["exceptions_list"]
    metrics = final_state["summary_metrics"]

    assert len(reconciled) == 40, f"Expected 40 reconciled, got {len(reconciled)}"
    assert len(exceptions) == 20, f"Expected 20 exceptions, got {len(exceptions)}"
    assert metrics["total_records"] == 60
    assert metrics["total_reconciled"] == 40
    assert metrics["total_exceptions"] == 20
    assert metrics["match_rate_pct"] == 66.67
    assert metrics["exception_rate_pct"] == 33.33

    status_breakdown = metrics["status_breakdown"]
    assert status_breakdown[ReconciliationStatus.FULLY_RECONCILED.value] == 40
    assert status_breakdown[ReconciliationStatus.FEE_DISCREPANCY.value] == 8
    assert status_breakdown[ReconciliationStatus.UNSETTLED_BY_BANK.value] == 6
    assert status_breakdown[ReconciliationStatus.MISSING_GATEWAY_RECORD.value] == 6
    assert status_breakdown[ReconciliationStatus.UNRESOLVED_EXCEPTION.value] == 0

    audit_trail = final_state["audit_trail"]
    assert len(audit_trail) >= 62
