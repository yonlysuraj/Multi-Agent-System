import json
from shared.groq_client import call_llm
from shared.utils import parse_json_from_llm
from shared.logger import trace_agent
from config.prompts.a1_prompts import PM_SYSTEM, PM_USER



class PMAgent:

    @trace_agent("ProductManager")
    def run(self, analyst_output: dict, marketing_output: dict, release_notes: str) -> dict:
        # 1. Build prompt with all prior agent outputs + release notes
        user_prompt = PM_USER.format(
            analyst_output=json.dumps(analyst_output, indent=2),
            marketing_output=json.dumps(marketing_output, indent=2),
            release_notes=release_notes
        )

        # 2. Call LLM for PM assessment
        response = call_llm(PM_SYSTEM, user_prompt)
        result = parse_json_from_llm(response)

        return result
