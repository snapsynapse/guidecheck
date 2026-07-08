#!/usr/bin/env python3
"""
GuideCheck instruction-surface scanner (adoption roadmap steps 1 and 2).

Scans instruction artifacts people already publish (AGENTS.md, CLAUDE.md,
README install sections, skill files, MCP tool descriptions saved as text)
for hidden-instruction channels:

- HTML comments carrying instruction-like text   -> surface.hidden-html-comment
- invisible Unicode (zero-width, bidi controls,
  tag characters)                                -> surface.invisible-unicode.*
- CSS-hidden text in embedded HTML               -> surface.css-hidden-text
- ESC-based escape sequences                     -> surface.ansi-escape

Detection favors precision over recall: comment and CSS-hidden findings are
gated on instruction-likeness so benign authoring notes never flag. A scan
must deliver value at zero ecosystem adoption of assistant-guide.txt, so the
scanner accepts any file, a directory (known instruction-surface filenames
inside), or an https URL (bare origins probe common surface paths).

Standard library only. URL mode reuses the SSRF-hardened fetch controls in
scripts/guidecheck_fetch.py. Exercised by scripts/test_scanner.py.
"""

from __future__ import annotations

import argparse
import bisect
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

import guidecheck_fetch as gf
from guidecheck_constants import GUIDECHECK_VERSION

SCANNER_NAME = "guidecheck-scanner"
SCAN_PROFILE = "instruction-surface-scan"

# Known instruction-surface filenames matched (case-insensitively) in
# directory mode. *.skill.md is matched by suffix.
SURFACE_FILENAMES = {
    "agents.md",
    "claude.md",
    "readme.md",
    "skill.md",
    "assistant-guide.txt",
}
SURFACE_SUFFIX = ".skill.md"

# Paths probed when the target URL is a bare origin.
ORIGIN_PROBE_PATHS = (
    "/assistant-guide.txt",
    "/.well-known/assistant-guide.txt",
    "/llms.txt",
    "/AGENTS.md",
    "/CLAUDE.md",
    "/README.md",
)

SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".tox",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    "build",
    "dist",
    "vendor",
}

MAX_LOCAL_BYTES = 2 * 1024 * 1024
EVIDENCE_MARGIN = 40
EVIDENCE_MAX = 160

# Invisible codepoint classes (kept deliberately narrow; under-flagging is
# preferred over false positives).
ZERO_WIDTH_CODEPOINTS = {0x200B, 0x200C, 0x200D, 0xFEFF}
BIDI_CONTROL_CODEPOINTS = set(range(0x202A, 0x202F)) | set(range(0x2066, 0x206A))
TAG_BLOCK = (0xE0000, 0xE007F)
VARIATION_SELECTORS = set(range(0xFE00, 0xFE10))

# Instruction-likeness gate. A strong pattern alone is enough; a weak verb
# needs command-shaped evidence alongside it. This keeps benign authoring
# notes (<!-- TODO: tidy this section -->) out of the findings.
STRONG_INSTRUCTION_RE = re.compile(
    r"\b(?:curl|wget|chmod|chown|sudo|eval|execute|export|disregard)\b"
    r"|\bignore\s+(?:all\s+|any\s+)?(?:previous|prior|earlier|above)\b"
    r"|\|\s*(?:sh|bash|zsh|python3?)\b",
    re.IGNORECASE,
)
WEAK_INSTRUCTION_RE = re.compile(
    r"\b(?:run|install|download|fetch|pipe|source)\b",
    re.IGNORECASE,
)
COMMAND_EVIDENCE_RE = re.compile(
    r"`[^`]+`"
    r"|https?://"
    r"|\$\s?[A-Za-z(./~]"
    r"|\b(?:pip3?|npm|npx|uvx?|brew|apt(?:-get)?|make|git\s+clone|bash|sh)\b",
    re.IGNORECASE,
)

HTML_COMMENT_RE = re.compile(r"<!--(.*?)-->", re.DOTALL)

