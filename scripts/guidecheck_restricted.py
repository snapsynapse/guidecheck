"""restricted-argv-1: the content policy of draft guide profile 3.0.0.

Status: unreleased. No released entry point imports this module, and the public
dispatcher in `guidecheck_profiles.py` still refuses 3.0.0 as unsupported.
Nothing here changes how a released profile is evaluated.

The normative text is `profiles/3.0.0/spec.md` and `verifier-conformance.md`.
This module evaluates guide bytes that declare 3.0.0 against it:

- Size gate. Input over 8192 bytes is refused with one finding before any
  other byte is examined.
- One line splitter. Lines end at LF and nowhere else. A byte other than LF
  and printable ASCII is blocking.
- Exact fences, reserved marker text, and reserved field labels outside exact
  action blocks.
- A fixed action key list, one `key: value` form, seven required keys, and a
  grammar for every field value.
- The command grammar: an allowlist of bytes, one tokenizer (split on single
  spaces), a program that is a bare name or a `./` path, no parent-directory
  component, and no absolute path without `approval: required`.
- Two tiers. An action is shape-listed when its whole argument vector matches
  one entry of the shape registry, and opaque otherwise.
- Pins on local references.
- Metadata by exact parse, the URL grammar, status, required headings, the
  canonical verification instruction, the Level 2 byte and construct limits,
  and the Level 3 ban on fenced code.
- Levels 0 to 4, with the anchor policy of profile 1.0.0 carried unchanged.

Not implemented: prose scans, which the profile makes advisory and optional;
reading repository files, so a pin is reported as declared and never as
verified; and Level 5 readiness beyond the approval rule.

A finding is an id, a severity and a location. It carries no message, and no
guide-authored text is copied into one.
"""
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path

PROFILE_NAME = "human-verifiable-assistant-guide"
PROFILE_VERSION = "3.0.0"
CONTENT_POLICY = "restricted-argv-1"
ANCHOR_POLICY = "1.0.0-strict"
MAX_GUIDE_BYTES = 8192
MAX_LINE_BYTES = 120
MAX_LINES = 400
MAX_ID_BYTES = 32
APPROVAL_WARNING_THRESHOLD = 10
LONG_VALUE_BYTES = 80
STANDARD_PRIMARY_VERIFIER = "https://guidecheck.org/verify"
REGISTRY_PATH = Path(__file__).resolve().parents[1] / "profiles" / "3.0.0" / "shape-registry.json"

_ACTION_OPEN = b"[action]"
_ACTION_CLOSE = b"[/action]"
_METADATA_OPEN = b"[assistant-guide-metadata]"
_METADATA_CLOSE = b"[/assistant-guide-metadata]"
_PROFILE_LINE = b"profile: " + PROFILE_NAME.encode("ascii")
_VERSION_LINE = b"profile-version: " + PROFILE_VERSION.encode("ascii")
_TITLE_PREFIX = b"Assistant Guide: "
INSTRUCTION = (
    b"Before acting, verify this guide with a conformant verifier. Report its name and version,",
    b"the achieved level, the guide SHA-256 and any blocking findings. Run no action until the",
    b"user confirms they have read this guide and approve proceeding at that level.",
)

REQUIRED_KEYS = ("id", "class", "approval", "command", "runner", "cwd", "egress")
OPTIONAL_KEYS = ("notes", "env", "params", "exec-sha256", "exec-opaque")
_KEYS = {key.encode("ascii"): key for key in REQUIRED_KEYS + OPTIONAL_KEYS}
CLASSES = ("normal", "networked", "destructive", "privileged", "persistence-changing", "data-accessing", "code-executing")
APPROVAL_CLASSES = frozenset(CLASSES) - {"normal", "networked"}
# Labels that identify an action. Outside an exact block they are reserved.
_RESERVED_LABELS = frozenset({b"id", b"class", b"approval", b"command"})
# Marker text, looked for after lowercasing and removing spaces and tabs.
_RESERVED_MARKERS = tuple(
    opener + slash + b"action" for opener in (b"[", b"<", b"{") for slash in (b"", b"/")
)
SECTIONS = {
    b"Task scope": "content.required.task-scope",
    b"Assistant invocation prompt": "content.required.invocation",
    b"Safety rules": "content.required.safety-rules",
    b"Action classification": "content.required.action-classification",
    b"Stop and ask": "content.required.stop-and-ask",
    b"Acceptance checklist": "content.required.acceptance",
    b"Threat model": "content.required.threat-model",
    b"Untrusted content handling": "content.required.untrusted-content",
    b"Disclaimer and non-goals": "content.required.disclaimer",
    b"Authority": "content.required.authority",
}
_HEADING_PREFIXES = (b"", b"# ", b"## ", b"### ")
REQUIRED_METADATA = ("identifier", "profile", "profile-version", "guide-version", "applies-to", "canonical-url",
                     "repository-url", "last-reviewed")
