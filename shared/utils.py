"""
Utility functions: JSON parsing from LLM output, file I/O, text cleaning.
"""

import json
import re
from pathlib import Path


def parse_json_from_llm(text: str) -> dict:
    """
    Extract JSON from LLM response.
    Handles markdown fences like ```json ... ```
    """
    # Try to find JSON in code fences
    match = re.search(r'```(?:json)?\s*\n?(.*?)\n?\s*```', text, re.DOTALL)
    if match:
        text = match.group(1)

    # Try to find JSON object
    text = text.strip()
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1:
        text = text[start:end + 1]

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"parse_error": True, "raw_text": text[:500]}


def clean_text(text: str) -> str:
    """Normalize whitespace in text."""
    return re.sub(r'\s+', ' ', text).strip()


def load_json(path: str) -> dict | list:
    """Load and parse a JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_text(path: str) -> str:
    """Load a text file as string."""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def save_json(data: dict | list, path: str):
    """Save data as formatted JSON."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
