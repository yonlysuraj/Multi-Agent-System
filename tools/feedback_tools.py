"""
Feedback analysis tools — TextBlob sentiment + keyword extraction.
No GPU. No API calls. Runs fully offline.
Used by Marketing agent.
"""

from textblob import TextBlob
from collections import Counter
import re
from shared.logger import log_tool_call, log_tool_result


def sentiment_analysis(feedback_list: list[str]) -> dict:
    """
    Runs TextBlob polarity on each feedback item.
    Returns: {scores: [...], mean_score: float, breakdown: {positive, neutral, negative}}
    No GPU. No API call. Runs offline.
    """
    log_tool_call("sentiment_analysis", f"{len(feedback_list)} items")

    scores = []
    for text in feedback_list:
        blob = TextBlob(text)
        scores.append(round(blob.sentiment.polarity, 3))

    positive = sum(1 for s in scores if s > 0.1)
    negative = sum(1 for s in scores if s < -0.1)
    neutral = len(scores) - positive - negative
    mean_score = round(sum(scores) / len(scores), 3) if scores else 0.0

    result = {
        "scores": scores,
        "mean_score": mean_score,
        "breakdown": {"positive": positive, "neutral": neutral, "negative": negative}
    }

    log_tool_result("sentiment_analysis", f"mean={mean_score}, pos={positive}, neg={negative}")
    return result


def summarize_feedback(feedback_list: list[str], top_n: int = 5) -> dict:
    """
    TF-IDF based keyword extraction to find top recurring phrases.
    Returns: {top_phrases: [...], frequency_map: {...}}
    """
    log_tool_call("summarize_feedback", f"{len(feedback_list)} items, top_n={top_n}")

    stop_words = {
        "the", "a", "an", "is", "it", "to", "and", "of", "in", "for", "on",
        "with", "my", "i", "this", "that", "was", "but", "not", "are", "have",
        "has", "had", "be", "been", "do", "does", "did", "so", "at", "from",
        "or", "can", "will", "just", "when", "after", "very", "too", "me",
        "its", "than", "then", "they", "them", "their", "what", "which",
        "who", "how", "all", "each", "every", "some", "any", "few", "more",
        "most", "other", "into", "over", "such", "now", "get", "got", "like"
    }

    words = []
    for text in feedback_list:
        tokens = re.findall(r'\b[a-z]{3,}\b', text.lower())
        words.extend([w for w in tokens if w not in stop_words])

    freq = Counter(words)
    top_phrases = freq.most_common(top_n)

    result = {
        "top_phrases": [{"phrase": p, "count": c} for p, c in top_phrases],
        "frequency_map": dict(freq.most_common(20))
    }

    log_tool_result("summarize_feedback", f"top phrases: {[p for p, _ in top_phrases]}")
    return result


def cluster_themes(feedback_list: list[str]) -> list[dict]:
    """
    Simple keyword-matching into predefined theme buckets
    (performance, crash, billing, UX, positive).
    Returns: [{theme: str, count: int, severity: str, examples: [...]}]
    """
    log_tool_call("cluster_themes", f"{len(feedback_list)} items")

    theme_keywords = {
        "crash": ["crash", "crashes", "crashing", "freezes", "freeze", "hang",
                  "hangs", "stuck", "force close", "unresponsive"],
        "performance": ["slow", "sluggish", "lag", "laggy", "loading",
                       "takes forever", "latency", "timeout", "takes long"],
        "billing": ["payment", "charge", "billing", "checkout", "refund",
                    "transaction", "order", "purchase", "pay", "charged"],
        "ux": ["confusing", "unintuitive", "ugly", "hard to use", "difficult",
              "navigation", "ui", "interface", "design", "button"],
        "positive": ["love", "great", "awesome", "amazing", "fantastic",
                    "excellent", "works well", "good", "best", "smooth",
                    "polished", "helpful", "easy"]
    }

    themes = []
    for theme_name, keywords in theme_keywords.items():
        matching = []
        for text in feedback_list:
            lower = text.lower()
            if any(kw in lower for kw in keywords):
                matching.append(text)

        if matching:
            themes.append({
                "theme": theme_name,
                "count": len(matching),
                "severity": (
                    "high" if len(matching) > len(feedback_list) * 0.25
                    else "medium" if len(matching) > len(feedback_list) * 0.1
                    else "low"
                ),
                "examples": matching[:3]
            })

    themes.sort(key=lambda x: x["count"], reverse=True)

    log_tool_result("cluster_themes", f"{len(themes)} themes found")
    return themes
