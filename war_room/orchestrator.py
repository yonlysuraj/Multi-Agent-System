"""
Assessment 1 — War Room Orchestrator
State machine that drives all agents in sequence, aggregates outputs,
and produces the final decision JSON.
"""

import json
from datetime import datetime, timezone

from shared.logger import set_context, log_info, log_error
from shared.utils import load_json, load_text

from war_room.agents.data_analyst import DataAnalystAgent
from war_room.agents.marketing_agent import MarketingAgent
from war_room.agents.pm_agent import PMAgent
from war_room.agents.risk_agent import RiskAgent
from war_room.agents.finance_agent import FinanceAgent
from war_room.agents.growth_agent import GrowthAgent


class WarRoomOrchestrator:
    """State machine orchestrator for the War Room decision pipeline."""

    STAGES = [
        "LOAD_DATA",
        "DATA_ANALYST",
        "MARKETING",
        "PM",
        "FINANCE",
        "GROWTH",
        "RISK",
        "AGGREGATE",
    ]

    def __init__(self, data_dir: str = "war_room/data"):
        self.data_dir = data_dir
        self.state = {}        # Holds all agent outputs
        self.current_stage = 0

    def _set_stage(self, stage_name: str):
        """Update logger context for current stage."""
        self.current_stage = self.STAGES.index(stage_name)
        set_context("A1", f"STAGE {self.current_stage}")
        log_info(f"Entering stage: {stage_name}")

    def run(self) -> dict:
        """Execute the full War Room pipeline and return the decision JSON."""

        # ── STAGE 0: Load Data ──
        self._set_stage("LOAD_DATA")
        metrics_data = load_json(f"{self.data_dir}/metrics.json")
        feedback_data = load_json(f"{self.data_dir}/feedback.json")
        release_notes = load_text(f"{self.data_dir}/release_notes.md")

        log_info(f"Loaded {len(metrics_data['metrics'])} metrics, "
                 f"{len(feedback_data['feedback'])} feedback items")

        # ── STAGE 1: Data Analyst ──
        self._set_stage("DATA_ANALYST")
        try:
            analyst = DataAnalystAgent()
            analyst_output = analyst.run(metrics_data)
            self.state["analyst"] = analyst_output
        except Exception as e:
            log_error("DataAnalyst", str(e))
            analyst_output = self._fallback_output("DataAnalyst")
            self.state["analyst"] = analyst_output

        # ── STAGE 2: Marketing ──
        self._set_stage("MARKETING")
        try:
            marketing = MarketingAgent()
            marketing_output = marketing.run(feedback_data)
            self.state["marketing"] = marketing_output
        except Exception as e:
            log_error("MarketingComms", str(e))
            marketing_output = self._fallback_output("MarketingComms")
            self.state["marketing"] = marketing_output

        # ── STAGE 3: Product Manager ──
        self._set_stage("PM")
        try:
            pm = PMAgent()
            pm_output = pm.run(analyst_output, marketing_output, release_notes)
            self.state["pm"] = pm_output
        except Exception as e:
            log_error("ProductManager", str(e))
            pm_output = self._fallback_output("ProductManager")
            self.state["pm"] = pm_output

        # ── STAGE 4: Finance (Bonus) ──
        self._set_stage("FINANCE")
        try:
            finance = FinanceAgent()
            finance_output = finance.run(metrics_data)
            self.state["finance"] = finance_output
        except Exception as e:
            log_error("Finance", str(e))
            finance_output = self._fallback_output("Finance")
            self.state["finance"] = finance_output

        # ── STAGE 5: Growth (Bonus) ──
        self._set_stage("GROWTH")
        try:
            growth = GrowthAgent()
            growth_output = growth.run(metrics_data)
            self.state["growth"] = growth_output
        except Exception as e:
            log_error("Growth", str(e))
            growth_output = self._fallback_output("Growth")
            self.state["growth"] = growth_output

        # ── STAGE 6: Risk / Critic ──
        self._set_stage("RISK")
        try:
            risk = RiskAgent()
            risk_output = risk.run(
                analyst_output, marketing_output, pm_output, metrics_data
            )
            self.state["risk"] = risk_output
        except Exception as e:
            log_error("RiskCritic", str(e))
            risk_output = self._fallback_output("RiskCritic")
            self.state["risk"] = risk_output

        # ── STAGE 7: Aggregate ──
        self._set_stage("AGGREGATE")
        decision = self._aggregate()
        log_info(f"Final decision: {decision['decision']} "
                 f"(confidence: {decision['confidence_score']})")

        return decision

    def _aggregate(self) -> dict:
        """
        Aggregate all agent outputs into the final decision JSON.
        No LLM call — pure logic.
        """
        # Collect votes from all agents
        agent_votes = {}
        vote_tally = {"Proceed": 0, "Pause": 0, "Roll Back": 0}

        agent_name_map = {
            "analyst": "DataAnalyst",
            "marketing": "Marketing",
            "pm": "ProductManager",
            "finance": "Finance",
            "growth": "Growth",
            "risk": "Risk",
        }

        for key, display_name in agent_name_map.items():
            output = self.state.get(key, {})
            rec = output.get("recommendation",
                  output.get("pm_recommendation",
                  output.get("critic_recommendation",
                  output.get("finance_recommendation",
                  output.get("growth_recommendation", "Pause")))))
            # Normalize the recommendation
            rec_normalized = self._normalize_recommendation(rec)
            agent_votes[display_name] = rec_normalized
            vote_tally[rec_normalized] = vote_tally.get(rec_normalized, 0) + 1

        # Decide by majority
        decision = max(vote_tally, key=vote_tally.get)

        # Compute confidence score
        confidence_score = self._compute_confidence()

        # Build metric snapshot
        analyst_out = self.state.get("analyst", {})
        marketing_out = self.state.get("marketing", {})
        pm_out = self.state.get("pm", {})

        metric_snapshot = {}
        metric_summary = analyst_out.get("metric_summary", {})
        if "error_rate" in metric_summary:
            metric_snapshot["error_rate_post_launch"] = metric_summary["error_rate"].get("delta_pct", 0)
        metric_snapshot["error_rate_threshold"] = pm_out.get("success_criteria", {}).get("error_rate_threshold", 0.02)
        metric_snapshot["sentiment_score"] = marketing_out.get("sentiment_score", 0)
        metric_snapshot["health_score"] = analyst_out.get("overall_health_score", 0.5)
        metric_snapshot["payment_success_rate"] = metric_summary.get("payment_success_rate", {}).get("delta_pct", 0)

        # Build risk register from Risk agent
        risk_out = self.state.get("risk", {})
        risk_register = risk_out.get("risk_register", [])

        # Build action plan based on decision
        action_plan = self._build_action_plan(decision)

        # Build communication plan from Marketing agent
        comm_plan = marketing_out.get("draft_communication", {
            "internal": "Awaiting marketing assessment.",
            "external": "Awaiting marketing assessment."
        })

        # Build rationale from all agents
        rationale = self._build_rationale()

        final_dict = {
            "task": "Assessment 1 — War Room Decision",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "decision": decision,
            "rationale": rationale,
            "confidence_score": confidence_score,
            "confidence_explanation": self._explain_confidence(confidence_score, decision),
            "agent_votes": agent_votes,
            "vote_tally": vote_tally,
            "metric_snapshot": metric_snapshot,
            "risk_register": risk_register,
            "action_plan": action_plan,
            "communication_plan": comm_plan
        }
        
        # Include full agent outputs only if verbose mode is enabled
        from config.settings import settings
        if getattr(settings, "VERBOSE_JSON_OUTPUT", False):
            final_dict["agent_outputs"] = {
                "data_analyst": analyst_out,
                "marketing": marketing_out,
                "product_manager": pm_out,
                "finance": self.state.get("finance", {}),
                "growth": self.state.get("growth", {}),
                "risk": risk_out,
            }
            
        return final_dict

    def _normalize_recommendation(self, rec: str) -> str:
        """Normalize varied recommendation strings to one of three options."""
        rec_lower = rec.lower().strip()
        if "roll" in rec_lower or "rollback" in rec_lower or "revert" in rec_lower:
            return "Roll Back"
        elif "proceed" in rec_lower or "go" in rec_lower or "continue" in rec_lower:
            return "Proceed"
        else:
            return "Pause"

    def _compute_confidence(self) -> float:
        """
        Weighted confidence score:
          0.35 * metric health  +  0.25 * sentiment  +  0.20 * criteria pass rate
          + 0.10 * stability  +  0.10 * finance signal
        """
        analyst_out = self.state.get("analyst", {})
        marketing_out = self.state.get("marketing", {})
        pm_out = self.state.get("pm", {})

        # Metric health (inverted: 0=bad → high concern)
        health = analyst_out.get("overall_health_score", 0.5)

        # Sentiment (normalize from [-1,1] to [0,1])
        sentiment = marketing_out.get("sentiment_score", 0)
        sentiment_norm = (sentiment + 1) / 2

        # Criteria pass rate
        pass_count = pm_out.get("criteria_pass_count", 0)
        total = pm_out.get("criteria_total", 5)
        criteria_rate = pass_count / total if total > 0 else 0.5

        # Stability (based on anomaly count — fewer anomalies = more stable)
        metric_summary = analyst_out.get("metric_summary", {})
        anomaly_count = sum(
            1 for m in metric_summary.values()
            if isinstance(m, dict) and m.get("anomaly", False)
        )
        total_metrics = max(len(metric_summary), 1)
        stability = 1 - (anomaly_count / total_metrics)

        # Finance risk (simple: if we have finance output with revenue at risk)
        finance_out = self.state.get("finance", {})
        rev_at_risk = finance_out.get("estimated_daily_revenue_at_risk_usd", 0)
        # Normalize: $0 = 1.0, $50,000+ = 0.0
        finance_factor = max(0, 1 - (rev_at_risk / 50000))

        confidence = (
            0.35 * health +
            0.25 * sentiment_norm +
            0.20 * criteria_rate +
            0.10 * stability +
            0.10 * finance_factor
        )

        return round(min(max(confidence, 0), 1), 2)

    def _explain_confidence(self, score: float, decision: str) -> str:
        """Generate a human-readable confidence explanation."""
        analyst_out = self.state.get("analyst", {})
        health = analyst_out.get("overall_health_score", 0.5)

        if score > 0.7:
            return (f"High confidence ({score}) in {decision}. "
                    f"Metrics health score is {health}, indicating manageable risk. "
                    f"Confidence would increase further with 7-day stability data.")
        elif score > 0.4:
            return (f"Moderate confidence ({score}) in {decision}. "
                    f"Metrics health at {health} with mixed signals across agents. "
                    f"Confidence would increase with A/B test data and confirmed root cause analysis.")
        else:
            return (f"Low confidence ({score}) in {decision} — situation is critical. "
                    f"Health score at {health}. Immediate action recommended. "
                    f"Confidence in recovery would increase with a confirmed bug fix and stable rollback metrics.")

    def _build_rationale(self) -> str:
        """Build a concise rationale from all agent outputs."""
        parts = []

        analyst_out = self.state.get("analyst", {})
        if analyst_out.get("narrative"):
            parts.append(analyst_out["narrative"])

        marketing_out = self.state.get("marketing", {})
        sentiment = marketing_out.get("sentiment_score", 0)
        pr_risk = marketing_out.get("pr_risk_level", "unknown")
        parts.append(f"User sentiment is {sentiment} with PR risk level: {pr_risk}.")

        pm_out = self.state.get("pm", {})
        pass_count = pm_out.get("criteria_pass_count", 0)
        total = pm_out.get("criteria_total", 5)
        parts.append(f"{pass_count} of {total} PM success criteria met.")

        finance_out = self.state.get("finance", {})
        rev = finance_out.get("estimated_daily_revenue_at_risk_usd", 0)
        if rev:
            parts.append(f"Finance estimates ${rev:,}/day revenue at risk.")

        return " ".join(parts)

    def _build_action_plan(self, decision: str) -> list[dict]:
        """Generate context-appropriate action plan based on the decision."""
        if decision == "Roll Back":
            return [
                {"action": "Immediately disable Smart Checkout v2 via feature flag",
                 "owner": "Engineering Lead", "timeframe": "Immediate"},
                {"action": "Roll back payment service to previous stable version",
                 "owner": "Backend Team", "timeframe": "1 hour"},
                {"action": "Verify legacy checkout flow is handling all traffic",
                 "owner": "SRE Team", "timeframe": "2 hours"},
                {"action": "Publish customer-facing status update",
                 "owner": "Marketing", "timeframe": "4 hours"},
                {"action": "Publish internal post-incident report",
                 "owner": "PM", "timeframe": "24-48 hours"},
            ]
        elif decision == "Pause":
            return [
                {"action": "Halt rollout at current traffic — do not expand",
                 "owner": "Engineering Lead", "timeframe": "Immediate"},
                {"action": "Isolate payment service — roll back to stable version",
                 "owner": "Backend Team", "timeframe": "2 hours"},
                {"action": "Publish internal incident report",
                 "owner": "PM", "timeframe": "24 hours"},
                {"action": "Draft and schedule customer-facing status update",
                 "owner": "Marketing", "timeframe": "4 hours"},
                {"action": "Set up 30-min war room sync for re-evaluation",
                 "owner": "PM", "timeframe": "48 hours"},
            ]
        else:  # Proceed
            return [
                {"action": "Continue gradual rollout to next traffic segment",
                 "owner": "Engineering Lead", "timeframe": "Next 24-48 hours"},
                {"action": "Monitor error rate and latency dashboards closely",
                 "owner": "SRE Team", "timeframe": "Ongoing"},
                {"action": "Prepare rollback plan in case metrics deteriorate",
                 "owner": "Backend Team", "timeframe": "24 hours"},
            ]

    def _fallback_output(self, agent_name: str) -> dict:
        """Return a safe fallback output when an agent fails."""
        return {
            "agent": agent_name,
            "error": True,
            "recommendation": "Pause",
            "narrative": f"{agent_name} agent failed to produce output — defaulting to Pause."
        }
