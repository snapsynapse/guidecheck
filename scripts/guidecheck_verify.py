#!/usr/bin/env python3
"""Version-aware entry point; legacy content helpers remain API-compatible."""
from guidecheck_legacy import *  # Re-export the established helper API.
import guidecheck_legacy as legacy
import guidecheck_strict as strict
import guidecheck_corrected as corrected
from guidecheck_profiles import ProfileError, select_profile, check_legacy_manifest
from guidecheck_constants import LATEST_RELEASED_PROFILE_VERSION


def evaluate_guide(data, manifest_text=None, anchor_texts=None, anchor_paths=None,
                   now=None, evidence_fetched=False, *, selection=None,
                   required_profile_version=None):
    selected_from_bytes = select_profile(data, required_profile_version)
    if selection is not None and selection != selected_from_bytes:
        raise ProfileError("profile-version-ambiguous", "caller selection does not match the guide-byte selector")
    selection = selected_from_bytes
    check_legacy_manifest(selection, manifest_text)
    engine = corrected if selection.corrected else strict if selection.strict else legacy
    return engine.evaluate_guide(data, manifest_text, anchor_texts, anchor_paths, now, evidence_fetched)


@dataclass
class DraftEvaluation:
    """A local evaluation under draft profile 3.0.0. `output_for` renders it in that profile's schema."""

    path: Path
    data: bytes
    profile_selection: object
    result: object


def evaluate_local_file(
    path: Path,
    manifest_path: Path | None = None,
    anchor_paths: dict[str, Path] | None = None,
    now: datetime | None = None,
    *, required_profile_version=None, allow_draft=False,
) -> Evaluation:
    data = path.read_bytes()
    manifest_text = manifest_path.read_text(encoding="utf-8") if manifest_path else None
    anchor_paths = anchor_paths or {}
    anchor_texts = {channel: anchor_path.read_text(encoding="utf-8") for channel, anchor_path in anchor_paths.items()}
    selection = select_profile(data, required_profile_version, allow_draft=allow_draft)
    evaluated_at = now or datetime.now(timezone.utc)
    if selection.restricted:
        # Only a caller that passed allow_draft reaches this branch.
        import guidecheck_restricted as restricted

        result = restricted.evaluate(data, manifest_text=manifest_text, anchor_texts=anchor_texts, now=evaluated_at)
        return DraftEvaluation(path, data, selection, result)
    findings, achieved, level5_ready, manifest_evidence, cross_channel_anchors = evaluate_guide(
        data,
        manifest_text,
        anchor_texts,
        anchor_paths,
        evaluated_at,
        selection=selection,
    )
    evaluation = Evaluation(
        path,
        data,
        manifest_path,
        manifest_text,
        anchor_paths,
        anchor_texts,
        evaluated_at,
        findings,
        achieved,
        level5_ready,
        manifest_evidence,
        cross_channel_anchors,
    )

    evaluation.profile_selection = selection
    return evaluation


def output_for(evaluation, *, required_level=None):
    if isinstance(evaluation, DraftEvaluation):
        import guidecheck_restricted as restricted
        from guidecheck_constants import GUIDECHECK_VERSION, LOCAL_VERIFIER_NAME

        return restricted.build_report(evaluation.result, verifier_name=LOCAL_VERIFIER_NAME,
                                       verifier_version=GUIDECHECK_VERSION, path=evaluation.path,
                                       required_level=required_level)
    result = legacy.output_for(evaluation)
    selection = getattr(evaluation, "profile_selection", None)
    if selection is None:
        # Preserve callers that construct the established Evaluation dataclass.
        selection = select_profile(evaluation.data)
    if selection.corrected:
        return corrected.decorate_report(result, selection)
    return strict.decorate_report(result, selection) if selection.strict else result


