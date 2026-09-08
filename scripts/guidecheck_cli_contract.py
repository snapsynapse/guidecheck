#!/usr/bin/env python3
"""Opt-in POSIX JSON process contract for the local GuideCheck verifier."""

from __future__ import annotations

import argparse
import errno
import json
import stat
import sys
from pathlib import Path
from typing import Callable

from guidecheck_legacy import ANCHOR_CHANNELS


CONTRACT_NAME = "posix-json-v1"
CONTRACT_VERSION = 1
EX_USAGE = 64
EX_DATAERR = 65
EX_NOINPUT = 66
EX_IOERR = 74
EX_NOPERM = 77


class ContractArgumentError(Exception):
    """A malformed opt-in invocation with a stable error identity."""

    def __init__(self, message: str, error_id: str = "invalid-invocation") -> None:
        super().__init__(message)
        self.error_id = error_id


class _ParserExit(Exception):
    def __init__(self, status: int) -> None:
        super().__init__(status)
        self.status = status


class _ContractParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ContractArgumentError(message)

    def exit(self, status: int = 0, message: str | None = None) -> None:
        if message:
            self._print_message(message, sys.stderr)
        raise _ParserExit(status)

    def print_help(self, file=None) -> None:  # type: ignore[no-untyped-def]
        super().print_help(file=sys.stderr if file is None else file)


def has_contract_selector(argv: list[str]) -> bool:
    """Return true when argv expressly selects any contract value or syntax."""
    option_argv = argv[: argv.index("--")] if "--" in argv else argv
    return any(arg == "--contract" or arg.startswith("--contract=") for arg in option_argv)


def _contract_identity() -> dict[str, object]:
    return {"name": CONTRACT_NAME, "version": CONTRACT_VERSION, "experimental": True}


def _gate(
    status: str,
    *,
    requested_level: int | None = None,
    fail_on_warning: bool = False,
) -> dict[str, object]:
    return {
        "mode": "verify",
        "status": status,
        "requested_level": requested_level,
        "fail_on_warning": fail_on_warning,
    }


def _result(
    *,
    operational: dict[str, object],
    gate: dict[str, object],
    report: dict[str, object] | None,
    legacy_exit_code: int | None,
    exit_code: int,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "contract": _contract_identity(),
        "operational": operational,
        "gate": gate,
        "report": report,
        "legacy_exit_code": legacy_exit_code,
        "exit_code": exit_code,
        "terminal": True,
    }


def _complete_result(
    *,
    gate: dict[str, object],
    report: dict[str, object] | None,
    legacy_exit_code: int | None,
    exit_code: int,
) -> dict[str, object]:
    return _result(
        operational={"status": "complete", "error": None},
        gate=gate,
        report=report,
        legacy_exit_code=legacy_exit_code,
        exit_code=exit_code,
    )


def _error_result(
    message: str,
    *,
    error_id: str,
    exit_code: int,
    requested_level: int | None = None,
    fail_on_warning: bool = False,
) -> dict[str, object]:
    return _result(
        operational={
            "status": "failed",
            "error": {
                "id": error_id,
                "exit_code": exit_code,
                "message": message,
                "retryable": False,
                "safe_to_repeat": False,
            },
        },
        gate=_gate(
            "not_evaluated",
            requested_level=requested_level,
            fail_on_warning=fail_on_warning,
        ),
        report=None,
        legacy_exit_code=None,
        exit_code=exit_code,
    )


def _emit(result: dict[str, object]) -> int:
    print(json.dumps(result, separators=(",", ":")))
    return int(result["exit_code"])


def _validate_selector(argv: list[str]) -> None:
    option_argv = argv[: argv.index("--")] if "--" in argv else argv
    if any(arg.startswith("--") and "=" in arg for arg in option_argv):
        raise ContractArgumentError(
            "contract options require separate values",
            "unsupported-option-syntax",
        )
    positions = [index for index, arg in enumerate(option_argv) if arg == "--contract"]
    if len(positions) != 1:
        raise ContractArgumentError("--contract must be specified exactly once")
    position = positions[0]
    if position + 1 >= len(argv) or argv[position + 1].startswith("-"):
        raise ContractArgumentError("--contract requires a value", "missing-contract-value")
    if argv[position + 1] != CONTRACT_NAME:
        raise ContractArgumentError(
            f"unsupported contract: {argv[position + 1]}",
            "unsupported-contract",
        )

    repeatable = {"--anchor"}
    singular = {
        "--contract",
        "--manifest",
        "--level",
        "--fail-on-warning",
        "--require-profile-version",
        "--format",
        "--json",
        "--pretty",
    }
    counts: dict[str, int] = {}
    for arg in option_argv:
        if arg in singular or arg in repeatable:
            counts[arg] = counts.get(arg, 0) + 1
    duplicate = next((flag for flag in singular if counts.get(flag, 0) > 1), None)
    if duplicate is not None:
        raise ContractArgumentError(f"duplicate option: {duplicate}", "duplicate-option")
    help_count = sum(arg in {"-h", "--help"} for arg in option_argv)
    if help_count > 1:
        raise ContractArgumentError("duplicate option: --help", "duplicate-option")


