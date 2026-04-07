"""
Shared Pydantic/TypedDict models for agent input/output schemas.
Keeps type safety across the entire pipeline.
"""

from typing import TypedDict


# ─── Assessment 1 Models ───

class MetricAnalysis(TypedDict):
    trend: str              # "rising", "declining", "stable"
    delta_pct: float
    anomaly: bool


class DataAnalystOutput(TypedDict):
    agent: str
    metric_summary: dict[str, MetricAnalysis]
    top_concerns: list[str]
    positive_signals: list[str]
    overall_health_score: float
    narrative: str


class MarketingOutput(TypedDict):
    agent: str
    sentiment_breakdown: dict[str, int]
    sentiment_score: float
    top_themes: list[dict]
    pr_risk_level: str
    draft_communication: dict[str, str]


class PMOutput(TypedDict):
    agent: str
    success_criteria: dict[str, float]
    criteria_met: dict[str, bool]
    criteria_pass_count: int
    criteria_total: int
    pm_recommendation: str
    user_impact_summary: str
    framing: str


class RiskOutput(TypedDict):
    agent: str
    challenged_assumptions: list[str]
    risk_register: list[dict]
    missing_evidence: list[str]
    critic_recommendation: str


# ─── Assessment 2 Models ───

class TriageOutput(TypedDict):
    agent: str
    title: str
    severity: str
    affected_component: str
    expected_behavior: str
    actual_behavior: str
    environment: dict[str, str]
    hypotheses: list[dict]
    reproduction_hints: list[str]


class LogAnalystOutput(TypedDict):
    agent: str
    error_count: int
    first_occurrence: str
    stack_traces: list[dict]
    correlated_hypothesis: str
    correlation_confidence: float
    red_herrings_ignored: list[str]


class ReproductionOutput(TypedDict):
    agent: str
    repro_script_path: str
    execution_result: dict
    repro_is_minimal: bool
    run_command: str


class FixPlannerOutput(TypedDict):
    agent: str
    root_cause: str
    root_cause_confidence: float
    patch_plan: dict
    validation_plan: list[str]


class CriticOutput(TypedDict):
    agent: str
    repro_is_truly_minimal: bool
    fix_plan_is_safe: bool
    concerns: list[str]
    suggested_edge_cases: list[str]
    open_questions: list[str]
    overall_assessment: str