URL_FIELDS = ("canonical-url", "repository-url", "recommended-verifier", "registry-url", "manifest-url", "superseded-by")
CHAIN_FIELDS = frozenset({"next-guide", "then-fetch", "chain-to", "follow-next", "continue-with"})
MANIFEST_REQUIRED = ("guide-path", "guide-version", "guide-sha256", "guide-bytes", "immutable-release-url", "profile",
                     "profile-version")
ANCHOR_CHANNELS = ("dns-txt", "package-registry", "repository-file", "signed-security-txt", "transparency-log")

_UPPER = b"ABCDEFGHIJKLMNOPQRSTUVWXYZ"
_LOWER = b"abcdefghijklmnopqrstuvwxyz"
_DIGITS = b"0123456789"
_ALNUM = _UPPER + _LOWER + _DIGITS
_ID_BYTES = _ALNUM + b"-"
_SEGMENT_BYTES = _ALNUM + b"-_.+"
_SEPARATOR_BYTES = b"/:=@,"
_ARGUMENT_BYTES = _SEGMENT_BYTES + _SEPARATOR_BYTES
_URL_SEGMENT_BYTES = _SEGMENT_BYTES + b"@"
_KEY_BYTES = _LOWER + _DIGITS + b"-"
_HEX_BYTES = _DIGITS + b"abcdef"
_PRINTABLE_BYTES = bytes(range(0x20, 0x7F))
_NOT_LOWERCASE = bytes(byte for byte in range(256) if not 0x61 <= byte <= 0x7A)
_SEPARATORS_TO_SLASH = bytes.maketrans(_SEPARATOR_BYTES, b"/" * len(_SEPARATOR_BYTES))

_OUTSIDE, _IN_METADATA, _IN_ACTION = range(3)

# Rule names used inside this module, and the registered finding id each reports.
_RULES = {rule: "action-block.malformed" for rule in (
    "marker", "nested", "orphan", "unclosed", "form", "value", "duplicate-key", "pin-form", "opaque-on-listed")}
_LEVEL4_PREFIXES = ("manifest.", "anchor.", "level4.")
_LEVEL2_PREFIXES = ("byte-profile.", "construct.")
_LEVEL1_IDS = frozenset({"verification-instruction.missing", "content.required.task-scope"})


class NotSelected(ValueError):
    """The guide bytes do not declare this profile exactly once in an exact metadata block."""


class RegistryError(ValueError):
    """The shape registry is missing or breaks a rule the profile sets for it."""


@dataclass(frozen=True)
class Finding:
    """An id, a severity and a location. There is no message field: see the module docstring."""

    id: str
    severity: str = "error"
    line: int | None = None
    section: str | None = None
    evidence: dict | None = None

    def as_dict(self):
        result = {"id": self.id, "severity": self.severity}
        for key in ("section", "line", "evidence"):
            if getattr(self, key) is not None:
                result[key] = getattr(self, key)
        return result


@dataclass(frozen=True)
class Action:
    """One exact action block. `argv` is None unless exactly one command is in the grammar."""

    line: int
    fields: dict
    argv: tuple | None
    tier: str = "opaque"
    shape: str | None = None


@dataclass(frozen=True)
class StructureReport:
    findings: tuple
    actions: tuple


@dataclass(frozen=True)
class Registry:
    entries: tuple
    sha256: str


@dataclass
class Evaluation:
    """The result of evaluating one guide. `build_report` turns it into schema-valid output."""

    sha256: str
    guide_bytes: int
    findings: list = field(default_factory=list)
    achieved_level: int = 0
    status: str = "unknown"
    canonical_url: str | None = None
    superseded_by: str | None = None
    actions: tuple = ()
    registry_sha256: str | None = None
    manifest: dict | None = None
    anchors: list = field(default_factory=list)
    level5_ready: bool = False
    evidence_fetched: bool = False
    evaluated_at: datetime | None = None


@dataclass
class _Scan:
    findings: list
    actions: list
    selected: bool
    metadata: list = field(default_factory=list)
    first_action_line: int | None = None


def _finding(rule, line=None, severity="error", evidence=None):
    return Finding(_RULES.get(rule, rule), severity, line, None, evidence)


def _only(value, allowed):
    """True when every byte of `value` is in `allowed`. One pass."""
    return not value.translate(None, allowed)


def _is_local_path(token):
    if not token.startswith(b"./"):
        return False
    return all(segment and _only(segment, _SEGMENT_BYTES) for segment in token[2:].split(b"/"))


def _is_program(token):
    return _only(token, _SEGMENT_BYTES) or _is_local_path(token)


def _has_parent_component(token):
    """True for a `..` component, including one attached to an option, as in `-C..`."""
    return any(
        piece.endswith(b"..") and not piece.endswith(b"...")
        for piece in token.translate(_SEPARATORS_TO_SLASH).split(b"/")
    )


def _is_absolute(token):
    return token.startswith(b"/") or token.partition(b"=")[2].startswith(b"/")


def _is_label(label):
    return 1 <= len(label) <= 63 and _only(label, _ID_BYTES) and label[:1] != b"-" and label[-1:] != b"-"


