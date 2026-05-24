#!/usr/bin/env python3
"""
CLI contract checks for scripts/guidecheck_verify.py.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "guidecheck_verify.py"
VALID = ROOT / "fixtures" / "valid" / "level-3" / "guide.txt"
VALID_LEVEL4 = ROOT / "fixtures" / "valid" / "level-4" / "guide.txt"
VALID_LEVEL4_MANIFEST = ROOT / "fixtures" / "valid" / "level-4" / "manifest.txt"
VALID_LEVEL4_ANCHOR = ROOT / "fixtures" / "valid" / "level-4" / "anchors" / "dns-txt.txt"
MISSING_ANCHOR = ROOT / "fixtures" / "invalid" / "anchor-independent-missing" / "guide.txt"
MISSING_ANCHOR_MANIFEST = ROOT / "fixtures" / "invalid" / "anchor-independent-missing" / "manifest.txt"
INVALID = ROOT / "fixtures" / "invalid" / "missing-verification" / "guide.txt"
PASSED = 0
FAILED = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"PASS {name}")
    else:
        FAILED += 1
        print(f"FAIL {name}")
        if detail:
            print(f"     {detail}")


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_json_default() -> None:
    result = run(str(VALID))
    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        check("default json parse", False, str(exc))
        return
    check("default json exit", result.returncode == 0)
    check("default json level", output["guide"]["achieved_level"] == 3)


def test_json_pretty_flag() -> None:
    result = run(str(VALID), "--json", "--pretty")
    check("json pretty exit", result.returncode == 0)
    check("json pretty formatted", "\n  " in result.stdout)


def test_level_assertion() -> None:
    valid = run(str(VALID), "--level", "3")
    valid_level4 = run(
        str(VALID_LEVEL4),
        "--manifest",
        str(VALID_LEVEL4_MANIFEST),
        "--anchor",
        f"dns-txt={VALID_LEVEL4_ANCHOR}",
        "--level",
        "4",
    )
    missing_anchor = run(
        str(MISSING_ANCHOR),
        "--manifest",
        str(MISSING_ANCHOR_MANIFEST),
        "--level",
        "4",
    )
    invalid = run(str(INVALID), "--level", "1")
    check("level assertion pass", valid.returncode == 0)
    check("level 4 assertion pass", valid_level4.returncode == 0, valid_level4.stderr)
    check("level 4 missing anchor fail", missing_anchor.returncode == 1)
    check("level assertion fail", invalid.returncode == 1)


def test_usage_exit() -> None:
    result = run(str(VALID), "--level", "5")
    check("usage exit", result.returncode == 2)


def main() -> int:
    test_json_default()
    test_json_pretty_flag()
    test_level_assertion()
    test_usage_exit()
    print(f"\n{PASSED} passed, {FAILED} failed")
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
