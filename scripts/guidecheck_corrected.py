"""Opt-in 2.0.0 content policy with strict 1.0.0 anchor qualification."""
from datetime import datetime, timezone
import hashlib
import re
import shlex

import guidecheck_legacy as legacy
from guidecheck_constants import GUIDECHECK_VERSION
from guidecheck_profiles import PROFILE_NAME, ProfileError, policy_key
from guidecheck_strict import AnchorEvidence


PROFILE_VERSION = "2.0.0"
CONTENT_POLICY = "corrected-content-1"
ANCHOR_POLICY = "1.0.0-strict"

_NEGATION = re.compile(
    r"\b(?:do ?not|don'?t|never|must ?not|mustn'?t|should ?not|shouldn'?t|"
    r"cannot|can'?t|will ?not|won'?t|is\s+not\s+permission\s+to)\b",
    re.IGNORECASE,
)
_COORDINATED_ITEM = re.compile(
    r"(?:broaden|expand)\s+(?:tool\s+)?(?:access|permissions)|"
    r"broaden\s+network\s+access|substitute\s+commands|widen\s+paths|skip\s+approval\s+gates|"
    r"fetch|follow(?:\s+another\s+.*\s+guide)?|decode(?:\s+and\s+execute)?|"
    r"disable\s+sandboxing|persist\s+.*(?:memory|guide)",
    re.IGNORECASE,
)
_GOVERNANCE_BREAK = re.compile(
    r"\b(?:but|however|then|you|we|they|if|when|unless|after|before)\b",
    re.IGNORECASE,
)
_STRUCTURED_LINE = re.compile(
    r"^\s*(?:\[/?[a-z0-9-]+\]|[a-z][a-z0-9-]*:|[-*+]\s+|\d+[.)]\s+)",
    re.IGNORECASE,
)


def _heading_line(line: str) -> bool:
    stripped = line.strip()
    return (
        0 < len(stripped) <= 80
        and len(stripped.split()) <= 8
        and stripped.istitle()
        and not re.search(r"[.!?;:]$", stripped)
    )


def _prose_units(text: str):
    """Yield sentence-bounded prose units while preserving ordinary wraps."""
    pending = []

    def flush():
        if pending:
            lines = [part.strip() for part in pending]
            pending.clear()
            paragraph = "\n".join(lines)
            return [
                unit
                for unit in re.split(r"(?<=[.!?;])(?:\s+|$)", paragraph)
                if unit
            ]
        return []

    for line in text.splitlines():
        if not line.strip():
            yield from flush()
            continue
        if _STRUCTURED_LINE.match(line) or _heading_line(line):
            yield from flush()
            yield line.strip()
            continue
        pending.append(line)
    yield from flush()


def _negation_governs(unit: str, match_start: int, match_end: int) -> bool:
    prefix = unit[:match_start]
    matches = list(_NEGATION.finditer(prefix))
    if not matches:
        return False
    raw_tail = prefix[matches[-1].end():]
    if raw_tail.count("\n") > 1:
        return False
    tail = raw_tail.strip()
    if tail in {"", ":"}:
        return True
    if ":" in tail or _GOVERNANCE_BREAK.search(tail):
        return False
    delimiter = re.search(r"(?P<delimiter>,|\b(?:and|or))\s*$", tail, re.IGNORECASE)
    if delimiter is None:
        return False
    coordinated = tail[:delimiter.start()].strip().rstrip(",")
    if not coordinated:
        return False
    parts = [part.strip() for part in re.split(r"\s*(?:,|\band\b|\bor\b)\s*", coordinated) if part.strip()]
    if not parts or not all(_COORDINATED_ITEM.fullmatch(part) for part in parts):
        return False
    if delimiter.group("delimiter") != ",":
        return True
    suffix = re.split(r"[;:.!?]", unit[match_end:], maxsplit=1)[0]
    return bool(re.search(r"(?:,|\s)\s*(?:and|or)\b", suffix, re.IGNORECASE))


def _flagged_occurrences(unit: str, pattern: str):
    for match in re.finditer(pattern, unit, re.IGNORECASE | re.DOTALL):
        if not _negation_governs(unit, match.start(), match.end()):
            yield match


