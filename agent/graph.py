"""StateGraph definition and compilation for 3-way reconciliation pipeline."""
from langgraph.graph import StateGraph, START, END
from agent.state import ReconciliationState
from agent.nodes import ingest_node, match_exact_node, synthesize_metrics_node


def build_reconciliation_graph() -> StateGraph:
    """Build and wire the reconciliation StateGraph."""
    graph = StateGraph(ReconciliationState)

    # Register nodes
    graph.add_node("ingest_node", ingest_node)
    graph.add_node("match_exact_node", match_exact_node)
    graph.add_node("synthesize_metrics_node", synthesize_metrics_node)

    # Define linear execution workflow
    graph.add_edge(START, "ingest_node")
    graph.add_edge("ingest_node", "match_exact_node")
    graph.add_edge("match_exact_node", "synthesize_metrics_node")
    graph.add_edge("synthesize_metrics_node", END)

    return graph


def get_compiled_graph():
    """Compile and return the executable LangGraph workflow."""
    workflow = build_reconciliation_graph()
    return workflow.compile()
