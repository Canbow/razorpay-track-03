"""State definitions for the LangGraph recovery workflow with operator.add reducers."""
import operator
from typing import Annotated, List, Optional, Dict, Any
from typing_extensions import TypedDict


class RecoveryGraphState(TypedDict, total=False):
    """
    LangGraph state schema for Autonomous AI Revenue Recovery.
    Uses operator.add reducers for accumulating recovery outcomes and audit traces.
    """
    # Current transaction under evaluation
    event: Dict[str, Any]
    current_hour_ist: int

    # Intermediate diagnostic & guard decisions
    failure_category: Optional[str]
    guard_passed: Optional[bool]
    guard_message: Optional[str]
    recovery_plan: Optional[Dict[str, Any]]
    recovery_status: Optional[str]

    # Accumulated reducers across pipeline executions
    recovered_events: Annotated[List[Dict[str, Any]], operator.add]
    scheduled_retries: Annotated[List[Dict[str, Any]], operator.add]
    dispatched_links: Annotated[List[Dict[str, Any]], operator.add]
    aborted_events: Annotated[List[Dict[str, Any]], operator.add]
    audit_trail: Annotated[List[Dict[str, Any]], operator.add]
