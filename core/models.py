"""Financial domain models with zero float tolerance."""
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ReconciliationStatus(str, Enum):
    FULLY_RECONCILED = "FULLY_RECONCILED"
    FEE_DISCREPANCY = "FEE_DISCREPANCY"
    UNSETTLED_BY_BANK = "UNSETTLED_BY_BANK"
    MISSING_GATEWAY_RECORD = "MISSING_GATEWAY_RECORD"
    UNRESOLVED_EXCEPTION = "UNRESOLVED_EXCEPTION"


class InternalOrder(BaseModel):
    model_config = ConfigDict(extra="ignore")

    order_id: str
    amount: Decimal = Field(..., description="Gross order amount including taxes")
    tax_amount: Decimal = Field(default=Decimal("0.00"), description="Internal tax component")
    customer_id: str
    status: str = Field(default="PAID", description="Order status in OMS, e.g. PAID, PENDING")
    created_at: str


class RazorpaySettlement(BaseModel):
    model_config = ConfigDict(extra="ignore")

    payment_id: str
    order_id: str
    gross_amount: Decimal = Field(..., description="Gross amount collected by Razorpay")
    fee: Decimal = Field(..., description="MDR fee deducted by Razorpay")
    tax_on_fee: Decimal = Field(..., description="GST on MDR fee (18%)")
    net_amount: Decimal = Field(..., description="Net settlement credited to merchant")
    utr: Optional[str] = Field(default=None, description="Unique Transaction Reference for bank payout")
    settled_at: str


class BankStatementEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")

    bank_ref: str
    utr: str
    credit_amount: Decimal = Field(..., description="Amount credited into the merchant bank account")
    value_date: str
    description: str


class AuditLogEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")

    timestamp: str
    order_id: str
    step: str
    action_taken: str
    math_verified: bool
    details: Dict[str, Any] = Field(default_factory=dict)


class ReconciliationResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    order_id: str
    status: ReconciliationStatus
    order_amount: Optional[Decimal] = None
    gross_amount: Optional[Decimal] = None
    net_settlement: Optional[Decimal] = None
    bank_credit: Optional[Decimal] = None
    fee_charged: Optional[Decimal] = None
    expected_fee: Optional[Decimal] = None
    fee_delta: Optional[Decimal] = None
    utr: Optional[str] = None
    discrepancy_reason: Optional[str] = None
    action_required: Optional[str] = None
    audit_events: List[AuditLogEntry] = Field(default_factory=list)
