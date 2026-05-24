# Changelog

All notable changes to GuideCheck's Human-Verifiable Assistant Guide profile and its companion documents are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) conventions. Profile versions follow Semantic Versioning as defined in `spec.md` section 11.

## [Unreleased]

### Added

- local-file reference verifier support for Level 4 manifest and
  independent-anchor evidence, including `--anchor CHANNEL=PATH`
- static valid Level 4, missing-anchor, and cross-channel hash divergence fixtures
- verifier output for local cross-channel anchor evidence

### Changed

- manifest failures now block Level 4 without lowering otherwise valid Level 3
  content evaluation

## [0.2.1] - 2026-05-22

### Added

- sanitized hosted-verifier product telemetry for target host, path category,
  selected agent category, expected level, achieved level, outcome, failure
  category, and coarse duration
- optional hosted-verifier agent category and expected-level inputs for
  compatibility troubleshooting across agent families

### Changed

- documentation and public verifier copy now describe the hosted verifier's
  limited product telemetry and distinguish it from normative verifier output

## [0.2.0] - 2026-05-21

Open-question resolution and restructure. Profile and verifier-profile versions are bumped from 0.1.0; the constraint tightenings below make this a 0.2.0, not a 0.1.x patch.

### Added

- `ADOPTION.md`, a practical adoption guide with the conformance ladder, a level-by-level path, and the guide-author checklist
- `operator-guide.md`, the non-normative defense-in-depth practices, lifted from spec section 28
- public append-only transparency log recognized as an independent cross-channel provenance anchor, discovered through the manifest `transparency-log-url` field (spec section 11, verifier-conformance section 23)
- a how-to-read guide and linked contents at the top of `spec.md`

### Changed

- profile and verifier-profile versions bumped to 0.2.0; the reference verifier, hosted verifier, examples, fixtures, and canonical pages report 0.2.0
- `code-executing` actions now require explicit approval at Level 3, consistent with the other high-consequence action classes (spec section 12, verifier-conformance section 18)
- the reference verifier and the eval harness enforce `code-executing` approval at Level 3 and report `last-reviewed` age as an informational finding
- guide copies served at both the well-known path and the repository root must be byte-identical (spec section 6)
- `repository-url` is defined as the source repository root, a single field, not a project page (spec section 11)
- staleness reporting keys off the publisher's `valid-until`; `last-reviewed` age is reported as informational with no arbitrary expiry threshold (spec section 21, verifier-conformance section 24)
- verifiers warn on non-URL metadata values longer than 80 bytes, replacing an unspecified length check (verifier-conformance section 14)
- `spec.md` problem statement trimmed; operator responsibilities moved out to `operator-guide.md`

### Removed

- the Open Questions sections from `spec.md` and `verifier-conformance.md`; resolved and future items now live in `roadmap.md`

## [0.1.0] - 2026-05-21

Initial draft for review.

### Specification

- Human-Verifiable Assistant Guide profile for `assistant-guide.txt`
- core artifact, one-artifact bounded-task scope, canonical well-known path
- strict ASCII byte profile, 8 KiB size cap, 120-byte line and 400-line limits
- disallowed constructs and Markdown-as-text clarification
- required sections at Level 3, compact verification instruction at Level 1, assistant invocation prompt content
- guide metadata block with normative fences, version-range syntax, and field set
- sidecar manifest provenance model and cross-channel hash publication (DNS TXT, package registry, public repository file, signed security.txt)
- action classification with seven classes including `code-executing`, structured `[action]` blocks, command field restrictions, `runner` semantics
- stop-and-ask conditions and canonical approval phrasing
- threat model, untrusted content handling, integrity-versus-instruction fetch distinction, hard ban on chained guides
- public information safety and risky pattern guidance
- five-level conformance ladder including Level 5 runtime-enforced execution
- discovery surfaces, HTTPS serving requirements, verifier requirements, verifier output schema
- residual threats and operator defense-in-depth checklist
- locale handling and final ASCII-only position

### Companion documents

- Verifier Conformance Profile defining public-web and local-file evaluation modes, fetch safety, SSRF defenses, level calculation, output schema, and fixture suite conformance
- design rationale capturing the reasoning behind the 8 KiB cap, ASCII-only profile, sidecar manifest, cross-channel publication, hard chained-guide ban, and other decisions
- threat register enumerating network, hosting, provenance, verifier, runtime, user, and availability risk classes
- JSON Schema for the manifest and verifier output

### Project

- designated standard primary verifier at `https://guidecheck.org/verify`
- canonical site at `https://guidecheck.org/`

[Unreleased]: https://github.com/snapsynapse/guidecheck/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/snapsynapse/guidecheck/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/snapsynapse/guidecheck/releases/tag/v0.2.0
[0.1.0]: https://github.com/snapsynapse/guidecheck/releases/tag/v0.1.0
