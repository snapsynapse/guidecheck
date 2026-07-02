# Changelog

All notable changes to GuideCheck's Human-Verifiable Assistant Guide profile and its companion documents are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) conventions. Profile versions follow Semantic Versioning as defined in `spec.md` section 11.

## [0.7.0] - 2026-07-02

### Added

- section 12 gains a normative "Code-executing actions and the review boundary"
  subsection: an action that invokes a publisher-controlled in-repo artifact
  (`bash scripts/setup.sh`, a `./`-invoked script, `make <target>`,
  `npm run <script>`, `docker build` against an in-repo Dockerfile) MUST inline
  the effective commands or pin the artifact bytes with `exec-sha256`, so the
  reviewed and executed surfaces stay one bounded artifact. Prompted by the 0din
  runtime-indirection class ("clone this repo and I own your machine"), which
  hides no text and materializes its payload at runtime over DNS. The
  bound-versus-exempt axis, the remedies, and the inline carve-out are defined
  in section 12; the design and its adversarial hardening are recorded in
  `handoffs/2026-07-02-0.7.0-transitive-execution-proposal.md`
- two optional action fields in section 12: `exec-sha256` (pins the invoked
  in-repo artifact's bytes to the reviewed guide) and `exec-opaque` (acknowledges
  an un-pinnable external-dependency command such as `npm ci`)
- section 13 gains a stop-and-ask condition for acting on remediation text
  emitted by a failing command, tool, or error message; section 15 is reinforced
  to treat command output, errors, tool results, and stack traces as untrusted
  generated content that MUST NOT be auto-run during error recovery
- five finding ids for the bounded-execution checks in `finding-ids.md`:
  `action.exec-unbounded`, `action.exec-opaque`, `exec-sha256.mismatch`,
  `exec-sha256.transitive-unpinned`, and `exec-sha256.unverified`

### Changed

- profile version to 0.7.0 across the spec, verifier-conformance profile, README,
  INTENT, the public pages, the examples, and the published guide plus its
  manifest

### Notes

- This release defines the bounded-execution requirement, its action fields, and
  its finding ids. Reference-verifier and hosted-verifier enforcement of
  `action.exec-unbounded`, `exec-sha256` verification, and transitive-closure
  scanning arrive in a subsequent 0.7.x release, so a guide's compliance with the
  bounded-execution rule is currently self-asserted, in the same way Level 5
  runtime conformance is specified ahead of a conformant runtime. The DNS-client,
  `/dev/tcp`, and path-qualified and container code-execution detection that
  landed under the 0.6.x line already surface the command shapes this rule
  governs.

## [0.6.0] - 2026-06-10

### Added