def check_disallowed(text: str, findings: list[legacy.Finding]) -> None:
    lowered = text.lower()
    if re.search(r"</?(html|script|style|iframe|img|link|meta)\b", lowered):
        legacy.add_finding(findings, "construct.html", "error", "HTML-like construct present")
    if re.search(r"!\[[^\]]*\]\([^)]+\)", text):
        legacy.add_finding(findings, "construct.markdown-image", "error", "Markdown image construct present")
    if "data:" in lowered:
        legacy.add_finding(findings, "construct.data-url", "error", "data URL present")
    javascript_scan = legacy._CLI_EVAL_EXPECTATION.sub("", lowered)
    if re.search(r"\bjavascript\s*:", lowered) or legacy._JAVASCRIPT_EVAL.search(javascript_scan):
        legacy.add_finding(findings, "construct.javascript", "error", "JavaScript construct present")
    encoded_execution = (
        r"\b(?:base64|encoded|obfuscated|decode|deobfuscate)\b.{0,40}?\b(?:execute|run|eval)\b|"
        r"\b(?:execute|run|eval)\b.{0,40}?\b(?:base64|encoded|obfuscated)\b"
    )
    for unit in _prose_units(text):
        if next(_flagged_occurrences(unit, encoded_execution), None):
            legacy.add_finding(findings, "prohibited.encoded-execution", "error", "decode and execute instruction")
            break


def check_prohibited(text: str, findings: list[legacy.Finding]) -> None:
    patterns = [
        ("prohibited.chained-guide", r"fetch\s+and\s+follow|follow\s+another\s+.{0,40}?(?:guide|script|instruction\s+file|runbook)|continue\s+with\s+.{0,40}?\.txt|pivot\s+(?:the\s+)?(?:current\s+)?session\s+to\s+(?:a\s+)?(?:different|another)\s+guide"),
        ("prohibited.next-guide-field", r"^(?:next-guide|then-fetch|chain-to|follow-next|continue-with):"),
        ("prohibited.rewrite-guide", r"modify.*?assistant-guide\.txt|replace.*?assistant-guide\.txt"),
        ("prohibited.memory", r"long-term assistant memory"),
        ("prohibited.skip-approval", r"skip approval gates|disable sandboxing|expand tool permissions"),
        ("prohibited.notes-as-command", r"treat .*?notes.*? as commands"),
    ]
    seen = set()
    for unit in _prose_units(text):
        for finding_id, pattern in patterns:
            if finding_id not in seen and next(_flagged_occurrences(unit, pattern), None):
                legacy.add_finding(findings, finding_id, "error", finding_id)
                seen.add(finding_id)


def _tokens(command: str):
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|\n")
        lexer.whitespace = " \t\r"
        lexer.whitespace_split = True
        lexer.commenters = ""
        segments = [[]]
        for token in lexer:
            if token and all(char in ";&|\n" for char in token):
                segments.append([])
            else:
                segments[-1].append(token)
        return [segment for segment in segments if segment]
    except ValueError:
        return None


def _strip_prefixes(tokens):
    tokens = list(tokens)
    while tokens:
        if re.fullmatch(r"[A-Za-z_]\w*=.*", tokens[0]):
            tokens = tokens[1:]
            continue
        if tokens[0] == "env":
            tokens = tokens[1:]
            while tokens:
                if tokens[0] == "--":
                    tokens = tokens[1:]
                    break
                if tokens[0] in {"-i", "--ignore-environment"} or tokens[0].startswith(("--unset=", "--chdir=")):
                    tokens = tokens[1:]
                    continue
                if tokens[0] in {"-u", "--unset", "-C", "--chdir"}:
                    if len(tokens) < 2:
                        return None
                    tokens = tokens[2:]
                    continue
                if re.fullmatch(r"[A-Za-z_]\w*=.*", tokens[0]):
                    tokens = tokens[1:]
                    continue
                if tokens[0].startswith("-"):
                    return None
                break
            continue
        if tokens[0] in {"sudo", "doas"}:
            tokens = tokens[1:]
            while tokens and tokens[0].startswith("-"):
                if tokens[0] == "--":
                    tokens = tokens[1:]
                    break
                if tokens[0] in {"-u", "--user", "-g", "--group", "-C", "--chdir"}:
                    if len(tokens) < 2:
                        return None
                    tokens = tokens[2:]
                    continue
                if tokens[0] in {"-n", "--non-interactive", "-E", "--preserve-env"}:
                    tokens = tokens[1:]
                    continue
                return None
            continue
        if tokens[0] in {"command", "exec", "nohup", "time", "nice"}:
            tokens = tokens[1:]
            if tokens and tokens[0] == "--":
                tokens = tokens[1:]
            elif tokens and tokens[0].startswith("-"):
                return None
            continue
        break
    return tokens