def is_url(value):
    """The URL grammar of guide-profile section 11, as an exact match over bytes."""
    if isinstance(value, str):
        value = value.encode("ascii", errors="replace")
    if not value.startswith(b"https://"):
        return False
    host, slash, path = value[8:].partition(b"/")
    labels = host.split(b".")
    if len(labels) < 2 or not all(_is_label(label) for label in labels):
        return False
    if not slash:
        return True
    segments = path.split(b"/")
    if segments[-1] == b"":
        segments.pop()
    return all(segment and _only(segment, _URL_SEGMENT_BYTES) for segment in segments)


def _url_host(value):
    return value[8:].partition("/")[0].lower()


def _check_command(value, approval_required):
    """Return (finding ids, argv). The tokenizer is one split on single spaces."""
    tokens = value.split(b" ")
    if not all(token and _only(token, _ARGUMENT_BYTES) for token in tokens) or not _is_program(tokens[0]):
        return ("command.grammar",), None
    found = []
    if any(_has_parent_component(token) for token in tokens):
        found.append("command.path.escape")
    if not approval_required and any(_is_absolute(token) for token in tokens):
        found.append("command.path.absolute")
    return tuple(found), tuple(token.decode("ascii") for token in tokens)


def check_command(command, *, approval_required=False):
    """Check one command value against the grammar. Accepts text or bytes."""
    if isinstance(command, str):
        command = command.encode("ascii", errors="replace")  # "?" is outside the grammar
    return _check_command(command, approval_required)


def _lines(data):
    lines = data.split(b"\n")
    if lines[-1] == b"":
        lines.pop()
    return lines


def _squeeze(line):
    return line.lower().replace(b" ", b"").replace(b"\t", b"")


def _has_marker_text(squeezed):
    return b"action" in squeezed and any(marker in squeezed for marker in _RESERVED_MARKERS)


def _letters(text):
    return text.lower().translate(None, _NOT_LOWERCASE)


def _has_reserved_label(line):
    """True when the text before any colon on the line reads as a reserved label."""
    return any(_letters(label) in _RESERVED_LABELS for label in line.split(b":")[:-1])


def _usable_value(value):
    return bool(value) and value[:1] != b" " and value[-1:] != b" " and _only(value, _PRINTABLE_BYTES)


class _Block:
    def __init__(self, line):
        self.line = line
        self.seen = set()
        self.fields = {}
        self.lines = {}
        self.commands = []
        self.command_lines = 0

    def add(self, number, line, findings):
        key, separator, value = line.partition(b": ")
        if not separator:
            findings.append(_finding("form", number))
            return
        name = _KEYS.get(key)
        if name is None:
            findings.append(_finding("action-block.unknown-key", number))
            return
        usable = _usable_value(value)
        if not usable:
            findings.append(_finding("value", number))
        if name in self.seen:
            findings.append(_finding("duplicate-key", number))
        self.command_lines += name == "command"
        if usable and name == "command":
            # Every command line is checked, including a repeated one.
            self.commands.append((number, value))
        if usable and name not in self.seen:
            self.fields[name] = value.decode("ascii")
            self.lines[name] = number
        self.seen.add(name)

    def close(self, findings, ids):
        if not self.seen.issuperset(REQUIRED_KEYS):
            findings.append(_finding("action-block.missing-required", self.line))
        action_id = self.fields.get("id")
        if action_id is not None:
            encoded = action_id.encode("ascii")
            if len(encoded) > MAX_ID_BYTES or not _only(encoded, _ID_BYTES):
                findings.append(_finding("action-block.id.invalid", self.line))
            elif action_id in ids:
                findings.append(_finding("action-block.duplicate-id", self.line))
            else:
                ids.add(action_id)
        approval_required = self.fields.get("approval") == "required"
        argv = None
        for number, value in self.commands:
            found, argv = _check_command(value, approval_required)
            findings.extend(_finding(finding_id, number) for finding_id in found)
        if self.command_lines != 1:
            argv = None
        return Action(self.line, self.fields, argv)


