"""
Structured trace logger with rich console output and file logging.
Format: [TIMESTAMP] [TASK] [STAGE N] [AgentName] EVENT
"""

import time
import functools
from datetime import datetime, timezone
from pathlib import Path
from rich.console import Console
from config.settings import settings

console = Console()
_log_file_path = Path(settings.OUTPUT_DIR) / "trace.log"

# Current task context (set by orchestrator)
_current_task = "SYSTEM"
_current_stage = "INIT"


def set_context(task: str, stage: str):
    """Set the current task and stage context for log entries."""
    global _current_task, _current_stage
    _current_task = task
    _current_stage = stage


def _write_log(line: str):
    """Write to both console and log file."""
    console.print(line)
    # Strip rich markup for file output
    clean_line = line
    for tag in ["[cyan]", "[/cyan]", "[yellow]", "[/yellow]", "[green]", "[/green]",
                "[bold red]", "[/bold red]", "[bold green]", "[/bold green]",
                "[bold]", "[/bold]"]:
        clean_line = clean_line.replace(tag, "")
    with open(_log_file_path, "a", encoding="utf-8") as f:
        f.write(clean_line + "\n")


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def log_tool_call(tool_name: str, summary: str):
    """Log a tool function call."""
    line = f"[{_timestamp()}] [{_current_task}] [TOOL]    {tool_name}() called — {summary}"
    _write_log(f"[cyan]{line}[/cyan]")


def log_tool_result(tool_name: str, result_summary: str):
    """Log a tool function result."""
    line = f"[{_timestamp()}] [{_current_task}] [TOOL]    {tool_name}() → {result_summary}"
    _write_log(f"[cyan]{line}[/cyan]")


def log_llm_call(model: str, tokens_in: int, tokens_out: int, latency: float):
    """Log a Groq LLM API call."""
    line = f"[{_timestamp()}] [{_current_task}] [LLM]     groq.chat() called — model={model}, tokens_in={tokens_in}"
    _write_log(f"[yellow]{line}[/yellow]")
    line2 = f"[{_timestamp()}] [{_current_task}] [LLM]     groq.chat() → tokens_out={tokens_out}, latency={latency:.1f}s"
    _write_log(f"[yellow]{line2}[/yellow]")


def log_error(agent_name: str, error: str):
    """Log an error during agent execution."""
    line = f"[{_timestamp()}] [{_current_task}] [{_current_stage}] [{agent_name}] [ERROR] {error}"
    _write_log(f"[bold red]{line}[/bold red]")


def log_info(message: str):
    """Log a general info message."""
    line = f"[{_timestamp()}] [{_current_task}] [{_current_stage}] [INFO] {message}"
    _write_log(f"[green]{line}[/green]")


def trace_agent(agent_name: str):
    """Decorator to log agent START/END with timing."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_line = f"[{_timestamp()}] [{_current_task}] [{_current_stage}] [{agent_name}] START"
            _write_log(f"[bold green]{start_line}[/bold green]")

            start = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start
                end_line = f"[{_timestamp()}] [{_current_task}] [{_current_stage}] [{agent_name}] END — took {elapsed:.1f}s"
                _write_log(f"[bold green]{end_line}[/bold green]")
                return result
            except Exception as e:
                log_error(agent_name, str(e))
                raise
        return wrapper
    return decorator
