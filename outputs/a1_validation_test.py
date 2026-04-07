"""
Validation test for Assessment 1 - War Room Decision output.
Verifies that a1_decision.json has all required fields and valid values.

Usage:
    python outputs/a1_validation_test.py
"""

import json
import sys
import os

# Fix Windows encoding
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

PASS = "[PASS]"
FAIL = "[FAIL]"


def validate_a1_output():
    """Validate the War Room decision JSON against the assessment requirements."""

    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "a1_decision.json")

    print("=" * 60)
    print("Assessment 1 - War Room Output Validation")
    print("=" * 60)

    # 1. Check file exists
    assert os.path.exists(output_path), f"Output file not found: {output_path}"
    print(f"{PASS} Output file exists: {output_path}")

    # 2. Load and parse JSON
    with open(output_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"{PASS} Valid JSON ({len(json.dumps(data)):,} chars)")

    # 3. Decision field - must be one of three values
    decision = data.get("decision")
    assert decision in ("Proceed", "Pause", "Roll Back"), \
        f"Invalid decision: {decision}"
    print(f"{PASS} Decision: {decision}")

    # 4. Rationale - must be a non-empty string
    rationale = data.get("rationale", "")
    assert isinstance(rationale, str) and len(rationale) > 20, \
        "Rationale is missing or too short"
    print(f"{PASS} Rationale: {rationale[:80]}...")

    # 5. Confidence score - must be float between 0 and 1
    confidence = data.get("confidence_score")
    assert isinstance(confidence, (int, float)) and 0 <= confidence <= 1, \
        f"Invalid confidence score: {confidence}"
    print(f"{PASS} Confidence score: {confidence}")

    # 6. Risk register - must be a non-empty list of dicts
    risks = data.get("risk_register", [])
    assert isinstance(risks, list) and len(risks) > 0, "Risk register is empty"
    for risk in risks:
        assert "risk" in risk, "Risk entry missing 'risk' field"
        assert "likelihood" in risk, "Risk entry missing 'likelihood' field"
        assert "impact" in risk, "Risk entry missing 'impact' field"
        assert "mitigation" in risk, "Risk entry missing 'mitigation' field"
    print(f"{PASS} Risk register: {len(risks)} risks (each with likelihood/impact/mitigation)")

    # 7. Action plan - must be a non-empty list with action/owner/timeframe
    actions = data.get("action_plan", [])
    assert isinstance(actions, list) and len(actions) > 0, "Action plan is empty"
    for action in actions:
        assert "action" in action, "Action entry missing 'action' field"
        assert "owner" in action, "Action entry missing 'owner' field"
        assert "timeframe" in action, "Action entry missing 'timeframe' field"
    print(f"{PASS} Action plan: {len(actions)} actions (each with owner/timeframe)")

    # 8. Communication plan - must have internal + external
    comm = data.get("communication_plan", {})
    assert "internal" in comm and len(comm["internal"]) > 10, \
        "Missing internal communication plan"
    assert "external" in comm and len(comm["external"]) > 10, \
        "Missing external communication plan"
    print(f"{PASS} Communication plan: internal ({len(comm['internal'])} chars) + external ({len(comm['external'])} chars)")

    # 9. Agent votes - must have multiple agents
    votes = data.get("agent_votes", {})
    assert len(votes) >= 4, f"Expected at least 4 agent votes, got {len(votes)}"
    for agent, vote in votes.items():
        assert vote in ("Proceed", "Pause", "Roll Back"), \
            f"Agent {agent} has invalid vote: {vote}"
    print(f"{PASS} Agent votes: {len(votes)} agents voted")

    # 10. Vote tally
    tally = data.get("vote_tally", {})
    assert sum(tally.values()) == len(votes), "Vote tally doesn't match agent count"
    print(f"{PASS} Vote tally: {tally}")

    print()
    print("=" * 60)
    print(f"ALL CHECKS PASSED | Decision: {decision} | Confidence: {confidence}")
    print("=" * 60)


if __name__ == "__main__":
    try:
        validate_a1_output()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n{FAIL} VALIDATION FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{FAIL} ERROR: {type(e).__name__}: {e}")
        sys.exit(1)
