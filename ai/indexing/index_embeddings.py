"""CLI entry point for loading real CSV data into the RAG ChromaDB index.

This script is intentionally thin. The indexing logic lives in indexer.py so
it can be reused by tests, scripts, or future commands.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai.indexing.indexer import main  # noqa: E402


if __name__ == "__main__":
    main()
