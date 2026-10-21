# README trial evidence, 2026-10-21

This file records the real output behind the "Try it" section of `README.md`. Each report below is the complete JSON written to stdout by the named command. Nothing is edited, trimmed, or simulated.

## Source

- Date captured: 2026-10-21
- Tag: `v2.0.0`
- Commit: `0991c18ec6dd8b966d67bab9802f6559e7e74b91`
- Python: 3.14.8
- Execution: local evaluation only. The verifier read each named file as data. No guide action was executed (the `npm` command in the failing fixture is data), and no provenance evidence was fetched.

Acquisition was a clean shallow clone of the tag, with each command then run from the checkout root.

Literal
```bash
git clone --branch v2.0.0 --depth 1 https://github.com/snapsynapse/guidecheck.git guidecheck-trial
```

## Run A: failing example

Fixture: `fixtures/profiles/2.0.0/corrected-bound-unpinned/guide.txt`. Exit code: 1.

Literal
```bash
python3 scripts/guidecheck_verify.py fixtures/profiles/2.0.0/corrected-bound-unpinned/guide.txt --level 3 --pretty
```
```json
{
  "compact_report": "Verifier: guidecheck-reference-local 2.0.0\nGuide: fixtures/profiles/2.0.0/corrected-bound-unpinned/guide.txt\nProfile: 2.0.0 (declared 2.0.0)\nContent policy: corrected-content-1\nAnchor policy: 1.0.0-strict\nQualifying anchors: 0\nLevel: 2\nSHA-256: 980af0ed73303120f7a9a5d643630b1b02e21579d1578c733174c1445518545c\nBlocking findings: 2\nWarnings: 0\nHash pinned: no\nProceed? no",
  "findings": [
    {
      "id": "metadata.last-reviewed.age",
      "message": "last-reviewed is 153 days old",
      "severity": "info"
    },
    {
      "evidence": "check-version",
      "id": "action.exec-unbounded",
      "message": "named or dispatched repository execution requires a valid exec-sha256 or replacement with inline actions; exec-opaque cannot exempt it",
      "severity": "error"
    },
    {
      "id": "anchor.independent.missing",
      "message": "no fetched qualifying independent anchor is available for Level 4",
      "severity": "error"
    }
  ],
  "guide": {
    "achieved_level": 2,
    "bytes": 3416,
    "level5_ready": false,
    "sha256": "980af0ed73303120f7a9a5d643630b1b02e21579d1578c733174c1445518545c"
  },
  "input": {
    "evaluation_mode": "local-file",
    "path": "fixtures/profiles/2.0.0/corrected-bound-unpinned/guide.txt"
  },
  "local_evaluation": {
    "evaluated_at": "2026-10-21T15:27:07.595543Z"
  },
  "profile_selection": {
    "anchor_policy": "1.0.0-strict",
    "content_policy": "corrected-content-1",
    "declared_version": "2.0.0",
    "evaluated_policy": "2.0.0"
  },
  "qualifying_anchor_count": 0,
  "summary": {
    "blocking_findings": 2,
    "infos": 1,
    "warnings": 0
  },
  "verifier": {
    "guide_profile": "human-verifiable-assistant-guide",
    "guide_profile_version": "2.0.0",
    "name": "guidecheck-reference-local",
    "verifier_profile": "human-verifiable-assistant-guide-verifier",
    "verifier_profile_version": "2.0.0",
    "version": "2.0.0"
  }
}
```

## Run E: positive control

Guide: `examples/level-3-assistant-guide.txt`. Exit code: 0. This guide declares profile-version 0.7.1, so the verifier selected the frozen legacy evaluator from the guide's own bytes and reports verifier version 0.7.1. It is a different known-valid guide, not a repaired version of the Run A guide.

Literal
```bash
python3 scripts/guidecheck_verify.py examples/level-3-assistant-guide.txt --level 3 --pretty
```
```json
{
  "compact_report": "Verifier: guidecheck-reference-local 0.7.1\nGuide: examples/level-3-assistant-guide.txt\nLevel: 3\nSHA-256: fa1abbfe47776b6af224b570f53f7749d321829f7201788bd09b65f885508b7e\nBlocking findings: 0\nWarnings: 0\nHash pinned: no\nProceed? yes",
  "findings": [
    {
      "id": "metadata.last-reviewed.age",
      "message": "last-reviewed is 152 days old",
      "severity": "info"
    }
  ],
  "guide": {
    "achieved_level": 3,
    "bytes": 5210,
    "level5_ready": false,
    "sha256": "fa1abbfe47776b6af224b570f53f7749d321829f7201788bd09b65f885508b7e"
  },
  "input": {
    "evaluation_mode": "local-file",
    "path": "examples/level-3-assistant-guide.txt"
  },
  "local_evaluation": {
    "evaluated_at": "2026-10-21T15:29:18.207321Z"
  },
  "summary": {
    "blocking_findings": 0,
    "infos": 1,
    "warnings": 0
  },
  "verifier": {
    "guide_profile": "human-verifiable-assistant-guide",
    "guide_profile_version": "0.7.1",
    "name": "guidecheck-reference-local",
    "verifier_profile": "human-verifiable-assistant-guide-verifier",
    "verifier_profile_version": "0.7.1",
    "version": "0.7.1"
  }
}
```

## Run C: scanner on an existing instruction file

Target: the checkout's own `CLAUDE.md`. Exit code: 0, with 0 findings. No findings means no supported hidden-instruction channel was detected in that input. It does not mean the file is safe.

Literal
```bash
python3 scripts/guidecheck_scan.py CLAUDE.md --json
```
```json
{"scanner": {"name": "guidecheck-scanner", "version": "2.0.0", "profile": "instruction-surface-scan"}, "target": "CLAUDE.md", "surfaces": [{"surface": "CLAUDE.md", "sha256": "c8cb2acacb5c13fe57491aff2a72797ab18dfc84d55b79c1f6d16bb0fbd76b5e", "bytes": 9732, "findings": 0}], "findings": [], "summary": {"surfaces_scanned": 1, "findings": 0, "errors": 0, "warnings": 0, "info": 0}}
```

## Notes

- Local 2.0.0 and 1.0.0 guides that declare `manifest-url` claim Level 4. The local verifier cannot fetch provenance evidence, so it reports blocking `anchor.independent.missing` and exits 1 even when `guide.achieved_level` is 3. Example: `fixtures/profiles/2.0.0/dns-only/guide.txt` reached achieved level 3 and exited 1 (guide SHA-256 `dcc28648441d8c5270984bd319850007470421e2c64428383cd481ca9be16c7e`). Every 2.0.0 fixture declares `manifest-url`, so none is a local exit 0 positive control. This is current behavior, recorded as observed.
- The Run A report and the dns-only report in the first note were also produced at `main` commit `34331b9`. Both are identical to the tag `v2.0.0` reports except for `local_evaluation.evaluated_at`. Runs E and C were captured at the tag only.
- Date-dependent fields: `local_evaluation.evaluated_at` is the evaluation time, and the `metadata.last-reviewed.age` info finding counts days since the guide's `last-reviewed` date (153 days for Run A and 152 days for Run E on this date). Output captured on another day will differ in at least those fields. The guide SHA-256 values above are properties of the guide bytes.
- Run A also reports blocking `anchor.independent.missing`, because the fixture declares `manifest-url` (it claims Level 4) and no fetched evidence is available locally. The blocking `action.exec-unbounded` finding is the one that holds the guide at achieved Level 2.