STYLED_ELEMENT_RE = re.compile(
    r"<(?P<tag>[a-zA-Z][a-zA-Z0-9-]*)\b[^>]*?\bstyle\s*=\s*(?P<q>[\"'])"
    r"(?P<style>.*?)(?P=q)[^>]*>(?P<body>.*?)</(?P=tag)\s*>",
    re.DOTALL | re.IGNORECASE,
)
CSS_HIDDEN_PROPERTY_RE = re.compile(
    r"display\s*:\s*none"
    r"|visibility\s*:\s*hidden"
    r"|font-size\s*:\s*0(?:px|pt|em|rem|%)?\s*(?:;|$)"
    r"|opacity\s*:\s*0(?:\.0+)?\s*(?:;|$)",
    re.IGNORECASE,
)
COLOR_PROP_RE = re.compile(r"(?<![-\w])color\s*:\s*([^;]+)", re.IGNORECASE)
BACKGROUND_PROP_RE = re.compile(r"\bbackground(?:-color)?\s*:\s*([^;]+)", re.IGNORECASE)
TAG_STRIP_RE = re.compile(r"<[^>]+>")

ANSI_ESCAPE_RE = re.compile(
    r"\x1b\[[0-9;?]*[ -/]*[@-~]"  # CSI sequences (colors, cursor, conceal)
    r"|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)"  # OSC sequences (titles, hyperlinks)
    r"|\x1b[@-Z\\-_]"  # other C1 escapes
    r"|\x1b"  # any bare ESC byte
)


class ScanError(Exception):
    """A usage or fetch failure that maps to exit code 2."""


@dataclass
class ScanFinding:
    id: str
    severity: str
    message: str
    surface: str
    line: int | None = None
    column: int | None = None
    offset: int | None = None
    evidence: str | None = None

    def as_dict(self) -> dict[str, object]:
        result: dict[str, object] = {
            "id": self.id,
            "severity": self.severity,
            "message": self.message,
            "surface": self.surface,
        }
        for key in ("line", "column", "offset", "evidence"):
            value = getattr(self, key)
            if value is not None:
                result[key] = value
        return result


@dataclass
class SurfaceReport:
    surface: str
    sha256: str
    size: int
    findings: list[ScanFinding] = field(default_factory=list)
    skipped: str | None = None

    def as_dict(self) -> dict[str, object]:
        result: dict[str, object] = {
            "surface": self.surface,
            "sha256": self.sha256,
            "bytes": self.size,
            "findings": len(self.findings),
        }
        if self.skipped is not None:
            result["skipped"] = self.skipped
        return result


class LineIndex:
    """Map character offsets to 1-based (line, column) positions."""

    def __init__(self, text: str) -> None:
        self._starts = [0]
        start = 0
        while True:
            newline = text.find("\n", start)
            if newline == -1:
                break
            start = newline + 1
            self._starts.append(start)

    def position(self, offset: int) -> tuple[int, int]:
        line = bisect.bisect_right(self._starts, offset)
        return line, offset - self._starts[line - 1] + 1


def _is_invisible_codepoint(cp: int) -> bool:
    return (
        cp in ZERO_WIDTH_CODEPOINTS
        or cp in BIDI_CONTROL_CODEPOINTS
        or cp in VARIATION_SELECTORS
        or TAG_BLOCK[0] <= cp <= TAG_BLOCK[1]
    )


def sanitize_excerpt(text: str, limit: int = EVIDENCE_MAX) -> str:
    """Make an excerpt safe to print: escape invisibles and control bytes.

    Findings must never smuggle the hidden channel they report, so every
    invisible or control character is rendered as a visible escape.
    """
    out: list[str] = []
    for ch in text:
        cp = ord(ch)
        if ch in ("\n", "\r", "\t"):
            out.append(" ")
        elif cp < 0x20 or cp == 0x7F:
            out.append(f"\\x{cp:02x}")
        elif _is_invisible_codepoint(cp):
            out.append(f"\\u{cp:04x}" if cp <= 0xFFFF else f"\\U{cp:08x}")
        else:
            out.append(ch)
    excerpt = "".join(out).strip()
    if len(excerpt) > limit:
        excerpt = excerpt[: limit - 3] + "..."
    return excerpt


def _context_excerpt(text: str, start: int, end: int) -> str:
    lo = max(0, start - EVIDENCE_MARGIN)
    hi = min(len(text), end + EVIDENCE_MARGIN)
    return sanitize_excerpt(text[lo:hi])


def looks_like_instruction(text: str) -> bool:
    """Instruction-likeness gate for comment and CSS-hidden findings."""
    if STRONG_INSTRUCTION_RE.search(text):
        return True
    return bool(WEAK_INSTRUCTION_RE.search(text)) and bool(COMMAND_EVIDENCE_RE.search(text))


