"""
Triage Agent — Parses bug report, extracts symptoms, ranks hypotheses.
Pure LLM reasoning (no tools needed).
"""

from shared.groq_client import call_llm
from shared.utils import parse_json_from_llm
from shared.logger import trace_agent
from config.prompts.a2_prompts import TRIAGE_SYSTEM, TRIAGE_USER


class TriageAgent:

    @trace_agent("Triage")
    def run(self, bug_report_text: str) -> dict:
        # Pure LLM — no tools needed for triage
        user_prompt = TRIAGE_USER.format(bug_report=bug_report_text)

        response = call_llm(TRIAGE_SYSTEM, user_prompt)
        result = parse_json_from_llm(response)

        return result
