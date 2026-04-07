import json
from shared.groq_client import call_llm
from shared.utils import parse_json_from_llm
from shared.logger import trace_agent
from config.prompts.a1_prompts import GROWTH_SYSTEM, GROWTH_USER
from tools.metrics_tools import analyze_metrics, trend_compare


class GrowthAgent:

    @trace_agent("Growth")
    def run(self, metrics_data: dict) -> dict:
        metrics = metrics_data["metrics"]
        launch_day = metrics_data["launch_day_index"]

        # 1. Analyze engagement-specific metrics
        growth_metrics = {
            k: v for k, v in metrics.items()
            if k in ("dau_wau", "retention_d1", "retention_d7", "conversion_rate")
        }
        metric_analysis = analyze_metrics(growth_metrics, launch_day)

        # 2. Compare against growth thresholds
        thresholds = {
            "dau_wau": {"threshold": 0.35, "direction": "above"},
            "retention_d1": {"threshold": 0.55, "direction": "above"},
            "retention_d7": {"threshold": 0.30, "direction": "above"},
            "conversion_rate": {"threshold": 0.10, "direction": "above"}
        }
        threshold_results = {}
        for metric_name, config in thresholds.items():
            if metric_name in metrics:
                threshold_results[metric_name] = trend_compare(
                    metrics[metric_name], {metric_name: config}
                )[metric_name]

        # 3. Build prompt and call LLM
        user_prompt = GROWTH_USER.format(
            metric_analysis=json.dumps(metric_analysis, indent=2),
            threshold_results=json.dumps(threshold_results, indent=2)
        )

        response = call_llm(GROWTH_SYSTEM, user_prompt)
        result = parse_json_from_llm(response)

        return result
