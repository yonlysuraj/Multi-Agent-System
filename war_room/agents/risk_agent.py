import json
from shared.groq_client import call_llm
from shared.utils import parse_json_from_llm
from shared.logger import trace_agent
from config.prompts.a1_prompts import RISK_SYSTEM, RISK_USER
from tools.metrics_tools import detect_anomalies


class RiskAgent:

    @trace_agent("RiskCritic")
    def run(self, analyst_output: dict, marketing_output: dict,
            pm_output: dict, metrics_data: dict, release_notes: str = "") -> dict:
        # 1. Re-run anomaly detection with stricter threshold (1.5 instead of 2.0)
        metrics = metrics_data["metrics"]
        strict_anomalies = {}
        for metric_name in metrics:
            strict_anomalies[metric_name] = detect_anomalies(
                metrics[metric_name], z_threshold=1.5
            )

        # 2. Build prompt with all prior outputs + release notes + stricter anomaly check
        user_prompt = RISK_USER.format(
            release_notes=release_notes,
            analyst_output=json.dumps(analyst_output, indent=2),
            marketing_output=json.dumps(marketing_output, indent=2),
            pm_output=json.dumps(pm_output, indent=2),
            strict_anomalies=json.dumps(strict_anomalies, indent=2)
        )

        # 3. Call LLM as adversarial reviewer
        response = call_llm(RISK_SYSTEM, user_prompt)
        result = parse_json_from_llm(response)

        return result