def _scan(data):
    """One pass over the lines. Work per line is proportional to its length."""
    findings, actions, ids, metadata = [], [], set(), []
    state, block, first_action = _OUTSIDE, None, None
    metadata_blocks, metadata_broken = 0, False
    profile_labels = version_labels = profile_exact = version_exact = 0
    bytes_clean = True
    for number, line in enumerate(_lines(data), 1):
        if bytes_clean and not _only(line, _PRINTABLE_BYTES):
            # Reported once, at the first line that has such a byte.
            bytes_clean = False
            findings.append(_finding("byte-profile.non-ascii-byte", number))
        if line == _ACTION_OPEN:
            if first_action is None:
                first_action = number
            if state == _OUTSIDE:
                state, block = _IN_ACTION, _Block(number)
            else:
                findings.append(_finding("nested", number))
        elif line == _ACTION_CLOSE:
            if state == _IN_ACTION:
                actions.append(block.close(findings, ids))
                state, block = _OUTSIDE, None
            else:
                findings.append(_finding("orphan", number))
        elif line == _METADATA_OPEN:
            if state == _OUTSIDE:
                state = _IN_METADATA
                metadata_blocks += 1
            else:
                metadata_broken = True
        elif line == _METADATA_CLOSE:
            if state == _IN_METADATA:
                state = _OUTSIDE
            else:
                metadata_broken = True
        else:
            squeezed = _squeeze(line)
            if b"assistant-guide-metadata" in squeezed:
                # Released dispatchers read padded and case-variant metadata
                # fences. Bytes that carry one have no single declaration.
                metadata_broken = True
            if state == _IN_METADATA:
                # Count selectors loosely, on every line, so a near-duplicate
                # is a conflict; then require the exact line.
                label = _letters(line.partition(b":")[0])
                profile_labels += label == b"profile"
                version_labels += label == b"profileversion"
                profile_exact += line == _PROFILE_LINE
                version_exact += line == _VERSION_LINE
                metadata.append((number, line))
            if _has_marker_text(squeezed):
                findings.append(_finding("marker", number))
            elif state == _IN_ACTION:
                block.add(number, line, findings)
            elif _has_reserved_label(line):
                findings.append(_finding("action-block.field-outside-block", number))
    if state == _IN_ACTION:
        findings.append(_finding("unclosed", block.line))
        actions.append(block.close(findings, ids))
    selected = (
        metadata_blocks == 1 and not metadata_broken and state != _IN_METADATA
        and profile_labels == profile_exact == 1 and version_labels == version_exact == 1
    )
    return _Scan(findings, actions, selected, metadata, first_action)


def check_structure(data: bytes) -> StructureReport:
    """Check action structure and command grammar for bytes that declare 3.0.0.

    Raises NotSelected for anything else. Input over the size cap is refused
    before the declaration is read, so the refusal does not depend on it and
    this function must not be used to probe which profile a guide declares.
    """
    data = bytes(data)
    if len(data) > MAX_GUIDE_BYTES:
        return StructureReport((_finding("byte-profile.size-limit"),), ())
    scan = _scan(data)
    if not scan.selected:
        raise NotSelected("guide bytes do not declare profile 3.0.0 exactly once in an exact metadata block")
    return StructureReport(tuple(scan.findings), tuple(scan.actions))


# --- shape registry ---------------------------------------------------------

def _slot_matches(kind, token):
    if kind == "local-ref":
        return _is_local_path(token)
    if kind == "https-url":
        return is_url(token)
    if kind == "word":
        return _only(token, _SEGMENT_BYTES) and token[:1] not in (b"-", b".", b"")
    return kind == "number" and bool(token) and _only(token, _DIGITS)


def _positions_overlap(left, right):
    if isinstance(left, str) and isinstance(right, str):
        return left == right
    if isinstance(left, str):
        return _slot_matches(right["slot"], left.encode("ascii"))
    if isinstance(right, str):
        return _slot_matches(left["slot"], right.encode("ascii"))
    return left["slot"] == right["slot"] or {left["slot"], right["slot"]} == {"word", "number"}


def _registry_problem(entries):
    """The first rule between entries or positions that the registry breaks, or None."""
    seen = set()
    for entry in entries:
        argv = entry["argv"]
        if entry["id"] in seen or not argv or not isinstance(argv[0], str):
            return "an entry id repeats, or a program position is not a literal"
        seen.add(entry["id"])
        literals = [element.encode("ascii") for element in argv if isinstance(element, str)]
        if not _is_program(literals[0]) or any(
            not token or not _only(token, _ARGUMENT_BYTES) or _has_parent_component(token) for token in literals
        ):
            return "a literal is outside the command grammar"
        slot = entry.get("pin", {}).get("slot")
        if slot is not None and not (0 < slot < len(argv) and argv[slot] == {"slot": "local-ref"}):
            return "a pin names a position that is not a local-ref slot"
        if (entry["execution"] == "bound") != ("pin" in entry) or not set(entry["class-floor"]) <= set(CLASSES):
            return "an entry has the wrong pin or an unknown class"
    for index, first in enumerate(entries):
        for second in entries[index + 1:]:
            if len(first["argv"]) == len(second["argv"]) and all(
                _positions_overlap(left, right) for left, right in zip(first["argv"], second["argv"])
            ):
                return "two entries can match the same argument vector"
    return None


def load_registry(path=None):
    """Load and check the shape registry. Raises RegistryError when it cannot be used."""
    raw = Path(path or REGISTRY_PATH).read_bytes()
    try:
        document = json.loads(raw.decode("ascii"))
        entries = document["entries"]
        if document["profile-version"] != PROFILE_VERSION:
            raise RegistryError("registry is for another profile version")
        problem = _registry_problem(entries)
    except (ValueError, KeyError, TypeError, AttributeError) as error:
        if isinstance(error, RegistryError):
            raise
        raise RegistryError("registry is not in the documented form") from None
    if problem:
        raise RegistryError(problem)
    return Registry(tuple(entries), hashlib.sha256(raw).hexdigest())


