"""
Metrics analysis tools — pure Python with numpy/scipy.
No LLM calls. Used by DataAnalyst, PM, Finance, Growth agents.
"""

import numpy as np
from scipy import stats
from shared.logger import log_tool_call, log_tool_result


def analyze_metrics(metrics: dict, launch_day_index: int) -> dict:
    """
    Computes per-metric stats: mean pre-launch, mean post-launch, delta%, direction.
    Returns structured dict ready for LLM consumption.
    Pure numpy — no LLM calls.
    """
    log_tool_call("analyze_metrics", f"{len(metrics)} metrics, launch_day={launch_day_index}")

    results = {}
    for name, values in metrics.items():
        pre = values[:launch_day_index]
        post = values[launch_day_index:]
        pre_mean = float(np.mean(pre))
        post_mean = float(np.mean(post))
        delta_pct = ((post_mean - pre_mean) / pre_mean * 100) if pre_mean != 0 else 0.0

        # For error_rate, support_tickets, api_latency: increase is bad
        inverted = name in ("error_rate", "support_tickets", "api_latency_p95")
        direction = "worsening" if (delta_pct > 0 and inverted) or (delta_pct < 0 and not inverted) else "improving"
        if abs(delta_pct) < 2:
            direction = "stable"

        results[name] = {
            "pre_mean": round(pre_mean, 4),
            "post_mean": round(post_mean, 4),
            "delta_pct": round(delta_pct, 2),
            "direction": direction
        }

    log_tool_result("analyze_metrics", f"analyzed {len(results)} metrics")
    return results


def detect_anomalies(series: list[float], z_threshold: float = 2.0) -> dict:
    """
    Z-score based anomaly detection.
    Returns: {has_anomaly: bool, anomaly_indices: [...], z_scores: [...], max_z: float}
    Uses scipy.stats.zscore — lightweight, no ML model needed.
    """
    log_tool_call("detect_anomalies", f"series_len={len(series)}, threshold={z_threshold}")

    z_scores = stats.zscore(series)
    anomaly_indices = [i for i, z in enumerate(z_scores) if abs(z) > z_threshold]

    result = {
        "has_anomaly": len(anomaly_indices) > 0,
        "anomaly_indices": anomaly_indices,
        "z_scores": [round(float(z), 3) for z in z_scores],
        "max_z": round(float(np.max(np.abs(z_scores))), 3)
    }

    log_tool_result("detect_anomalies", f"anomaly={'Yes' if result['has_anomaly'] else 'No'}, indices={anomaly_indices}")
    return result


def trend_compare(series: list[float], thresholds: dict) -> dict:
    """
    Compares a metric's recent average against defined thresholds.
    Returns: {metric_name: {current, threshold, passed, gap_pct}}
    
    thresholds format: {"metric_name": {"threshold": 0.02, "direction": "below"}}
    direction: "below" means current must be <= threshold to pass.
               "above" means current must be >= threshold to pass.
    """
    log_tool_call("trend_compare", f"comparing against {len(thresholds)} thresholds")

    results = {}
    recent_avg = float(np.mean(series[-3:])) if len(series) >= 3 else float(np.mean(series))

    for metric_name, t in thresholds.items():
        threshold_val = t["threshold"]
        direction = t.get("direction", "below")

        if direction == "below":
            passed = recent_avg <= threshold_val
        else:  # "above"
            passed = recent_avg >= threshold_val

        gap_pct = ((recent_avg - threshold_val) / threshold_val * 100) if threshold_val != 0 else 0

        results[metric_name] = {
            "current": round(recent_avg, 4),
            "threshold": threshold_val,
            "passed": passed,
            "gap_pct": round(gap_pct, 2)
        }

    log_tool_result("trend_compare", f"{sum(1 for r in results.values() if r['passed'])}/{len(results)} passed")
    return results
