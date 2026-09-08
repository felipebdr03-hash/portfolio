#!/usr/bin/env python3
"""Run the project's available Python tests."""

from __future__ import annotations

import shutil
import subprocess
import sys


def run(command: list[str]) -> int:
    print("$", " ".join(command))
    return subprocess.run(command).returncode


def main() -> int:
    if shutil.which("pytest"):
        return run([sys.executable, "-m", "pytest", "-q"])

    print("pytest not found. Falling back to unittest discovery.")
    return run([sys.executable, "-m", "unittest", "discover", "-v"])


if __name__ == "__main__":
    raise SystemExit(main())
