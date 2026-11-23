"""restricted-argv-1: structure slice of an opt-in content policy for guide profile 3.0.0.

Status: unreleased and partial. No released entry point imports this module,
and the public dispatcher in `guidecheck_profiles.py` still refuses 3.0.0 as
unsupported. Nothing here changes how a released profile is evaluated.

This slice answers one question about guide bytes that declare 3.0.0: which
lines are action blocks, and is each `command` inside the grammar. It awards
no level and prints no verdict, so a result from it is never a pass.

Implemented:

- Size gate. Input over 8192 bytes is refused with one finding before any
  other byte is examined.
- One line splitter. Lines end at LF and nowhere else. Any byte other than
  LF and printable ASCII is blocking, because a reader may show it as a line
  break or use it to hide or overwrite text, and every rule below is stated
  over lines.
- Exact fences. `[action]` and `[/action]` open and close a block only as
  whole lines. The marker text is reserved: a line that contains it in any
  other form is blocking.
- Reserved field labels. A line on which the text before any colon reads,
  letters only, as `id`, `class`, `approval` or `command` is blocking outside
  an exact action block, whatever surrounds it.
- Fixed key list inside a block, each key at most once, one `key: value`
  form, printable ASCII values with no leading or trailing space, and the
  seven required keys.
- Action `id` grammar and uniqueness by exact bytes.
- Command grammar: an allowlist of bytes, one tokenizer (split on single
  spaces), a program that is a bare name or a `./` path, no `..` component
  between any two separators or at the end of an attached option value, and
  no absolute path without `approval: required`.

Not implemented, and therefore not checked by this module: program tiers and
the shape registry, pins, parameters, value grammars
for `class`, `approval`, `runner`, `cwd`, `egress` and `env`, required
sections, the verification instruction, prose scans, line length and line
count, disallowed constructs, metadata values, manifests, anchors, levels and
the verdict line.

Findings locate a problem by line number only. No guide-authored text is
copied into a message or into evidence.
"""
from dataclasses import dataclass

from guidecheck_legacy import Finding

PROFILE_NAME = "human-verifiable-assistant-guide"
PROFILE_VERSION = "3.0.0"
CONTENT_POLICY = "restricted-argv-1"
MAX_GUIDE_BYTES = 8192
MAX_ID_BYTES = 32

_ACTION_OPEN = b"[action]"
_ACTION_CLOSE = b"[/action]"
_METADATA_OPEN = b"[assistant-guide-metadata]"
_METADATA_CLOSE = b"[/assistant-guide-metadata]"
_PROFILE_LINE = b"profile: " + PROFILE_NAME.encode("ascii")
_VERSION_LINE = b"profile-version: " + PROFILE_VERSION.encode("ascii")

REQUIRED_KEYS = ("id", "class", "approval", "command", "runner", "cwd", "egress")
OPTIONAL_KEYS = ("notes", "env", "params", "exec-sha256", "exec-opaque")
_KEYS = {key.encode("ascii"): key for key in REQUIRED_KEYS + OPTIONAL_KEYS}
# Labels that identify an action. Outside an exact block they are reserved.
_RESERVED_LABELS = frozenset({b"id", b"class", b"approval", b"command"})
# Marker text, looked for after lowercasing and removing spaces and tabs.
_RESERVED_MARKERS = tuple(
    opener + slash + b"action" for opener in (b"[", b"<", b"{") for slash in (b"", b"/")
)

_ALNUM = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
_ID_BYTES = _ALNUM + b"-"
_SEGMENT_BYTES = _ALNUM + b"-_.+"
_SEPARATOR_BYTES = b"/:=@,"
_ARGUMENT_BYTES = _SEGMENT_BYTES + _SEPARATOR_BYTES
_PRINTABLE_BYTES = bytes(range(0x20, 0x7F))
_NOT_LOWERCASE = bytes(byte for byte in range(256) if not 0x61 <= byte <= 0x7A)
_SEPARATORS_TO_SLASH = bytes.maketrans(_SEPARATOR_BYTES, b"/" * len(_SEPARATOR_BYTES))

