#!/usr/bin/env python3
"""Subprocess checks for the opt-in GuideCheck POSIX JSON CLI contract."""

from __future__ import annotations

import copy
import contextlib
import errno
import io
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import validate_contracts as vc
import guidecheck_cli_contract as contract_module
import guidecheck_verify as verifier_module


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "guidecheck_verify.py"
DISPATCHER = ROOT / "scripts" / "guidecheck_cli.py"
SCHEMA_PATH = ROOT / "schemas" / "cli-result-posix-json-v1.json"
SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
VALID = ROOT / "fixtures" / "valid" / "level-3" / "guide.txt"
VALID_LEVEL2 = ROOT / "fixtures" / "valid" / "level-2" / "guide.txt"
STRICT = ROOT / "fixtures" / "profiles" / "1.0.0" / "dns-only" / "guide.txt"
CORRECTED = ROOT / "fixtures" / "profiles" / "2.0.0" / "corrected-safe-negation" / "guide.txt"
WARNING = ROOT / "fixtures" / "valid" / "registry-url-mismatch" / "guide.txt"
WARNING_MANIFEST = ROOT / "fixtures" / "valid" / "registry-url-mismatch" / "manifest.txt"
WARNING_ANCHOR = ROOT / "fixtures" / "valid" / "registry-url-mismatch" / "anchors" / "package-registry.txt"
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


