import json
from shared.groq_client import call_llm
from shared.utils import parse_json_from_llm
from shared.logger import trace_agent
from config.prompts.a1_prompts import MARKETING_SYSTEM, MARKETING_USER
from tools.feedback_tools import sentiment_analysis, summarize_feedback, cluster_themes


class MarketingAgent:

    @trace_agent("MarketingComms")
    def run(self, feedback_data: dict) -> dict:
        feedback_texts = [f["text"] for f in feedback_data["feedback"]]

        # 1. Sentiment analysis
        sentiment_results = sentiment_analysis(feedback_texts)

        # 2. Theme clustering
        theme_results = cluster_themes(feedback_texts)

        # 3. Keyword summary
        summary_results = summarize_feedback(feedback_texts)

        # 4. Build prompt and call LLM
        user_prompt = MARKETING_USER.format(
            sentiment_results=json.dumps(sentiment_results, indent=2),
            theme_results=json.dumps(theme_results, indent=2),
            summary_results=json.dumps(summary_results, indent=2),
            feedback_samples=json.dumps(feedback_data["feedback"][:10], indent=2)
        )

        response = call_llm(MARKETING_SYSTEM, user_prompt)
        result = parse_json_from_llm(response)

        return result
