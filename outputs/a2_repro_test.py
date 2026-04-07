import sys
import os
from pathlib import Path
project_root = Path(__file__).resolve().parents[1]
mini_repo = project_root / "bug_triage" / "data" / "mini_repo"
sys.path.insert(0, str(mini_repo))
from app import handle_checkout

# Trigger the bug by simulating an order over $500
handle_checkout(1, ["item1", "item2"], 501.0)