_OUTSIDE, _IN_METADATA, _IN_ACTION = range(3)

_MESSAGES = {
    "byte-profile.size-limit": "guide exceeds 8192 bytes and was not examined",
    "byte-profile.non-ascii-byte": "guide contains a byte other than LF and printable ASCII",
    "marker": "action marker text appears outside an exact marker line",
    "nested": "action block opened inside another block",
    "orphan": "action block closed where none is open",
    "unclosed": "action block is not closed",
    "form": "line inside an action block is not in the form key, colon, one space, value",
    "value": "action value is empty, has a leading or trailing space, or has a byte outside printable ASCII",
    "duplicate-key": "action key appears more than once in one block",
    "action-block.unknown-key": "action key is not in the fixed key list",
    "action-block.missing-required": "action block lacks a required key",
    "action-block.field-outside-block": "action field label appears outside an exact action block",
    "action-block.id.invalid": "action id is not 1 to 32 letters, digits or hyphens",
    "action-block.duplicate-id": "action id repeats an earlier action id",
    "command.grammar": "command is outside the restricted argv grammar",
    "command.path.escape": "command contains a parent-directory component",
    "command.path.absolute": "command contains an absolute path and the action does not require approval",
}
_MALFORMED = ("marker", "nested", "orphan", "unclosed", "form", "value", "duplicate-key")


class NotSelected(ValueError):
    """The guide bytes do not declare this profile exactly once in an exact metadata block."""


@dataclass(frozen=True)
class Action:
    """One exact action block. `argv` is None unless exactly one command is in the grammar."""

    line: int
    fields: dict
    argv: tuple | None


@dataclass(frozen=True)
class StructureReport:
    findings: tuple
    actions: tuple


@dataclass
class _Scan:
    findings: list
    actions: list
    selected: bool


def _finding(rule, line=None):
    finding_id = "action-block.malformed" if rule in _MALFORMED else rule
    return Finding(finding_id, "error", _MESSAGES[rule], line=line)


def _only(value, allowed):
    """True when every byte of `value` is in `allowed`. One pass."""
    return not value.translate(None, allowed)


def _is_program(token):
    if _only(token, _SEGMENT_BYTES):
        return True
    if not token.startswith(b"./"):
        return False
    return all(segment and _only(segment, _SEGMENT_BYTES) for segment in token[2:].split(b"/"))


def _has_parent_component(token):
    """True for a `..` component, including one attached to an option, as in `-C..`."""
    return any(
        piece.endswith(b"..") and not piece.endswith(b"...")
        for piece in token.translate(_SEPARATORS_TO_SLASH).split(b"/")
    )


def _check_command(value, approval_required):
    """Return (finding ids, argv). The tokenizer is one split on single spaces."""
    tokens = value.split(b" ")
    if not all(token and _only(token, _ARGUMENT_BYTES) for token in tokens) or not _is_program(tokens[0]):
        return ("command.grammar",), None
    found = []
    if any(_has_parent_component(token) for token in tokens):
        found.append("command.path.escape")
    if not approval_required and any(
        token.startswith(b"/") or token.partition(b"=")[2].startswith(b"/") for token in tokens
    ):
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


class _Block:
    def __init__(self, line):
        self.line = line
        self.seen = set()
        self.fields = {}
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
        usable = bool(value) and value[:1] != b" " and value[-1:] != b" " and _only(value, _PRINTABLE_BYTES)
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
    findings, actions, ids = [], [], set()
    state, block = _OUTSIDE, None
    metadata_blocks, metadata_broken = 0, False
    profile_labels = version_labels = profile_exact = version_exact = 0
    bytes_clean = True
    for number, line in enumerate(_lines(data), 1):
        if bytes_clean and not _only(line, _PRINTABLE_BYTES):
            # Reported once, at the first line that has such a byte.
            bytes_clean = False
            findings.append(_finding("byte-profile.non-ascii-byte", number))
        if line == _ACTION_OPEN:
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
    return _Scan(findings, actions, selected)


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
