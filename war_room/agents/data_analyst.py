import json
from shared.groq_client import call_llm
from shared.utils import parse_json_from_llm
from shared.logger import trace_agent
from config.prompts.a1_prompts import DATA_ANALYST_SYSTEM, DATA_ANALYST_USER
from tools.metrics_tools import analyze_metrics, detect_anomalies


class DataAnalystAgent:

    @trace_agent("DataAnalyst")
    def run(self, metrics_data: dict) -> dict:
        metrics = metrics_data["metrics"]
        launch_day = metrics_data["launch_day_index"]

        # 1. Analyze all metrics
        metric_analysis = analyze_metrics(metrics, launch_day)

        # 2. Detect anomalies on key metrics
        anomaly_results = {}
        for metric_name in ["error_rate", "api_latency_p95", "support_tickets"]:
            if metric_name in metrics:
                anomaly_results[metric_name] = detect_anomalies(metrics[metric_name])

        # 3. Build prompt and call LLM
        user_prompt = DATA_ANALYST_USER.format(
            metric_analysis=json.dumps(metric_analysis, indent=2),
            anomaly_results=json.dumps(anomaly_results, indent=2)
        )

        response = call_llm(DATA_ANALYST_SYSTEM, user_prompt)
        result = parse_json_from_llm(response)

        return result
