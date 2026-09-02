"""Tests for Real CSV Ingestion Adapter and CSV Reconciliation."""
from decimal import Decimal
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from core.models import ReconciliationStatus
from data.csv_adapter import (
    clean_currency_str,
    export_sample_csvs,
    load_csv_dataset,
    parse_bank_statements_csv,
    parse_orders_csv,
    parse_settlements_csv,
)
from run_reconciliation import run_pipeline
from chat.server import app


@pytest.fixture
def api_client():
    return TestClient(app)


def test_clean_currency_str():
    """Test flexible currency string sanitization and conversion."""
    assert clean_currency_str("₹ 10,000.50") == Decimal("10000.50")
    assert clean_currency_str("INR 1,234.56") == Decimal("1234.56")
    assert clean_currency_str("$500.00") == Decimal("500.00")
    assert clean_currency_str("  15499.00  ") == Decimal("15499.00")
    assert clean_currency_str(2500) == Decimal("2500.00")
    assert clean_currency_str(None) == Decimal("0.00")


def test_parse_orders_csv_flexible_headers():
    """Test parsing orders CSV with mixed case and alternative header names."""
    csv_text = '''Order Number,User Id,Total Price,Tax,State,Order Date
ORD_TEST_1,CUST_99,"₹ 5,000.00","₹ 900.00",PAID,2026-09-01T10:00:00Z
ORD_TEST_2,CUST_100,10000.00,1800.00,PAID,2026-09-01T10:05:00Z
'''
    orders = parse_orders_csv(csv_text)
    assert len(orders) == 2
    assert orders[0]["order_id"] == "ORD_TEST_1"
    assert orders[0]["amount"] == Decimal("5000.00")
    assert orders[0]["tax_amount"] == Decimal("900.00")
    assert orders[0]["customer_id"] == "CUST_99"


def test_parse_settlements_csv():
    """Test parsing Razorpay settlements CSV."""
    csv_text = '''Transaction ID,Order ID,Gross Amount,Gateway Fee,Fee Tax,Net Amount,Bank UTR,Date
pay_001,ORD_TEST_1,"₹ 5,000.00",100.00,18.00,4882.00,UTRTEST001,2026-09-01T11:00:00Z
'''
    settlements = parse_settlements_csv(csv_text)
    assert len(settlements) == 1
    assert settlements[0]["payment_id"] == "pay_001"
    assert settlements[0]["order_id"] == "ORD_TEST_1"
    assert settlements[0]["gross_amount"] == Decimal("5000.00")
    assert settlements[0]["fee"] == Decimal("100.00")
    assert settlements[0]["tax_on_fee"] == Decimal("18.00")
    assert settlements[0]["net_amount"] == Decimal("4882.00")
    assert settlements[0]["utr"] == "UTRTEST001"


def test_parse_bank_statements_csv():
    """Test parsing Bank statement credits CSV."""
    csv_text = '''Reference,UTR Number,Credit Amount,Value Date,Narration
BNK_001,UTRTEST001,"₹ 4,882.00",2026-09-01,ACH CR RAZORPAY SETTLEMENT UTRTEST001
'''
    bank_entries = parse_bank_statements_csv(csv_text)
    assert len(bank_entries) == 1
    assert bank_entries[0]["bank_ref"] == "BNK_001"
    assert bank_entries[0]["utr"] == "UTRTEST001"
    assert bank_entries[0]["credit_amount"] == Decimal("4882.00")


def test_full_csv_export_and_reconciliation_pipeline(tmp_path):
    """Test exporting sample CSVs, loading them into pipeline, and reconciling with exact invariants."""
    exported = export_sample_csvs(output_dir=tmp_path)
    assert exported["orders_csv"].exists()
    assert exported["settlements_csv"].exists()
    assert exported["bank_csv"].exists()

    final_state = run_pipeline(
        orders_csv=exported["orders_csv"],
        settlements_csv=exported["settlements_csv"],
        bank_csv=exported["bank_csv"],
        audit_file=tmp_path / "test_audit.jsonl",
    )

    metrics = final_state["summary_metrics"]
    assert metrics["total_records"] == 60
    assert metrics["total_reconciled"] == 40
    assert metrics["total_exceptions"] == 20
    assert metrics["match_rate_pct"] == 66.67
    assert metrics["status_breakdown"][ReconciliationStatus.FULLY_RECONCILED.value] == 40
    assert metrics["status_breakdown"][ReconciliationStatus.FEE_DISCREPANCY.value] == 8
    assert metrics["status_breakdown"][ReconciliationStatus.UNSETTLED_BY_BANK.value] == 6
    assert metrics["status_breakdown"][ReconciliationStatus.MISSING_GATEWAY_RECORD.value] == 6
    assert Decimal(metrics["total_fee_overcharges_recoverable"]) == Decimal("1300.92")


def test_fastapi_csv_upload_endpoint(api_client, tmp_path):
    """Test FastAPI /api/reconcile-csv multipart upload endpoint."""
    exported = export_sample_csvs(output_dir=tmp_path)

    with open(exported["orders_csv"], "rb") as f_orders, \
         open(exported["settlements_csv"], "rb") as f_settle, \
         open(exported["bank_csv"], "rb") as f_bank:
        
        response = api_client.post(
            "/api/reconcile-csv",
            files={
                "orders_file": ("orders.csv", f_orders, "text/csv"),
                "settlements_file": ("razorpay.csv", f_settle, "text/csv"),
                "bank_file": ("bank.csv", f_bank, "text/csv"),
            }
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["summary"]["total_transactions"] == 60
    assert data["summary"]["match_rate"] == "66.67%"
