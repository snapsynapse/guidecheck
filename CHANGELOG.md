# Changelog

All notable changes to GuideCheck's Human-Verifiable Assistant Guide profile and its companion documents are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) conventions. Profile versions follow Semantic Versioning as defined in `spec.md` section 11.

## [Unreleased]

## [0.4.0] - 2026-05-29

### Security

- detector negation handling rewritten: a negation now suppresses a prohibited
  or encoded-execution pattern only when it directly governs that pattern, so
  inserting `do not` elsewhere on the line no longer disables the detector
- marker discipline: action and metadata fences that differ only by surrounding
  whitespace or letter case (for example `[ACTION]`) are no longer silently
  dropped; they raise a blocking malformed finding so a verifier and a lenient
  agent parser cannot diverge on which actions exist
- command and class consistency: a command is cross-checked against its declared
  class by command-head analysis; a network fetch piped into an interpreter
  blocks as `command.fetch-execute`, and under-declared network or code-executing
  commands raise warnings
- registry anchors: a `registry-url` is counted toward Level 4 only when its host
  is a recognized independent registry, closing a self-hosted-anchor path

### Added

- finding ids `command.fetch-execute`, `network.command-implies-networked`,
  `approval.command-implies-required`, `anchor.registry.unrecognized-host`, and
  `level4.requires-fetch`
- `verifier-conformance.md` sections for marker discipline and command/class
  consistency
- a recorded adversarial review in `threat-register.md`

### Changed

- the local-file reference verifier now caps the achieved level at Level 3. It
  still checks supplied manifest and anchor evidence for consistency and reports
  `level4.requires-fetch`, but Level 4 (independent provenance) is assertable
  only by the fetching hosted verifier, matching `verifier-conformance.md`
  section 6
- the eval runner imports the primary engine instead of carrying a second copy
  of the checks, so there is one source of truth
- profile, verifier, hosted verifier, spec, verifier-conformance, examples, and
  public pages now report 0.4.0; guide `verifier-conformance` ranges move to
  `>=0.4.0, <0.5.0` and `applies-to` to `guidecheck 0.4.x`
- the published `docs/.well-known/assistant-guide.txt` is resynced byte-for-byte
  with the repository `assistant-guide.txt` (it had drifted at 0.3.1)

## [0.3.2] - 2026-05-28

### Added

- non-normative ACS integration note for runtime control hooks, Guardian
  enforcement, trace records, and AgBOM inventory
- non-normative draft registry for Level 5 runtime reason codes, kept separate
  from guide-side verifier finding ids

### Changed

- profile, verifier, hosted verifier, examples, and public pages now report
  0.3.2
- Level 5 draft material now records resolved defaults for claim scope, session
  boundaries, optional enforced-surface subprofiles, memory controls, and
  reason-code handling
- verifier conformance now defines the canonical `level5_ready: true`
  predicate as a guide-side preparation signal, not an achieved runtime level
- roadmap and implementation planning now keep MCP and A2A as optional
  enforced-surface design work unless a future spec promotes them to core
  requirements

## [0.3.1] - 2026-05-27

### Added

- MCP and A2A integration notes for agent ecosystem positioning
- database MCP server Level 3 example guide
- homepage trust-boundary sequence and delegated-authority positioning

### Changed

- profile, verifier, hosted verifier, examples, and public pages now report
  0.3.1
- public positioning now frames GuideCheck as a trust boundary protocol for
  agent instruction surfaces while preserving the conformance-is-not-safety
  limitation
- `.gitignore` now excludes local handoff note directories

## [0.3.0] - 2026-05-24

### Added

- local-file reference verifier support for Level 4 manifest and
  independent-anchor evidence, including `--anchor CHANNEL=PATH`
- static valid Level 4, missing-anchor, and cross-channel hash divergence fixtures
- verifier output for local cross-channel anchor evidence
- hosted verifier Level 4 support for sidecar manifest fetches, package-registry
  anchors, and transparency-log anchors
- Level 5 readiness reporting for Level 4 guides, including static ready and
  not-ready fixtures
- hosted API coverage for Level 4 guides that are not Level 5-ready
- hosted verifier public-web warnings for content variation and missing or
  incompatible response headers

### Changed

- manifest failures now block Level 4 without lowering otherwise valid Level 3
  content evaluation
- hosted verifier result copy now surfaces Level 5 readiness without presenting
  it as achieved Level 5
- public score language now frames Level 4 as the highest guide-file score and
  Level 5 as separate runtime enforcement
- public-web fetch replay tests now capture reportable response headers and
  exercise hosted content-variation checks
- adoption guidance now includes npm, PyPI, Cargo, and generic package
  registry metadata examples for Level 4 anchors

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

[Unreleased]: https://github.com/snapsynapse/guidecheck/compare/v0.3.2...HEAD
[0.3.2]: https://github.com/snapsynapse/guidecheck/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/snapsynapse/guidecheck/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/snapsynapse/guidecheck/compare/v0.2.0...v0.3.0
[0.2.1]: https://github.com/snapsynapse/guidecheck/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/snapsynapse/guidecheck/releases/tag/v0.2.0
[0.1.0]: https://github.com/snapsynapse/guidecheck/releases/tag/v0.1.0
