#!/usr/bin/env python3
"""
Run the local reference verifier against static fixture expectations.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import guidecheck_verify


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"


def fixture_dirs() -> list[Path]:
    return sorted(path.parent for path in FIXTURES.glob("*/*/expected.json"))


def fixture_anchor_paths(path: Path) -> dict[str, Path]:
    anchor_dir = path / "anchors"
    if not anchor_dir.is_dir():
        return {}
    anchors: dict[str, Path] = {}
    for anchor_path in sorted(anchor_dir.glob("*.txt")):
        channel = anchor_path.stem
        if channel in guidecheck_verify.ANCHOR_CHANNELS:
            anchors[channel] = anchor_path
    return anchors


def compare_fixture(path: Path) -> list[str]:
    expected = json.loads((path / "expected.json").read_text(encoding="utf-8"))
    if expected["evaluation_mode"] != "local-file":
        return []
    guide = path / "guide.txt"
    manifest = path / "manifest.txt"
    anchors = fixture_anchor_paths(path)
    evaluation = guidecheck_verify.evaluate_local_file(
        guide,
        manifest if manifest.exists() else None,
        anchors,
    )
    output = guidecheck_verify.output_for(evaluation)
    actual_blocking = sorted(
        finding["id"] for finding in output["findings"] if finding["severity"] == "error"
    )
    actual_warnings = sorted(
        finding["id"] for finding in output["findings"] if finding["severity"] == "warning"
    )

    errors: list[str] = []
    if output["input"]["evaluation_mode"] != expected["evaluation_mode"]:
        errors.append(
            f"evaluation_mode expected {expected['evaluation_mode']} got {output['input']['evaluation_mode']}"
        )
    if output["guide"]["achieved_level"] != expected["achieved_level"]:
        errors.append(
            f"achieved_level expected {expected['achieved_level']} got {output['guide']['achieved_level']}"
        )
    if "guide_sha256" in expected and output["guide"]["sha256"] != expected["guide_sha256"]:
        errors.append("guide_sha256 mismatch")
    if "guide_bytes" in expected and output["guide"]["bytes"] != expected["guide_bytes"]:
        errors.append(
            f"guide_bytes expected {expected['guide_bytes']} got {output['guide']['bytes']}"
        )
    if actual_blocking != sorted(expected["blocking_finding_ids"]):
        errors.append(
            "blocking_finding_ids expected "
            f"{sorted(expected['blocking_finding_ids'])} got {actual_blocking}"
        )
    missing_warnings = sorted(set(expected["required_warning_ids"]) - set(actual_warnings))
    if missing_warnings:
        errors.append(f"required warnings missing {missing_warnings}")
    if output["guide"]["level5_ready"] != expected["level5_ready"]:
        errors.append(
            f"level5_ready expected {expected['level5_ready']} got {output['guide']['level5_ready']}"
        )
    return errors


def main() -> int:
    failures: list[str] = []
    fixtures = fixture_dirs()
    checked = 0
    for fixture in fixtures:
        expected = json.loads((fixture / "expected.json").read_text(encoding="utf-8"))
        if expected["evaluation_mode"] != "local-file":
            continue
        checked += 1
        errors = compare_fixture(fixture)
        if errors:
            failures.append(f"{fixture.relative_to(ROOT)}: {'; '.join(errors)}")
    if failures:
        print("Reference verifier fixture failures:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print(f"Reference verifier fixtures passed: {checked} cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
