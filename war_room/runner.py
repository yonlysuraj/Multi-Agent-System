"""
Assessment 1 — War Room Runner
Entry point that creates and runs the orchestrator, saves output.
"""

import sys
import os
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from shared.utils import save_json
from config.settings import settings
from war_room.orchestrator import WarRoomOrchestrator

# Force UTF-8 output on Windows
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

console = Console(force_terminal=True)


def run_war_room() -> dict:
    """
    Execute the full War Room decision pipeline.
    Returns the final decision dict and saves it to outputs/a1_decision.json.
    """
    console.print(Panel(
        "[bold magenta]WAR ROOM - Product Launch Decision[/bold magenta]\n"
        "Simulating a multi-agent war room to evaluate a product launch.\n"
        "Agents: DataAnalyst -> Marketing -> PM -> Finance -> Growth -> Risk -> Decision",
        border_style="magenta"
    ))

    # Run the orchestrator pipeline
    console.print("\n[bold cyan]Running War Room pipeline...[/bold cyan]\n")
    orchestrator = WarRoomOrchestrator()
    result = orchestrator.run()
    console.print("\n[bold green]Pipeline complete![/bold green]")

    # Save output
    output_path = Path(settings.OUTPUT_DIR) / "a1_decision.json"
    save_json(result, str(output_path))
    console.print(f"\n[green]Output saved to {output_path}[/green]")

    # Print summary
    _print_summary(result)

    return result


def _print_summary(result: dict):
    """Print a formatted summary of the War Room decision."""

    # Decision Panel
    decision = result.get("decision", "N/A")
    confidence = result.get("confidence_score", 0)
    decision_color = {
        "Proceed": "green",
        "Pause": "yellow",
        "Roll Back": "red"
    }.get(decision, "white")

    console.print(Panel(
        f"[bold {decision_color}]Decision: {decision}[/bold {decision_color}]\n"
        f"Confidence: {confidence}\n\n"
        f"{result.get('rationale', '')}",
        title="[WAR ROOM VERDICT]",
        border_style=decision_color
    ))

    # Agent Votes Table
    votes_table = Table(title="Agent Votes", show_lines=True)
    votes_table.add_column("Agent", style="cyan", width=18)
    votes_table.add_column("Recommendation", style="bold")

    for agent, vote in result.get("agent_votes", {}).items():
        vote_color = {"Proceed": "green", "Pause": "yellow", "Roll Back": "red"}.get(vote, "white")
        votes_table.add_row(agent, f"[{vote_color}]{vote}[/{vote_color}]")

    console.print(votes_table)

    # Vote Tally
    tally = result.get("vote_tally", {})
    tally_str = " | ".join(f"{k}: {v}" for k, v in tally.items())
    console.print(f"\n[bold]Vote Tally:[/bold] {tally_str}")

    # Action Plan
    console.print("\n[bold]ACTION PLAN:[/bold]")
    for item in result.get("action_plan", []):
        console.print(
            f"  - {item['action']} "
            f"[dim](Owner: {item['owner']} | {item['timeframe']})[/dim]"
        )

    # Risk Register
    risks = result.get("risk_register", [])
    if risks:
        console.print("\n[bold]RISK REGISTER:[/bold]")
        for risk in risks[:5]:
            if isinstance(risk, dict):
                console.print(
                    f"  - [yellow]{risk.get('risk', 'N/A')}[/yellow] "
                    f"(Likelihood: {risk.get('likelihood', '?')}, "
                    f"Impact: {risk.get('impact', '?')})"
                )

    console.print()
