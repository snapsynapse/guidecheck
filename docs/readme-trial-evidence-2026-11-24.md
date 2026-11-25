# README trial evidence, 2026-11-24

This file records the real output behind the "Try it" section of `README.md`. Each report below is the complete JSON written to stdout by the named command, and the diff is the complete output of `diff`. Nothing is edited, trimmed, or simulated. It supersedes `docs/readme-trial-evidence-2026-10-21.md`, which records the earlier trial whose positive control was a different guide under the legacy 0.7.1 profile.

## Source

- Date captured: 2026-11-24
- Commit: `3feb5e0043b224379d59782a8700bc795ede9a0d` (adds `examples/2.0.0-corrected-bound-inline/guide.txt`; follows the `v2.0.0` release, with the verifier still at version 2.0.0)
- Python: 3.15.2
- Execution: local evaluation only. The verifier read each named file as data. No guide action was executed (the `npm` command in the failing fixture and `example-verifier` in the repaired guide are data), and no provenance evidence was fetched.

Acquisition was a fresh clone checked out at the commit above, with each command then run from the checkout root. The capture cloned the maintainer's local repository before the commit was pushed; the README clones the same commit from GitHub.

## Run A: failing guide

Fixture: `fixtures/profiles/2.0.0/corrected-bound-unpinned/guide.txt`. Exit code: 1.

Literal
```bash
python3 scripts/guidecheck_verify.py fixtures/profiles/2.0.0/corrected-bound-unpinned/guide.txt --require-profile-version 2.0.0 --level 3 --pretty
```
```json
{
  "compact_report": "Verifier: guidecheck-reference-local 2.0.0\nGuide: fixtures/profiles/2.0.0/corrected-bound-unpinned/guide.txt\nProfile: 2.0.0 (declared 2.0.0)\nContent policy: corrected-content-1\nAnchor policy: 1.0.0-strict\nQualifying anchors: 0\nLevel: 2\nSHA-256: 980af0ed73303120f7a9a5d643630b1b02e21579d1578c733174c1445518545c\nBlocking findings: 2\nWarnings: 0\nHash pinned: no\nProceed? no",
  "findings": [
    {
      "id": "metadata.last-reviewed.age",
      "message": "last-reviewed is 188 days old",
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
    "evaluated_at": "2026-11-25T04:02:07.962719Z"
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

## The repair

Exit code: 1, because the files differ.

Literal
```bash
diff fixtures/profiles/2.0.0/corrected-bound-unpinned/guide.txt examples/2.0.0-corrected-bound-inline/guide.txt
```
```text
7c7
< guide-version: 2.0.0
---
> guide-version: 2.0.1
12,13c12
< manifest-url: https://snapsynapse.github.io/compat/.well-known/assistant-guide-manifest.txt
< last-reviewed: 2026-05-21
---
> last-reviewed: 2026-11-24
56,58c55,57
< class: code-executing
< approval: required
< command: npm --prefix subdir run check
---
> class: normal
> approval: not-required
> command: example-verifier --version
73c72
< - guidecheck --version exits zero
---
> - example-verifier --version exits zero
79,80c78,79
< guide or stale instructions. The sidecar manifest and independent hash anchor
< raise the cost of undetected guide replacement but do not prove safety.
---
> guide or stale instructions. This guide declares no sidecar manifest, so a
> local check reports Level 3 at most; Level 3 does not prove safety.
```

## Run B: repaired guide

Example: `examples/2.0.0-corrected-bound-inline/guide.txt`. Exit code: 0.

Literal
```bash
python3 scripts/guidecheck_verify.py examples/2.0.0-corrected-bound-inline/guide.txt --require-profile-version 2.0.0 --level 3 --pretty
```
```json
{
  "compact_report": "Verifier: guidecheck-reference-local 2.0.0\nGuide: examples/2.0.0-corrected-bound-inline/guide.txt\nProfile: 2.0.0 (declared 2.0.0)\nContent policy: corrected-content-1\nAnchor policy: 1.0.0-strict\nQualifying anchors: 0\nLevel: 3\nSHA-256: 8620b986985ca00fa3b6da536291756dd6b60000853a064ba79db6c6104b6e66\nBlocking findings: 0\nWarnings: 0\nHash pinned: no\nProceed? yes",
  "findings": [
    {
      "id": "metadata.last-reviewed.age",
      "message": "last-reviewed is 1 days old",
      "severity": "info"
    }
  ],
  "guide": {
    "achieved_level": 3,
    "bytes": 3316,
    "level5_ready": false,
    "sha256": "8620b986985ca00fa3b6da536291756dd6b60000853a064ba79db6c6104b6e66"
  },
  "input": {
    "evaluation_mode": "local-file",
    "path": "examples/2.0.0-corrected-bound-inline/guide.txt"
  },
  "local_evaluation": {
    "evaluated_at": "2026-11-25T04:02:08.036841Z"
  },
  "profile_selection": {
    "anchor_policy": "1.0.0-strict",
    "content_policy": "corrected-content-1",
    "declared_version": "2.0.0",
    "evaluated_policy": "2.0.0"
  },
  "qualifying_anchor_count": 0,
  "summary": {
    "blocking_findings": 0,
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

## What the runs show

- Same verifier (`guidecheck-reference-local 2.0.0`), same content policy (`corrected-content-1`), same gate, same guide apart from the diff above.
- Run A: Level 2, blocking `action.exec-unbounded` (evidence `check-version`) and `anchor.independent.missing`, `Proceed? no`.
- Run B: Level 3, no blocking findings, no warnings, `Proceed? yes`.
- Conformance is not safety. Level 3 says the guide's actions are bounded and reviewable; it does not say they are safe to run.
