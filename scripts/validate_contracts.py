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
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import check_reference_verifier as crv
import guidecheck_verify as gv


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
FINDING_ID = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
SEMVER = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-+].*)?$")
SEVERITIES = {"error", "warning", "info"}
SCHEMA_FILES = [
    ROOT / "schemas" / "manifest.schema.json",
    ROOT / "schemas" / "verifier-output.schema.json",
    ROOT / "schemas" / "fixture-expected.schema.json",
]


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


def type_matches(value: object, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "number":
        return (isinstance(value, int) or isinstance(value, float)) and not isinstance(value, bool)
    if expected == "null":
        return value is None
    return True


def check_format(value: object, fmt: str) -> bool:
    if not isinstance(value, str):
        return False
    if fmt == "uri":
        parsed = urlparse(value)
        return bool(parsed.scheme and parsed.netloc)
    if fmt == "date-time":
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return False
        return True
    return True


def validate_json_schema_instance(
    errors: list[str],
    label: Path,
    instance: object,
    schema: dict,
    *,
    at: str = "$",
) -> None:
    if "anyOf" in schema:
        trial_errors: list[list[str]] = []
        for option in schema["anyOf"]:
            option_errors: list[str] = []
            validate_json_schema_instance(option_errors, label, instance, option, at=at)
            if not option_errors:
                return
            trial_errors.append(option_errors)
        fail(errors, label, f"{at} does not match any allowed schema")
        return

    if "type" in schema:
        expected = schema["type"]
        if isinstance(expected, list):
            if not any(type_matches(instance, item) for item in expected):
                fail(errors, label, f"{at} has wrong type")
                return
        elif not type_matches(instance, expected):
            fail(errors, label, f"{at} must be {expected}")
            return

    if "enum" in schema and instance not in schema["enum"]:
        fail(errors, label, f"{at} must be one of {schema['enum']}")
    if "const" in schema and instance != schema["const"]:
        fail(errors, label, f"{at} must equal {schema['const']!r}")

    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            fail(errors, label, f"{at} is shorter than minLength")
        if "pattern" in schema and not re.fullmatch(schema["pattern"], instance):
            fail(errors, label, f"{at} does not match pattern")
        if "format" in schema and not check_format(instance, schema["format"]):
            fail(errors, label, f"{at} is not a valid {schema['format']}")

    if isinstance(instance, int) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            fail(errors, label, f"{at} is below minimum")
        if "maximum" in schema and instance > schema["maximum"]:
            fail(errors, label, f"{at} is above maximum")

    if isinstance(instance, list):
        if schema.get("uniqueItems"):
            seen = {json.dumps(item, sort_keys=True) for item in instance}
            if len(seen) != len(instance):
                fail(errors, label, f"{at} must contain unique items")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(instance):
                validate_json_schema_instance(errors, label, item, item_schema, at=f"{at}[{index}]")

    if isinstance(instance, dict):
        for key in schema.get("required", []):
            if key not in instance:
                fail(errors, label, f"{at}.{key} is required")
        properties = schema.get("properties", {})
        for key, value in instance.items():
            child_schema = properties.get(key)
            if isinstance(child_schema, dict):
                validate_json_schema_instance(errors, label, value, child_schema, at=f"{at}.{key}")
            elif schema.get("additionalProperties") is False:
                fail(errors, label, f"{at}.{key} is not allowed")


def load_schema(errors: list[str], schema_path: Path) -> dict | None:
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(errors, schema_path, f"invalid JSON Schema: {exc}")
        return None
    if not isinstance(schema, dict):
        fail(errors, schema_path, "schema root must be an object")
        return None
    for key in ("$schema", "$id", "title", "type"):
        if key not in schema:
            fail(errors, schema_path, f"schema missing {key}")
    return schema


def parse_manifest_for_schema(path: Path) -> dict:
    data = gv.parse_manifest(path.read_text(encoding="utf-8"))
    if "guide-bytes" in data:
        try:
            data["guide-bytes"] = int(data["guide-bytes"])
        except ValueError:
            pass
    return data


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
    if not (fixture_dir / "guide.txt").exists():
        return
    evaluation = gv.evaluate_local_file(
        fixture_dir / "guide.txt",
        fixture_dir / "manifest.txt" if (fixture_dir / "manifest.txt").exists() else None,
        crv.fixture_anchor_paths(fixture_dir),
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


def validate_public_fetch_scenario(errors: list[str], fixture_dir: Path) -> None:
    scenario_path = fixture_dir / "scenario.json"
    if not scenario_path.exists():
        return
    try:
        scenario = json.loads(scenario_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(errors, scenario_path, f"invalid JSON: {exc}")
        return
    if not isinstance(scenario.get("url"), str) or not scenario["url"]:
        fail(errors, scenario_path, "url must be a non-empty string")
    if "redirects" in scenario:
        redirects = scenario["redirects"]
        if not isinstance(redirects, list) or not all(isinstance(item, str) for item in redirects):
            fail(errors, scenario_path, "redirects must be an array of strings")
    if "tls_valid" in scenario and not isinstance(scenario["tls_valid"], bool):
        fail(errors, scenario_path, "tls_valid must be boolean")
    if "headers" in scenario and not (
        isinstance(scenario["headers"], dict)
        and all(isinstance(key, str) and isinstance(value, str) for key, value in scenario["headers"].items())
    ):
        fail(errors, scenario_path, "headers must be an object of strings")
    if "variant_bodies" in scenario:
        bodies = scenario["variant_bodies"]
        if not isinstance(bodies, list) or len(bodies) != 2 or not all(isinstance(item, str) for item in bodies):
            fail(errors, scenario_path, "variant_bodies must be an array of two strings")


def main() -> int:
    errors: list[str] = []
    schemas: dict[str, dict] = {}
    for schema_path in SCHEMA_FILES:
        schema = load_schema(errors, schema_path)
        if schema is not None:
            schemas[schema_path.name] = schema

    registered_ids = registered_finding_ids()
    fixture_dirs = crv.fixture_dirs()
    for fixture_dir in fixture_dirs:
        expected_path = fixture_dir / "expected.json"
        validate_fixture_expected(errors, expected_path)
        if "fixture-expected.schema.json" in schemas:
            try:
                expected_data = json.loads(expected_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                expected_data = None
            if expected_data is not None:
                validate_json_schema_instance(
                    errors,
                    expected_path,
                    expected_data,
                    schemas["fixture-expected.schema.json"],
                )

        validate_verifier_output(errors, fixture_dir)
        if "verifier-output.schema.json" in schemas and (fixture_dir / "guide.txt").exists():
            evaluation = gv.evaluate_local_file(
                fixture_dir / "guide.txt",
                fixture_dir / "manifest.txt" if (fixture_dir / "manifest.txt").exists() else None,
                crv.fixture_anchor_paths(fixture_dir),
            )
            validate_json_schema_instance(
                errors,
                fixture_dir / "expected.json",
                gv.output_for(evaluation),
                schemas["verifier-output.schema.json"],
            )

        if "manifest.schema.json" in schemas and (fixture_dir / "manifest.txt").exists():
            validate_json_schema_instance(
                errors,
                fixture_dir / "manifest.txt",
                parse_manifest_for_schema(fixture_dir / "manifest.txt"),
                schemas["manifest.schema.json"],
            )

        validate_public_fetch_scenario(errors, fixture_dir)
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