def _build_parser() -> _ContractParser:
    parser = _ContractParser(
        prog="guidecheck verify",
        description="Verify a local assistant-guide.txt at local Levels 1-3; check Level 4 evidence consistency without awarding Level 4.",
        allow_abbrev=False,
        add_help=False,
    )
    parser.add_argument("path", type=Path, nargs="?", help="Path to assistant-guide.txt")
    parser.add_argument("-h", "--help", action="store_true", help="show this help message and exit")
    parser.add_argument("--manifest", type=Path, help="Optional local sidecar manifest path")
    parser.add_argument(
        "--anchor",
        action="append",
        type=_parse_contract_anchor_arg,
        default=[],
        metavar="CHANNEL=PATH",
        help="Optional local independent anchor evidence; repeatable",
    )
    parser.add_argument("--level", type=int, choices=range(0, 5), metavar="N")
    parser.add_argument("--fail-on-warning", action="store_true")
    parser.add_argument("--require-profile-version")
    parser.add_argument("--contract", required=True)
    parser.add_argument("--format", choices=["json", "text"])
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    return parser


def _parse_contract_anchor_arg(value: str) -> tuple[str, Path]:
    """Parse anchor syntax without turning a missing input into usage error."""
    if "=" not in value:
        raise argparse.ArgumentTypeError("anchor must use CHANNEL=PATH")
    channel, raw_path = value.split("=", 1)
    if channel not in ANCHOR_CHANNELS:
        choices = ", ".join(sorted(ANCHOR_CHANNELS))
        raise argparse.ArgumentTypeError(
            f"unknown anchor channel {channel!r}; expected one of {choices}"
        )
    return channel, Path(raw_path)


def _parse_contract_args(
    argv: list[str],
) -> argparse.Namespace:
    _validate_selector(argv)
    args = _build_parser().parse_args(argv)
    # --json already means JSON in the legacy CLI and is therefore a harmless
    # redundant assertion here.  Text and pretty output would change the
    # required one-line terminal record.
    if args.format == "text" or args.pretty:
        raise ContractArgumentError(
            "--format text and --pretty cannot be combined with --contract",
            "conflicting-output-option",
        )
    channels = [channel for channel, _path in args.anchor]
    if len(channels) != len(set(channels)):
        raise ContractArgumentError(
            "duplicate anchor channel",
            "duplicate-anchor-channel",
        )
    if args.path is None and not args.help:
        raise ContractArgumentError("the following arguments are required: path")
    return args


def _missing_input_result(label: str, path: Path, args: argparse.Namespace) -> dict[str, object]:
    return _error_result(
        f"{label} not found: {path}",
        error_id=f"{label}-input-missing",
        exit_code=EX_NOINPUT,
        requested_level=args.level,
        fail_on_warning=args.fail_on_warning,
    )


def _is_regular_file(path: Path) -> bool:
    return stat.S_ISREG(path.stat().st_mode)


def _classify_io_error(exc: OSError, args: argparse.Namespace) -> dict[str, object]:
    if isinstance(exc, PermissionError) or exc.errno in (errno.EACCES, errno.EPERM):
        exit_code = EX_NOPERM
        error_id = "input-permission-denied"
    elif isinstance(exc, FileNotFoundError) or exc.errno == errno.ENOENT:
        exit_code = EX_NOINPUT
        error_id = "input-missing"
    else:
        exit_code = EX_IOERR
        error_id = "input-io-failure"
    return _error_result(
        str(exc),
        error_id=error_id,
        exit_code=exit_code,
        requested_level=args.level,
        fail_on_warning=args.fail_on_warning,
    )


