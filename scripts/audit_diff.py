#!/usr/bin/env python3
"""Show repository state and current diff for Codex auditing."""

from __future__ import annotations

import shutil
import subprocess
import sys


def git(*args: str) -> None:
    result = subprocess.run(
        ["git", *args],
        text=True,
        capture_output=True,
    )
    print(f"$ git {' '.join(args)}")
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)


def main() -> int:
    if not shutil.which("git"):
        print("ERROR: git is not installed or not on PATH.")
        return 1

    git("status", "--short")
    git("diff", "--stat")
    git("diff", "--", ":!AUDIT.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