def check_hidden_html_comments(text: str, surface: str, index: LineIndex, findings: list[ScanFinding]) -> None:
    for match in HTML_COMMENT_RE.finditer(text):
        inner = match.group(1)
        if not looks_like_instruction(inner):
            continue
        line, column = index.position(match.start())
        findings.append(
            ScanFinding(
                id="surface.hidden-html-comment",
                severity="warning",
                message="HTML comment contains instruction-like text that is invisible in rendered output",
                surface=surface,
                line=line,
                column=column,
                offset=match.start(),
                evidence=sanitize_excerpt(inner),
            )
        )


def _nearest_visible_codepoint(text: str, position: int, step: int) -> int | None:
    j = position + step
    while 0 <= j < len(text):
        cp = ord(text[j])
        if not _is_invisible_codepoint(cp):
            return cp
        j += step
    return None


def _joiner_in_legitimate_context(text: str, position: int) -> bool:
    """ZWNJ/ZWJ next to non-ASCII text (emoji, joining scripts) is normal."""
    prev_cp = _nearest_visible_codepoint(text, position, -1)
    next_cp = _nearest_visible_codepoint(text, position, +1)
    if prev_cp is not None and prev_cp > 0x7F:
        return True
    if next_cp is not None and next_cp > 0x7F:
        return True
    return False


def _decode_tag_run(codepoints: list[int]) -> str:
    chars = []
    for cp in codepoints:
        low = cp - TAG_BLOCK[0]
        if 0x20 <= low < 0x7F:
            chars.append(chr(low))
    return "".join(chars)


def check_invisible_unicode(text: str, surface: str, index: LineIndex, findings: list[ScanFinding]) -> None:
    hits: list[tuple[int, int, str]] = []
    for i, ch in enumerate(text):
        cp = ord(ch)
        category: str | None = None
        if TAG_BLOCK[0] <= cp <= TAG_BLOCK[1]:
            category = "tag"
        elif cp in BIDI_CONTROL_CODEPOINTS:
            category = "bidi"
        elif cp in ZERO_WIDTH_CODEPOINTS:
            if cp == 0xFEFF and i == 0:
                continue  # a leading byte-order mark is legitimate
            if cp in (0x200C, 0x200D) and _joiner_in_legitimate_context(text, i):
                continue  # legitimate in emoji sequences and joining scripts
            category = "zero-width"
        if category is not None:
            hits.append((i, cp, category))

    groups: list[list[tuple[int, int, str]]] = []
    for hit in hits:
        if groups and hit[2] == groups[-1][-1][2] and hit[0] - groups[-1][-1][0] <= 16:
            groups[-1].append(hit)
        else:
            groups.append([hit])

    for group in groups:
        start, _, category = group[0]
        end = group[-1][0] + 1
        count = len(group)
        codepoints = [cp for _, cp, _ in group]
        line, column = index.position(start)
        names = ", ".join(sorted({f"U+{cp:04X}" for cp in codepoints}))
        if category == "tag":
            decoded = _decode_tag_run(codepoints)
            message = f"{count} Unicode tag character(s) encode invisible ASCII text"
            evidence = f"decodes to: {sanitize_excerpt(decoded)}" if decoded else names
            finding_id = "surface.invisible-unicode.tag-characters"
            severity = "error"
        elif category == "bidi":
            message = f"{count} bidirectional control character(s) ({names}) can reorder how the text is displayed"
            evidence = _context_excerpt(text, start, end)
            finding_id = "surface.invisible-unicode.bidi-control"
            severity = "error"
        else:
            message = f"{count} zero-width character(s) ({names}) embedded in text"
            evidence = _context_excerpt(text, start, end)
            finding_id = "surface.invisible-unicode.zero-width"
            severity = "warning"
        findings.append(
            ScanFinding(
                id=finding_id,
                severity=severity,
                message=message,
                surface=surface,
                line=line,
                column=column,
                offset=start,
                evidence=evidence,
            )
        )


def _normalize_color(value: str) -> str:
    value = value.strip().lower().rstrip(";").strip()
    if re.fullmatch(r"#[0-9a-f]{3}", value):
        value = "#" + "".join(ch * 2 for ch in value[1:])
    return value


