"""Interactive Rich Terminal Chat for AI Finance Controller Copilot."""
import sys
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

# Ensure root is on path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from chat.controller import FinanceControllerAgent

console = Console(highlight=False)


def start_cli_chat():
    """Launch interactive Rich chat session."""
    agent = FinanceControllerAgent()
    summary = agent.get_financial_summary()

    welcome_banner = f"""
[bold cyan]AI FINANCE CONTROLLER COPILOT[/bold cyan] [green]v1.0.0[/green]
[dim]Razorpay Buildathon — Track 04: Agentic Financial Workflows[/dim]

[bold]Current Batch Health:[/bold]
• [bold green]Match Rate:[/bold green] {summary['match_rate']} ({summary['fully_reconciled']} Clean Matches)
• [bold red]Exceptions:[/bold red] {summary['total_exceptions']} Anomalies Flagged
• [bold yellow]Recoverable Overcharges:[/bold yellow] {summary['recoverable_fee_overcharge']}
• [bold magenta]Amount at Risk:[/bold magenta] {summary['total_amount_at_risk']}

[bold white]Available Slash Commands:[/bold white]
[cyan]/summary[/cyan]     - View executive KPI summary
[cyan]/overcharges[/cyan] - List all MDR fee leakage orders
[cyan]/unsettled[/cyan]   - List unsettled bank credits & ghost orders
[cyan]/dispute[/cyan]     - Generate formal Razorpay refund claim letter
[cyan]/bank[/cyan]        - Generate Bank UTR tracing inquiry
[cyan]/inspect ID[/cyan]  - Deep dive order (e.g. /inspect ORD_1041)
[cyan]/reconcile[/cyan]   - Re-run the 3-way reconciliation pipeline
[cyan]/help[/cyan]        - Show suggested questions
[cyan]/exit[/cyan]        - Exit chat session
"""

    console.print(Panel(welcome_banner.strip(), title="[bold white on blue] AI FINANCE COPILOT ACTIVE [/bold white on blue]", border_style="blue"))

    while True:
        try:
            user_input = Prompt.ask("\n[bold green]You[/bold green]")
            if not user_input or not user_input.strip():
                continue

            cmd = user_input.strip()

            if cmd.lower() in ["/exit", "exit", "quit", ":q"]:
                console.print("[yellow]Exiting AI Finance Controller. Have a great day![/yellow]")
                break

            if cmd.lower() == "/summary":
                cmd = "What is our reconciliation status today?"
            elif cmd.lower() == "/overcharges":
                cmd = "Show all fee overcharges and MDR leakage"
            elif cmd.lower() == "/unsettled":
                cmd = "Show unsettled bank entries and money at risk"
            elif cmd.lower() == "/dispute":
                cmd = "Generate Razorpay dispute claim letter"
            elif cmd.lower() == "/bank":
                cmd = "Generate Bank UTR inquiry sheet"
            elif cmd.lower().startswith("/inspect"):
                parts = cmd.split(maxsplit=1)
                order_arg = parts[1] if len(parts) > 1 else "ORD_1041"
                cmd = f"Inspect order {order_arg}"
            elif cmd.lower() == "/reconcile":
                cmd = "Run reconciliation now"
            elif cmd.lower() == "/help":
                cmd = "Help"

            console.print("\n[dim]AI Controller is analyzing financial ledgers...[/dim]")
            response = agent.chat(cmd)
            reply_md = response.get("reply", "")

            console.print("\n[bold blue]AI Controller[/bold blue]:")
            console.print(Markdown(reply_md))

        except KeyboardInterrupt:
            console.print("\n[yellow]Session interrupted. Goodbye![/yellow]")
            break
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")


if __name__ == "__main__":
    start_cli_chat()