def _local_arg(value: str) -> bool:
    return value in {".", ".."} or value.startswith(("./", "../", "/", "file:"))


def _classify_tokens(tokens) -> str:
    tokens = _strip_prefixes(tokens)
    if tokens is None:
        return "ambiguous"
    if not tokens:
        return "none"
    raw, *args = tokens
    head = re.sub(r"[0-9][0-9.]*$", "", raw.rsplit("/", 1)[-1].lower())
    if head == "npx":
        return "ambiguous"
    if head == "npm":
        separator = args.index("--") if "--" in args else len(args)
        control_args = args[:separator]
        remaining = []
        global_install = False
        index = 0
        while index < len(control_args):
            arg = control_args[index]
            if arg in {"-g", "--global"}:
                global_install = True
                index += 1
                continue
            if arg == "--prefix":
                if index + 1 >= len(control_args):
                    return "ambiguous"
                index += 2
                continue
            if arg.startswith("--prefix=") and len(arg) > len("--prefix="):
                index += 1
                continue
            if arg in {"--version", "-v", "--help", "-h"}:
                remaining.append(arg)
                index += 1
                continue
            if arg.startswith("-"):
                return "ambiguous"
            remaining.append(arg)
            index += 1
        if remaining in (["--version"], ["-v"], ["--help"], ["-h"]) or (remaining and remaining[0] == "help"):
            return "none"
        if global_install and (not remaining or remaining[0] not in {"install", "ci"}):
            return "ambiguous"
        if remaining and remaining[0] in {"install", "ci"}:
            return legacy._classify_exec_tokens(["npm", *remaining])
        if remaining and remaining[0] == "exec":
            return "ambiguous"
        if remaining and remaining[0] == "test":
            return "bound-script"
        if remaining and remaining[0] == "run":
            return "bound-script" if len(remaining) > 1 else "none"
        return legacy._classify_exec_tokens(tokens)
    if head == "make":
        index = 0
        query = False
        targets = False
        while index < len(args):
            arg = args[index]
            if arg in {"-C", "--directory", "-f", "--file", "--makefile"}:
                if index + 1 >= len(args):
                    return "ambiguous"
                index += 2
                continue
            if arg.startswith(("--directory=", "--file=", "--makefile=")):
                index += 1
                continue
            if arg in {"--version", "--help", "-h"}:
                query = True
                index += 1
                continue
            if arg in {"-s", "--silent", "-n", "--dry-run", "-B", "--always-make"}:
                index += 1
                continue
            if not arg.startswith("-"):
                targets = True
                index += 1
                continue
            return "ambiguous"
        if query and not targets:
            return "none"
        return "bound-script"
    if head == "just":
        query = {"--version", "--help", "-h", "--list", "-l", "--summary"}
        index = 0
        recipe = False
        configured_dispatch = False
        query_only = False
        while index < len(args):
            arg = args[index]
            if arg in {"--justfile", "-f", "--working-directory", "-d"}:
                if index + 1 >= len(args):
                    return "ambiguous"
                configured_dispatch = True
                index += 2
                continue
            if arg.startswith(("--justfile=", "--working-directory=")):
                configured_dispatch = True
                index += 1
                continue
            if arg in query:
                query_only = True
                index += 1
                continue
            if arg.startswith("-"):
                return "ambiguous"
            recipe = True
            index += 1
        if query_only and not recipe:
            return "none"
        return "bound-script" if recipe or configured_dispatch or not args else "none"
    if head == "pip" and args in (["--version"], ["-V"], ["--help"], ["-h"]):
        return "none"
    if head == "pip" and args and args[0] == "install":
        if args[1:] in (["--help"], ["-h"]):
            return "none"
        install_args = args[1:]
        value_options = {
            "--abi", "--cache-dir", "--cert", "--client-cert", "--config-settings", "-C",
            "--extra-index-url", "--find-links", "-f", "--global-option", "--implementation",
            "--index-url", "-i", "--install-option", "--platform", "--prefix", "--proxy",
            "--python-version", "--report", "--retries", "--root", "--src", "--target", "-t",
            "--timeout", "--trusted-host", "--upgrade-strategy", "--only-binary", "--no-binary",
        }
        flag_options = {
            "--break-system-packages", "--compile", "--dry-run", "--force-reinstall",
            "--ignore-installed", "-I", "--ignore-requires-python", "--no-build-isolation",
            "--no-clean", "--no-compile", "--no-deps", "--no-index", "--no-warn-conflicts",
            "--no-warn-script-location", "--pre", "--prefer-binary", "--quiet",
            "-q", "--require-hashes", "--use-pep517", "--upgrade", "-U", "--user", "--verbose", "-v",
        }
        sources = []
        editable_targets = []
        has_requirements = False
        index = 0
        while index < len(install_args):
            arg = install_args[index]
            if arg == "--":
                sources.extend(install_args[index + 1:])
                break
            if arg in {"-e", "--editable"}:
                if index + 1 >= len(install_args):
                    return "ambiguous"
                editable_targets.append(install_args[index + 1])
                index += 2
                continue
            if arg.startswith("--editable="):
                editable_targets.append(arg.split("=", 1)[1])
                index += 1
                continue
            if arg.startswith("-e") and arg != "-e":
                editable_targets.append(arg[2:])
                index += 1
                continue
            if arg in {"-r", "--requirement"}:
                if index + 1 >= len(install_args):
                    return "ambiguous"
                has_requirements = True
                index += 2
                continue
            if arg.startswith("--requirement=") or (arg.startswith("-r") and arg != "-r"):
                has_requirements = True
                index += 1
                continue
            if arg in value_options:
                if index + 1 >= len(install_args):
                    return "ambiguous"
                index += 2
                continue
            if any(arg.startswith(option + "=") for option in value_options if option.startswith("--")):
                index += 1
                continue
            if arg in flag_options:
                index += 1
                continue
            if arg.startswith("-"):
                return "ambiguous"
            sources.append(arg)
            index += 1
        if any(not _local_arg(arg) for arg in editable_targets):
            return "ambiguous"
        if any(_local_arg(arg) for arg in sources + editable_targets):
            return "bound-script"
        if has_requirements or sources:
            return "exempt-installer"
        return "ambiguous"
    if head == "go":
        if args in (["version"], ["help"], ["help", "generate"]):
            return "none"
        if args and args[0] == "generate":
            return "none" if args[1:] in (["--help"], ["-h"]) else "bound-script"
    if head == "docker":
        if args in (["--help"], ["-h"], ["help"]):
            return "none"
        if not args or args[0] != "build":
            return "ambiguous" if args and args[0] == "buildx" else legacy._classify_exec_tokens(tokens)
        build_args = args[1:]
        index = 0
        file_value = None
        context = None
        query = False
        while index < len(build_args):
            arg = build_args[index]
            if arg in {"--help", "-h"}:
                query = True
                index += 1
                continue
            if arg in {"--file", "-f"}:
                if index + 1 >= len(build_args):
                    return "ambiguous"
                file_value = build_args[index + 1]
                index += 2
                continue
            if arg.startswith("--file="):
                file_value = arg.split("=", 1)[1]
                index += 1
                continue
            if arg.startswith("-") or context is not None:
                return "ambiguous"
            context = arg
            index += 1
        if query and context is None:
            return "none"
        local_file = file_value is None or bool(file_value and file_value != "-" and not re.match(r"^(?:[a-z]+:|//)", file_value, re.IGNORECASE))
        local_context = bool(context and _local_arg(context))
        return "bound-script" if local_file and local_context else "ambiguous"
    return legacy._classify_exec_tokens(tokens)


