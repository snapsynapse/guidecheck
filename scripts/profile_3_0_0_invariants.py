"""Draft profile 3.0.0: the rules its JSON Schemas cannot state.

A schema bounds the form of one value. It cannot relate two fields, compare two
registry entries, or see that a manifest key was written twice. Those rules are
normative in `profiles/3.0.0/verifier-conformance.md` (sections 19, 22 and 27)
and are collected here as plain functions, so a test, a fixture harness or a
verifier can apply them next to schema validation.

Status: unreleased. Nothing here evaluates a guide, and no released entry point
imports this module.
"""
import re

SIZE_LIMIT = 8192
REASONS = ("blocking findings", "below Level 3", "below the required level")
SEVERITY_COUNTS = (("error", "blocking_findings"), ("warning", "warnings"), ("info", "infos"))

_SEG = r"[A-Za-z0-9._+-]+"
_LABEL = r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
_SLOT_PATTERNS = {
    "local-ref": re.compile(rf"\./{_SEG}(?:/{_SEG})*"),
    "https-url": re.compile(rf"https://{_LABEL}(?:\.{_LABEL})+(?:/[A-Za-z0-9._+@-]+)*/?"),
    "word": re.compile(r"[A-Za-z0-9_+][A-Za-z0-9._+-]*"),
    "number": re.compile(r"[0-9]+"),
}
# Slot types whose languages intersect. Every number is also a word.
_OVERLAPPING_SLOTS = {frozenset({"word", "number"})}
_SEPARATORS = re.compile(r"[/:=@,]")
_MANIFEST_KEY = re.compile(r"[a-z0-9-]+")
_SHA256 = re.compile(r"[0-9a-f]{64}")
_PLAIN_COUNT = re.compile(r"[1-9][0-9]*")
_PRINTABLE = re.compile(r"[ -~]*")


def expected_verdict(report):
    """The verdict that conformance section 25 derives from the rest of the report."""
    level = report["guide"]["achieved_level"]
    if report["summary"]["blocking_findings"]:
        return {"proceed": False, "reason": REASONS[0]}
    if level < 3:
        return {"proceed": False, "reason": REASONS[1]}
    if level < report["input"].get("required_level", 0):
        return {"proceed": False, "reason": REASONS[2]}
    return {"proceed": True}


def render_compact_report(report):
    """The one compact report a conforming verifier renders from these fields."""
    guide, actions, summary = report["guide"], report["actions"], report["summary"]
    shown = guide.get("canonical_url") or report["input"].get("path") or "n/a"
    verdict = expected_verdict(report)
    lines = [
        f"Verifier: {report['verifier']['name']} {report['verifier']['version']}",
        f"Guide: {shown}",
        "Profile: 3.0.0",
        "Content policy: restricted-argv-1",
        "Anchor policy: 1.0.0-strict",
        f"Qualifying anchors: {report['qualifying_anchor_count']}",
        f"Level: {guide['achieved_level']}",
        f"SHA-256: {guide['sha256']}",
        f"Actions: {actions['total']} ({actions['shape_listed']} shape-listed, {actions['opaque']} opaque)",
        f"Blocking findings: {summary['blocking_findings']}",
        f"Warnings: {summary['warnings']}",
        f"Hash pinned: {'yes' if guide['achieved_level'] >= 4 else 'n/a'}",
        f"Proceed? {'yes' if verdict['proceed'] else 'no'}",
    ]
    if not verdict["proceed"]:
        lines.append(f"Reason: {verdict['reason']}")
    return "\n".join(lines)


def check_report(report, registered_ids):
    """Return the invariants a schema-valid 3.0.0 report breaks. Empty means none.

    `registered_ids` is the set of finding ids in `finding-ids.md`. It is not
    optional: an id the registry does not define has no meaning a reader can
    look up, and a report that carries one is not conforming.
    """
    problems = []
    guide, actions, summary, findings = report["guide"], report["actions"], report["summary"], report["findings"]
    level, status, mode = guide["achieved_level"], guide["status"], report["input"]["evaluation_mode"]
    errors = {finding["id"] for finding in findings if finding["severity"] == "error"}
    anchors = report.get("cross_channel_anchors", [])

    if actions["total"] != actions["shape_listed"] + actions["opaque"]:
        problems.append("actions.total is not the sum of the two tiers")
    for severity, key in SEVERITY_COUNTS:
        if summary[key] != sum(finding["severity"] == severity for finding in findings):
            problems.append(f"summary.{key} does not count the {severity} findings")
    if report["verdict"] != expected_verdict(report):
        problems.append("verdict does not follow from blocking findings, achieved level and required level")
    if report["compact_report"] != render_compact_report(report):
        problems.append("compact_report is not the rendering of the report fields")

    refused = any(finding["id"] == "byte-profile.size-limit" for finding in findings)
    if refused and "byte-profile.size-limit" not in errors:
        problems.append("byte-profile.size-limit is always an error")
    if refused != (guide["bytes"] > SIZE_LIMIT):
        problems.append("byte-profile.size-limit must be reported exactly when the guide exceeds the size limit")
    if refused and not (level == 0 and status == "unknown" and actions["total"] == 0 and len(findings) == 1
                        and "canonical_url" not in guide and "shape_registry_sha256" not in report):
        problems.append("a guide refused for size has level 0, unknown status, no actions and one finding")
    if status == "unknown" and not refused:
        problems.append("status is unknown only for a guide refused for size")

    if level >= 3 and status != "active":
        problems.append("Level 3 requires an active status")
    if status == "deprecated" and (level > 2 or "metadata.status.deprecated" not in errors):
        problems.append("a deprecated guide is capped at Level 2 and carries metadata.status.deprecated")
    if status == "revoked" and (level > 1 or "metadata.status.revoked" not in errors):
        problems.append("a revoked guide is capped at Level 1 and carries metadata.status.revoked")
    if "superseded_by" in guide and status not in ("deprecated", "revoked"):
        problems.append("superseded_by is reported only for a deprecated or revoked guide")
    if level >= 3 and actions["total"] == 0:
        problems.append("Level 3 requires at least one action block")
    if ("shape_registry_sha256" in report) != (actions["total"] > 0):
        problems.append("shape_registry_sha256 is present exactly when the guide has an action block")
    if guide.get("level5_ready") and level < 4:
        problems.append("level5_ready requires Level 4")

    qualifying = [anchor for anchor in anchors if anchor["qualifies_for_level4"]]
    if report["qualifying_anchor_count"] != len(qualifying):
        problems.append("qualifying_anchor_count does not count the qualifying anchors")
    for anchor in qualifying:
        if anchor["channel"] == "repository-file":
            problems.append("a repository file never qualifies for Level 4")
        if anchor["status"] != "present-matches" or anchor["qualification_reason"] != "qualifying-channel":
            problems.append("a qualifying anchor is a fetched match on a qualifying channel")
    if mode == "local-file":
        if qualifying:
            problems.append("evidence that was not fetched never qualifies")
        if "fetch" in report:
            problems.append("fetch is reported only in public-web evaluation")
        if "path" not in report["input"]:
            problems.append("local-file evaluation reports the local path")
    elif "fetch" not in report:
        problems.append("public-web evaluation reports fetch evidence")
    if level == 4:
        manifest = report.get("manifest", {})
        if not (mode == "public-web" and qualifying and manifest.get("fetched") and manifest.get("valid")
                and manifest.get("hash_match") and manifest.get("bytes_match")):
            problems.append("Level 4 requires a fetched valid matching manifest and a qualifying anchor")

    for finding in findings:
        if finding["id"] not in registered_ids:
            problems.append("a finding id is not registered")
    return problems


