"""Executable CLI runner for AI Finance Controller 3-Way Reconciliation."""
import argparse
import json
import os
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Optional

from rich.console import Console
from rich.panel import Panel
from tabulate import tabulate

# Ensure current repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent.graph import get_compiled_graph
from audit.logger import AuditLogger
from data.csv_adapter import export_sample_csvs, load_csv_dataset
from data.generate_batch import generate_dataset, get_dataset_path

console = Console(highlight=False)


def run_pipeline(
    dataset_file: Optional[Path] = None,
    orders_csv: Optional[Path] = None,
    settlements_csv: Optional[Path] = None,
    bank_csv: Optional[Path] = None,
    audit_file: Optional[Path] = None,
) -> Dict[str, Any]:
    """Execute the end-to-end 3-way reconciliation pipeline from JSON or CSV feeds."""
    log_path = audit_file or (REPO_ROOT / "audit_trail.jsonl")

    # Determine input source
    if orders_csv and settlements_csv and bank_csv:
        console.print(f"[bold blue]Ingesting CSV Sources:[/bold blue]")
        console.print(f"  • Orders:      [cyan]{orders_csv}[/cyan]")
        console.print(f"  • Settlements: [cyan]{settlements_csv}[/cyan]")
        console.print(f"  • Bank Feed:   [cyan]{bank_csv}[/cyan]\n")
        dataset = load_csv_dataset(orders_csv, settlements_csv, bank_csv)
    else:
        data_path = dataset_file or get_dataset_path()
        if not data_path.exists():
            console.print(f"[yellow]Dataset not found at {data_path}. Generating benchmark batch...[/yellow]")
            generate_dataset(data_path)

        with open(data_path, "r", encoding="utf-8") as f:
            dataset = json.load(f)

    # Initialize LangGraph State
    initial_state = {
        "raw_orders": dataset.get("internal_orders", []),
        "raw_settlements": dataset.get("razorpay_settlements", []),
        "raw_bank_entries": dataset.get("bank_statement_entries", []),
        "indexed_orders": {},
        "indexed_settlements_by_order": {},
        "indexed_bank_by_utr": {},
        "reconciled_records": [],
        "exceptions_list": [],
        "audit_trail": [],
        "summary_metrics": {},
    }

    # Run compiled graph
    console.print("[bold blue]Executing LangGraph 3-Way Reconciliation Workflow...[/bold blue]")
    graph = get_compiled_graph()
    final_state = graph.invoke(initial_state)

    # Write structured audit log
    logger = AuditLogger(log_path=log_path)
    logger.clear()
    for entry in final_state.get("audit_trail", []):
        logger.log(entry)

    console.print(f"[green][OK] Audit trail written atomically to: {log_path}[/green]\n")
    return final_state


