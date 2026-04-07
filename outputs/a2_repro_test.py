"""
Minimal reproduction script for BUG-2847.
Reproduces: AttributeError: 'NoneType' object has no attribute 'transaction_id'
"""
import sys
import os
from pathlib import Path

# Add mini_repo to path using a path relative to this script
project_root = Path(__file__).resolve().parents[1]
mini_repo = project_root / "bug_triage" / "data" / "mini_repo"
sys.path.insert(0, str(mini_repo))

from app import handle_checkout

print("Testing: Large order ($549.99) - should trigger the bug")
print("=" * 60)

try:
    result = handle_checkout(user_id=1188, items=["laptop"], total=549.99)
    print(f"UNEXPECTED: Payment succeeded - {result}")
    print("BUG NOT REPRODUCED")
    sys.exit(0)
except AttributeError as e:
    print(f"BUG REPRODUCED: {e}")
    sys.exit(1)
except Exception as e:
    print(f"DIFFERENT ERROR: {type(e).__name__}: {e}")
    sys.exit(2)
