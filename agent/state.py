"""State schema for LangGraph 3-Way Reconciliation Agent."""
import operator
from typing import Annotated, Any, Dict, List, Optional
from typing_extensions import TypedDict


class ReconciliationState(TypedDict):
    """LangGraph State representation for the financial reconciliation pipeline."""
    # Raw incoming batches
    raw_orders: List[Dict[str, Any]]
    raw_settlements: List[Dict[str, Any]]
    raw_bank_entries: List[Dict[str, Any]]

    # Indexed lookup tables
    indexed_orders: Dict[str, Dict[str, Any]]
    indexed_settlements_by_order: Dict[str, Dict[str, Any]]
    indexed_bank_by_utr: Dict[str, Dict[str, Any]]

    # State accumulation channels with operator.add reducers
    reconciled_records: Annotated[List[Dict[str, Any]], operator.add]
    exceptions_list: Annotated[List[Dict[str, Any]], operator.add]
    audit_trail: Annotated[List[Dict[str, Any]], operator.add]

    # Aggregated KPI & summary metrics
    summary_metrics: Dict[str, Any]
