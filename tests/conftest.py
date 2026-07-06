import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

# must come after the sys.path insert above, or seido is not importable
from seido.app import limiter
limiter.enabled = False  # rate limits are out of test scope (manual check)
