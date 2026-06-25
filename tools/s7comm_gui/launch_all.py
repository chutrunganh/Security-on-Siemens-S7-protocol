"""Launch Attack + Rules GUI (two separate windows)."""
from __future__ import annotations

import os
import subprocess
import sys
import time

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LOG_FILE = os.path.join(REPO_ROOT, "tools", "s7comm_gui", "launch_errors.log")

MODULES = (
    "tools.s7comm_gui.attack_app",
    "tools.s7comm_gui.rules_app",
)


def _pythonw() -> str:
    exe = sys.executable
    if exe.lower().endswith("pythonw.exe"):
        return exe
    if exe.lower().endswith("python.exe"):
        candidate = exe[:-10] + "pythonw.exe"
        if os.path.isfile(candidate):
            return candidate
    return "pythonw"


def main() -> int:
    pyw = _pythonw()
    errors: list[str] = []

    for mod in MODULES:
        try:
            flags = 0
            if os.name == "nt":
                flags = subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]
            subprocess.Popen(
                [pyw, "-m", mod],
                cwd=REPO_ROOT,
                creationflags=flags,
            )
            time.sleep(0.8)
        except OSError as e:
            errors.append(f"{mod}: {e!r}")

    if errors:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write("\n".join(errors) + "\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
