"""LangGraph orchestration wiring the closed-loop recovery workflow."""
from langgraph.graph import StateGraph, START, END

from revenue_recovery_agent.agent.state import RecoveryGraphState
from revenue_recovery_agent.agent.nodes import (
    diagnose_node,
    policy_guard_node,
    execution_node,
)


def create_recovery_graph():
    """
    Constructs and compiles the deterministic recovery StateGraph:
    START -> diagnose -> policy_guard -> execution -> END
    """
    workflow = StateGraph(RecoveryGraphState)

    # Register workflow nodes
    workflow.add_node("diagnose", diagnose_node)
    workflow.add_node("policy_guard", policy_guard_node)
    workflow.add_node("execution", execution_node)

    # Wire deterministic linear flow with internal guard branching
    workflow.add_edge(START, "diagnose")
    workflow.add_edge("diagnose", "policy_guard")
    workflow.add_edge("policy_guard", "execution")
    workflow.add_edge("execution", END)

    return workflow.compile()
