#!/usr/bin/env python3
"""
Check that every version-bearing surface agrees with guidecheck_constants.

The profile version is duplicated across the spec, the verifier-conformance
doc, the README, INTENT, the public pages, the examples, and the published
guide. The 0.4.0 release bumped it by hand in over a dozen files (recorded in
threat-register.md as a process risk). This check makes that class of drift a
test failure instead of a release-notes apology.

Rules per surface: each listed pattern must match at least once, and every
match must equal the independently pinned release, engine, or self-guide version.
Also asserts the published .well-known guide copy is byte-identical to the
repository guide (it drifted once at 0.3.1), and that security.txt declares
the SHA-256 digest of those guide bytes.
"""

from __future__ import annotations

import hashlib
import re
import sys
from datetime import date
from pathlib import Path

from guidecheck_constants import (GUIDECHECK_VERSION, LATEST_RELEASED_PROFILE_VERSION,
                                 SELF_GUIDE_VERSION, SELF_GUIDE_PROFILE_VERSION,
                                 LEGACY_ENGINE_VERSION, STRICT_ENGINE_VERSION,
                                 CORRECTED_ENGINE_VERSION)

ROOT = Path(__file__).resolve().parents[1]

# Public release identity, legacy contracts, and the self-guide are separate.
# A dispatcher or public release bump must never rotate anchored self-guide bytes.
RELEASE_VERSION = GUIDECHECK_VERSION
LEGACY_VERSION = LEGACY_ENGINE_VERSION
MAJOR, MINOR, _PATCH = (int(part) for part in LEGACY_VERSION.split("."))
SERIES = f"{MAJOR}.{MINOR}.x"
RANGE_LOW = f"{MAJOR}.{MINOR}.0"
RANGE_HIGH = f"{MAJOR}.{MINOR + 1}.0"

# (file, pattern with one capture group, expected captured value)
CHECKS: list[tuple[str, str, str]] = [
    ("spec.md", r"^profile-version: (\S+)$", LEGACY_VERSION),
    ("spec.md", r"guide-profile version (\d+\.\d+\.x)", SERIES),
    ("verifier-conformance.md", r"verifier-profile version (\d+\.\d+\.x)", SERIES),
    ("verifier-conformance.md", r"\"version\": \"(\d+\.\d+\.\d+)\"", LEGACY_VERSION),
    ("verifier-conformance.md", r"_profile_version\": \"(\d+\.\d+\.\d+)\"", LEGACY_VERSION),
    ("README.md", r"current release is (\d+\.\d+\.\d+)", RELEASE_VERSION),
    ("ADOPTION.md", r"current release is\s+\[(\d+\.\d+\.\d+)\]", RELEASE_VERSION),
    ("INTENT.md", r"current release version is (\d+\.\d+\.\d+)", RELEASE_VERSION),
    ("PROJECT_CONTEXT.md", r"current release is (\d+\.\d+\.\d+)", RELEASE_VERSION),
    ("CLAUDE.md", r"current release is (\d+\.\d+\.\d+)", RELEASE_VERSION),
    ("operator-guide.md", r"current release profile is (\d+\.\d+\.\d+)", RELEASE_VERSION),
    ("docs/llms.txt", r"Current release: (\d+\.\d+\.\d+)", RELEASE_VERSION),
    ("schemas/README.md", r"current release profile (\d+\.\d+\.\d+)", RELEASE_VERSION),
    ("assistant-guide.txt", r"^profile-version: (\S+)$", SELF_GUIDE_PROFILE_VERSION),
    ("assistant-guide.txt", r"^guide-version: (\S+)$", SELF_GUIDE_VERSION),
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
    ("examples/level-3-assistant-guide.txt", r"^profile-version: (\S+)$", LEGACY_VERSION),
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
        LEGACY_VERSION,
    ),
    ("examples/manifest.txt", r"^profile-version: (\S+)$", LEGACY_VERSION),
    ("docs/index.html", r"v(\d+\.\d+\.\d+)", RELEASE_VERSION),
    ("docs/index.html", r"[Pp]rofile release (\d+\.\d+\.\d+)", RELEASE_VERSION),
    ("docs/verify/index.html", r"profile (\d+\.\d+\.\d+)", RELEASE_VERSION),
    ("docs/verify/index.html", r"v(\d+\.\d+\.\d+)", RELEASE_VERSION),
    (
        "docs/verifier-examples.html",
        r"guidecheck-reference-local (\d+\.\d+\.\d+)",
        LEGACY_VERSION,
    ),
    ("docs/verifier-examples.html", r"\"version\": \"(\d+\.\d+\.\d+)\"", LEGACY_VERSION),
    ("profiles/1.0.0/spec.md", r"^profile-version: (\S+)$", STRICT_ENGINE_VERSION),
    ("profiles/1.0.0/verifier-conformance.md", r"_profile_version\": \"(\d+\.\d+\.\d+)\"", STRICT_ENGINE_VERSION),
    ("profiles/2.0.0/spec.md", r"^Status: released profile (\d+\.\d+\.\d+)\.", CORRECTED_ENGINE_VERSION),
    ("profiles/2.0.0/verifier-conformance.md", r"^Status: released profile (\d+\.\d+\.\d+)\.", CORRECTED_ENGINE_VERSION),
    ("RELEASE_NOTES-2.0.0.md", r"^Release version: (\d+\.\d+\.\d+)$", RELEASE_VERSION),
    ("docs/release-2.0.0.md", r"^Release version: (\d+\.\d+\.\d+)$", RELEASE_VERSION),
]