def caller_notes(selection, *, required_profile_version, requested_level, fail_on_warning,
                 achieved, blocking, warnings) -> list[str]:
    """Explain what the exit status does and does not mean for this run.

    The report and the exit status are a released contract and are not changed
    here. These notes go to stderr only. They cover the cases where a reader
    of the exit status, or of the report's last line, would assume more was
    checked or required than actually was: the party who wrote the guide chose
    the evaluator, or no level was required, or the exit status reflects a
    gate that the report's own summary line does not.
    """
    notes: list[str] = []
    if required_profile_version is None and selection.policy_version != LATEST_RELEASED_PROFILE_VERSION:
        declared = selection.declared_version or "no profile version"
        notes.append(
            f"evaluated under the {selection.policy_version} policy because the guide declares {declared}. "
            f"The guide's author makes that choice, and the checks added by profile "
            f"{LATEST_RELEASED_PROFILE_VERSION} did not run. Pass --require-profile-version "
            f"{LATEST_RELEASED_PROFILE_VERSION} to refuse guides that do not declare it."
        )
    if blocking:
        return notes
    if requested_level is None and achieved < 3:
        notes.append(
            f"exit status 0 at achieved Level {achieved}: no blocking finding was raised and no level "
            f"was required. Required sections and action blocks are checked only when a guide "
            f"qualifies for Level 3 evaluation. Pass --level 3 to require them."
        )
    elif requested_level is not None and achieved < requested_level:
        notes.append(
            f"exit status 1: achieved Level {achieved} is below the requested Level {requested_level}. "
            f"The report's 'Proceed?' line counts blocking findings only and does not reflect --level."
        )
    elif fail_on_warning and warnings:
        notes.append(
            f"exit status 1: --fail-on-warning with {warnings} warning(s). The report's 'Proceed?' "
            f"line counts blocking findings only and does not reflect --fail-on-warning."
        )
    return notes


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify a local assistant-guide.txt at GuideCheck Levels 1 through 3. Level 4 evidence is checked for consistency only; Level 4 is never awarded locally.")
    parser.add_argument("path", type=Path, help="Path to assistant-guide.txt")
    parser.add_argument("--manifest", type=Path, help="Optional local sidecar manifest path")
    parser.add_argument(
        "--anchor",
        action="append",
        type=parse_anchor_arg,
        default=[],
        metavar="CHANNEL=PATH",
        help="Optional local independent anchor evidence; repeatable. Channels: dns-txt, package-registry, repository-file, signed-security-txt, transparency-log",
    )
    parser.add_argument("--format", choices=["json", "text"], default="json", help="Output format")
    parser.add_argument("--json", action="store_const", const="json", dest="format", help="Emit JSON output")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    parser.add_argument("--level", type=int, choices=range(0, 5), metavar="N", help="Require at least this achieved level")
    parser.add_argument("--fail-on-warning", action="store_true", help="Exit nonzero when warnings are present")
    parser.add_argument("--require-profile-version", help="Require a supported guide profile version; never reinterpret guide bytes")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    raw_argv = argv or sys.argv[1:]
    from guidecheck_cli_contract import has_contract_selector, run_contract

    if has_contract_selector(raw_argv):
        return run_contract(
            raw_argv,
            evaluate_local_file=evaluate_local_file,
            output_for=output_for,
            profile_error_type=ProfileError,
        )

    args = parse_args(raw_argv)
    if not args.path.is_file():
        print(f"guidecheck_verify: guide not found: {args.path}", file=sys.stderr)
        return 2
    if args.manifest and not args.manifest.is_file():
        print(f"guidecheck_verify: manifest not found: {args.manifest}", file=sys.stderr)
        return 2

    anchor_paths = dict(args.anchor)
    try:
        evaluation = evaluate_local_file(args.path, args.manifest, anchor_paths,
                                         required_profile_version=args.require_profile_version, allow_draft=True)
    except ProfileError as exc:
        print(f"guidecheck_verify: {exc.code}: {exc.message}", file=sys.stderr)
        return 2
    draft = isinstance(evaluation, DraftEvaluation)
    result = output_for(evaluation, required_level=args.level) if draft else output_for(evaluation)
    if args.format == "text":
        print(result["compact_report"])
    else:
        indent = 2 if args.pretty else None
        print(json.dumps(result, indent=indent, sort_keys=bool(indent)))

    blocking = result["summary"]["blocking_findings"]  # type: ignore[index]
    warnings = result["summary"]["warnings"]  # type: ignore[index]
    achieved = result["guide"]["achieved_level"]  # type: ignore[index]
    if draft:
        # Draft profile 3.0.0: the exit status follows the verdict, which
        # already accounts for blocking findings, Level 3 and --level.
        print("guidecheck_verify: note: evaluated under draft profile 3.0.0 (restricted-argv-1), which is "
              "unreleased. The result is not a released conformance claim.", file=sys.stderr)
        proceed = result["verdict"]["proceed"]  # type: ignore[index]
        if proceed and args.fail_on_warning and warnings:
            print(f"guidecheck_verify: note: exit status 1: --fail-on-warning with {warnings} warning(s). "
                  "The verdict does not reflect --fail-on-warning.", file=sys.stderr)
            return 1
        return 0 if proceed else 1
    for note in caller_notes(
        evaluation.profile_selection,
        required_profile_version=args.require_profile_version,
        requested_level=args.level,
        fail_on_warning=args.fail_on_warning,
        achieved=achieved,
        blocking=blocking,
        warnings=warnings,
    ):
        print(f"guidecheck_verify: note: {note}", file=sys.stderr)
    if blocking:
        return 1
    if args.level is not None and achieved < args.level:
        return 1
    if args.fail_on_warning and warnings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