def match_shape(argv, registry):
    """The one registry entry the whole argument vector matches, or None."""
    tokens = [token.encode("ascii") for token in argv]
    for entry in registry.entries:
        shape = entry["argv"]
        if len(shape) == len(tokens) and all(
            (element == token.decode("ascii")) if isinstance(element, str) else _slot_matches(element["slot"], token)
            for element, token in zip(shape, tokens)
        ):
            return entry
    return None


# --- field grammars ----------------------------------------------------------

def _split_list(value):
    """Split at comma-space. None when an item is empty, repeats, or has an edge space."""
    items = value.split(", ")
    if any(not item or item != item.replace(" ", "") for item in items) or len(set(items)) != len(items):
        return None
    return items


def _is_host_pattern(pattern):
    labels = (pattern[2:] if pattern.startswith("*.") else pattern).encode("ascii").split(b".")
    return len(labels) >= 2 and all(_is_label(label) for label in labels)


def _is_cwd(value):
    if value == ".":
        return True
    segments = value[1:].split("/") if value.startswith("/") else value.split("/")
    return all(segment and segment != ".." and _only(segment.encode("ascii"), _SEGMENT_BYTES) for segment in segments)


def _is_env_name(name):
    encoded = name.encode("ascii")
    return bool(encoded) and encoded[:1] not in _DIGITS and _only(encoded, _ALNUM + b"_") and encoded[:1] != b""


def _is_param_name(name):
    return 2 <= len(name) <= 32 and _only(name.encode("ascii"), _UPPER + _DIGITS + b"_")


def _local_references(argv):
    """Each token, or text after the first `=` of a token, that begins with `./`."""
    references = []
    for token in argv:
        for candidate in (token, token.partition("=")[2]):
            if candidate.startswith("./"):
                references.append(candidate)
                break
    return references


def _check_action(action, registry, add):
    """Field values, tier and pins for one action. Returns the action with its tier set."""
    fields, line = action.fields, action.line
    classes = _split_list(fields["class"]) if "class" in fields else None
    if "class" in fields and (classes is None or not set(classes) <= set(CLASSES)):
        add("action-block.class.invalid", line)
        classes = None
    if classes and "normal" in classes and len(classes) > 1:
        add("action-block.class.normal-mixed", line)
    declared = set(classes or ())
    approval = fields.get("approval")
    if approval is not None and approval not in ("required", "not-required"):
        add("action-block.approval.invalid", line)
    if "runner" in fields and fields["runner"] != "argv":
        add("action-block.runner.invalid", line)
    if declared & APPROVAL_CLASSES and approval != "required":
        add("approval.required-missing", line)
    if "cwd" in fields and (not _is_cwd(fields["cwd"]) or (fields["cwd"].startswith("/") and approval != "required")):
        add("filesystem.cwd.invalid", line)
    if "egress" in fields:
        hosts = [] if fields["egress"] == "none" else _split_list(fields["egress"])
        if hosts is None or not all(_is_host_pattern(host) for host in hosts):
            add("egress.pattern", line)
        elif "networked" in declared and not hosts:
            add("egress.missing", line)
        elif classes is not None and "networked" not in declared and hosts:
            add("egress.class-mismatch", line)
    if "env" in fields:
        names = _split_list(fields["env"])
        if names is None or not all(_is_env_name(name) for name in names):
            add("env.invalid", line)
    params = None
    if "params" in fields:
        params = _split_list(fields["params"])
        tokens = set(action.argv or ()) | {token.partition("=")[2] for token in action.argv or ()}
        if (params is None or not all(_is_param_name(name) for name in params)
                or (action.argv is not None and (not set(params) <= tokens or action.argv[0] in params))):
            add("params.invalid", line)
    pin = fields.get("exec-sha256")
    if pin is not None and not (len(pin) == 64 and _only(pin.encode("ascii"), _HEX_BYTES)):
        add("pin-form", line)
        pin = None
    opaque_ack = fields.get("exec-opaque")
    if opaque_ack is not None and opaque_ack != "acknowledged":
        add("value", line)

    entry = match_shape(action.argv, registry) if action.argv is not None and params is None and "params" not in fields else None
    needs_pin = 0
    if entry is not None:
        # A floor of `normal` requires nothing: `normal` excludes every other class.
        if classes is not None and not set(entry["class-floor"]) - {"normal"} <= declared:
            add("action-block.class.under-declared", line)
        if "exec-opaque" in fields:
            add("opaque-on-listed", line)
        needs_pin += entry["execution"] == "bound"
    else:
        add("action.program-opaque", line, "warning")
        if classes is not None and "code-executing" not in declared:
            add("action-block.class.under-declared", line)
        if approval != "required" and not declared & APPROVAL_CLASSES:
            add("approval.required-missing", line)
        if opaque_ack != "acknowledged" or "notes" not in fields:
            add("action.program-opaque.unacknowledged", line)
    if action.argv is not None:
        references = _local_references(action.argv)
        program_is_local = action.argv[0].startswith("./")
        code_executing = "code-executing" in declared or entry is None
        if entry is None or entry["execution"] != "bound" or "slot" not in entry.get("pin", {}):
            needs_pin += len(references) if code_executing else int(program_is_local)
        if needs_pin > 1 or (needs_pin == 1 and pin is None):
            add("command.local-ref.unpinned", line)
        elif needs_pin == 0 and "exec-sha256" in fields:
            add("action.exec-target-unresolved", line)
        elif needs_pin == 1:
            add("exec-sha256.unverified", line, "info")
    return Action(action.line, fields, action.argv, "shape-listed" if entry else "opaque", entry["id"] if entry else None)