- the hosted verifier now fetches and evaluates two additional Level 4
  cross-channel anchors: `repository-file` (scoped to github.com in 0.6.0)
  and `dns-txt` (resolved over DNS-over-HTTPS via cloudflare-dns.com,
  reporting the resolver's DNSSEC AD bit). The fetcher allowlist and DoH
  resolver choice are documented in `roadmap.md`
- `scripts/guidecheck_hosted_anchors.py` owns the URL derivation,
  repository-host allowlist, and DoH response parser for the two new
  channels; `scripts/test_hosted_anchors.py` covers the helpers and
  `scripts/test_hosted_api.py` covers the integrated paths
- GuideCheck's own `assistant-guide.txt` now declares Level 4 evidence
  through a `manifest-url` at `docs/.well-known/assistant-guide-manifest.txt`,
  a `_assistant-guide.guidecheck.org` DNS TXT record, and a `source-path`
  pointing into the repository's `docs/` tree so the github.com repository-file
  channel resolves
- `.github/workflows/release.yml` runs on `v*` tag pushes and signs the
  release-archive tarball, zip, the conformance kit, and `SHA256SUMS` with
  Sigstore cosign keyless. The verification identity is locked to
  `https://github.com/snapsynapse/guidecheck/.github/workflows/release.yml@refs/tags/v*`
  and the procedure is documented in `SECURITY.md`
- a new `anchor.repository-file.host-not-supported` info finding records
  when the hosted verifier cannot treat a publisher's `repository-url`
  host as an independent anchor in the current allowlist; the channel
  does not count toward Level 4 in that case

### Changed

- the hosted fetch budget rises from five to seven outbound fetches per
  request to admit the new DNS TXT and repository-file anchor probes
  alongside the existing guide, variation, manifest, registry, and
  transparency-log paths
- `safe_fetch` accepts an `accept_override` keyword so the DoH path can
  request `application/dns-json` while keeping the SSRF, redirect, size,
  and timeout controls unchanged
- `roadmap.md` now commits to Sigstore keyless as the release-signing
  mechanism (superseding the prior "minisign or Sigstore are the
  candidates" placeholder) and records the second-verifier port to Go or
  Rust as the first reactivation move per the 2026-06-09 disposition note

## [0.5.0] - 2026-06-09

### Security

- package-registry JSON anchors now bind the hash to assistant-guide-specific
  metadata (`assistantGuide` or `assistant-guide`) instead of accepting the
  first `sha256` field anywhere in the registry record
- hosted verification now enforces a five-fetch per-request budget with exact
  fetch deduplication, uses one deterministically selected unbranded
  content-variation probe, warns on off-domain recommended verifiers, and warns
  when package-registry assistant-guide URLs disagree with `canonical-url`

### Added

- `scripts/check_version_sync.py` runs in `make test` and asserts every
  version-bearing surface agrees with `guidecheck_constants.py`, including a
  byte-identity check that the published `docs/.well-known/assistant-guide.txt`
  matches the repository `assistant-guide.txt`
- optional fixture expectation fields `warnings_exact` and
  `forbidden_warning_ids` so fixtures can fail on unexpected warnings (false
  positives), not just missing ones; 68 of 68 local-file fixtures now pin
  their warning sets exactly
- deterministic parser tests for the dns-txt, repository-file,
  signed-security-txt, and transparency-log anchor channels, covering
  extraction semantics, agreement, mismatch blocking, and absent evidence
- the verifier-output schema documents the `valid` and `guide_sha256` fields
  the reference verifier emits in manifest evidence

### Changed

- code-level version constants are centralized for the local verifier, hosted
  verifier, and hosted fetch user agent
- contract validation now requires every emitted finding id in the verifier and
  hosted API code to be documented in `finding-ids.md`; `CONTRIBUTING.md` now
  lists `finding-ids.md` as normative for the finding-id registry
- `ADOPTION.md` reframes MCP and A2A as ecosystem integrations of the core
  profile rather than primary audiences; the three integration notes carry an
  explicit advisory status statement
- `INTENT.md` records the Level 5 ownership decision: GuideCheck owns the
  runtime fixture suite and evaluator, gated by
  `docs/pre-level-5-readiness.md`

### Fixed

- the published `docs/.well-known/assistant-guide.txt` had drifted from the
  repository `assistant-guide.txt` again after the 0.4.0 hardening commit; it
  is resynced and the new version-sync check makes this drift a test failure

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

[Unreleased]: https://github.com/snapsynapse/guidecheck/compare/v0.5.0...HEAD
[0.5.0]: https://github.com/snapsynapse/guidecheck/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/snapsynapse/guidecheck/compare/v0.3.2...v0.4.0
[0.3.2]: https://github.com/snapsynapse/guidecheck/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/snapsynapse/guidecheck/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/snapsynapse/guidecheck/compare/v0.2.0...v0.3.0
[0.2.1]: https://github.com/snapsynapse/guidecheck/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/snapsynapse/guidecheck/releases/tag/v0.2.0
[0.1.0]: https://github.com/snapsynapse/guidecheck/releases/tag/v0.1.0
