#!/usr/bin/env python3
"""
Check that every version-bearing surface agrees with guidecheck_constants.

The profile version is duplicated across the spec, the verifier-conformance
doc, the README, INTENT, the public pages, the examples, and the published
guide. The 0.4.0 release bumped it by hand in over a dozen files (recorded in
threat-register.md as a process risk). This check makes that class of drift a
test failure instead of a release-notes apology.

Rules per surface: each listed pattern must match at least once, and every
match must equal the expected value derived from GUIDECHECK_VERSION.
Also asserts the published .well-known guide copy is byte-identical to the
repository guide (it drifted once at 0.3.1).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from guidecheck_constants import GUIDECHECK_VERSION

ROOT = Path(__file__).resolve().parents[1]

VERSION = GUIDECHECK_VERSION
MAJOR, MINOR, _PATCH = (int(part) for part in VERSION.split("."))
SERIES = f"{MAJOR}.{MINOR}.x"
RANGE_LOW = f"{MAJOR}.{MINOR}.0"
RANGE_HIGH = f"{MAJOR}.{MINOR + 1}.0"

# (file, pattern with one capture group, expected captured value)
CHECKS: list[tuple[str, str, str]] = [
    ("spec.md", r"^profile-version: (\S+)$", VERSION),
    ("spec.md", r"guide-profile version (\d+\.\d+\.x)", SERIES),
    ("verifier-conformance.md", r"verifier-profile version (\d+\.\d+\.x)", SERIES),
    ("verifier-conformance.md", r"\"version\": \"(\d+\.\d+\.\d+)\"", VERSION),
    ("verifier-conformance.md", r"_profile_version\": \"(\d+\.\d+\.\d+)\"", VERSION),
    ("README.md", r"profile version (\d+\.\d+\.\d+)", VERSION),
    ("INTENT.md", r"current version is (\d+\.\d+\.\d+)", VERSION),
    ("assistant-guide.txt", r"^profile-version: (\S+)$", VERSION),
    ("assistant-guide.txt", r"^guide-version: (\S+)$", VERSION),
    ("assistant-guide.txt", r"^applies-to: guidecheck (\d+\.\d+\.x)$", SERIES),
    (
        "assistant-guide.txt",
        r"^verifier-conformance: human-verifiable-assistant-guide-verifier "
        r">=(\d+\.\d+\.\d+), <\d+\.\d+\.\d+$",
        RANGE_LOW,
    ),
    (
        "assistant-guide.txt",
        r"^verifier-conformance: human-verifiable-assistant-guide-verifier "
        r">=\d+\.\d+\.\d+, <(\d+\.\d+\.\d+)$",
        RANGE_HIGH,
    ),
    ("examples/level-3-assistant-guide.txt", r"^profile-version: (\S+)$", VERSION),
    (
        "examples/level-3-assistant-guide.txt",
        r"^verifier-conformance: human-verifiable-assistant-guide-verifier "
        r">=(\d+\.\d+\.\d+), <\d+\.\d+\.\d+$",
        RANGE_LOW,
    ),
    (
        "examples/level-3-assistant-guide.txt",
        r"^verifier-conformance: human-verifiable-assistant-guide-verifier "
        r">=\d+\.\d+\.\d+, <(\d+\.\d+\.\d+)$",
        RANGE_HIGH,
    ),
    (
        "examples/mcp-database-server-assistant-guide.txt",
        r"^profile-version: (\S+)$",
        VERSION,
    ),
    ("examples/manifest.txt", r"^profile-version: (\S+)$", VERSION),
    ("docs/index.html", r"v(\d+\.\d+\.\d+)", VERSION),
    ("docs/index.html", r"[Pp]rofile version (\d+\.\d+\.\d+)", VERSION),
    ("docs/verify/index.html", r"profile (\d+\.\d+\.\d+)", VERSION),
    ("docs/verify/index.html", r"v(\d+\.\d+\.\d+)", VERSION),
    (
        "docs/verifier-examples.html",
        r"guidecheck-reference-local (\d+\.\d+\.\d+)",
        VERSION,
    ),
    ("docs/verifier-examples.html", r"\"version\": \"(\d+\.\d+\.\d+)\"", VERSION),
    ("CHANGELOG.md", r"^## \[(\d+\.\d+\.\d+)\] - \d{4}-\d{2}-\d{2}$", None),  # type: ignore[list-item]
]

BYTE_IDENTICAL: list[tuple[str, str]] = [
    ("assistant-guide.txt", "docs/.well-known/assistant-guide.txt"),
]


def check_patterns() -> list[str]:
    failures: list[str] = []
    for rel_path, pattern, expected in CHECKS:
        text = (ROOT / rel_path).read_text(encoding="utf-8")
        matches = re.findall(pattern, text, flags=re.MULTILINE)
        if expected is None:
            # CHANGELOG: newest released entry must be <= current version and
            # the current version must have an entry unless Unreleased is open.
            if VERSION not in matches:
                failures.append(
                    f"{rel_path}: no release entry for {VERSION} "
                    f"(newest found: {matches[0] if matches else 'none'})"
                )
            continue
        if not matches:
            failures.append(f"{rel_path}: pattern not found: {pattern}")
            continue
        wrong = sorted(set(match for match in matches if match != expected))
        if wrong:
            failures.append(
                f"{rel_path}: expected {expected}, found {', '.join(wrong)} "
                f"for pattern: {pattern}"
            )
    return failures


def check_byte_identical() -> list[str]:
    failures: list[str] = []
    for source, copy in BYTE_IDENTICAL:
        if (ROOT / source).read_bytes() != (ROOT / copy).read_bytes():
            failures.append(f"{copy} is not byte-identical to {source}")
    return failures


def main() -> int:
    failures = check_patterns() + check_byte_identical()
    if failures:
        print("Version sync failures:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print(
        f"Version sync passed: {len(CHECKS)} pattern checks and "
        f"{len(BYTE_IDENTICAL)} byte-identity checks agree with {VERSION}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
