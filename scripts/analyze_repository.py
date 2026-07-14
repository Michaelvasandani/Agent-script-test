#!/usr/bin/env python3
"""Analyze repository contents and print a stable JSON report."""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any


EXCLUDED_DIRECTORIES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "node_modules",
    "venv",
}


def _line_count(path: Path) -> int:
    """Return the number of UTF-8 text lines, or zero for non-text files."""
    try:
        with path.open("r", encoding="utf-8") as file:
            return sum(1 for _ in file)
    except (OSError, UnicodeDecodeError):
        return 0


def analyze_repository(root: Path) -> dict[str, Any]:
    """Collect deterministic statistics for a repository directory."""
    root = root.resolve()
    extension_counts: Counter[str] = Counter()
    total_directories = 0
    total_files = 0
    text_lines = 0

    for current_root, directory_names, file_names in os.walk(root):
        directory_names[:] = sorted(
            name for name in directory_names if name not in EXCLUDED_DIRECTORIES
        )
        file_names.sort()
        total_directories += len(directory_names)

        for file_name in file_names:
            path = Path(current_root) / file_name
            if not path.is_file():
                continue

            total_files += 1
            extension = path.suffix.lower() or "[no extension]"
            extension_counts[extension] += 1
            text_lines += _line_count(path)

    return {
        "execution_confirmed": True,
        "script": "scripts/analyze_repository.py",
        "schema_version": 1,
        "statistics": {
            "files_by_extension": dict(sorted(extension_counts.items())),
            "python_files": extension_counts[".py"],
            "text_lines": text_lines,
            "total_directories": total_directories,
            "total_files": total_files,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "repository",
        nargs="?",
        default=".",
        type=Path,
        help="repository directory to analyze (default: current directory)",
    )
    args = parser.parse_args()
    print(json.dumps(analyze_repository(args.repository), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