# --- document checks -----------------------------------------------------------

def _parse_date(value):
    parts = value.split("-")
    if len(parts) != 3 or [len(part) for part in parts] != [4, 2, 2] or not all(_only(p.encode("ascii"), _DIGITS) for p in parts):
        return None
    try:
        return date(int(parts[0]), int(parts[1]), int(parts[2]))
    except ValueError:
        return None


def _check_metadata(scan, today, add):
    """Exact metadata parse. Returns the fields that were well formed."""
    values, lines = {}, {}
    for number, line in scan.metadata:
        key, separator, value = line.partition(b": ")
        if not separator or not key or not _only(key, _KEY_BYTES) or not _usable_value(value) or key.decode("ascii") in values:
            add("metadata.malformed", number)
            continue
        name = key.decode("ascii")
        values[name], lines[name] = value.decode("ascii"), number
        if name in CHAIN_FIELDS:
            add("prohibited.next-guide-field", number)
    for name in REQUIRED_METADATA:
        if name not in values:
            add("metadata.missing-required")
    for name in URL_FIELDS:
        if name in values and not is_url(values[name]):
            add("metadata.url.invalid", lines[name])
            del values[name]
    for name, value in values.items():
        if name not in URL_FIELDS and len(value) > LONG_VALUE_BYTES:
            add("metadata.value.long", lines[name], "warning")
    status = values.get("status", "active")
    if status not in ("active", "deprecated", "revoked"):
        add("metadata.status.invalid", lines["status"])
        status = "active"
    elif status != "active":
        add(f"metadata.status.{status}", lines["status"])
        if "superseded-by" not in values:
            add("metadata.superseded-by.missing", lines["status"], "warning")
    if "last-reviewed" in values:
        reviewed = _parse_date(values["last-reviewed"])
        if reviewed is None:
            add("metadata.last-reviewed.invalid", lines["last-reviewed"], "warning")
        elif reviewed > today:
            add("metadata.last-reviewed.future", lines["last-reviewed"], "warning")
        else:
            add("metadata.last-reviewed.age", lines["last-reviewed"], "info", {"days": (today - reviewed).days})
    if "valid-until" in values:
        until = _parse_date(values["valid-until"])
        if until is None:
            add("metadata.valid-until.invalid", lines["valid-until"], "warning")
        elif until < today:
            add("metadata.valid-until.expired", lines["valid-until"], "warning")
    verifier, canonical = values.get("recommended-verifier"), values.get("canonical-url")
    if verifier and canonical and verifier != STANDARD_PRIMARY_VERIFIER and _url_host(verifier) != _url_host(canonical):
        add("metadata.recommended-verifier.off-domain", lines["recommended-verifier"], "warning")
    return values, status


def _check_document(lines, scan, add):
    """Limits, constructs, headings and the canonical instruction. One pass."""
    if len(lines) > MAX_LINES:
        add("byte-profile.line-count", MAX_LINES + 1, evidence={"count": len(lines), "limit": MAX_LINES})
    headings = {name: 0 for name in SECTIONS}
    reported = set()
    instruction_line = None
    for number, line in enumerate(lines, 1):
        if len(line) > MAX_LINE_BYTES and "length" not in reported:
            reported.add("length")
            add("byte-profile.line-length", number, evidence={"bytes": len(line), "limit": MAX_LINE_BYTES})
        if b"```" in line or b"~~~" in line:
            add("construct.code-fence", number)
        lowered = line.lower()
        position = line.find(b"<")
        while position != -1:
            following = line[position + 1:position + 2]
            if following and (following in b"/!?" or _only(following, _UPPER + _LOWER)):
                add("construct.html", number)
                break
            position = line.find(b"<", position + 1)
        if b"![" in line:
            add("construct.markdown-image", number)
        if b";base64," in lowered or any(b"data:" + kind in lowered for kind in (b"text/", b"image/", b"application/")):
            add("construct.data-url", number)
        if b"javascript:" in lowered:
            add("construct.javascript", number)
        for prefix in _HEADING_PREFIXES:
            name = line[len(prefix):] if line.startswith(prefix) else None
            if name in headings:
                headings[name] += 1
                break
        if line == INSTRUCTION[0] and instruction_line is None and tuple(lines[number - 1:number + 2]) == INSTRUCTION:
            instruction_line = number
    for name, count in headings.items():
        if count != 1:
            add(SECTIONS[name])
    if instruction_line is None or (scan.first_action_line is not None and scan.first_action_line < instruction_line):
        add("verification-instruction.missing")
    if not lines or not lines[0].startswith(_TITLE_PREFIX) or len(lines[0]) == len(_TITLE_PREFIX):
        add("content.required.title", 1)
    if not scan.actions:
        add("content.required.actions")


