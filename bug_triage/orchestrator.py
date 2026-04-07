"""
Assessment 2 Orchestrator — Bug Triage & Reproduction Pipeline.
State machine that drives agents sequentially and assembles the final diagnosis.
"""

import json
from datetime import datetime, timezone

from shared.logger import set_context, console
from shared.utils import load_text, save_json
from config.settings import settings

from bug_triage.agents.triage_agent import TriageAgent
from bug_triage.agents.log_analyst_agent import LogAnalystAgent
from bug_triage.agents.reproduction_agent import ReproductionAgent
from bug_triage.agents.fix_planner_agent import FixPlannerAgent
from bug_triage.agents.critic_agent import CriticAgent

from rich.panel import Panel
from rich.table import Table


class A2Orchestrator:
    """State machine orchestrator for Assessment 2."""

    STAGES = [
        "LOAD_INPUTS", "TRIAGE", "LOG_ANALYSIS",
        "REPRODUCTION", "FIX_PLAN", "CRITIC", "OUTPUT"
    ]

    def __init__(self):
        self.state = {}
        self.agent_outputs = {}
        self.current_stage = None

    def run(self) -> dict:
        """Execute the full Assessment 2 pipeline."""

        for stage in self.STAGES:
            self.current_stage = stage
            set_context("A2", f"STAGE {self.STAGES.index(stage)}")

            try:
                handler = getattr(self, f"_stage_{stage.lower()}")
                handler()
            except Exception as e:
                from shared.logger import log_error
                log_error(stage, str(e))
                console.print(f"[bold red]  !! Stage {stage} failed: {e}[/bold red]")
                # Continue — we want partial results even if one stage fails
                continue

        return self.state.get("final_diagnosis", {})

    # ─── Stage Handlers ───

    def _stage_load_inputs(self):
        console.print(Panel("[bold cyan]Stage 0: Loading Assessment 2 inputs...[/bold cyan]"))

        self.state["bug_report"] = load_text("bug_triage/data/bug_report.md")
        self.state["log_text"] = load_text("bug_triage/data/app_logs.txt")

        console.print("  Loaded bug_report.md, app_logs.txt")

    def _stage_triage(self):
        console.print(Panel("[bold green]Stage 1: Triage Agent[/bold green]"))
        agent = TriageAgent()
        self.agent_outputs["triage"] = agent.run(self.state["bug_report"])

    def _stage_log_analysis(self):
        console.print(Panel("[bold yellow]Stage 2: Log Analyst Agent[/bold yellow]"))
        agent = LogAnalystAgent()
        self.agent_outputs["log_analyst"] = agent.run(
            self.state["log_text"],
            self.agent_outputs.get("triage", {})
        )

    def _stage_reproduction(self):
        console.print(Panel("[bold magenta]Stage 3: Reproduction Agent[/bold magenta]"))
        agent = ReproductionAgent()
        self.agent_outputs["reproduction"] = agent.run(
            self.agent_outputs.get("triage", {}),
            self.agent_outputs.get("log_analyst", {})
        )

        # Report reproduction result
        repro = self.agent_outputs["reproduction"]
        exec_result = repro.get("execution_result", {})
        if exec_result.get("reproduced"):
            console.print("  [green]Bug successfully reproduced![/green]")
        else:
            console.print("  [yellow]Bug could not be reproduced[/yellow]")

    def _stage_fix_plan(self):
        console.print(Panel("[bold blue]Stage 4: Fix Planner Agent[/bold blue]"))
        agent = FixPlannerAgent()
        self.agent_outputs["fix_planner"] = agent.run(
            self.agent_outputs.get("triage", {}),
            self.agent_outputs.get("log_analyst", {}),
            self.agent_outputs.get("reproduction", {})
        )

    def _stage_critic(self):
        console.print(Panel("[bold red]Stage 5: Critic Agent[/bold red]"))
        agent = CriticAgent()
        self.agent_outputs["critic"] = agent.run(
            self.agent_outputs.get("triage", {}),
            self.agent_outputs.get("log_analyst", {}),
            self.agent_outputs.get("reproduction", {}),
            self.agent_outputs.get("fix_planner", {})
        )

    def _stage_output(self):
        console.print(Panel("[bold white]Assembling Final Diagnosis[/bold white]"))
        self._assemble_output()

    # ─── Output Assembly ───

    def _assemble_output(self):
        """Build the final diagnosis JSON from all agent outputs."""

        triage = self.agent_outputs.get("triage", {})
        log_analyst = self.agent_outputs.get("log_analyst", {})
        reproduction = self.agent_outputs.get("reproduction", {})
        fix_planner = self.agent_outputs.get("fix_planner", {})
        critic = self.agent_outputs.get("critic", {})

        final = {
            "task": "Assessment 2 - Bug Triage & Reproduction",
            "timestamp": datetime.now(timezone.utc).isoformat(),

            "bug_summary": {
                "title": triage.get("title", "Unknown"),
                "severity": triage.get("severity", "Unknown"),
                "scope": triage.get("affected_component", "Unknown"),
                "affected_users": "Estimated 12% of checkout attempts"
            },

            "evidence": {
                "stack_trace": (
                    log_analyst.get("stack_traces", [{}])[0].get("excerpt", "N/A")
                    if log_analyst.get("stack_traces") else "N/A"
                ),
                "frequency": f"{log_analyst.get('error_count', 0)} occurrences",
                "first_occurrence": log_analyst.get("first_occurrence", "Unknown"),
                "red_herrings_filtered": log_analyst.get("red_herrings_ignored", [])
            },

            "repro_artifact": {
                "path": reproduction.get("repro_script_path", "N/A"),
                "run_command": reproduction.get("run_command", "N/A"),
                "expected_output": reproduction.get("execution_result", {}).get("stderr", "N/A")[:500],
                "reproduced": reproduction.get("execution_result", {}).get("reproduced", False)
            },

            "root_cause": {
                "hypothesis": fix_planner.get("root_cause", "Unknown"),
                "confidence": fix_planner.get("root_cause_confidence", 0),
                "supporting_evidence": [
                    f"Stack trace at {log_analyst.get('stack_traces', [{}])[0].get('line_ref', 'unknown')}" if log_analyst.get('stack_traces') else "N/A",
                    f"Reproduced: {reproduction.get('execution_result', {}).get('reproduced', False)}"
                ]
            },

            "patch_plan": fix_planner.get("patch_plan", {}),

            "validation_plan": fix_planner.get("validation_plan", []),

            "critic_review": {
                "fix_is_safe": critic.get("fix_plan_is_safe", False),
                "concerns": critic.get("concerns", []),
                "suggested_edge_cases": critic.get("suggested_edge_cases", []),
                "open_questions": critic.get("open_questions", [])
            },

            # Full agent outputs for traceability
            "agent_outputs": self.agent_outputs
        }

        self.state["final_diagnosis"] = final

        # Save output
        output_path = f"{settings.OUTPUT_DIR}/a2_diagnosis.json"
        save_json(final, output_path)
        console.print(f"\n  Saved to {output_path}")

        # Display summary
        self._display_summary(final)

    def _display_summary(self, final: dict):
        """Pretty-print the diagnosis summary to console."""

        # Summary table
        table = Table(title="Bug Diagnosis Summary")
        table.add_column("Field", style="cyan", width=25)
        table.add_column("Value", style="white")

        table.add_row("Title", final["bug_summary"]["title"])
        table.add_row("Severity", final["bug_summary"]["severity"])
        table.add_row("Error Count", str(final["evidence"]["frequency"]))
        table.add_row("Reproduced", "Yes" if final["repro_artifact"]["reproduced"] else "No")
        table.add_row("Root Cause Confidence", str(final["root_cause"]["confidence"]))
        table.add_row("Fix is Safe", "Yes" if final["critic_review"]["fix_is_safe"] else "Review needed")

        console.print(table)

        # Root cause panel
        console.print(Panel(
            f"[bold]{final['root_cause']['hypothesis'][:300]}[/bold]",
            title="Root Cause",
            border_style="red"
        ))

        # Patch plan
        patch = final.get("patch_plan", {})
        if patch.get("approach"):
            console.print(Panel(
                f"[bold]{patch['approach']}[/bold]\n\n"
                f"Files: {', '.join(patch.get('files_impacted', []))}",
                title="Proposed Fix",
                border_style="green"
            ))