def display_results(final_state: Dict[str, Any]) -> None:
    """Render high-fidelity terminal summary cards and tabulate exception table."""
    metrics = final_state.get("summary_metrics", {})
    exceptions = final_state.get("exceptions_list", [])

    # Display Metrics Summary Panel
    status_counts = metrics.get("status_breakdown", {})
    summary_text = f"""
[bold green]Total Transactions Processed:[/bold green] {metrics.get('total_records')}
[bold green]Match Rate (Fully Reconciled):[/bold green] {metrics.get('match_rate_pct')}% ({metrics.get('total_reconciled')} orders)
[bold red]Exception Rate:[/bold red] {metrics.get('exception_rate_pct')}% ({metrics.get('total_exceptions')} orders)

[bold cyan]Financial Exposure Breakdown:[/bold cyan]
  - Total Volume Processed:        INR {Decimal(metrics.get('total_volume_processed', 0)):,.2f}
  - Total Amount at Risk:          INR {Decimal(metrics.get('total_amount_at_risk', 0)):,.2f}
  - Recoverable MDR Overcharge:    INR {Decimal(metrics.get('total_fee_overcharges_recoverable', 0)):,.2f}

[bold yellow]Status Categorization:[/bold yellow]
  - FULLY_RECONCILED:         {status_counts.get('FULLY_RECONCILED', 0)}
  - FEE_DISCREPANCY (3% MDR): {status_counts.get('FEE_DISCREPANCY', 0)}
  - UNSETTLED_BY_BANK:        {status_counts.get('UNSETTLED_BY_BANK', 0)}
  - MISSING_GATEWAY_RECORD:   {status_counts.get('MISSING_GATEWAY_RECORD', 0)}
  - UNRESOLVED_EXCEPTION:     {status_counts.get('UNRESOLVED_EXCEPTION', 0)}
"""
    console.print(Panel(summary_text.strip(), title="[bold white on blue] AI FINANCE CONTROLLER - EXECUTIVE RECONCILIATION SUMMARY [/bold white on blue]", expand=False))

    # Build Tabulate Exception Table
    table_data = []
    for exc in exceptions:
        order_id = exc.get("order_id")
        raw_status = exc.get("status")
        status = raw_status.value if hasattr(raw_status, "value") else str(raw_status).replace("ReconciliationStatus.", "")
        amt = f"INR {Decimal(str(exc.get('order_amount') or 0)):,.2f}"
        net = f"INR {Decimal(str(exc.get('net_settlement') or 0)):,.2f}" if exc.get("net_settlement") is not None else "N/A"
        bank = f"INR {Decimal(str(exc.get('bank_credit') or 0)):,.2f}" if exc.get("bank_credit") is not None else "N/A"
        delta = f"INR {Decimal(str(exc.get('fee_delta') or 0)):,.2f}" if exc.get("fee_delta") is not None else "-"
        reason = exc.get("discrepancy_reason") or "N/A"
        action = exc.get("action_required") or "N/A"

        table_data.append([
            order_id,
            status,
            amt,
            net,
            bank,
            delta,
            reason,
            action
        ])

    headers = [
        "Order ID",
        "Recon Status",
        "Order Amt",
        "Gateway Net",
        "Bank Credit",
        "Fee Delta",
        "Discrepancy Root Cause",
        "Action Item"
    ]

    console.print("\n[bold red]DETAILED EXCEPTIONS & DISCREPANCIES TABLE:[/bold red]")
    print(tabulate(table_data, headers=headers, tablefmt="grid", maxcolwidths=[12, 22, 14, 14, 14, 12, 35, 35]))


def main():
    parser = argparse.ArgumentParser(
        description="AI Finance Controller: 3-Way Reconciliation CLI & CSV Ingestion Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run on default 60-record benchmark batch:
  python run_reconciliation.py

  # Run on real CSV files:
  python run_reconciliation.py --orders orders.csv --settlements razorpay.csv --bank bank.csv

  # Export sample CSV files for testing:
  python run_reconciliation.py --export-samples
        """
    )
    parser.add_argument("--orders", type=Path, help="Path to Internal Orders CSV (OMS)")
    parser.add_argument("--settlements", type=Path, help="Path to Razorpay Settlements CSV")
    parser.add_argument("--bank", type=Path, help="Path to Bank Statement Credits CSV")
    parser.add_argument("--dataset", type=Path, help="Path to JSON dataset file")
    parser.add_argument("--audit-file", type=Path, help="Custom path for output audit_trail.jsonl")
    parser.add_argument("--export-samples", action="store_true", help="Export benchmark batch to sample CSV files in data/samples/")

    args = parser.parse_args()

    if args.export_samples:
        paths = export_sample_csvs()
        console.print("[bold green]Successfully exported sample CSV files:[/bold green]")
        for k, p in paths.items():
            console.print(f"  • {k}: [cyan]{p}[/cyan]")
        console.print("\nYou can now run:\n[bold yellow]python run_reconciliation.py --orders data/samples/sample_orders.csv --settlements data/samples/sample_razorpay.csv --bank data/samples/sample_bank.csv[/bold yellow]")
        return

    # Check if partial CSV flags passed
    csv_flags = [args.orders, args.settlements, args.bank]
    if any(csv_flags) and not all(csv_flags):
        console.print("[bold red]Error:[/bold red] To run CSV reconciliation, you must provide all 3 flags: --orders, --settlements, and --bank.")
        sys.exit(1)

    final_state = run_pipeline(
        dataset_file=args.dataset,
        orders_csv=args.orders,
        settlements_csv=args.settlements,
        bank_csv=args.bank,
        audit_file=args.audit_file,
    )
    display_results(final_state)


if __name__ == "__main__":
    main()