def _style_hides_text(style: str) -> bool:
    if CSS_HIDDEN_PROPERTY_RE.search(style):
        return True
    color_match = COLOR_PROP_RE.search(style)
    background_match = BACKGROUND_PROP_RE.search(style)
    if color_match and background_match:
        color = _normalize_color(color_match.group(1))
        background = _normalize_color(background_match.group(1))
        if color and color == background and color not in ("transparent", "inherit", "initial", "unset"):
            return True
    return False


def check_css_hidden_text(text: str, surface: str, index: LineIndex, findings: list[ScanFinding]) -> None:
    if "<" not in text or "style" not in text.lower():
        return
    for match in STYLED_ELEMENT_RE.finditer(text):
        if not _style_hides_text(match.group("style")):
            continue
        inner = TAG_STRIP_RE.sub(" ", match.group("body"))
        if not inner.strip() or not looks_like_instruction(inner):
            continue
        line, column = index.position(match.start())
        findings.append(
            ScanFinding(
                id="surface.css-hidden-text",
                severity="error",
                message="Instruction-like text is styled to be invisible to human readers",
                surface=surface,
                line=line,
                column=column,
                offset=match.start(),
                evidence=sanitize_excerpt(inner),
            )
        )


def check_ansi_escapes(text: str, surface: str, index: LineIndex, findings: list[ScanFinding]) -> None:
    per_line: dict[int, list[int]] = {}
    for match in ANSI_ESCAPE_RE.finditer(text):
        line, _ = index.position(match.start())
        per_line.setdefault(line, []).append(match.start())
    for line in sorted(per_line):
        offsets = per_line[line]
        first = offsets[0]
        _, column = index.position(first)
        findings.append(
            ScanFinding(
                id="surface.ansi-escape",
                severity="error",
                message=f"{len(offsets)} ESC-based escape sequence(s); terminal rendering can conceal or restyle text",
                surface=surface,
                line=line,
                column=column,
                offset=first,
                evidence=_context_excerpt(text, first, first + 1),
            )
        )


def scan_text(text: str, surface: str) -> list[ScanFinding]:
    """Run every detection channel over one decoded surface."""
    index = LineIndex(text)
    findings: list[ScanFinding] = []
    check_invisible_unicode(text, surface, index, findings)
    check_ansi_escapes(text, surface, index, findings)
    check_hidden_html_comments(text, surface, index, findings)
    check_css_hidden_text(text, surface, index, findings)
    findings.sort(key=lambda finding: (finding.offset if finding.offset is not None else 0, finding.id))
    return findings


def scan_bytes(data: bytes, surface: str) -> SurfaceReport:
    digest = hashlib.sha256(data).hexdigest()
    if b"\x00" in data:
        return SurfaceReport(
            surface=surface,
            sha256=digest,
            size=len(data),
            skipped="binary content (NUL bytes); not scanned",
        )
    text = data.decode("utf-8", errors="replace")
    return SurfaceReport(surface=surface, sha256=digest, size=len(data), findings=scan_text(text, surface))


def scan_file(path: Path, surface: str | None = None) -> SurfaceReport:
    data = path.read_bytes()
    if len(data) > MAX_LOCAL_BYTES:
        data = data[:MAX_LOCAL_BYTES]
    return scan_bytes(data, surface or str(path))


def iter_directory_surfaces(root: Path) -> list[Path]:
    """Known instruction-surface files under root, skipping vendored trees."""
    matches: list[Path] = []
    for path in sorted(root.rglob("*")):
        relative_parts = path.relative_to(root).parts
        if any(part in SKIP_DIRS for part in relative_parts[:-1]):
            continue
        if not path.is_file():
            continue
        name = path.name.lower()
        if name in SURFACE_FILENAMES or name.endswith(SURFACE_SUFFIX):
            matches.append(path)
    return matches


def _fetch_surface(url: str) -> SurfaceReport:
    try:
        fetched = gf.safe_fetch(url)
    except gf.FetchError as exc:
        raise ScanError(f"fetch failed for {url}: {exc.message} ({exc.code})")
    if fetched.status != 200:
        raise ScanError(f"fetch failed for {url}: HTTP {fetched.status}")
    return scan_bytes(fetched.body, fetched.final_url)


