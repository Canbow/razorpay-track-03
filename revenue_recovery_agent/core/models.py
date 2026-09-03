"""Domain models and enumerations for Autonomous AI Revenue Recovery Engine."""
from decimal import Decimal
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class PaymentRail(str, Enum):
    """Supported payment rails."""
    UPI = "UPI"
    CARD = "CARD"
    NETBANKING = "NETBANKING"
    MANDATE = "MANDATE"


class FailureCategory(str, Enum):
    """Categorization of failure root causes."""
    TRANSIENT_DOWNTIME = "TRANSIENT_DOWNTIME"
    CUSTOMER_ACTIONABLE = "CUSTOMER_ACTIONABLE"
    TERMINAL_FAILURE = "TERMINAL_FAILURE"


class RecoveryAction(str, Enum):
    """Autonomous recovery actions taken by the agent."""
    SCHEDULED_SILENT_RETRY = "SCHEDULED_SILENT_RETRY"
    DISPATCH_DYNAMIC_LINK = "DISPATCH_DYNAMIC_LINK"
    ABORT_TERMINAL = "ABORT_TERMINAL"


class PaymentStatus(str, Enum):
    """Lifecycle status of a payment recovery attempt."""
    FAILED = "FAILED"
    RETRY_SCHEDULED = "RETRY_SCHEDULED"
    LINK_DISPATCHED = "LINK_DISPATCHED"
    RECOVERED = "RECOVERED"
    ABORTED_MAX_RETRIES = "ABORTED_MAX_RETRIES"


class FailedPaymentEvent(BaseModel):
    """Incoming failed payment webhook event representation."""
    model_config = ConfigDict(populate_by_name=True)

    invoice_id: str = Field(description="Unique invoice reference identifier (e.g., INV-001)")
    customer_id: str = Field(description="Customer reference identifier (e.g., CUST-101)")
    amount: Decimal = Field(description="Transaction amount in INR with exact decimal precision")
    payment_rail: PaymentRail = Field(description="Payment rail where the transaction failed")
    error_code: str = Field(description="Standardized error code from gateway/bank")
    error_description: str = Field(description="Human-readable description of payment failure")
    attempt_count: int = Field(default=0, ge=0, description="Number of prior recovery attempts already made")
    failed_at: str = Field(description="ISO 8601 timestamp of failure")
    is_locked: bool = Field(default=False, description="Idempotency lock preventing concurrent actions")


class RecoveryPlan(BaseModel):
    """Actionable recovery plan formulated by the agent."""
    invoice_id: str = Field(description="Unique invoice reference identifier")
    action: RecoveryAction = Field(description="Selected recovery action")
    target_rail: Optional[PaymentRail] = Field(default=None, description="Rail on which recovery will be executed")
    scheduled_at: Optional[str] = Field(default=None, description="ISO timestamp for scheduled silent retry")
    dynamic_link: Optional[str] = Field(default=None, description="Self-serve multi-rail checkout link")
    reasoning: str = Field(description="Deterministic AI rationale explaining decision")


class AuditLogRecord(BaseModel):
    """Immutable audit trail record for regulatory compliance and tracing."""
    timestamp: str = Field(description="Microsecond-precision ISO 8601 timestamp")
    invoice_id: str = Field(description="Unique invoice reference identifier")
    event_type: str = Field(description="Type of audit event (e.g., DIAGNOSIS, GUARD_EVALUATION, EXECUTION)")
    action: str = Field(description="Action executed or proposed")
    guard_check_passed: bool = Field(description="Whether all regulatory and business guardrails passed")
    details: Dict[str, Any] = Field(default_factory=dict, description="Detailed diagnostic context and metrics")
