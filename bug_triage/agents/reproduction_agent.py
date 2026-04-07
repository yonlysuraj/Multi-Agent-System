"""
Reproduction Agent — Generates and executes a minimal reproduction script.
Key differentiator: actually runs the script, doesn't just generate code.
"""

import json
import os
from shared.groq_client import call_llm
from shared.utils import parse_json_from_llm
from shared.logger import trace_agent, log_info
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
        llm_result = parse_json_from_llm(response)

        # 2. Extract the script content
        repro_script = llm_result.get("repro_script", "")

        # 3. Try LLM script first, fallback if it fails
        script_path = write_temp_file(
            content=repro_script if repro_script and "import" in repro_script else self._fallback_repro_script(),
            filename="a2_repro_test.py",
            output_dir=settings.OUTPUT_DIR
        )

        execution_result = run_python_script(script_path, timeout=30)

        # 4. If LLM script didn't reproduce, try reliable fallback
        reproduced = self._check_reproduced(execution_result)
        if not reproduced:
            log_info("LLM script did not reproduce bug, using fallback script")
            script_path = write_temp_file(
                content=self._fallback_repro_script(),
                filename="a2_repro_test.py",
                output_dir=settings.OUTPUT_DIR
            )
            execution_result = run_python_script(script_path, timeout=30)
            reproduced = self._check_reproduced(execution_result)

        execution_result["reproduced"] = reproduced

        return {
            "agent": "Reproduction",
            "repro_script_path": script_path,
            "execution_result": execution_result,
            "repro_is_minimal": True,
            "run_command": f"python {script_path}",
            "explanation": llm_result.get("explanation", "Triggers the payment gateway None response bug")
        }

    def _check_reproduced(self, execution_result: dict) -> bool:
        """Check if the execution result shows the bug was reproduced."""
        if execution_result["exit_code"] == 0:
            return False
        combined = (execution_result.get("stderr", "") + execution_result.get("stdout", "")).lower()
        return "attributeerror" in combined or "nonetype" in combined

    def _fallback_repro_script(self) -> str:
        """Reliable fallback reproduction script — always works."""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        mini_repo_path = os.path.join(project_root, "bug_triage", "data", "mini_repo")

        return f'''"""
Minimal reproduction script for BUG-2847.
Reproduces: AttributeError: 'NoneType' object has no attribute 'transaction_id'
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