def scan_url(
    target: str,
    reports: list[SurfaceReport],
    fetch_notes: list[str],
    emit: "callable[[SurfaceReport], None] | None" = None,
) -> None:
    """Scan an https URL; bare origins probe common instruction surfaces."""
    parts = urlsplit(target)
    if parts.scheme != "https":
        raise ScanError("only https URLs are supported")
    if not parts.hostname:
        raise ScanError(f"the URL has no host: {target}")
    bare_origin = parts.path in ("", "/") and not parts.query

    if not bare_origin:
        report = _fetch_surface(target)
        reports.append(report)
        if emit:
            emit(report)
        return

    origin = f"https://{parts.netloc}"
    for probe_path in ORIGIN_PROBE_PATHS:
        probe_url = origin + probe_path
        try:
            fetched = gf.safe_fetch(probe_url)
        except gf.FetchError as exc:
            fetch_notes.append(f"{probe_url}: {exc.message} ({exc.code})")
            continue
        if fetched.status != 200:
            continue
        report = scan_bytes(fetched.body, fetched.final_url)
        reports.append(report)
        if emit:
            emit(report)
    if not reports:
        raise ScanError(
            f"no instruction surfaces reachable at {origin} "
            f"(probed {len(ORIGIN_PROBE_PATHS)} common paths)"
        )


def output_for(target: str, reports: list[SurfaceReport], fetch_notes: list[str]) -> dict[str, object]:
    findings = [finding.as_dict() for report in reports for finding in report.findings]
    severity_counts = {"error": 0, "warning": 0, "info": 0}
    for report in reports:
        for finding in report.findings:
            severity_counts[finding.severity] = severity_counts.get(finding.severity, 0) + 1
    result: dict[str, object] = {
        "scanner": {
            "name": SCANNER_NAME,
            "version": GUIDECHECK_VERSION,
            "profile": SCAN_PROFILE,
        },
        "target": target,
        "surfaces": [report.as_dict() for report in reports],
        "findings": findings,
        "summary": {
            "surfaces_scanned": len(reports),
            "findings": len(findings),
            "errors": severity_counts["error"],
            "warnings": severity_counts["warning"],
            "info": severity_counts["info"],
        },
    }
    if fetch_notes:
        result["fetch_notes"] = fetch_notes
    return result


def print_report(report: SurfaceReport) -> None:
    if report.skipped is not None:
        print(f"{report.surface}: skipped ({report.skipped})")
        return
    if not report.findings:
        print(f"{report.surface}: clean")
        return
    print(f"{report.surface}: {len(report.findings)} finding(s)")
    for finding in report.findings:
        location = ""
        if finding.line is not None:
            location = f" (line {finding.line}, col {finding.column})"
        print(f"  [{finding.severity}] {finding.id}{location}")
        print(f"      {finding.message}")
        if finding.evidence:
            print(f"      evidence: {finding.evidence}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="guidecheck scan",
        description=(
            "Scan an instruction surface (file, directory, or https URL) for "
            "hidden-instruction channels: HTML comments, invisible Unicode, "
            "CSS-hidden text, and escape sequences."
        ),
    )
    parser.add_argument("target", help="File path, directory, or https URL")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    target: str = args.target
    emit = None if args.json else print_report

    reports: list[SurfaceReport] = []
    fetch_notes: list[str] = []
    try:
        if target.startswith(("https://", "http://")):
            scan_url(target, reports, fetch_notes, emit)
        else:
            path = Path(target)
            if path.is_dir():
                surfaces = iter_directory_surfaces(path)
                if not surfaces:
                    raise ScanError(f"no known instruction surfaces found under {path}")
                for surface_path in surfaces:
                    report = scan_file(surface_path)
                    reports.append(report)
                    if emit:
                        emit(report)
            elif path.is_file():
                report = scan_file(path)
                reports.append(report)
                if emit:
                    emit(report)
            else:
                raise ScanError(f"target not found: {target}")
    except ScanError as exc:
        print(f"guidecheck scan: {exc}", file=sys.stderr)
        return 2

    total = sum(len(report.findings) for report in reports)
    if args.json:
        indent = 2 if args.pretty else None
        print(json.dumps(output_for(target, reports, fetch_notes), indent=indent, sort_keys=bool(indent)))
    else:
        for note in fetch_notes:
            print(f"note: {note}")
        surfaces_word = "surface" if len(reports) == 1 else "surfaces"
        if total:
            print(f"\n{total} finding(s) across {len(reports)} {surfaces_word}.")
        else:
            print(f"\nNo findings across {len(reports)} {surfaces_word}.")
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
