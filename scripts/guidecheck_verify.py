#!/usr/bin/env python3
"""Version-aware entry point; legacy content helpers remain API-compatible."""
from guidecheck_legacy import *  # Re-export the established helper API.
import guidecheck_legacy as legacy
import guidecheck_strict as strict
import guidecheck_corrected as corrected
from guidecheck_profiles import ProfileError, select_profile, check_legacy_manifest


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


def evaluate_local_file(
    path: Path,
    manifest_path: Path | None = None,
    anchor_paths: dict[str, Path] | None = None,
    now: datetime | None = None,
    *, required_profile_version=None,
) -> Evaluation:
    data = path.read_bytes()
    manifest_text = manifest_path.read_text(encoding="utf-8") if manifest_path else None
    anchor_paths = anchor_paths or {}
    anchor_texts = {channel: anchor_path.read_text(encoding="utf-8") for channel, anchor_path in anchor_paths.items()}
    selection = select_profile(data, required_profile_version)
    evaluated_at = now or datetime.now(timezone.utc)
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


def output_for(evaluation):
    result = legacy.output_for(evaluation)
    selection = getattr(evaluation, "profile_selection", None)
    if selection is None:
        # Preserve callers that construct the established Evaluation dataclass.
        selection = select_profile(evaluation.data)
    if selection.corrected:
        return corrected.decorate_report(result, selection)
    return strict.decorate_report(result, selection) if selection.strict else result


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify a local assistant-guide.txt through GuideCheck Level 4.")
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
    args = parse_args(argv or sys.argv[1:])
    if not args.path.is_file():
        print(f"guidecheck_verify: guide not found: {args.path}", file=sys.stderr)
        return 2
    if args.manifest and not args.manifest.is_file():
        print(f"guidecheck_verify: manifest not found: {args.manifest}", file=sys.stderr)
        return 2

    anchor_paths = dict(args.anchor)
    try:
        evaluation = evaluate_local_file(args.path, args.manifest, anchor_paths, required_profile_version=args.require_profile_version)
    except ProfileError as exc:
        print(f"guidecheck_verify: {exc.code}: {exc.message}", file=sys.stderr)
        return 2
    result = output_for(evaluation)
    if args.format == "text":
        print(result["compact_report"])
    else:
        indent = 2 if args.pretty else None
        print(json.dumps(result, indent=indent, sort_keys=bool(indent)))

    blocking = result["summary"]["blocking_findings"]  # type: ignore[index]
    warnings = result["summary"]["warnings"]  # type: ignore[index]
    achieved = result["guide"]["achieved_level"]  # type: ignore[index]
    if blocking:
        return 1
    if args.level is not None and achieved < args.level:
        return 1
    if args.fail_on_warning and warnings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
