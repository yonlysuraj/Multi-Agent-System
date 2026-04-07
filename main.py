"""
PurpleMerit AI/ML Assessment - CLI Entry Point
Usage:
    python main.py --task a1      # War Room Decision
    python main.py --task a2      # Bug Triage
    python main.py --task both    # Run both
"""

import argparse
import sys
from rich.console import Console
from rich.panel import Panel

console = Console()


def main():
    parser = argparse.ArgumentParser(
        description="PurpleMerit AI/ML Multi-Agent Assessment"
    )
    parser.add_argument(
        "--task",
        choices=["a1", "a2", "both"],
        required=True,
        help="Which assessment to run: a1 (War Room), a2 (Bug Triage), or both"
    )
    args = parser.parse_args()

    console.print(Panel(
        "[bold cyan]PurpleMerit AI/ML Assessment[/bold cyan]\n"
        f"Task: {args.task}",
        title="Starting",
        border_style="cyan"
    ))

    if args.task in ("a1", "both"):
        console.print("\n[bold]--- Assessment 1: War Room Decision ---[/bold]\n")
        try:
            from war_room.runner import run_war_room
            result = run_war_room()
            decision = result.get("decision", "N/A")
            console.print(f"\n[green]Assessment 1 complete. Decision: {decision}[/green]")
        except Exception as e:
            console.print(f"\n[bold red]Assessment 1 failed: {e}[/bold red]")

    if args.task in ("a2", "both"):
        console.print("\n[bold]--- Assessment 2: Bug Triage ---[/bold]\n")
        try:
            from bug_triage.runner import run_bug_triage
            result = run_bug_triage()
            reproduced = result.get("repro_artifact", {}).get("reproduced", False)
            console.print(f"\n[green]Assessment 2 complete. Bug reproduced: {reproduced}[/green]")
        except Exception as e:
            console.print(f"\n[bold red]Assessment 2 failed: {e}[/bold red]")

    console.print(Panel("[bold green]All tasks complete![/bold green]", border_style="green"))


if __name__ == "__main__":
    main()