def classify_exec_target(command: str) -> str:
    segments = _tokens(command)
    if segments is None:
        return "ambiguous"
    kinds = [_classify_tokens(segment) for segment in segments]
    return next((kind for kind in ("ambiguous", "bound-script", "exempt-installer", "inline") if kind in kinds), "none")


def check_bounded_execution(action: dict[str, str], findings: list[legacy.Finding]) -> None:
    kind = classify_exec_target(action.get("command", ""))
    pin = action.get("exec-sha256", "")
    opaque = "exec-opaque" in action
    evidence = action.get("id", "")
    valid_pin = bool(re.fullmatch(r"[0-9a-f]{64}", pin))
    if kind == "bound-script" and (opaque or not valid_pin):
        legacy.add_finding(findings, "action.exec-unbounded", "error", "named or dispatched repository execution requires a valid exec-sha256 or replacement with inline actions; exec-opaque cannot exempt it", evidence=evidence)
    if kind == "ambiguous":
        legacy.add_finding(findings, "action.exec-target-unresolved", "error", "effective execution target ownership is unresolved; a declared hash cannot identify it", evidence=evidence)
    if opaque and kind == "exempt-installer" and action["exec-opaque"] == "acknowledged" and action.get("notes"):
        legacy.add_finding(findings, "action.exec-opaque", "warning", "external dependency execution is acknowledged and not self-contained", evidence=evidence)
    if opaque and kind in {"inline", "none", "ambiguous"}:
        legacy.add_finding(findings, "action-block.malformed", "error", "exec-opaque is only permitted for established exempt dependency commands", evidence=evidence)
    if valid_pin:
        legacy.add_finding(findings, "exec-sha256.unverified", "info", "artifact bytes were not read; exec-sha256 is declared, not verified", evidence=evidence)