def _check_manifest(data, manifest_text, add):
    """Text form, required fields, selectors and the hash and byte count. Returns the report object."""
    fields, seen = {}, set()
    valid = True
    lines = manifest_text.encode("utf-8", errors="replace").split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()
    for line in lines:
        if line == b"":
            continue
        key, separator, value = line.partition(b": ")
        if not separator or not key or not _only(key, _KEY_BYTES) or not _usable_value(value) or key in seen:
            add("manifest.malformed")
            valid = False
            continue
        seen.add(key)
        fields[key.decode("ascii")] = value.decode("ascii")
    for name in MANIFEST_REQUIRED:
        if name not in fields:
            add("manifest.missing-required")
            valid = False
    if fields.get("profile") != PROFILE_NAME or fields.get("profile-version") != PROFILE_VERSION:
        add("manifest.profile-version.mismatch")
        valid = False
    declared_hash = fields.get("guide-sha256", "")
    hash_ok = len(declared_hash) == 64 and _only(declared_hash.encode("ascii"), _HEX_BYTES)
    if "guide-sha256" in fields and not hash_ok:
        add("manifest.hash-invalid")
        valid = False
    count = fields.get("guide-bytes", "")
    count_ok = bool(count) and _only(count.encode("ascii"), _DIGITS) and count[0] != "0"
    if "guide-bytes" in fields and not count_ok:
        add("manifest.bytes-invalid")
        valid = False
    for name in ("immutable-release-url", "transparency-log-url", "canonical-url", "repository-url", "changelog-url"):
        if name in fields and not is_url(fields[name]):
            add("manifest.malformed")
            valid = False
    result = {"valid": valid, "sha256": hashlib.sha256(manifest_text.encode("utf-8", errors="replace")).hexdigest()}
    if hash_ok:
        result["guide_sha256"] = declared_hash
        result["hash_match"] = declared_hash == hashlib.sha256(data).hexdigest()
        if not result["hash_match"]:
            add("manifest.hash-mismatch")
    if count_ok:
        result["bytes_match"] = int(count) == len(data)
        if not result["bytes_match"]:
            add("manifest.bytes-mismatch")
    result["valid"] = valid and result.get("hash_match", False) and result.get("bytes_match", False)
    return result


def _check_anchors(anchor_texts, manifest, evidence_fetched, add):
    """The 1.0.0 strict anchor policy, unchanged: a repository file never qualifies."""
    import guidecheck_legacy as legacy  # anchor text formats are shared with the released engines

    anchors = []
    expected = (manifest or {}).get("guide_sha256")
    for channel, text in sorted(anchor_texts.items()):
        if channel not in ANCHOR_CHANNELS:
            add("anchor.channel.unsupported", None, "warning")
            continue
        try:
            observed = legacy.extract_anchor_sha256(channel, text)
        except (RecursionError, ValueError, TypeError):
            observed = None
        if observed is not None and not (len(observed) == 64 and _only(observed.encode("ascii", errors="replace"), _HEX_BYTES)):
            observed = None
        status = "absent" if observed is None else "present-matches" if observed == expected else "present-mismatch"
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
        anchor = {"channel": channel, "status": status, "qualifies_for_level4": reason == "qualifying-channel",
                  "qualification_reason": reason}
        if observed is not None:
            anchor["observed_sha256"] = observed
        if channel == "repository-file":
            anchor["independence"] = "unestablished"
            if observed is not None:
                add("anchor.repository-file.independence-unestablished", None, "warning")
        if status == "present-mismatch":
            add("anchor.repository-file.mismatch" if channel == "repository-file" else "anchor.independent.mismatch")
        anchors.append(anchor)
    return anchors