BYTE_IDENTICAL: list[tuple[str, str]] = [
    ("assistant-guide.txt", "docs/.well-known/assistant-guide.txt"),
    ("assistant-guide-manifest.txt", "docs/.well-known/assistant-guide-manifest.txt"),
]


def check_patterns() -> list[str]:
    failures: list[str] = []
    for rel_path, pattern, expected in CHECKS:
        text = (ROOT / rel_path).read_text(encoding="utf-8")
        matches = re.findall(pattern, text, flags=re.MULTILINE)
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


def check_dated_release_record() -> list[str]:
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    match = re.search(
        rf"^## \[{re.escape(RELEASE_VERSION)}\] - (\d{{4}}-\d{{2}}-\d{{2}})$",
        changelog,
        re.MULTILINE,
    )
    if match is None:
        return [f"CHANGELOG.md: missing dated release entry for {RELEASE_VERSION}"]
    release_date = date.fromisoformat(match.group(1))
    iso = release_date.isoformat()
    label = f"{release_date:%B} {release_date.day}, {release_date.year}"
    page = (ROOT / "docs/index.html").read_text(encoding="utf-8")
    checks = [
        ("structured modification date", r'"dateModified": "([^"]+)"', [iso]),
        ("visible updated date", r'Updated <time datetime="([^"]+)">([^<]+)</time>', [(iso, label)]),
        ("substantive release date", r'Release 2\.0\.0 published:\s*<time datetime="([^"]+)">([^<]+)</time>', [(iso, iso)]),
    ]
    return [
        f"docs/index.html: {name} must match release {RELEASE_VERSION} ({iso})"
        for name, pattern, expected in checks
        if re.findall(pattern, page) != expected
    ]


def check_byte_identical() -> list[str]:
    failures: list[str] = []
    for source, copy in BYTE_IDENTICAL:
        if (ROOT / source).read_bytes() != (ROOT / copy).read_bytes():
            failures.append(f"{copy} is not byte-identical to {source}")
    return failures


def check_security_guide_hash() -> list[str]:
    security_path = ROOT / "docs" / ".well-known" / "security.txt"
    fields = re.findall(
        r"^Assistant-Guide-SHA256:[ \t]*(.*?)[ \t]*$",
        security_path.read_text(encoding="utf-8"),
        flags=re.MULTILINE,
    )
    if len(fields) != 1:
        return [
            "docs/.well-known/security.txt: expected exactly one "
            "Assistant-Guide-SHA256 field"
        ]
    if re.fullmatch(r"[0-9a-f]{64}", fields[0]) is None:
        return [
            "docs/.well-known/security.txt: Assistant-Guide-SHA256 must be "
            "exactly 64 lowercase hexadecimal characters"
        ]

    expected = hashlib.sha256((ROOT / "assistant-guide.txt").read_bytes()).hexdigest()
    if fields[0] != expected:
        return [
            "docs/.well-known/security.txt: Assistant-Guide-SHA256 does not "
            "match assistant-guide.txt"
        ]
    return []


def main() -> int:
    failures = (
        check_patterns()
        + check_byte_identical()
        + check_security_guide_hash()
        + check_dated_release_record()
    )
    if SELF_GUIDE_VERSION != "0.7.1" or SELF_GUIDE_PROFILE_VERSION != "0.7.1" or LEGACY_ENGINE_VERSION != "0.7.1" or STRICT_ENGINE_VERSION != "1.0.0" or CORRECTED_ENGINE_VERSION != "2.0.0":
        failures.append("engine/self-guide profile identities disagree with the versioned contracts")
    if not re.fullmatch(r"2\.0\.0", GUIDECHECK_VERSION):
        failures.append("dispatcher must use release version 2.0.0")
    if LATEST_RELEASED_PROFILE_VERSION != CORRECTED_ENGINE_VERSION:
        failures.append("latest released profile must be the corrected 2.0.0 profile")
    if failures:
        print("Version sync failures:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print(
        f"Version sync passed: {len(CHECKS)} pattern checks and "
        f"{len(BYTE_IDENTICAL)} byte-identity checks agree with release {RELEASE_VERSION}; "
        "security.txt matches the self-guide hash; release surfaces agree; "
        "2.0.0 is the latest released profile"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