def check_actions(actions: list[dict[str, str]], findings: list[legacy.Finding]) -> None:
    required_approvals = 0
    for action in actions:
        classes = legacy.action_classes(action)
        if action.get("approval") == "required":
            required_approvals += 1
        if not classes or not classes <= legacy.ALLOWED_CLASSES:
            legacy.add_finding(findings, "action-block.class.invalid", "error", f"invalid class list: {action.get('class', '')}")
        if "normal" in classes and len(classes) > 1:
            legacy.add_finding(findings, "action-block.class.normal-mixed", "error", "normal class is mutually exclusive")
        if classes & legacy.APPROVAL_REQUIRED_CLASSES and action.get("approval") != "required":
            legacy.add_finding(findings, "approval.required-missing", "error", "sensitive action lacks required approval", evidence=action.get("id", ""))
        if "networked" in classes and "egress" not in action:
            legacy.add_finding(findings, "egress.missing", "error", "networked action lacks egress", evidence=action.get("id", ""))
        if "egress" in action and re.search(r"(^|,\s*)\*", action["egress"]):
            legacy.add_finding(findings, "egress.wildcard-too-broad", "error", "egress wildcard is too broad")
        command = action.get("command", "")
        executes_code = legacy.command_executes_code(command)
        is_networked = legacy.command_is_networked(command)
        if "code-executing" not in classes and executes_code:
            legacy.add_finding(findings, "action-block.class.code-executing-missing", "warning", "command likely executes code", evidence=action.get("id", ""))
        if "networked" not in classes and is_networked:
            legacy.add_finding(findings, "network.command-implies-networked", "warning", "command performs network access but class omits networked", evidence=action.get("id", ""))
        if action.get("approval") != "required" and not (classes & legacy.APPROVAL_REQUIRED_CLASSES) and (is_networked or executes_code):
            legacy.add_finding(findings, "approval.command-implies-required", "warning", "command implies a sensitive action but approval is not required", evidence=action.get("id", ""))
        if action.get("runner") == "shell" and not action.get("notes"):
            legacy.add_finding(findings, "runner.shell.missing-rationale", "warning", "shell runner lacks notes rationale", evidence=action.get("id", ""))
        check_bounded_execution(action, findings)
        legacy.check_command(action, classes, findings)
    if required_approvals > legacy.DEFAULT_APPROVAL_WARNING_THRESHOLD:
        legacy.add_finding(findings, "approval.required.too-many", "warning", "guide contains many required approvals")


