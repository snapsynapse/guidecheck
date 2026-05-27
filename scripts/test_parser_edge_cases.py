#!/usr/bin/env python3
"""
Parser edge-case evals for metadata blocks and Level 4 manifests.
"""

from __future__ import annotations

from pathlib import Path

import guidecheck_verify as gv
import validate_contracts as vc


ROOT = Path(__file__).resolve().parents[1]
BASE_GUIDE = (ROOT / "fixtures" / "valid" / "level-3" / "guide.txt").read_text(encoding="utf-8")
VALID_MANIFEST = (ROOT / "fixtures" / "valid" / "level-3" / "manifest.txt").read_text(encoding="utf-8")


def finding_ids_for(text: str, manifest: str | None, severity: str) -> set[str]:
    findings, _level, _ready, _manifest, _anchors = gv.evaluate_guide(
        text.encode("utf-8"),
        manifest_text=manifest,
    )
    return {finding.id for finding in findings if finding.severity == severity}


def replace_once(text: str, old: str, new: str) -> str:
    if old not in text:
        raise AssertionError(f"missing source text: {old[:40]}")
    return text.replace(old, new, 1)


def expect_findings(label: str, text: str, expected_errors: set[str]) -> bool:
    got = finding_ids_for(text, None, "error")
    missing = sorted(expected_errors - got)
    if missing:
        print(f"FAIL {label}: missing {missing}; got {sorted(got)}")
        return False
    print(f"PASS {label}")
    return True


def expect_manifest_findings(label: str, manifest: str, expected_errors: set[str]) -> bool:
    got = finding_ids_for(BASE_GUIDE, manifest, "error")
    missing = sorted(expected_errors - got)
    if missing:
        print(f"FAIL {label}: missing {missing}; got {sorted(got)}")
        return False
    print(f"PASS {label}")
    return True


def expect_no_schema_errors(label: str, manifest: str) -> bool:
    schema = vc.load_schema([], ROOT / "schemas" / "manifest.schema.json")
    assert schema is not None
    errors: list[str] = []
    parsed = gv.parse_manifest(manifest)
    parsed["guide-bytes"] = int(parsed["guide-bytes"])
    vc.validate_json_schema_instance(errors, ROOT / "fixtures" / "valid" / "level-3" / "manifest.txt", parsed, schema)
    if errors:
        print(f"FAIL {label}: unexpected schema errors {errors}")
        return False
    print(f"PASS {label}")
    return True


def main() -> int:
    duplicate_key = replace_once(
        BASE_GUIDE,
        "guide-version: 1.0.0\n",
        "guide-version: 1.0.0\nguide-version: 1.0.1\n",
    )
    nested_fence = replace_once(
        BASE_GUIDE,
        "identifier: assistant-guide\n",
        "identifier: assistant-guide\n[assistant-guide-metadata]\n",
    )
    missing_close = BASE_GUIDE.replace("[/assistant-guide-metadata]\n", "", 1)
    duplicate_block = replace_once(
        BASE_GUIDE,
        "[/assistant-guide-metadata]\n",
        "[/assistant-guide-metadata]\n[assistant-guide-metadata]\nidentifier: duplicate\n[/assistant-guide-metadata]\n",
    )

    missing_manifest_field = "\n".join(
        line for line in VALID_MANIFEST.splitlines() if not line.startswith("immutable-release-url:")
    )
    bad_manifest_bytes = replace_once(VALID_MANIFEST, "guide-bytes: 5135", "guide-bytes: not-an-integer")
    extra_manifest_field = VALID_MANIFEST + "\nextra-field: allowed\n"

    ok = True
    ok &= expect_findings("metadata duplicate key", duplicate_key, {"metadata.malformed"})
    ok &= expect_findings("metadata nested fence", nested_fence, {"metadata.malformed", "metadata.missing-required"})
    ok &= expect_findings("metadata missing close", missing_close, {"metadata.block-count"})
    ok &= expect_findings("metadata duplicate block", duplicate_block, {"metadata.block-count"})
    ok &= expect_manifest_findings("manifest missing required", missing_manifest_field, {"manifest.missing-required"})
    ok &= expect_manifest_findings("manifest bytes invalid", bad_manifest_bytes, {"manifest.bytes-invalid"})
    ok &= expect_no_schema_errors("manifest extra fields allowed", extra_manifest_field)

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
