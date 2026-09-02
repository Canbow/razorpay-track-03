"""Tests for AI Finance Controller Conversational Agent and FastAPI endpoints."""
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from chat.controller import FinanceControllerAgent
from chat.server import app


@pytest.fixture
def chat_agent():
    return FinanceControllerAgent()


@pytest.fixture
def api_client():
    return TestClient(app)


def test_agent_get_financial_summary(chat_agent):
    """Test retrieving summary KPIs from conversational agent."""
    summary = chat_agent.get_financial_summary()
    assert summary["total_transactions"] == 60
    assert summary["fully_reconciled"] == 40
    assert summary["match_rate"] == "66.67%"
    assert summary["total_exceptions"] == 20
    assert "1,300.92" in summary["recoverable_fee_overcharge"]


def test_agent_inspect_order(chat_agent):
    """Test deep-dive inspection on clean order, overcharged order, and non-existent order."""
    # 1. Clean order
    res_clean = chat_agent.inspect_order("ORD_1001")
    assert res_clean["found"] is True
    assert "FULLY_RECONCILED" in res_clean["status"]
    assert res_clean["razorpay_settlement"] is not None
    assert res_clean["bank_statement"] is not None

    # 2. Overcharged order
    res_over = chat_agent.inspect_order("ORD_1041")
    assert res_over["found"] is True
    assert "FEE_DISCREPANCY" in res_over["status"]
    assert "Overcharge" in res_over["reason"]

    # 3. Non-existent order
    res_missing = chat_agent.inspect_order("ORD_99999")
    assert res_missing["found"] is False


def test_agent_generate_razorpay_dispute_letter(chat_agent):
    """Test dispute letter generation with correct total delta."""
    dispute = chat_agent.generate_razorpay_dispute_letter()
    assert dispute["disputed_orders_count"] == 8
    assert Decimal(dispute["total_recoverable_inr"]) == Decimal("1300.92")
    assert "OFFICIAL MERCHANT DISPUTE" in dispute["dispute_letter_markdown"]
    assert "ORD_1041" in dispute["dispute_letter_markdown"]


def test_agent_generate_bank_inquiry_sheet(chat_agent):
    """Test bank UTR tracing inquiry sheet generation."""
    bank_inq = chat_agent.generate_bank_inquiry_sheet()
    assert bank_inq["unsettled_count"] == 6
    assert Decimal(bank_inq["total_unsettled_inr"]) > 0
    assert "BANK UTR TRACING" in bank_inq["inquiry_markdown"]


def test_agent_chat_nlp_intents(chat_agent):
    """Test NLP intent routing across various user phrasings."""
    # 1. Summary intent
    res_summary = chat_agent.chat("What is our reconciliation status and match rate?")
    assert res_summary["intent"] == "financial_summary"
    assert "Executive Status Report" in res_summary["reply"]

    # 2. Dispute intent
    res_dispute = chat_agent.chat("Please draft a dispute letter for Razorpay for the 3% MDR fee leakage")
    assert res_dispute["intent"] == "generate_dispute"
    assert "DISP-RZP-" in res_dispute["reply"]

    # 3. Order inspection intent
    res_inspect = chat_agent.chat("Can you check ORD_1041 and explain why it failed?")
    assert res_inspect["intent"] == "order_inspection"
    assert "3-Way Inspection: `ORD_1041`" in res_inspect["reply"]

    # 4. Fee leakage intent
    res_fee = chat_agent.chat("How much fee leakage occurred due to overcharged MDR?")
    assert res_fee["intent"] == "fee_overcharges"
    assert "1,300.92" in res_fee["reply"]


def test_fastapi_rest_endpoints(api_client):
    """Test FastAPI endpoints."""
    # GET /api/metrics
    r_metrics = api_client.get("/api/metrics")
    assert r_metrics.status_code == 200
    assert r_metrics.json()["total_transactions"] == 60

    # GET /api/discrepancies
    r_disc = api_client.get("/api/discrepancies?status=FEE_DISCREPANCY")
    assert r_disc.status_code == 200
    assert len(r_disc.json()) == 8

    # GET /api/order/{order_id}
    r_order = api_client.get("/api/order/ORD_1041")
    assert r_order.status_code == 200
    assert r_order.json()["order_id"] == "ORD_1041"

    # POST /api/chat
    r_chat = api_client.post("/api/chat", json={"message": "What is our reconciliation status?"})
    assert r_chat.status_code == 200
    assert "reply" in r_chat.json()
