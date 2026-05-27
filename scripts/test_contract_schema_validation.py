#!/usr/bin/env python3
"""
Negative tests for the repository-local schema validation helpers.
"""

from __future__ import annotations

import json
from pathlib import Path

import validate_contracts as vc


ROOT = Path(__file__).resolve().parents[1]


def load_schema(name: str) -> dict:
    return json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))


def expect_errors(label: str, instance: object, schema: dict, expected: list[str]) -> bool:
    errors: list[str] = []
    vc.validate_json_schema_instance(errors, ROOT / "schemas" / "fixture-expected.schema.json", instance, schema)
    missing = [item for item in expected if not any(item in error for error in errors)]
    if missing:
        print(f"FAIL {label}: missing expected errors {missing}; got {errors}")
        return False
    print(f"PASS {label}")
    return True


def main() -> int:
    fixture_schema = load_schema("fixture-expected.schema.json")
    manifest_schema = load_schema("manifest.schema.json")

    ok = True
    ok &= expect_errors(
        "expected duplicate finding ids",
        {
            "evaluation_mode": "local-file",
            "achieved_level": 3,
            "blocking_finding_ids": ["metadata.malformed", "metadata.malformed"],
            "required_warning_ids": [],
            "level5_ready": False,
        },
        fixture_schema,
        ["must contain unique items"],
    )
    ok &= expect_errors(
        "expected invalid finding id",
        {
            "evaluation_mode": "local-file",
            "achieved_level": 3,
            "blocking_finding_ids": ["Bad.ID"],
            "required_warning_ids": [],
            "level5_ready": False,
        },
        fixture_schema,
        ["does not match pattern"],
    )
    ok &= expect_errors(
        "expected achieved level 5 rejected",
        {
            "evaluation_mode": "local-file",
            "achieved_level": 5,
            "blocking_finding_ids": [],
            "required_warning_ids": [],
            "level5_ready": False,
        },
        fixture_schema,
        ["above maximum"],
    )
    ok &= expect_errors(
        "manifest bad guide bytes",
        {
            "guide-path": "/.well-known/assistant-guide.txt",
            "guide-version": "1.0.0",
            "guide-sha256": "0" * 64,
            "guide-bytes": "not-an-integer",
            "immutable-release-url": "https://example.com/release",
        },
        manifest_schema,
        ["guide-bytes must be integer"],
    )
    ok &= expect_errors(
        "manifest bad sha",
        {
            "guide-path": "/.well-known/assistant-guide.txt",
            "guide-version": "1.0.0",
            "guide-sha256": "not-a-sha",
            "guide-bytes": 100,
            "immutable-release-url": "https://example.com/release",
        },
        manifest_schema,
        ["guide-sha256 does not match pattern"],
    )
    ok &= expect_errors(
        "manifest missing immutable release",
        {
            "guide-path": "/.well-known/assistant-guide.txt",
            "guide-version": "1.0.0",
            "guide-sha256": "0" * 64,
            "guide-bytes": 100,
        },
        manifest_schema,
        ["immutable-release-url is required"],
    )

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
