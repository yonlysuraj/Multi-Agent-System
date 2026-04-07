"""
Log Analyst Agent — Parses logs, extracts stack traces, correlates with hypotheses.
"""

import json
from shared.groq_client import call_llm
from shared.utils import parse_json_from_llm
from shared.logger import trace_agent
from config.prompts.a2_prompts import LOG_ANALYST_SYSTEM, LOG_ANALYST_USER
from tools.log_tools import parse_logs, extract_stack_traces, search_log_pattern


class LogAnalystAgent:

    @trace_agent("LogAnalyst")
    def run(self, log_text: str, triage_output: dict) -> dict:
        # 1. Parse all log lines
        parsed_logs = parse_logs(log_text)

        # 2. Extract stack traces
        stack_traces = extract_stack_traces(log_text)

        # 3. Search for key patterns from triage hints
        search_terms = triage_output.get("key_search_terms", ["AttributeError", "NoneType", "500"])
        pattern_results = {}
        for term in search_terms:
            pattern_results[term] = search_log_pattern(log_text, term)

        # 4. Build prompt and call LLM
        user_prompt = LOG_ANALYST_USER.format(
            triage_output=json.dumps(triage_output, indent=2),
            parsed_logs=json.dumps({
                "total_lines": parsed_logs["total_lines"],
                "error_count": parsed_logs["error_count"],
                "warn_count": parsed_logs["warn_count"],
                # Send only error/warning lines to keep prompt size manageable
                "error_lines": [
                    l for l in parsed_logs["parsed_lines"]
                    if l.get("level") in ("ERROR", "CRITICAL", "WARNING")
                ][:30]  # Cap at 30 to avoid token overflow
            }, indent=2),
            stack_traces=json.dumps([
                {"trace_text": t["trace_text"][:500],
                 "exception_type": t["exception_type"],
                 "line_ref": t["line_ref"]}
                for t in stack_traces[:10]  # Cap at 10 unique traces
            ], indent=2),
            pattern_results=json.dumps({
                k: {"count": v["count"], "first_occurrence": v["first_occurrence"]}
                for k, v in pattern_results.items()
            }, indent=2)
        )

        response = call_llm(LOG_ANALYST_SYSTEM, user_prompt)
        result = parse_json_from_llm(response)

        return result
