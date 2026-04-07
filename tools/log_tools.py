"""
Log analysis tools — regex-based parsing, stack trace extraction, pattern search.
No LLM calls. Used by LogAnalyst agent.
"""

import re
from shared.logger import log_tool_call, log_tool_result


def parse_logs(log_text: str) -> dict:
    """
    Splits log lines, extracts timestamps, levels (ERROR/WARN/INFO), and messages.
    Returns: {total_lines: int, error_count: int, warn_count: int, parsed_lines: [...]}
    """
    log_tool_call("parse_logs", f"{len(log_text)} chars")

    lines = log_text.strip().split('\n')
    parsed = []
    error_count = 0
    warn_count = 0

    log_pattern = re.compile(
        r'\[?(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}[^\]]*)\]?\s*'
        r'\[?(DEBUG|INFO|WARNING|WARN|ERROR|CRITICAL)\]?\s*'
        r'(.*)'
    )

    for i, line in enumerate(lines):
        match = log_pattern.match(line)
        if match:
            timestamp, level, message = match.groups()
            level = level.upper()
            if level == "WARN":
                level = "WARNING"
            if level in ("ERROR", "CRITICAL"):
                error_count += 1
            if level == "WARNING":
                warn_count += 1
            parsed.append({
                "line_num": i + 1,
                "timestamp": timestamp.strip(),
                "level": level,
                "message": message.strip()
            })
        else:
            # Non-matching lines (stack trace continuations, etc.)
            parsed.append({
                "line_num": i + 1,
                "timestamp": None,
                "level": None,
                "message": line.strip()
            })

    result = {
        "total_lines": len(lines),
        "error_count": error_count,
        "warn_count": warn_count,
        "parsed_lines": parsed
    }

    log_tool_result("parse_logs", f"total={len(lines)}, errors={error_count}, warns={warn_count}")
    return result


def extract_stack_traces(log_text: str) -> list[dict]:
    """
    Regex-based stack trace extraction.
    Finds Python tracebacks (Traceback ... Error lines).
    Returns: [{trace_text: str, exception_type: str, line_ref: str}]
    """
    log_tool_call("extract_stack_traces", f"{len(log_text)} chars")

    # Match Python tracebacks
    pattern = re.compile(
        r'(Traceback \(most recent call last\):.*?(?:\w+Error|\w+Exception).*?)(?=\n\[|\n\d{4}-|\Z)',
        re.DOTALL
    )

    traces = []
    for match in pattern.finditer(log_text):
        trace_text = match.group(1).strip()

        # Extract exception type
        exc_match = re.search(r'(\w+(?:Error|Exception)):?\s*(.*)', trace_text.split('\n')[-1])
        exception_type = exc_match.group(1) if exc_match else "Unknown"

        # Extract file + line reference
        file_match = re.findall(r'File ["\']([^"\']+)["\'],\s*line (\d+)', trace_text)
        line_ref = f"{file_match[-1][0]}:{file_match[-1][1]}" if file_match else "unknown"

        traces.append({
            "trace_text": trace_text,
            "exception_type": exception_type,
            "line_ref": line_ref
        })

    log_tool_result("extract_stack_traces", f"found {len(traces)} stack traces")
    return traces


def search_log_pattern(log_text: str, pattern: str) -> dict:
    """
    Searches log for a regex/keyword pattern.
    Returns: {matches: [...], count: int, first_occurrence: str}
    Used to filter red herrings and find signal.
    """
    log_tool_call("search_log_pattern", f"pattern='{pattern}'")

    lines = log_text.strip().split('\n')
    matches = []

    try:
        compiled = re.compile(pattern, re.IGNORECASE)
    except re.error:
        compiled = re.compile(re.escape(pattern), re.IGNORECASE)

    for i, line in enumerate(lines):
        if compiled.search(line):
            matches.append({"line_num": i + 1, "content": line.strip()})

    first_occurrence = matches[0]["content"] if matches else None

    result = {
        "matches": matches,
        "count": len(matches),
        "first_occurrence": first_occurrence
    }

    log_tool_result("search_log_pattern", f"{len(matches)} matches")
    return result