def guide_text_in_output(serialized_report, forbidden_substrings):
    """Substrings of a fixture guide that leaked into the serialized report."""
    return [text for text in forbidden_substrings if text in serialized_report]


def _positions_overlap(left, right):
    if isinstance(left, str) and isinstance(right, str):
        return left == right
    if isinstance(left, str):
        return bool(_SLOT_PATTERNS[right["slot"]].fullmatch(left))
    if isinstance(right, str):
        return bool(_SLOT_PATTERNS[left["slot"]].fullmatch(right))
    return left["slot"] == right["slot"] or frozenset({left["slot"], right["slot"]}) in _OVERLAPPING_SLOTS


def _has_parent_component(token):
    """Rule G3 of the command grammar: a piece that ends with exactly two dots."""
    return any(piece.endswith("..") and not piece.endswith("...") for piece in _SEPARATORS.split(token))


def check_registry(registry):
    """Return the registry rules a schema-valid 3.0.0 registry breaks. Empty means none."""
    problems = []
    entries = registry["entries"]
    seen = set()
    for entry in entries:
        if entry["id"] in seen:
            problems.append(f"entry id {entry['id']} is used more than once")
        seen.add(entry["id"])
        argv = entry["argv"]
        if not isinstance(argv[0], str):
            problems.append(f"entry {entry['id']} has a slot in the program position")
        if any(isinstance(element, str) and _has_parent_component(element) for element in argv):
            problems.append(f"entry {entry['id']} has a literal with a parent-directory component, which no command may contain")
        slot = entry.get("pin", {}).get("slot")
        if slot is not None and not (slot < len(argv) and argv[slot] == {"slot": "local-ref"}):
            problems.append(f"entry {entry['id']} pins a position that is not a local-ref slot")
    for index, first in enumerate(entries):
        for second in entries[index + 1:]:
            if len(first["argv"]) == len(second["argv"]) and all(
                _positions_overlap(left, right) for left, right in zip(first["argv"], second["argv"])
            ):
                problems.append(f"entries {first['id']} and {second['id']} can match the same argument vector")
    return problems


def parse_manifest_text(text):
    """Parse a 3.0.0 manifest. Return (fields, finding ids); the fields then go to the manifest schema.

    Lines end at LF. A blank line is skipped. Every other line is a lowercase
    key, a colon, one space and a printable value with no edge spaces. A key
    appears once. `guide-bytes` is plain digits with no sign, separator or
    leading zero, and `guide-sha256` is 64 lowercase hexadecimal characters.
    """
    fields, found = {}, []
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    for line in lines:
        if line == "":
            continue
        key, separator, value = line.partition(": ")
        well_formed = (separator and _MANIFEST_KEY.fullmatch(key) and value and _PRINTABLE.fullmatch(value)
                       and value[0] != " " and value[-1] != " ")
        if not well_formed or key in fields:
            found.append("manifest.malformed")
            continue
        fields[key] = value
    if "guide-sha256" in fields and not _SHA256.fullmatch(fields["guide-sha256"]):
        found.append("manifest.hash-invalid")
        del fields["guide-sha256"]
    if "guide-bytes" in fields:
        # No guide is longer than 8192 bytes, so a longer number is refused before it is converted.
        if _PLAIN_COUNT.fullmatch(fields["guide-bytes"]) and len(fields["guide-bytes"]) <= 4:
            fields["guide-bytes"] = int(fields["guide-bytes"])
        else:
            found.append("manifest.bytes-invalid")
            del fields["guide-bytes"]
    return fields, sorted(set(found))