def run(*args: str, dispatcher: bool = False) -> subprocess.CompletedProcess[str]:
    script = DISPATCHER if dispatcher else CLI
    prefix = ["verify"] if dispatcher else []
    return subprocess.run(
        [sys.executable, str(script), *prefix, *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def parse_terminal(label: str, result: subprocess.CompletedProcess[str]) -> dict | None:
    decoder = json.JSONDecoder()
    try:
        parsed, end = decoder.raw_decode(result.stdout)
    except json.JSONDecodeError as exc:
        check(f"{label} terminal json", False, f"{exc}: {result.stdout!r}")
        return None
    check(f"{label} one stdout value", not result.stdout[end:].strip(), result.stdout[end:])
    check(f"{label} object", isinstance(parsed, dict), repr(parsed))
    if not isinstance(parsed, dict):
        return None
    errors: list[str] = []
    vc.validate_json_schema_instance(errors, SCHEMA_PATH, parsed, SCHEMA)
    check(f"{label} schema", not errors, "; ".join(errors))
    check(f"{label} terminal", parsed.get("terminal") is True)
    check(f"{label} exit agrees", parsed.get("exit_code") == result.returncode)
    return parsed


def normalized_report(report: dict) -> dict:
    normalized = copy.deepcopy(report)
    normalized.get("local_evaluation", {}).pop("evaluated_at", None)
    return normalized


def test_accepted_and_report_compatibility() -> None:
    legacy = run(str(VALID))
    selected = run(str(VALID), "--contract", "posix-json-v1")
    output = parse_terminal("accepted", selected)
    check("accepted exit", selected.returncode == 0, selected.stderr)
    if output is None:
        return
    check("accepted operational", output["operational"] == {"status": "complete", "error": None})
    check("accepted gate", output["gate"]["status"] == "accepted")
    check("accepted legacy exit", output["legacy_exit_code"] == 0)
    legacy_report = json.loads(legacy.stdout)
    check(
        "nested report unchanged",
        normalized_report(output["report"]) == normalized_report(legacy_report),
    )


def test_selected_profile_report_compatibility() -> None:
    for label, guide in (("strict", STRICT), ("corrected", CORRECTED)):
        legacy = run(str(guide))
        selected = run(str(guide), "--contract", "posix-json-v1")
        output = parse_terminal(f"{label}-parity", selected)
        check(f"{label} native result parseable", bool(legacy.stdout.strip()), legacy.stderr)
        check(f"{label} contract operational complete", output is not None and output["operational"]["status"] == "complete")
        if output is not None:
            check(
                f"{label} nested report unchanged",
                normalized_report(output["report"]) == normalized_report(json.loads(legacy.stdout)),
            )


def test_dispatcher_reaches_contract() -> None:
    result = run(str(VALID), "--contract", "posix-json-v1", dispatcher=True)
    output = parse_terminal("dispatcher", result)
    check("dispatcher accepted", output is not None and output["gate"]["status"] == "accepted")


def test_gate_mappings() -> None:
    cases = [
        ("blocking", (str(INVALID), "--contract", "posix-json-v1"), 2, "rejected", 1),
        ("lower-level", (str(VALID_LEVEL2), "--level", "3", "--contract", "posix-json-v1"), 2, "rejected", 1),
        ("level4-cap", (str(VALID), "--level", "4", "--contract", "posix-json-v1"), 3, "inconclusive", 1),
        ("level4-blocking", (str(INVALID), "--level", "4", "--contract", "posix-json-v1"), 2, "rejected", 1),
        ("warning-policy", (str(WARNING), "--manifest", str(WARNING_MANIFEST), "--anchor", f"package-registry={WARNING_ANCHOR}", "--fail-on-warning", "--contract", "posix-json-v1"), 2, "rejected", 1),
    ]
    for label, args, expected_exit, expected_gate, legacy_exit in cases:
        result = run(*args)
        output = parse_terminal(label, result)
        check(f"{label} exit", result.returncode == expected_exit, result.stderr)
        if output is not None:
            check(f"{label} gate", output["gate"]["status"] == expected_gate)
            check(f"{label} legacy exit", output["legacy_exit_code"] == legacy_exit)
            check(f"{label} operational complete", output["operational"]["status"] == "complete")


def test_operational_failures() -> None:
    missing = run("missing-guide.txt", "--contract", "posix-json-v1")
    missing_output = parse_terminal("missing", missing)
    check("missing exit", missing.returncode == 66)
    if missing_output is not None:
        check("missing operational failed", missing_output["operational"]["status"] == "failed")
        check("missing no report", missing_output["report"] is None)

    missing_manifest = run(
        str(VALID), "--manifest", "missing-manifest.txt", "--contract", "posix-json-v1"
    )
    manifest_output = parse_terminal("missing-manifest", missing_manifest)
    check("missing manifest exit", missing_manifest.returncode == 66)
    check("missing manifest id", manifest_output is not None and manifest_output["operational"]["error"]["id"] == "manifest-input-missing")

    missing_anchor = run(
        str(VALID), "--anchor", "dns-txt=missing-anchor.txt", "--contract", "posix-json-v1"
    )
    anchor_output = parse_terminal("missing-anchor", missing_anchor)
    check("missing anchor exit", missing_anchor.returncode == 66)
    check("missing anchor id", anchor_output is not None and anchor_output["operational"]["error"]["id"] == "anchor-input-missing")

    invalid_profile = run(
        str(VALID),
        "--require-profile-version",
        "9.9.9",
        "--contract",
        "posix-json-v1",
    )
    profile_output = parse_terminal("invalid-profile", invalid_profile)
    check("invalid profile exit", invalid_profile.returncode == 65)
    if profile_output is not None:
        check("invalid profile data id", profile_output["operational"]["error"]["id"] == "invalid-profile-data")

    mismatch = run(
        str(VALID), "--require-profile-version", "1.0.0", "--contract", "posix-json-v1"
    )
    mismatch_output = parse_terminal("profile-mismatch", mismatch)
    check("supported profile mismatch exit", mismatch.returncode == 65)
    check("supported profile mismatch id", mismatch_output is not None and mismatch_output["operational"]["error"]["id"] == "invalid-profile-data")

    with tempfile.TemporaryDirectory() as directory:
        invalid_manifest = Path(directory) / "invalid-manifest.txt"
        invalid_manifest.write_bytes(b"\xff")
        invalid_text = run(
            str(VALID), "--manifest", str(invalid_manifest), "--contract", "posix-json-v1"
        )
    invalid_text_output = parse_terminal("invalid-text", invalid_text)
    check("invalid text exit", invalid_text.returncode == 65)
    check("invalid text id", invalid_text_output is not None and invalid_text_output["operational"]["error"]["id"] == "invalid-input-text")


def run_injected(*, input_reader=None, evaluate_local_file=None) -> tuple[int, dict]:
    stream = io.StringIO()
    with contextlib.redirect_stdout(stream):
        code = contract_module.run_contract(
            [str(VALID), "--contract", "posix-json-v1"],
            evaluate_local_file=evaluate_local_file or verifier_module.evaluate_local_file,
            output_for=verifier_module.output_for,
            profile_error_type=verifier_module.ProfileError,
            input_reader=input_reader,
        )
    return code, json.loads(stream.getvalue())


def test_injected_operational_failures() -> None:
    def denied(_path: Path) -> bytes:
        raise PermissionError(errno.EACCES, "denied")

    permission_code, permission = run_injected(input_reader=denied)
    check("injected permission exit", permission_code == 77)
    check("injected permission id", permission["operational"]["error"]["id"] == "input-permission-denied")

    def io_failure(_path: Path) -> bytes:
        raise OSError(errno.EIO, "i/o failure")

    io_code, io_result = run_injected(input_reader=io_failure)
    check("injected io exit", io_code == 74)
    check("injected io id", io_result["operational"]["error"]["id"] == "input-io-failure")

    def unknown_failure(*_args, **_kwargs):
        raise RuntimeError("unknown callback failure")

    unknown_code, unknown = run_injected(evaluate_local_file=unknown_failure)
    check("injected unknown exit", unknown_code == 1)
    check("injected unknown id", unknown["operational"]["error"]["id"] == "operational-failure")


def test_contract_invocation_errors() -> None:
    cases = [
        ("unsupported-contract", (str(VALID), "--contract", "other")),
        ("equals-syntax", (str(VALID), "--contract=posix-json-v1")),
        ("abbreviated-option", (str(VALID), "--lev", "3", "--contract", "posix-json-v1")),
        ("duplicate-option", (str(VALID), "--level", "3", "--level", "3", "--contract", "posix-json-v1")),
        ("duplicate-anchor-channel", (str(VALID), "--anchor", "dns-txt=a", "--anchor", "dns-txt=b", "--contract", "posix-json-v1")),
        ("pretty-conflict", (str(VALID), "--contract", "posix-json-v1", "--pretty")),
        ("text-conflict", (str(VALID), "--contract", "posix-json-v1", "--format", "text")),
    ]
    for label, args in cases:
        result = run(*args)
        output = parse_terminal(label, result)
        check(f"{label} exit", result.returncode == 64, result.stderr)
        if output is not None:
            check(f"{label} failed", output["operational"]["status"] == "failed")

    redundant_json = run(str(VALID), "--json", "--contract", "posix-json-v1")
    redundant_output = parse_terminal("redundant-json", redundant_json)
    check("redundant json accepted", redundant_json.returncode == 0)
    check(
        "redundant json gate accepted",
        redundant_output is not None and redundant_output["gate"]["status"] == "accepted",
    )

    help_result = run("--contract", "posix-json-v1", "--help")
    help_output = parse_terminal("contract-help", help_result)
    check("contract help exit", help_result.returncode == 0)
    check("contract help on stderr", "usage:" in help_result.stderr)
    if help_output is not None:
        check("contract help no report", help_output["report"] is None)
        check("contract help gate not requested", help_output["gate"]["status"] == "not_requested")

    for label, args in (
        ("help-unknown", ("--contract", "posix-json-v1", "--help", "--bogus")),
        ("help-text", ("--contract", "posix-json-v1", "--help", "--format", "text")),
        ("help-pretty", ("--contract", "posix-json-v1", "--help", "--pretty")),
        ("duplicate-help-alias", ("--contract", "posix-json-v1", "-h", "--help")),
        ("missing-path", ("--contract", "posix-json-v1")),
    ):
        result = run(*args)
        output = parse_terminal(label, result)
        check(f"{label} exit", result.returncode == 64, result.stderr)
        check(
            f"{label} operational failed",
            output is not None and output["operational"]["status"] == "failed",
        )

    literal_selector = run("--", "--contract")
    check("literal selector uses legacy path", literal_selector.returncode == 2)
    check("literal selector emits no contract json", not literal_selector.stdout.strip())
    check("literal selector is treated as path", "guide not found: --contract" in literal_selector.stderr)


def test_legacy_and_scan_unchanged() -> None:
    legacy = run(str(INVALID))
    check("legacy verifier exit remains 1", legacy.returncode == 1)
    check("legacy verifier report remains bare", "contract" not in json.loads(legacy.stdout))

    scan = subprocess.run(
        [
            sys.executable,
            str(DISPATCHER),
            "scan",
            str(VALID),
            "--contract",
            "posix-json-v1",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    check("scan contract remains unsupported", scan.returncode == 2)
    check("scan contract emits no json envelope", not scan.stdout.strip())


def main() -> int:
    test_accepted_and_report_compatibility()
    test_selected_profile_report_compatibility()
    test_dispatcher_reaches_contract()
    test_gate_mappings()
    test_operational_failures()
    test_injected_operational_failures()
    test_contract_invocation_errors()
    test_legacy_and_scan_unchanged()
    print(f"\n{PASSED} passed, {FAILED} failed")
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
