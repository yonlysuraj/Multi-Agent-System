"""Entry function for Assessment 2."""

from bug_triage.orchestrator import A2Orchestrator


def run_bug_triage() -> dict:
    """Run the full Assessment 2 - Bug Triage pipeline."""
    orchestrator = A2Orchestrator()
    result = orchestrator.run()
    return result
