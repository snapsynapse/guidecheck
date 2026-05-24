#!/usr/bin/env python3
"""
GuideCheck reference verifier CLI for local-file Levels 1 through 4.

This verifier intentionally does not claim hosted public-web Level 4
verification or Level 5 runtime conformance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


VERIFIER_NAME = "guidecheck-reference-local"
VERIFIER_VERSION = "0.3.0"
VERIFIER_PROFILE = "human-verifiable-assistant-guide-verifier"
VERIFIER_PROFILE_VERSION = "0.3.0"
GUIDE_PROFILE = "human-verifiable-assistant-guide"
GUIDE_PROFILE_VERSION = "0.3.0"
DEFAULT_APPROVAL_WARNING_THRESHOLD = 10
DEFAULT_METADATA_VALUE_WARNING_LENGTH = 80
ANCHOR_CHANNELS = {
    "dns-txt",
    "package-registry",
    "repository-file",
    "signed-security-txt",
    "transparency-log",
}

ALLOWED_CLASSES = {
    "normal",
    "networked",
    "destructive",
    "privileged",
    "persistence-changing",
    "data-accessing",
    "code-executing",
}
APPROVAL_REQUIRED_CLASSES = {
    "privileged",
    "destructive",
    "persistence-changing",
    "data-accessing",
    "code-executing",
}
REQUIRED_METADATA = {
    "identifier",
    "profile",
    "profile-version",
    "guide-version",
    "applies-to",
    "canonical-url",
    "repository-url",
    "last-reviewed",
}
URL_FIELDS = {
    "canonical-url",
    "repository-url",
    "recommended-verifier",
    "registry-url",
    "manifest-url",
    "superseded-by",
}
SECTION_PATTERNS = {
    "content.required.title": [r"^Assistant Guide:"],
    "content.required.canonical-url": [r"canonical-url:", r"Canonical URL:"],
    "content.required.repository-url": [r"repository-url:", r"Repository:"],
    "content.required.metadata": [r"\[assistant-guide-metadata\]"],
    "content.required.task-scope": [r"Task scope"],
    "content.required.invocation": [r"Assistant invocation prompt"],
    "content.required.safety-rules": [r"Safety rules"],
    "content.required.action-classification": [r"Action classification"],
    "content.required.actions": [r"\[action\]"],
    "content.required.stop-and-ask": [r"Stop and ask"],
    "content.required.acceptance": [r"Acceptance checklist"],
    "content.required.threat-model": [r"Threat model"],
    "content.required.untrusted-content": [r"Untrusted content handling"],
    "content.required.disclaimer": [r"Disclaimer and non-goals"],
    "content.required.authority": [r"Authority"],
}


@dataclass
class Finding:
    id: str
    severity: str
    message: str
    section: str | None = None
    line: int | None = None
    column: int | None = None
    remediation: str | None = None
    evidence: str | None = None

    def as_dict(self) -> dict[str, object]:
        result: dict[str, object] = {
            "id": self.id,
            "severity": self.severity,
            "message": self.message,
        }
        for key in ("section", "line", "column", "remediation", "evidence"):
            value = getattr(self, key)
            if value is not None:
                result[key] = value
        return result


@dataclass
class ManifestEvidence:
    sha256: str
    fetched: bool
    hash_match: bool
    bytes_match: bool
    valid: bool
    guide_sha256: str | None

    def as_dict(self) -> dict[str, object]:
        result: dict[str, object] = {
            "sha256": self.sha256,
            "fetched": self.fetched,
            "hash_match": self.hash_match,
            "bytes_match": self.bytes_match,
            "valid": self.valid,
        }
        if self.guide_sha256 is not None:
            result["guide_sha256"] = self.guide_sha256
        return result


@dataclass
class AnchorEvidence:
    channel: str
    status: str
    observed_sha256: str | None = None
    evidence_path: str | None = None

    def as_dict(self) -> dict[str, object]:
        result: dict[str, object] = {
            "channel": self.channel,
            "status": self.status,
        }
        if self.observed_sha256 is not None:
            result["observed_sha256"] = self.observed_sha256
        if self.evidence_path is not None:
            result["evidence_path"] = self.evidence_path
        return result


@dataclass
class Evaluation:
    path: Path
    data: bytes
    manifest_path: Path | None
    manifest_text: str | None
    anchor_paths: dict[str, Path]
    anchor_texts: dict[str, str]
    evaluated_at: datetime
    findings: list[Finding]
    achieved_level: int
    level5_ready: bool
    manifest_evidence: ManifestEvidence | None
    cross_channel_anchors: list[AnchorEvidence]

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.data).hexdigest()

    @property
    def blocking_ids(self) -> list[str]:
        return sorted({f.id for f in self.findings if f.severity == "error"})

    @property
    def warning_ids(self) -> list[str]:
        return sorted({f.id for f in self.findings if f.severity == "warning"})


def add_finding(
    findings: list[Finding],
    fid: str,
    severity: str,
    message: str,
    *,
    section: str | None = None,
    line: int | None = None,
    column: int | None = None,
    remediation: str | None = None,
    evidence: str | None = None,
) -> None:
    findings.append(
        Finding(
            fid,
            severity,
            message,
            section=section,
            line=line,
            column=column,
            remediation=remediation,
            evidence=evidence,
        )
    )


def decode_text(data: bytes) -> str:
    return data.decode("utf-8", errors="replace")


def line_column(data: bytes, offset: int) -> tuple[int, int]:
    line = data.count(b"\n", 0, offset) + 1
    line_start = data.rfind(b"\n", 0, offset) + 1
    return line, offset - line_start + 1


def parse_key_block(text: str, start: str, end: str) -> tuple[list[dict[str, str]], list[str]]:
    blocks: list[dict[str, str]] = []
    errors: list[str] = []
    in_block = False
    current: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.rstrip("\n")
        if line == start:
            if in_block:
                errors.append("nested")
            in_block = True
            current = {}
            continue
        if line == end:
            if not in_block:
                errors.append("orphan-close")
            else:
                blocks.append(current)
            in_block = False
            current = {}
            continue
        if in_block:
            if line in (start, end):
                errors.append("nested")
            elif ":" not in line:
                errors.append("malformed")
            else:
                key, value = line.split(":", 1)
                value = value[1:] if value.startswith(" ") else value
                if not re.fullmatch(r"[a-z0-9-]+", key):
                    errors.append("bad-key")
                if key in current:
                    errors.append(f"duplicate:{key}")
                current[key] = value
    if in_block:
        errors.append("missing-close")
    return blocks, errors


def is_ascii_https_url(value: str) -> bool:
    try:
        value.encode("ascii")
    except UnicodeEncodeError:
        return False
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc) and parsed.hostname is not None


def looks_like_registry_record(value: str) -> bool:
    parsed = urlparse(value)
    if "registry.npmjs.org" in parsed.netloc:
        return len([p for p in parsed.path.split("/") if p]) >= 2
    if "pypi.org" in parsed.netloc:
        return "/pypi/" in parsed.path and parsed.path.endswith("/json")
    return parsed.path not in {"", "/"}


def check_byte_profile(data: bytes, findings: list[Finding]) -> None:
    if len(data) > 8192:
        add_finding(
            findings,
            "byte-profile.size-limit",
            "error",
            "guide exceeds 8192 bytes",
            section="verifier-conformance.11",
            remediation="shorten the guide to 8192 bytes or less",
        )
    line_count = data.count(b"\n") + (0 if data.endswith(b"\n") else 1)
    if line_count > 400:
        add_finding(
            findings,
            "byte-profile.line-count",
            "error",
            "guide exceeds 400 lines",
            section="verifier-conformance.11",
            remediation="shorten the guide to 400 lines or fewer",
        )
    for idx, byte in enumerate(data):
        if byte == 0x09:
            line, column = line_column(data, idx)
            add_finding(
                findings,
                "byte-profile.no-tabs",
                "error",
                "tab character is not allowed",
                section="verifier-conformance.11",
                line=line,
                column=column,
                remediation="replace tabs with spaces",
            )
            break
    if b"\r" in data:
        idx = data.index(b"\r")
        line, column = line_column(data, idx)
        add_finding(
            findings,
            "byte-profile.no-carriage-returns",
            "error",
            "carriage return byte is not allowed",
            section="verifier-conformance.11",
            line=line,
            column=column,
            remediation="convert line endings to LF",
        )
    if b"\x00" in data:
        idx = data.index(b"\x00")
        line, column = line_column(data, idx)
        add_finding(findings, "byte-profile.no-nul", "error", "NUL byte is not allowed", line=line, column=column)
    if b"\x1b" in data:
        idx = data.index(b"\x1b")
        line, column = line_column(data, idx)
        add_finding(
            findings,
            "byte-profile.no-ansi-escape",
            "error",
            "ANSI escape byte is not allowed",
            line=line,
            column=column,
        )
    for idx, byte in enumerate(data):
        if byte not in (0x0A, 0x09, 0x0D, 0x00, 0x1B) and not (0x20 <= byte <= 0x7E):
            line, column = line_column(data, idx)
            add_finding(
                findings,
                "byte-profile.non-ascii-byte",
                "error",
                "byte outside LF and printable ASCII is not allowed",
                section="verifier-conformance.11",
                line=line,
                column=column,
                remediation="replace non-ASCII content with printable ASCII",
            )
            break
    for line_no, raw in enumerate(data.split(b"\n"), start=1):
        if raw.endswith(b"\r"):
            raw = raw[:-1]
        if len(raw) > 120:
            add_finding(
                findings,
                "byte-profile.line-length",
                "error",
                "line exceeds 120 bytes",
                section="verifier-conformance.11",
                line=line_no,
                remediation="wrap the line to 120 bytes or fewer",
            )
            break


def check_disallowed(text: str, findings: list[Finding]) -> None:
    lowered = text.lower()
    if re.search(r"</?(html|script|style|iframe|img|link|meta)\b", lowered):
        add_finding(findings, "construct.html", "error", "HTML-like construct present")
    if re.search(r"!\[[^\]]*\]\([^)]+\)", text):
        add_finding(findings, "construct.markdown-image", "error", "Markdown image construct present")
    if "data:" in lowered:
        add_finding(findings, "construct.data-url", "error", "data URL present")
    if re.search(r"\bjavascript\s*:", lowered) or re.search(r"\beval\s*\(", lowered):
        add_finding(findings, "construct.javascript", "error", "JavaScript construct present")
    for line in lowered.splitlines():
        if "do not" in line:
            continue
        if re.search(r"(base64|decode).{0,40}(execute|run|eval)", line):
            add_finding(findings, "prohibited.encoded-execution", "error", "decode and execute instruction")


def check_verification_instruction(text: str, findings: list[Finding]) -> bool:
    lower = text.lower()
    before_action = lower.split("[action]", 1)[0]
    concepts = [
        ("verify", "verifier"),
        ("achieved level", "blocking findings"),
        ("ask the user", "confirmation"),
        ("do not execute", "before confirmation"),
    ]
    ok = all(a in before_action and b in before_action for a, b in concepts)
    if not ok:
        add_finding(
            findings,
            "verification-instruction.missing",
            "error",
            "compact verification instruction is missing or incomplete",
            section="verifier-conformance.15",
            remediation="add the Level 1 compact verification instruction before action instructions",
        )
    if re.search(r"only\s+(?:authoritative|valid|approved)\s+verifier", lower):
        add_finding(
            findings,
            "verification-instruction.single-authority",
            "error",
            "guide implies only one verifier is authoritative",
            section="verifier-conformance.15",
            remediation="allow use of another conformant verifier",
        )
    return ok


def parse_metadata(text: str, findings: list[Finding], today: date) -> dict[str, str]:
    blocks, errors = parse_key_block(text, "[assistant-guide-metadata]", "[/assistant-guide-metadata]")
    if len(blocks) != 1:
        add_finding(findings, "metadata.block-count", "error", "metadata block count is not one")
        return {}
    if errors:
        add_finding(findings, "metadata.malformed", "error", "metadata block is malformed", evidence=",".join(errors))
    meta = blocks[0]
    missing = sorted(REQUIRED_METADATA - set(meta))
    if missing:
        add_finding(findings, "metadata.missing-required", "error", "required metadata fields are missing", evidence=",".join(missing))
    for key, value in meta.items():
        if key not in URL_FIELDS and len(value) > DEFAULT_METADATA_VALUE_WARNING_LENGTH:
            add_finding(findings, "metadata.value.long", "warning", f"metadata value for {key} is unusually long")
    for key in URL_FIELDS:
        if key in meta and not is_ascii_https_url(meta[key]):
            add_finding(findings, "metadata.url.invalid", "error", f"metadata URL field is invalid: {key}")
    status = meta.get("status", "active")
    if status not in {"active", "deprecated", "revoked"}:
        add_finding(findings, "metadata.status.invalid", "error", f"unsupported status: {status}")
    if status == "revoked":
        add_finding(findings, "metadata.status.revoked", "error", "guide status is revoked")
    if status in {"deprecated", "revoked"} and "superseded-by" not in meta:
        add_finding(findings, "metadata.superseded-by.missing", "warning", "deprecated or revoked guide lacks superseded-by")
    if "registry-url" in meta and not looks_like_registry_record(meta["registry-url"]):
        add_finding(findings, "metadata.registry-url.not-record", "error", "registry-url does not identify a specific record")
    check_dates(meta, findings, today)
    return meta


def check_dates(meta: dict[str, str], findings: list[Finding], today: date) -> None:
    if "last-reviewed" in meta:
        parsed = parse_iso_date(meta["last-reviewed"])
        if parsed is None:
            add_finding(findings, "metadata.last-reviewed.invalid", "warning", "last-reviewed date is malformed")
        else:
            age = (today - parsed).days
            add_finding(findings, "metadata.last-reviewed.age", "info", f"last-reviewed is {age} days old")
            if age < -7:
                add_finding(findings, "metadata.last-reviewed.future", "warning", "last-reviewed date appears to be in the future")
    if "valid-until" in meta:
        parsed = parse_iso_date(meta["valid-until"])
        if parsed is None:
            add_finding(findings, "metadata.valid-until.invalid", "warning", "valid-until date is malformed")
        elif parsed < today:
            add_finding(findings, "metadata.valid-until.expired", "warning", "valid-until is in the past")


def parse_iso_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def check_sections(text: str, findings: list[Finding]) -> None:
    for fid, patterns in SECTION_PATTERNS.items():
        if not any(re.search(pattern, text, re.IGNORECASE | re.MULTILINE) for pattern in patterns):
            add_finding(findings, fid, "error", fid, section="verifier-conformance.16")


def parse_actions(text: str, findings: list[Finding]) -> list[dict[str, str]]:
    blocks, errors = parse_key_block(text, "[action]", "[/action]")
    if errors:
        add_finding(findings, "action-block.malformed", "error", "action block is malformed", evidence=",".join(errors))
    seen: set[str] = set()
    actions: list[dict[str, str]] = []
    for action in blocks:
        missing = {"id", "class", "approval", "command"} - set(action)
        if missing:
            add_finding(findings, "action-block.missing-required", "error", "action block lacks required fields", evidence=",".join(sorted(missing)))
        action_id = action.get("id")
        if action_id:
            if action_id in seen:
                add_finding(findings, "action-block.duplicate-id", "error", f"duplicate action id: {action_id}")
            seen.add(action_id)
        if action.get("approval") not in {"required", "not-required"}:
            add_finding(findings, "action-block.approval.invalid", "error", f"invalid approval: {action.get('approval')}")
        if "runner" in action and action["runner"] not in {"argv", "shell"}:
            add_finding(findings, "action-block.runner.invalid", "error", f"invalid runner: {action['runner']}")
        actions.append(action)
    return actions


def action_classes(action: dict[str, str]) -> set[str]:
    return {c.strip() for c in action.get("class", "").split(",") if c.strip()}


def check_actions(actions: list[dict[str, str]], findings: list[Finding]) -> None:
    required_approvals = 0
    for action in actions:
        classes = action_classes(action)
        if action.get("approval") == "required":
            required_approvals += 1
        if not classes or not classes <= ALLOWED_CLASSES:
            add_finding(findings, "action-block.class.invalid", "error", f"invalid class list: {action.get('class', '')}")
        if "normal" in classes and len(classes) > 1:
            add_finding(findings, "action-block.class.normal-mixed", "error", "normal class is mutually exclusive")
        if classes & APPROVAL_REQUIRED_CLASSES and action.get("approval") != "required":
            add_finding(findings, "approval.required-missing", "error", "sensitive action lacks required approval", evidence=action.get("id", ""))
        if "networked" in classes and "egress" not in action:
            add_finding(findings, "egress.missing", "error", "networked action lacks egress", evidence=action.get("id", ""))
        if "egress" in action and re.search(r"(^|,\s*)\*($|,|\.)", action["egress"]):
            add_finding(findings, "egress.wildcard-too-broad", "error", "egress wildcard is too broad")
        if "code-executing" not in classes and command_executes_code(action.get("command", "")):
            add_finding(findings, "action-block.class.code-executing-missing", "warning", "command likely executes code", evidence=action.get("id", ""))
        if action.get("runner") == "shell" and not action.get("notes"):
            add_finding(findings, "runner.shell.missing-rationale", "warning", "shell runner lacks notes rationale", evidence=action.get("id", ""))
        check_command(action, classes, findings)
    if required_approvals > DEFAULT_APPROVAL_WARNING_THRESHOLD:
        add_finding(findings, "approval.required.too-many", "warning", "guide contains many required approvals")


def check_level5_readiness(actions: list[dict[str, str]], findings: list[Finding]) -> bool:
    before = len(findings)
    for action in actions:
        classes = action_classes(action)
        action_id = action.get("id", "")
        if "runner" not in action:
            add_finding(
                findings,
                "level5.runner.missing",
                "warning",
                "Level 5 readiness expects every executable action to declare runner",
                section="verifier-conformance.18",
                evidence=action_id,
            )
        if "networked" in classes and action.get("approval") != "required":
            add_finding(
                findings,
                "level5.networked-approval.missing",
                "warning",
                "Level 5 readiness expects networked actions to require approval",
                section="verifier-conformance.18",
                evidence=action_id,
            )
        if action.get("runner") == "shell" and action.get("approval") != "required":
            add_finding(
                findings,
                "level5.shell-approval.missing",
                "warning",
                "Level 5 readiness expects shell actions to require approval",
                section="verifier-conformance.19",
                evidence=action_id,
            )
    readiness_warning_ids = {
        "action-block.class.code-executing-missing",
        "runner.shell.missing-rationale",
        "level5.runner.missing",
        "level5.networked-approval.missing",
        "level5.shell-approval.missing",
    }
    return not any(
        finding.severity == "warning" and finding.id in readiness_warning_ids
        for finding in findings[before:] + findings[:before]
    )


def command_executes_code(command: str) -> bool:
    return bool(re.search(r"\b(npm|pnpm|yarn|pytest|python|node|make|just|go test|cargo)\b", command))


def check_command(action: dict[str, str], classes: set[str], findings: list[Finding]) -> None:
    command = action.get("command", "")
    if any(token in command for token in ["&&", "||", ";", "\n"]):
        add_finding(findings, "command.chaining", "error", "command uses chaining", evidence=command)
    if "$(" in command or "${" in command or "`" in command:
        add_finding(findings, "command.substitution", "error", "command uses shell substitution", evidence=command)
    if ("|" in command or ">" in command or "<" in command) and classes != {"normal"}:
        add_finding(findings, "command.pipe-or-redirection", "error", "non-normal command uses pipe or redirection", evidence=command)
    if ("destructive" in classes or "privileged" in classes) and "*" in command:
        add_finding(findings, "command.glob-destructive", "error", "destructive or privileged command uses a glob", evidence=command)
    vars_used = sorted(set(re.findall(r"\$([A-Za-z_][A-Za-z0-9_]*)", command)))
    if vars_used:
        declared = {v.strip() for v in action.get("env", "").split(",") if v.strip()}
        if not declared:
            add_finding(findings, "env.missing", "error", "command references environment variables without env", evidence=command)
        elif not set(vars_used) <= declared:
            add_finding(findings, "env.unlisted-variable", "error", "command references undeclared environment variables", evidence=command)
    if filesystem_command(command) and "cwd" not in action:
        add_finding(findings, "filesystem.cwd.missing", "error", "filesystem action lacks cwd", evidence=action.get("id", ""))


def filesystem_command(command: str) -> bool:
    return bool(re.search(r"\b(cat|sed|awk|jq|ls|cp|mv|rm|chmod|chown|npm|python|node|make|touch)\b", command))


def check_prohibited(text: str, findings: list[Finding]) -> None:
    exact_patterns = [
        ("prohibited.chained-guide", r"fetch and follow|follow another .*guide|continue with .*\.txt"),
        ("prohibited.next-guide-field", r"^(next-guide|then-fetch|chain-to|follow-next|continue-with):"),
        ("prohibited.rewrite-guide", r"modify.*assistant-guide\.txt|replace.*assistant-guide\.txt"),
        ("prohibited.memory", r"long-term assistant memory"),
        ("prohibited.skip-approval", r"skip approval gates and|disable sandboxing|expand tool permissions"),
        ("prohibited.notes-as-command", r"treat .*notes.* as commands"),
    ]
    for raw_line in text.lower().splitlines():
        if "do not" in raw_line:
            continue
        for fid, pattern in exact_patterns:
            if re.search(pattern, raw_line):
                add_finding(findings, fid, "error", fid)


def parse_manifest(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw in text.splitlines():
        if ":" in raw:
            key, value = raw.split(":", 1)
            result[key] = value.strip()
    return result


def check_manifest(data: bytes, manifest_text: str | None, findings: list[Finding]) -> ManifestEvidence | None:
    if manifest_text is None:
        return None
    manifest = parse_manifest(manifest_text)
    required = {"guide-path", "guide-version", "guide-sha256", "guide-bytes", "immutable-release-url"}
    missing = required - set(manifest)
    if missing:
        add_finding(findings, "manifest.missing-required", "error", "manifest lacks required fields", evidence=",".join(sorted(missing)))
    guide_sha = hashlib.sha256(data).hexdigest()
    hash_match = manifest.get("guide-sha256") == guide_sha
    if manifest.get("guide-sha256") and not hash_match:
        add_finding(findings, "manifest.hash-mismatch", "error", "manifest guide-sha256 does not match guide bytes")
    bytes_match = False
    if manifest.get("guide-bytes"):
        try:
            bytes_match = int(manifest["guide-bytes"]) == len(data)
            if not bytes_match:
                add_finding(findings, "manifest.bytes-mismatch", "error", "manifest guide-bytes does not match guide bytes")
        except ValueError:
            add_finding(findings, "manifest.bytes-invalid", "error", "manifest guide-bytes is not an integer")
    return ManifestEvidence(
        sha256=hashlib.sha256(manifest_text.encode("utf-8")).hexdigest(),
        fetched=False,
        hash_match=hash_match,
        bytes_match=bytes_match,
        valid=not missing and hash_match and bytes_match,
        guide_sha256=manifest.get("guide-sha256"),
    )


def extract_anchor_sha256(channel: str, text: str) -> str | None:
    if channel == "repository-file":
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    if channel == "package-registry":
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = None
        found = find_json_sha256(data) if data is not None else None
        if found:
            return found

    patterns = [
        r"\bsha256=([0-9a-f]{64})\b",
        r"\bguide-sha256:\s*([0-9a-f]{64})\b",
        r"\bAssistant-Guide-SHA256:\s*([0-9a-f]{64})\b",
        r'"sha256"\s*:\s*"([0-9a-f]{64})"',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).lower()
    return None


def find_json_sha256(value: object) -> str | None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "sha256" and isinstance(item, str) and re.fullmatch(r"[0-9a-f]{64}", item):
                return item
            found = find_json_sha256(item)
            if found:
                return found
    elif isinstance(value, list):
        for item in value:
            found = find_json_sha256(item)
            if found:
                return found
    return None


def check_anchors(
    manifest_evidence: ManifestEvidence | None,
    anchor_texts: dict[str, str],
    anchor_paths: dict[str, Path],
    findings: list[Finding],
    *,
    level4_claimed: bool,
) -> list[AnchorEvidence]:
    if manifest_evidence is None or manifest_evidence.guide_sha256 is None:
        return []

    anchors: list[AnchorEvidence] = []
    for channel, text in sorted(anchor_texts.items()):
        evidence_path = str(anchor_paths[channel]) if channel in anchor_paths else None
        observed = extract_anchor_sha256(channel, text)
        if observed is None:
            anchors.append(
                AnchorEvidence(
                    channel=channel,
                    status="absent",
                    evidence_path=evidence_path,
                )
            )
            continue
        status = "present-matches" if observed == manifest_evidence.guide_sha256 else "present-mismatch"
        anchors.append(
            AnchorEvidence(
                channel=channel,
                status=status,
                observed_sha256=observed,
                evidence_path=evidence_path,
            )
        )
        if status == "present-mismatch":
            add_finding(
                findings,
                "anchor.independent.mismatch",
                "error",
                "independent anchor hash does not match manifest guide-sha256",
                section="verifier-conformance.23",
                evidence=channel,
            )

    if level4_claimed and not anchors:
        add_finding(
            findings,
            "anchor.independent.missing",
            "error",
            "no independent anchor is available for Level 4",
            section="verifier-conformance.23",
            remediation="publish the guide hash on DNS TXT, package registry metadata, repository file, signed security.txt, or a transparency log",
        )
    elif level4_claimed and anchors and not any(anchor.status == "present-matches" for anchor in anchors):
        if not any(anchor.status == "present-mismatch" for anchor in anchors):
            add_finding(
                findings,
                "anchor.independent.missing",
                "error",
                "no independent anchor hash was found for Level 4",
                section="verifier-conformance.23",
            )
    return anchors


def evaluate_guide(
    data: bytes,
    manifest_text: str | None = None,
    anchor_texts: dict[str, str] | None = None,
    anchor_paths: dict[str, Path] | None = None,
    now: datetime | None = None,
) -> tuple[list[Finding], int, bool, ManifestEvidence | None, list[AnchorEvidence]]:
    """Run Level 1-4 local checks on raw guide bytes.

    Returns (findings, achieved_level, level5_ready, manifest evidence,
    cross-channel anchor evidence). Shared by the local-file CLI and the
    hosted public-web API so both apply identical content checks.
    """
    evaluated_at = now or datetime.now(timezone.utc)
    anchor_texts = anchor_texts or {}
    anchor_paths = anchor_paths or {}
    findings: list[Finding] = []
    text = decode_text(data)

    check_byte_profile(data, findings)
    check_disallowed(text, findings)
    has_l1_instruction = check_verification_instruction(text, findings)
    meta = parse_metadata(text, findings, evaluated_at.date()) if "[assistant-guide-metadata]" in text else {}
    has_repo = "repository-url" in meta or re.search(r"Repository:\s*https://", text)
    has_canonical = "canonical-url" in meta or re.search(r"Canonical URL:\s*https://", text)
    has_scope = "Task scope" in text
    actions = parse_actions(text, findings)
    wants_level3_checks = bool(actions) or "Assistant invocation prompt" in text
    if "[assistant-guide-metadata]" in text and wants_level3_checks:
        check_sections(text, findings)
        check_actions(actions, findings)
    check_prohibited(text, findings)
    manifest_evidence = check_manifest(data, manifest_text, findings)
    level4_claimed = bool(meta.get("manifest-url"))
    cross_channel_anchors = check_anchors(
        manifest_evidence,
        anchor_texts,
        anchor_paths,
        findings,
        level4_claimed=level4_claimed,
    )

    error_ids = {f.id for f in findings if f.severity == "error"}
    l1_blockers = {"verification-instruction.missing"}
    achieved = 0
    if has_l1_instruction and has_repo and has_canonical and has_scope:
        achieved = 1
    byte_blockers = {fid for fid in error_ids if fid.startswith("byte-profile.") or fid.startswith("construct.")}
    if achieved >= 1 and not byte_blockers:
        achieved = 2
    level4_blockers = {
        fid for fid in error_ids if fid.startswith("manifest.") or fid.startswith("anchor.")
    }
    level3_blockers = error_ids - byte_blockers - l1_blockers - level4_blockers
    if achieved >= 2 and "[assistant-guide-metadata]" in text and actions and not level3_blockers:
        achieved = 3
    anchor_matches = any(anchor.status == "present-matches" for anchor in cross_channel_anchors)
    anchor_mismatches = any(anchor.status == "present-mismatch" for anchor in cross_channel_anchors)
    if (
        achieved >= 3
        and level4_claimed
        and manifest_evidence is not None
        and manifest_evidence.valid
        and anchor_matches
        and not anchor_mismatches
    ):
        achieved = 4
    if "metadata.status.revoked" in error_ids:
        achieved = min(achieved, 1)

    level5_ready = check_level5_readiness(actions, findings) if achieved >= 4 else False

    return findings, achieved, level5_ready, manifest_evidence, cross_channel_anchors


def evaluate_local_file(
    path: Path,
    manifest_path: Path | None = None,
    anchor_paths: dict[str, Path] | None = None,
    now: datetime | None = None,
) -> Evaluation:
    data = path.read_bytes()
    manifest_text = manifest_path.read_text(encoding="utf-8") if manifest_path else None
    anchor_paths = anchor_paths or {}
    anchor_texts = {channel: anchor_path.read_text(encoding="utf-8") for channel, anchor_path in anchor_paths.items()}
    evaluated_at = now or datetime.now(timezone.utc)
    findings, achieved, level5_ready, manifest_evidence, cross_channel_anchors = evaluate_guide(
        data,
        manifest_text,
        anchor_texts,
        anchor_paths,
        evaluated_at,
    )
    return Evaluation(
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


def output_for(evaluation: Evaluation) -> dict[str, object]:
    findings = [finding.as_dict() for finding in evaluation.findings]
    warnings = sum(1 for finding in evaluation.findings if finding.severity == "warning")
    infos = sum(1 for finding in evaluation.findings if finding.severity == "info")
    blocking = sum(1 for finding in evaluation.findings if finding.severity == "error")
    result: dict[str, object] = {
        "verifier": {
            "name": VERIFIER_NAME,
            "version": VERIFIER_VERSION,
            "verifier_profile": VERIFIER_PROFILE,
            "verifier_profile_version": VERIFIER_PROFILE_VERSION,
            "guide_profile": GUIDE_PROFILE,
            "guide_profile_version": GUIDE_PROFILE_VERSION,
        },
        "input": {
            "evaluation_mode": "local-file",
            "path": str(evaluation.path),
        },
        "guide": {
            "bytes": len(evaluation.data),
            "sha256": evaluation.sha256,
            "achieved_level": evaluation.achieved_level,
            "level5_ready": evaluation.level5_ready,
        },
        "local_evaluation": {
            "evaluated_at": evaluation.evaluated_at.isoformat().replace("+00:00", "Z"),
        },
        "summary": {
            "blocking_findings": blocking,
            "warnings": warnings,
            "infos": infos,
        },
        "findings": findings,
    }
    if evaluation.manifest_path:
        result["input"]["manifest_path"] = str(evaluation.manifest_path)  # type: ignore[index]
    if evaluation.anchor_paths:
        result["input"]["anchor_paths"] = {
            channel: str(path) for channel, path in sorted(evaluation.anchor_paths.items())
        }  # type: ignore[index]
    if evaluation.manifest_evidence is not None:
        result["manifest"] = {
            "path": str(evaluation.manifest_path),
            **evaluation.manifest_evidence.as_dict(),
        }
    if evaluation.cross_channel_anchors:
        result["cross_channel_anchors"] = [
            anchor.as_dict() for anchor in evaluation.cross_channel_anchors
        ]
    result["compact_report"] = compact_report(result)
    return result


def compact_report(result: dict[str, object]) -> str:
    verifier = result["verifier"]  # type: ignore[index]
    guide = result["guide"]  # type: ignore[index]
    summary = result["summary"]  # type: ignore[index]
    input_info = result["input"]  # type: ignore[index]
    return "\n".join(
        [
            f"Verifier: {verifier['name']} {verifier['version']}",  # type: ignore[index]
            f"Guide: {input_info['path']}",  # type: ignore[index]
            f"Level: {guide['achieved_level']}",  # type: ignore[index]
            f"SHA-256: {guide['sha256']}",  # type: ignore[index]
            f"Blocking findings: {summary['blocking_findings']}",  # type: ignore[index]
            f"Warnings: {summary['warnings']}",  # type: ignore[index]
            f"Hash pinned: {'yes' if guide['achieved_level'] >= 4 else 'no'}",  # type: ignore[index]
            f"Proceed? {'yes' if summary['blocking_findings'] == 0 else 'no'}",  # type: ignore[index]
        ]
    )


def parse_anchor_arg(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("anchor must use CHANNEL=PATH")
    channel, raw_path = value.split("=", 1)
    if channel not in ANCHOR_CHANNELS:
        choices = ", ".join(sorted(ANCHOR_CHANNELS))
        raise argparse.ArgumentTypeError(f"unknown anchor channel {channel!r}; expected one of {choices}")
    path = Path(raw_path)
    if not path.is_file():
        raise argparse.ArgumentTypeError(f"anchor file not found: {path}")
    return channel, path


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
    evaluation = evaluate_local_file(args.path, args.manifest, anchor_paths)
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
