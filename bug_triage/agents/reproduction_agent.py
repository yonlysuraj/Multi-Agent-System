"""
Reproduction Agent — Generates and executes a minimal reproduction script.
Key differentiator: actually runs the script, doesn't just generate code.

Extraction strategy (in order):
  1. Parse ```python block + ```json block from LLM response (new format)
  2. Parse repro_script field from JSON (old embedded format, handles \\n escaping)
  3. Hardcoded fallback (guaranteed to work, logged explicitly)
"""

import json
import re
import os
from shared.groq_client import call_llm
from shared.utils import parse_json_from_llm
from shared.logger import trace_agent, log_info, log_tool_call, log_tool_result
from config.prompts.a2_prompts import REPRODUCTION_SYSTEM, REPRODUCTION_USER
from config.settings import settings
from tools.execution_tools import write_temp_file, run_python_script


class ReproductionAgent:

    @trace_agent("Reproduction")
    def run(self, triage_output: dict, log_output: dict) -> dict:
        # 1. Ask LLM to generate a reproduction script
        user_prompt = REPRODUCTION_USER.format(
            triage_output=json.dumps(triage_output, indent=2),
            log_output=json.dumps(log_output, indent=2)
        )

        response = call_llm(REPRODUCTION_SYSTEM, user_prompt)

        # 2. Extract script + metadata using multi-strategy parser
        repro_script, metadata, script_source = self._extract_response(response)

        log_info(f"Script source: {script_source}")
        log_tool_call("write_temp_file", f"source={script_source}, has_script={bool(repro_script)}")

        # 3. Write and execute the script
        script_path = write_temp_file(
            content=repro_script,
            filename="a2_repro_test.py",
            output_dir=settings.OUTPUT_DIR
        )
        log_tool_result("write_temp_file", f"saved to {script_path}")

        execution_result = run_python_script(script_path, timeout=30)
        reproduced = self._check_reproduced(execution_result)
        execution_result["reproduced"] = reproduced

        log_info(f"Execution result: exit_code={execution_result['exit_code']}, reproduced={reproduced}")

        return {
            "agent": "Reproduction",
            "script_source": script_source,
            "repro_script_path": script_path,
            "execution_result": execution_result,
            "repro_is_minimal": metadata.get("repro_is_minimal", True),
            "run_command": f"python {script_path}",
            "expected_error": metadata.get("expected_error", "AttributeError: 'NoneType' object has no attribute 'transaction_id'"),
            "explanation": metadata.get("explanation", "Triggers the payment gateway None response bug for orders > $500")
        }

    # ── Extraction strategies ──────────────────────────────────────────────

    def _extract_response(self, response: str) -> tuple[str, dict, str]:
        """
        Returns (script_content, metadata_dict, source_label).
        Tries three strategies in order of reliability.
        """

        # Strategy 1: new format — ```python block + ```json block
        script, metadata = self._extract_code_and_json_blocks(response)
        if script and self._is_valid_python(script):
            log_info("Script extraction: Strategy 1 succeeded (code block + JSON block)")
            return script, metadata, "llm-generated (code-block format)"

        # Strategy 2: old format — script embedded in JSON string field
        script, metadata = self._extract_from_json_field(response)
        if script and self._is_valid_python(script):
            log_info("Script extraction: Strategy 2 succeeded (JSON-embedded string)")
            return script, metadata, "llm-generated (json-embedded format)"

        # Strategy 3: guaranteed fallback
        log_info("Script extraction: LLM strategies failed, using hardcoded fallback")
        return self._fallback_repro_script(), {}, "hardcoded-fallback"

    def _extract_code_and_json_blocks(self, response: str) -> tuple[str, dict]:
        """Extract script from ```python block and metadata from ```json block."""
        script = ""
        metadata = {}

        py_match = re.search(r'```python\s*\n(.*?)\n?```', response, re.DOTALL)
        if py_match:
            script = py_match.group(1).strip()

        json_match = re.search(r'```json\s*\n(.*?)\n?```', response, re.DOTALL)
        if json_match:
            try:
                metadata = json.loads(json_match.group(1))
            except json.JSONDecodeError:
                metadata = {}

        return script, metadata

    def _extract_from_json_field(self, response: str) -> tuple[str, dict]:
        """Extract script from the repro_script field in a JSON object (old format)."""
        llm_result = parse_json_from_llm(response)
        if llm_result.get("parse_error"):
            return "", {}

        raw_script = llm_result.get("repro_script", "")
        # Fix JSON-escaped newlines that LLMs sometimes emit as literal \n
        script = raw_script.replace("\\n", "\n").replace("\\t", "\t")
        return script, llm_result

    def _is_valid_python(self, script: str) -> bool:
        """Return True if the script compiles without SyntaxError."""
        if not script or "import" not in script:
            return False
        try:
            compile(script, "<repro_script>", "exec")
            return True
        except SyntaxError:
            return False

    # ── Bug detection ──────────────────────────────────────────────────────

    def _check_reproduced(self, execution_result: dict) -> bool:
        """Check if the execution result shows the bug was reproduced."""
        if execution_result["exit_code"] == 0:
            return False
        combined = (execution_result.get("stderr", "") + execution_result.get("stdout", "")).lower()
        return "attributeerror" in combined or "nonetype" in combined

    # ── Fallback script ────────────────────────────────────────────────────

    def _fallback_repro_script(self) -> str:
        """Reliable fallback reproduction script — always works."""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        mini_repo_path = os.path.join(project_root, "bug_triage", "data", "mini_repo")

        return f'''"""
Minimal reproduction script for BUG-2847.
Reproduces: AttributeError: 'NoneType' object has no attribute 'transaction_id'
Source: hardcoded-fallback (LLM extraction failed)
"""
import sys
import os

# Add mini_repo to path using absolute path
mini_repo = r"{mini_repo_path}"
sys.path.insert(0, mini_repo)

from app import handle_checkout

print("Testing: Large order ($549.99) - should trigger the bug")
print("=" * 60)

try:
    result = handle_checkout(user_id=1188, items=["laptop"], total=549.99)
    print(f"UNEXPECTED: Payment succeeded - {{result}}")
    print("BUG NOT REPRODUCED")
    sys.exit(0)
except AttributeError as e:
    print(f"BUG REPRODUCED: {{e}}")
    sys.exit(1)
except Exception as e:
    print(f"DIFFERENT ERROR: {{type(e).__name__}}: {{e}}")
    sys.exit(2)
'''
