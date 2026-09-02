"""Interactive Terminal Runner for AI Finance Controller Chat."""
import sys
from pathlib import Path

# Ensure root is on path
REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from chat.cli import start_cli_chat

if __name__ == "__main__":
    start_cli_chat()
