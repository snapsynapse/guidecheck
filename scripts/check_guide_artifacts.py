#!/usr/bin/env python3
"""
Check repository-owned guide artifacts that should satisfy the byte profile.
"""

from __future__ import annotations

import sys
from pathlib import Path

import guidecheck_verify as gv


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = [
    ROOT / "assistant-guide.txt",
    ROOT / "examples" / "level-1-assistant-guide.txt",
    ROOT / "examples" / "level-3-assistant-guide.txt",
    ROOT / "fixtures" / "valid" / "level-2" / "guide.txt",
    ROOT / "fixtures" / "valid" / "level-3" / "guide.txt",
    ROOT / "fixtures" / "valid" / "prompterkit-level-3" / "guide.txt",
]


def main() -> int:
    failures: list[str] = []
    for path in ARTIFACTS:
        data = path.read_bytes()
        findings: list[gv.Finding] = []
        gv.check_byte_profile(data, findings)
        errors = [finding.id for finding in findings if finding.severity == "error"]
        if errors:
            failures.append(f"{path.relative_to(ROOT)}: {', '.join(errors)}")

    if failures:
        print("Guide artifact byte-profile failures:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print(f"Guide artifact byte profiles passed: {len(ARTIFACTS)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