def evaluate(data, *, registry=None, manifest_text=None, anchor_texts=None, evidence_fetched=False, now=None):
    """Evaluate guide bytes that declare 3.0.0. Raises NotSelected for anything else.

    Every check is linear in the size of the guide, and nothing but the size
    is examined when the guide is over the limit.
    """
    data = bytes(data)
    now = now or datetime.now(timezone.utc)
    result = Evaluation(hashlib.sha256(data).hexdigest(), len(data), evidence_fetched=evidence_fetched, evaluated_at=now)
    if len(data) > MAX_GUIDE_BYTES:
        result.findings.append(_finding("byte-profile.size-limit", evidence={"bytes": len(data), "limit": MAX_GUIDE_BYTES}))
        return result
    scan = _scan(data)
    if not scan.selected:
        raise NotSelected("guide bytes do not declare profile 3.0.0 exactly once in an exact metadata block")
    registry = registry or load_registry()
    findings = result.findings = list(scan.findings)

    def add(finding_id, line=None, severity="error", evidence=None):
        findings.append(_finding(finding_id, line, severity, evidence))

    lines = _lines(data)
    _check_document(lines, scan, add)
    metadata, result.status = _check_metadata(scan, now.date(), add)
    result.canonical_url = metadata.get("canonical-url")
    if result.status != "active":
        result.superseded_by = metadata.get("superseded-by")
    result.actions = tuple(_check_action(action, registry, add) for action in scan.actions)
    if result.actions:
        result.registry_sha256 = registry.sha256
    if sum(action.fields.get("approval") == "required" for action in result.actions) > APPROVAL_WARNING_THRESHOLD:
        add("approval.required.too-many", None, "warning")

    claims_level4 = "manifest-url" in metadata
    if manifest_text is not None:
        result.manifest = _check_manifest(data, manifest_text, add)
        result.manifest["fetched"] = evidence_fetched
    result.anchors = _check_anchors(anchor_texts or {}, result.manifest, evidence_fetched, add)
    qualifying = any(anchor["qualifies_for_level4"] for anchor in result.anchors)
    if claims_level4 and not evidence_fetched:
        add("level4.requires-fetch", None, "info")
    elif claims_level4 and not qualifying and not any(a["status"] == "present-mismatch" for a in result.anchors):
        add("anchor.independent.missing")

    errors = {finding.id for finding in findings if finding.severity == "error"}
    content_errors = {finding_id for finding_id in errors if not finding_id.startswith(_LEVEL4_PREFIXES)}
    level1 = (not errors & _LEVEL1_IDS and "canonical-url" in metadata and "repository-url" in metadata)
    level2 = level1 and not any(i.startswith(_LEVEL2_PREFIXES) and i != "construct.code-fence" for i in errors)
    level3 = level2 and not content_errors and bool(result.actions) and result.status == "active"
    level4 = (level3 and evidence_fetched and claims_level4 and qualifying and bool(result.manifest)
              and result.manifest["valid"] and not errors)
    result.achieved_level = 4 if level4 else 3 if level3 else 2 if level2 else 1 if level1 else 0
    if result.status == "revoked":
        result.achieved_level = min(result.achieved_level, 1)
    elif result.status == "deprecated":
        result.achieved_level = min(result.achieved_level, 2)
    result.level5_ready = result.achieved_level == 4 and all(
        action.fields.get("approval") == "required" for action in result.actions
        if set(_split_list(action.fields.get("class", "")) or ()) - {"normal"}
    )
    return result


def _path_token(path):
    """A caller-supplied path with every byte outside a narrow set replaced by an underscore."""
    encoded = str(path).encode("utf-8", errors="replace")
    keep = _ALNUM + b"._/+@-"
    return bytes(byte if byte in keep else 0x5F for byte in encoded)[:300].decode("ascii") or "_"


def build_report(evaluation, *, verifier_name, verifier_version, path=None, required_level=None, fetch=None):
    """Machine-readable output for a 3.0.0 evaluation, in the shape of schemas/3.0.0/verifier-output.schema.json."""
    from profile_3_0_0_invariants import expected_verdict, render_compact_report

    findings = [finding.as_dict() for finding in evaluation.findings]
    guide = {"bytes": evaluation.guide_bytes, "sha256": evaluation.sha256, "achieved_level": evaluation.achieved_level,
             "status": evaluation.status, "level5_ready": evaluation.level5_ready}
    if evaluation.canonical_url:
        guide["canonical_url"] = evaluation.canonical_url
    if evaluation.superseded_by:
        guide["superseded_by"] = evaluation.superseded_by
    report = {
        "verifier": {"name": verifier_name, "version": verifier_version,
                     "verifier_profile": "human-verifiable-assistant-guide-verifier",
                     "verifier_profile_version": PROFILE_VERSION,
                     "guide_profile": PROFILE_NAME, "guide_profile_version": PROFILE_VERSION},
        "input": {"evaluation_mode": "public-web" if fetch else "local-file", "repository_read": False},
        "evaluated_at": evaluation.evaluated_at.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "guide": guide,
        "actions": {"total": len(evaluation.actions),
                    "shape_listed": sum(action.tier == "shape-listed" for action in evaluation.actions),
                    "opaque": sum(action.tier == "opaque" for action in evaluation.actions)},
        "summary": {key: sum(finding["severity"] == severity for finding in findings)
                    for severity, key in (("error", "blocking_findings"), ("warning", "warnings"), ("info", "infos"))},
        "findings": findings,
        "profile_selection": {"declared_version": PROFILE_VERSION, "evaluated_policy": PROFILE_VERSION,
                              "content_policy": CONTENT_POLICY, "anchor_policy": ANCHOR_POLICY},
        "qualifying_anchor_count": sum(anchor["qualifies_for_level4"] for anchor in evaluation.anchors),
    }
    if fetch:
        report["fetch"] = fetch
    else:
        report["input"]["path"] = _path_token(path if path is not None else "guide")
    if required_level is not None:
        report["input"]["required_level"] = required_level
    if evaluation.registry_sha256:
        report["shape_registry_sha256"] = evaluation.registry_sha256
    if evaluation.manifest is not None:
        report["manifest"] = evaluation.manifest
    if evaluation.anchors:
        report["cross_channel_anchors"] = evaluation.anchors
    report["verdict"] = expected_verdict(report)
    report["compact_report"] = render_compact_report(report)
    return report