def _evaluate_content(data, manifest_text, now):
    findings = []
    text = legacy.decode_text(data)
    legacy.check_byte_profile(data, findings)
    check_disallowed(text, findings)
    has_l1_instruction = legacy.check_verification_instruction(text, findings)
    has_metadata = bool(re.search(r"\[assistant-guide-metadata\]", text, re.IGNORECASE))
    metadata = legacy.parse_metadata(text, findings, now.date()) if has_metadata else {}
    has_repo = "repository-url" in metadata or re.search(r"Repository:\s*https://", text)
    has_canonical = "canonical-url" in metadata or re.search(r"Canonical URL:\s*https://", text)
    has_scope = "Task scope" in text
    actions = legacy.parse_actions(text, findings)
    if has_metadata and (actions or "Assistant invocation prompt" in text):
        legacy.check_sections(text, findings)
        check_actions(actions, findings)
    check_prohibited(text, findings)
    manifest = legacy.check_manifest(data, manifest_text, findings)
    error_ids = {finding.id for finding in findings if finding.severity == "error"}
    achieved = 1 if has_l1_instruction and has_repo and has_canonical and has_scope else 0
    byte_blockers = {finding_id for finding_id in error_ids if finding_id.startswith(("byte-profile.", "construct."))}
    if achieved >= 1 and not byte_blockers:
        achieved = 2
    level4_blockers = {finding_id for finding_id in error_ids if finding_id.startswith(("manifest.", "anchor."))}
    level3_blockers = error_ids - byte_blockers - {"verification-instruction.missing"} - level4_blockers
    if achieved >= 2 and has_metadata and actions and not level3_blockers:
        achieved = 3
    if "metadata.status.revoked" in error_ids:
        achieved = min(achieved, 1)
    return findings, achieved, manifest, metadata, actions


def manifest_profile_matches(text):
    fields = {"profile": [], "profile-version": []}
    for line in text.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            if key.strip().lower() in fields:
                fields[key.strip().lower()].append(value.strip())
    if fields["profile"] != [PROFILE_NAME] or len(fields["profile-version"]) != 1:
        return False
    try:
        return policy_key(fields["profile-version"][0]) == PROFILE_VERSION
    except ProfileError:
        return False


