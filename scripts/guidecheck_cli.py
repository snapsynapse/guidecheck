#!/usr/bin/env python3
"""
Console entry point for the packaged `guidecheck` command.

One-command entry (adoption roadmap step 2): `uvx guidecheck scan <target>`
should reach a first finding within seconds. This module only dispatches:

  guidecheck scan <file|dir|https-url> [--json] [--pretty]
  guidecheck verify <path> [verify options]

`scan` is the instruction-surface scanner in scripts/guidecheck_scan.py;
`verify` wraps the existing reference verifier CLI in
scripts/guidecheck_verify.py without changing its behavior.
"""

from __future__ import annotations

import sys

from guidecheck_constants import GUIDECHECK_VERSION

USAGE = """\
usage: guidecheck <command> [options]

commands:
  scan <file|dir|https-url>   Scan instruction surfaces (AGENTS.md, CLAUDE.md,
                              READMEs, skill files, assistant-guide.txt) for
                              hidden-instruction channels.
  verify <path>               Verify a local assistant-guide.txt through
                              GuideCheck Level 4 (reference verifier).

Run `guidecheck scan --help` or `guidecheck verify --help` for options.
"""


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print(USAGE, file=sys.stderr, end="")
        return 2
    command, rest = args[0], args[1:]
    if command in ("-h", "--help", "help"):
        print(USAGE, end="")
        return 0
    if command in ("--version", "version"):
        print(f"guidecheck {GUIDECHECK_VERSION}")
        return 0
    if command == "scan":
        import guidecheck_scan

        return guidecheck_scan.main(rest)
    if command == "verify":
        if not rest:
            # guidecheck_verify.main falls back to sys.argv on an empty list,
            # which would re-read the subcommand; fail with usage instead.
            print("guidecheck verify: missing guide path", file=sys.stderr)
            return 2
        import guidecheck_verify

        return guidecheck_verify.main(rest)
    print(f"guidecheck: unknown command {command!r}", file=sys.stderr)
    print(USAGE, file=sys.stderr, end="")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
