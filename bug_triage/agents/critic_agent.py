"""
Critic Agent — Adversarial reviewer of the entire diagnosis and fix plan.
"""

import json
from shared.groq_client import call_llm
from shared.utils import parse_json_from_llm
from shared.logger import trace_agent
from config.prompts.a2_prompts import CRITIC_SYSTEM, CRITIC_USER


class CriticAgent:

    @trace_agent("Critic")
    def run(self, triage_output: dict, log_output: dict,
            repro_output: dict, fix_output: dict) -> dict:
        user_prompt = CRITIC_USER.format(
            triage_output=json.dumps(triage_output, indent=2),
            log_output=json.dumps(log_output, indent=2),
            repro_output=json.dumps(repro_output, indent=2),
            fix_output=json.dumps(fix_output, indent=2)
        )

        response = call_llm(CRITIC_SYSTEM, user_prompt)
        result = parse_json_from_llm(response)

        return result