def run_contract(
    argv: list[str],
    *,
    evaluate_local_file: Callable[..., object],
    output_for: Callable[[object], dict[str, object]],
    profile_error_type: type[Exception],
    input_reader: Callable[[Path], bytes] | None = None,
) -> int:
    """Run one selected verifier contract invocation and emit one JSON object."""
    try:
        args = _parse_contract_args(argv)
    except ContractArgumentError as exc:
        return _emit(
            _error_result(
                str(exc),
                error_id=exc.error_id,
                exit_code=EX_USAGE,
            )
        )

    if args.help:
        _build_parser().print_help()
        return _emit(
            _complete_result(
                gate=_gate("not_requested"),
                report=None,
                legacy_exit_code=None,
                exit_code=0,
            )
        )

    try:
        try:
            guide_is_file = _is_regular_file(args.path)
        except FileNotFoundError:
            return _emit(_missing_input_result("guide", args.path, args))
        if not guide_is_file:
            return _emit(_missing_input_result("guide", args.path, args))
        if args.manifest is not None:
            try:
                manifest_is_file = _is_regular_file(args.manifest)
            except FileNotFoundError:
                return _emit(_missing_input_result("manifest", args.manifest, args))
            if not manifest_is_file:
                return _emit(_missing_input_result("manifest", args.manifest, args))
        for _channel, anchor_path in args.anchor:
            try:
                anchor_is_file = _is_regular_file(anchor_path)
            except FileNotFoundError:
                return _emit(_missing_input_result("anchor", anchor_path, args))
            if not anchor_is_file:
                return _emit(_missing_input_result("anchor", anchor_path, args))

        # An injected read boundary makes known permission and I/O classifications
        # testable without relying on the invoking account's filesystem mode.
        if input_reader is not None:
            input_reader(args.path)
        anchor_paths = dict(args.anchor)
        evaluation = evaluate_local_file(
            args.path,
            args.manifest,
            anchor_paths,
            required_profile_version=args.require_profile_version,
        )
        report = output_for(evaluation)
    except profile_error_type as exc:
        code = getattr(exc, "code", "invalid-profile-data")
        message = getattr(exc, "message", str(exc))
        return _emit(
            _error_result(
                f"{code}: {message}",
                error_id="invalid-profile-data",
                exit_code=EX_DATAERR,
                requested_level=args.level,
                fail_on_warning=args.fail_on_warning,
            )
        )
    except UnicodeError as exc:
        return _emit(
            _error_result(
                str(exc) or "input text is not valid Unicode",
                error_id="invalid-input-text",
                exit_code=EX_DATAERR,
                requested_level=args.level,
                fail_on_warning=args.fail_on_warning,
            )
        )
    except OSError as exc:
        return _emit(_classify_io_error(exc, args))
    except Exception as exc:  # Fail closed at the selected process boundary.
        return _emit(
            _error_result(
                str(exc) or exc.__class__.__name__,
                error_id="operational-failure",
                exit_code=1,
                requested_level=args.level,
                fail_on_warning=args.fail_on_warning,
            )
        )

    try:
        summary = report["summary"]
        guide = report["guide"]
        blocking = int(summary["blocking_findings"])  # type: ignore[index]
        warnings = int(summary["warnings"])  # type: ignore[index]
        achieved = int(guide["achieved_level"])  # type: ignore[index]
        warning_rejection = args.fail_on_warning and warnings > 0
        level_unmet = args.level is not None and achieved < args.level
        legacy_exit_code = 1 if blocking or warning_rejection or level_unmet else 0

        if blocking or warning_rejection:
            gate_status = "rejected"
            exit_code = 2
        elif args.level == 4 and level_unmet:
            gate_status = "inconclusive"
            exit_code = 3
        elif level_unmet:
            gate_status = "rejected"
            exit_code = 2
        else:
            gate_status = "accepted"
            exit_code = 0

        result = _complete_result(
            gate=_gate(
                gate_status,
                requested_level=args.level,
                fail_on_warning=args.fail_on_warning,
            ),
            report=report,
            legacy_exit_code=legacy_exit_code,
            exit_code=exit_code,
        )
    except Exception as exc:  # Report conversion remains inside the process boundary.
        result = _error_result(
            str(exc) or exc.__class__.__name__,
            error_id="operational-failure",
            exit_code=1,
            requested_level=args.level,
            fail_on_warning=args.fail_on_warning,
        )
    return _emit(result)