def evaluate_guide(data, manifest_text=None, anchor_texts=None, anchor_paths=None,
                   now=None, evidence_fetched=False):
    now = now or datetime.now(timezone.utc)
    findings, achieved, manifest, metadata, actions = _evaluate_content(data, manifest_text, now)
    claimed = bool(metadata.get("manifest-url"))
    if manifest is not None and not manifest_profile_matches(manifest_text):
        manifest.valid = False
        legacy.add_finding(findings, "manifest.profile-version.mismatch", "error", "manifest must declare exactly one matching profile name and version")
    anchors = []
    for channel, text in sorted((anchor_texts or {}).items()):
        if channel not in legacy.ANCHOR_CHANNELS:
            legacy.add_finding(findings, "anchor.channel.unsupported", "warning", "unsupported anchor channel cannot qualify", evidence=channel)
            continue
        observed = legacy.extract_anchor_sha256(channel, text)
        expected = manifest.guide_sha256 if manifest is not None else None
        status = "absent" if observed is None else ("present-matches" if observed == expected else "present-mismatch")
        if status == "absent":
            reason = "absent"
        elif status == "present-mismatch":
            reason = "hash-mismatch"
        elif not evidence_fetched:
            reason = "local-evidence-not-fetched"
        elif channel == "repository-file":
            reason = "repository-independence-unestablished"
        else:
            reason = "qualifying-channel"
        anchors.append(AnchorEvidence(
            channel=channel, status=status, observed_sha256=observed,
            evidence_path=str(anchor_paths[channel]) if anchor_paths and channel in anchor_paths else None,
            qualifies_for_level4=reason == "qualifying-channel", qualification_reason=reason,
        ))
        if channel == "repository-file" and observed is not None:
            legacy.add_finding(findings, "anchor.repository-file.independence-unestablished", "warning", "repository hash evidence does not establish independent provenance and cannot qualify for Level 4")
        if status == "present-mismatch":
            finding_id = "anchor.repository-file.mismatch" if channel == "repository-file" else "anchor.independent.mismatch"
            legacy.add_finding(findings, finding_id, "error", "anchor hash does not match manifest guide-sha256", evidence=channel)
        anchor_url = legacy.extract_anchor_url(channel, text)
        if metadata.get("canonical-url") and anchor_url and anchor_url != metadata["canonical-url"]:
            legacy.add_finding(findings, "anchor.registry.url-mismatch", "warning", "package-registry assistant-guide URL does not match canonical-url", evidence=anchor_url)
    qualifying = any(anchor.qualifies_for_level4 for anchor in anchors)
    mismatches = any(anchor.status == "present-mismatch" for anchor in anchors)
    if claimed and not qualifying and not mismatches:
        legacy.add_finding(findings, "anchor.independent.missing", "error", "no fetched qualifying independent anchor is available for Level 4")
    if not evidence_fetched and any(anchor.status == "present-matches" for anchor in anchors):
        legacy.add_finding(findings, "level4.requires-fetch", "info", "local evidence was checked for consistency only; Level 4 requires fetched qualifying evidence")
    anchor_blockers = any(finding.severity == "error" and finding.id.startswith(("anchor.", "manifest.")) for finding in findings)
    if achieved >= 3 and claimed and manifest is not None and manifest.valid and qualifying and not anchor_blockers:
        achieved = 4
    else:
        achieved = min(achieved, 3)
    ready = legacy.check_level5_readiness(actions, findings) if achieved >= 4 else False
    return findings, achieved, ready, manifest, anchors


def decorate_report(result, selection):
    result["verifier"].update(
        version=GUIDECHECK_VERSION,
        verifier_profile_version=PROFILE_VERSION,
        guide_profile_version=PROFILE_VERSION,
    )
    result["profile_selection"] = {
        "declared_version": selection.declared_version,
        "evaluated_policy": PROFILE_VERSION,
        "content_policy": CONTENT_POLICY,
        "anchor_policy": ANCHOR_POLICY,
    }
    anchors = result.get("cross_channel_anchors", [])
    count = sum(anchor["qualifies_for_level4"] for anchor in anchors)
    result["qualifying_anchor_count"] = count
    lines = [
        f"Profile: {PROFILE_VERSION} (declared {selection.declared_version})",
        f"Content policy: {CONTENT_POLICY}",
        f"Anchor policy: {ANCHOR_POLICY}",
        f"Qualifying anchors: {count}",
    ]
    for anchor in anchors:
        if anchor["channel"] == "repository-file":
            lines.append(f"Repository hash: {anchor['status']}; independent provenance: unestablished; counts toward Level 4: no")
    guide, summary, verifier = result["guide"], result["summary"], result["verifier"]
    source = result["input"].get("url", result["input"].get("path"))
    result["compact_report"] = "\n".join([
        f"Verifier: {verifier['name']} {verifier['version']}", f"Guide: {source}",
        *lines, f"Level: {guide['achieved_level']}", f"SHA-256: {guide['sha256']}",
        f"Blocking findings: {summary['blocking_findings']}", f"Warnings: {summary['warnings']}",
        f"Hash pinned: {'yes' if guide['achieved_level'] >= 4 else 'no'}",
        f"Proceed? {'yes' if summary['blocking_findings'] == 0 else 'no'}",
    ])
    if "hosted_limitations" in result:
        result["hosted_limitations"] = [
            "Profile 2.0.0 uses the 1.0.0 strict anchor policy and excludes repository-file hashes from Level 4 qualification.",
            *result["hosted_limitations"],
        ]
    return result
