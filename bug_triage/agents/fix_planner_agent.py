"""
Fix Planner Agent — Proposes root cause and patch plan with validation steps.
"""

import json
from shared.groq_client import call_llm
from shared.utils import parse_json_from_llm
from shared.logger import trace_agent
from config.prompts.a2_prompts import FIX_PLANNER_SYSTEM, FIX_PLANNER_USER


class FixPlannerAgent:

    @trace_agent("FixPlanner")
    def run(self, triage_output: dict, log_output: dict, repro_output: dict) -> dict:
        user_prompt = FIX_PLANNER_USER.format(
            triage_output=json.dumps(triage_output, indent=2),
            log_output=json.dumps(log_output, indent=2),
            repro_output=json.dumps(repro_output, indent=2)
        )

        response = call_llm(FIX_PLANNER_SYSTEM, user_prompt)
        result = parse_json_from_llm(response)

        return result
