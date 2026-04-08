import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[1]
mini_repo = project_root / "bug_triage" / "data" / "mini_repo"
sys.path.insert(0, str(mini_repo))

from app import handle_checkout
handle_checkout(user_id=1, items=["item"], total=501.0)