import json
from shared.groq_client import call_llm
from shared.utils import parse_json_from_llm
from shared.logger import trace_agent
from config.prompts.a1_prompts import FINANCE_SYSTEM, FINANCE_USER
from tools.metrics_tools import analyze_metrics


class FinanceAgent:

    @trace_agent("Finance")
    def run(self, metrics_data: dict) -> dict:
        metrics = metrics_data["metrics"]
        launch_day = metrics_data["launch_day_index"]

        # 1. Analyze payment + conversion metrics specifically
        finance_metrics = {
            k: v for k, v in metrics.items()
            if k in ("payment_success_rate", "conversion_rate", "error_rate")
        }
        metric_analysis = analyze_metrics(finance_metrics, launch_day)

        # 2. Build prompt and call LLM
        user_prompt = FINANCE_USER.format(
            metric_analysis=json.dumps(metric_analysis, indent=2)
        )

        response = call_llm(FINANCE_SYSTEM, user_prompt)
        result = parse_json_from_llm(response)

        return result
