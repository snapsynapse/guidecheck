#!/usr/bin/env python3
"""
Dependency-free contract checks for GuideCheck fixtures and verifier output.

This is intentionally narrower than full JSON Schema validation. It validates
the fields this repository publishes as a stable fixture and verifier-output
contract, without adding a third-party dependency to the eval path.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import check_reference_verifier as crv
import guidecheck_verify as gv


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
FINDING_ID = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
SEMVER = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-+].*)?$")
SEVERITIES = {"error", "warning", "info"}


def fail(errors: list[str], path: Path, message: str) -> None:
    errors.append(f"{path.relative_to(ROOT)}: {message}")


def require_type(errors: list[str], path: Path, obj: dict, key: str, typ: type) -> bool:
    if key not in obj:
        fail(errors, path, f"missing required key {key}")
        return False
    if not isinstance(obj[key], typ):
        fail(errors, path, f"{key} must be {typ.__name__}")
        return False
    return True


def validate_id_list(errors: list[str], path: Path, obj: dict, key: str) -> None:
    if not require_type(errors, path, obj, key, list):
        return
    seen: set[str] = set()
    for item in obj[key]:
        if not isinstance(item, str) or not FINDING_ID.fullmatch(item):
            fail(errors, path, f"{key} contains invalid finding id {item!r}")
        if item in seen:
            fail(errors, path, f"{key} contains duplicate finding id {item}")
        seen.add(item)


def validate_fixture_expected(errors: list[str], expected_path: Path) -> None:
    try:
        data = json.loads(expected_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(errors, expected_path, f"invalid JSON: {exc}")
        return

    require_type(errors, expected_path, data, "description", str)
    if require_type(errors, expected_path, data, "evaluation_mode", str):
        if data["evaluation_mode"] not in {"public-web", "local-file"}:
            fail(errors, expected_path, "evaluation_mode must be public-web or local-file")
    if require_type(errors, expected_path, data, "achieved_level", int):
        if not 0 <= data["achieved_level"] <= 4:
            fail(errors, expected_path, "achieved_level must be between 0 and 4")
    if "guide_sha256" in data and not (
        isinstance(data["guide_sha256"], str) and HEX64.fullmatch(data["guide_sha256"])
    ):
        fail(errors, expected_path, "guide_sha256 must be lowercase hex SHA-256")
    if "guide_bytes" in data and not (
        isinstance(data["guide_bytes"], int) and data["guide_bytes"] >= 0
    ):
        fail(errors, expected_path, "guide_bytes must be a non-negative integer")
    validate_id_list(errors, expected_path, data, "blocking_finding_ids")
    validate_id_list(errors, expected_path, data, "required_warning_ids")
    require_type(errors, expected_path, data, "level5_ready", bool)


def registered_finding_ids() -> set[str]:
    registry = ROOT / "finding-ids.md"
    text = registry.read_text(encoding="utf-8")
    return set(re.findall(r"`([a-z0-9][a-z0-9._-]*)`", text))


def validate_verifier_output(errors: list[str], fixture_dir: Path) -> None:
    evaluation = gv.evaluate_local_file(
        fixture_dir / "guide.txt",
        fixture_dir / "manifest.txt" if (fixture_dir / "manifest.txt").exists() else None,
    )
    output = gv.output_for(evaluation)
    label = fixture_dir / "expected.json"

    for key in ("verifier", "input", "guide", "summary", "findings"):
        if key not in output:
            fail(errors, label, f"verifier output missing {key}")
    verifier = output.get("verifier", {})
    if not isinstance(verifier, dict):
        fail(errors, label, "verifier output verifier must be an object")
    else:
        for key in (
            "name",
            "version",
            "verifier_profile",
            "verifier_profile_version",
            "guide_profile",
            "guide_profile_version",
        ):
            if not isinstance(verifier.get(key), str) or not verifier[key]:
                fail(errors, label, f"verifier.{key} must be a non-empty string")
        for key in ("version", "verifier_profile_version", "guide_profile_version"):
            if isinstance(verifier.get(key), str) and not SEMVER.fullmatch(verifier[key]):
                fail(errors, label, f"verifier.{key} must be SemVer")

    guide = output.get("guide", {})
    if not isinstance(guide, dict):
        fail(errors, label, "verifier output guide must be an object")
    else:
        if not isinstance(guide.get("bytes"), int) or guide["bytes"] < 0:
            fail(errors, label, "guide.bytes must be a non-negative integer")
        if not isinstance(guide.get("sha256"), str) or not HEX64.fullmatch(guide["sha256"]):
            fail(errors, label, "guide.sha256 must be lowercase hex SHA-256")
        if not isinstance(guide.get("achieved_level"), int):
            fail(errors, label, "guide.achieved_level must be an integer")
        if not isinstance(guide.get("level5_ready"), bool):
            fail(errors, label, "guide.level5_ready must be boolean")

    summary = output.get("summary", {})
    if not isinstance(summary, dict):
        fail(errors, label, "summary must be an object")
    else:
        for key in ("blocking_findings", "warnings", "infos"):
            if not isinstance(summary.get(key), int) or summary[key] < 0:
                fail(errors, label, f"summary.{key} must be a non-negative integer")

    findings = output.get("findings", [])
    if not isinstance(findings, list):
        fail(errors, label, "findings must be an array")
    else:
        for finding in findings:
            if not isinstance(finding, dict):
                fail(errors, label, "finding entries must be objects")
                continue
            if not isinstance(finding.get("id"), str) or not FINDING_ID.fullmatch(finding["id"]):
                fail(errors, label, f"finding id is invalid: {finding.get('id')!r}")
            if finding.get("severity") not in SEVERITIES:
                fail(errors, label, f"finding severity is invalid: {finding.get('severity')!r}")
            if not isinstance(finding.get("message"), str) or not finding["message"]:
                fail(errors, label, "finding message must be a non-empty string")

    if not isinstance(output.get("compact_report"), str) or not output["compact_report"]:
        fail(errors, label, "compact_report must be a non-empty string")


def main() -> int:
    errors: list[str] = []
    registered_ids = registered_finding_ids()
    fixture_dirs = crv.fixture_dirs()
    for fixture_dir in fixture_dirs:
        validate_fixture_expected(errors, fixture_dir / "expected.json")
        validate_verifier_output(errors, fixture_dir)
        expected = json.loads((fixture_dir / "expected.json").read_text(encoding="utf-8"))
        for key in ("blocking_finding_ids", "required_warning_ids"):
            for finding_id in expected[key]:
                if finding_id not in registered_ids:
                    fail(errors, fixture_dir / "expected.json", f"{finding_id} is not in finding-ids.md")

    if errors:
        print(f"Contract validation failed: {len(errors)} issue(s)", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"Contract validation passed: {len(fixture_dirs)} fixtures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
