"""
Script execution tools — write files, run Python scripts, run pytest.
Used by Reproduction agent to execute generated repro scripts.
"""

import subprocess
import os
from pathlib import Path
from shared.logger import log_tool_call, log_tool_result


def write_temp_file(content: str, filename: str, output_dir: str) -> str:
    """Writes generated script to disk. Returns file path."""
    log_tool_call("write_temp_file", f"filename={filename}")

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    path = os.path.join(output_dir, filename)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

    log_tool_result("write_temp_file", f"saved to {path}")
    return path


def run_python_script(script_path: str, timeout: int = 30) -> dict:
    """
    Executes a Python script via subprocess.
    Returns: {exit_code: int, stdout: str, stderr: str, timed_out: bool}
    """
    log_tool_call("run_python_script", f"path={script_path}, timeout={timeout}s")

    try:
        abs_script = os.path.abspath(script_path)
        result = subprocess.run(
            ["python", abs_script],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        output = {
            "exit_code": result.returncode,
            "stdout": result.stdout[:2000],
            "stderr": result.stderr[:2000],
            "timed_out": False
        }
    except subprocess.TimeoutExpired:
        output = {
            "exit_code": -1,
            "stdout": "",
            "stderr": "Script timed out",
            "timed_out": True
        }
    except Exception as e:
        output = {
            "exit_code": -1,
            "stdout": "",
            "stderr": str(e),
            "timed_out": False
        }

    log_tool_result("run_python_script", f"exit_code={output['exit_code']}, timed_out={output['timed_out']}")
    return output


def run_pytest(test_path: str, timeout: int = 60) -> dict:
    """
    Runs pytest on a specific file.
    Returns: {passed: int, failed: int, output: str, exit_code: int}
    """
    log_tool_call("run_pytest", f"path={test_path}, timeout={timeout}s")

    try:
        result = subprocess.run(
            ["python", "-m", "pytest", test_path, "-v", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=timeout
        )

        output_text = result.stdout + result.stderr
        passed = output_text.count(" PASSED")
        failed = output_text.count(" FAILED")

        output = {
            "passed": passed,
            "failed": failed,
            "output": output_text[:3000],
            "exit_code": result.returncode
        }
    except subprocess.TimeoutExpired:
        output = {
            "passed": 0,
            "failed": 0,
            "output": "Pytest timed out",
            "exit_code": -1
        }

    log_tool_result("run_pytest", f"passed={output['passed']}, failed={output['failed']}")
    return output
