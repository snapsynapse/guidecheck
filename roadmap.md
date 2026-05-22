# Roadmap

Status: planning notes for actions not yet executed and decisions not yet made.

This roadmap is not normative. It records likely future work so unresolved
items are visible without being treated as commitments.

## Resolved in the 0.1.0 review

A round of open-question resolution on 2026-05-21 settled the decisions below.
Normative outcomes are already in `spec.md` and `verifier-conformance.md`; the
implementation-detail outcomes are pinned here as specs to build against.

- Verifier CLI: the reference verifier is invoked as `guidecheck-verify`, with
  `--json` (default), `--pretty`, and `--level N` flags; exit code 0 on pass,
  1 on conformance failure or a result below the asserted level, 2 on usage or
  IO error.
- Verifier input object: a single `input` object with a `mode` discriminator
  (`file` or `url`) and mode-appropriate fields; no separate object variants.
- Verifier thresholds: approval-count warning at 10; non-URL metadata value
  warning over 80 bytes; fetch caps and timeouts per `verifier-conformance.md`
  section 9. No fixed `last-reviewed` expiry; staleness keys off the
  publisher's `valid-until` only, and `last-reviewed` age is reported as info.
- `repository-url` is the source repository root, a single field, not a
  project page (`spec.md` section 11).
- Root and well-known guide copies, when both are served, must be
  byte-identical (`spec.md` section 6).
- `code-executing` actions require approval at Level 3 (`spec.md` section 12,
  `verifier-conformance.md` section 18).
- `networked` actions stay SHOULD-approval at Level 3 and MUST at Level 5; no
  change.
- The Level 4 anchor wire formats in `spec.md` section 11 are ratified as the
  0.2.0 normative set.
- The cross-channel anchors stay equal; signed `security.txt` is not promoted
  above the others.
- A public append-only transparency log is recognized as an independent
  cross-channel anchor (`spec.md` section 11).
- finding ids remain fixture-contract identifiers for the 0.2.0 release and
  become normative once the fixture corpus is complete.
- Generated evals are acceptable as a regression harness for the 0.2.0 release;
  a verifier conformance claim requires static fixtures, which 0.2.0 does not
  yet make.
- Hosted verifier UX stays implementation guidance; the compact report and the
  output schema are the only contract.

## Future profile directions

Candidates for 0.2.0 and later. Not commitments.

- A higher provenance tier above Level 5 requiring a code signature and a
  transparency-log entry. The conformance ladder stays 0 to 5 for now;
  provenance hardening would land within the existing tiers, not as a numbered
  Level 6.
- An optional signed verifier-report envelope for hosted checkers, CI, and
  assistant-runtime consumption.
- A requirement that Level 5 runtimes publish an attestation or conformance
  report.
- A self-verification report published by hosted verifiers.
- A separate Level 5 runtime-conformance fixture suite, distinct from the
  verifier-conformance fixture corpus, once Level 5 work begins.
- Signing fixture-suite releases once `verifier-conformance.md` reaches a
  stable conformance target; tracked also in `CONTRIBUTING.md`.

## Near-term actions

- The reference verifier CLI and the hosted public-web verifier both cover
  Level 1 through Level 3 only. The hosted verifier is live as a preview at
  https://guidecheck.org/verify; do not present it as fully conformant, and do
  not claim Level 4 or Level 5 conformance, until the supporting fixture suites
  are complete.
- Promote generated eval cases into static fixtures where they should become
  hard verifier conformance gates.
- Add valid Level 1 and Level 4 static fixtures with complete `expected.json`
  files.
- Add manifest mismatch, over-size, overlong-line, missing verification,
  metadata-error, missing-section, malformed-action, approval-gate, egress,
  shell-runner, chained-guide, encoded-execution, revoked, and stale-date
  fixture directories.
- Add public-fetch fixture descriptions for SSRF, redirect, TLS, and header
  scenarios, even if live network replay remains implementation-specific.
- Add a static fixture for GuideCheck's own `assistant-guide.txt` once the
  public deployment URL and repository URL are settled.
- Add a Level 4 manifest for GuideCheck's own guide after an independent hash
  anchor is published.
- Add a signed or otherwise independently anchored `security.txt` plan before
  claiming it as a Level 4 channel.
- Add a schema-backed validation path for fixture `expected.json` once a
  portable JSON Schema validator is chosen.
- Add CI that runs `make eval`, JSON parse checks, and byte-profile checks for
  guide artifacts.
- Add immutable release URLs and a static fixture for the tagged 0.2.0 release.

## Documentation work

- Extend the contents-with-anchor-links approach added to `spec.md` to
  `verifier-conformance.md` so both docs are navigable without depending on
  section numbers.
- Expand verifier author guidance with examples of compact reports and full
  machine-readable output.
- Add examples for package registry metadata in npm, PyPI, Cargo, and generic
  registries.
- Document how generated evals map to future static fixture names.
- Add a short threat-model primer for maintainers adding new finding ids.

## Implementation work

- Maintain the local-file reference verifier CLI and the hosted public-web
  verifier for Levels 1 through 3 on shared check logic. Do not extend either
  to Level 4 provenance or Level 5 runtime conformance until the supporting
  fixtures exist.
- Implement the verifier CLI name, flags, exit codes, and input object pinned
  in the resolved-decisions section above.
- Sync the reference verifier and `scripts/eval_guidecheck.py` to the resolved
  verifier behavior: enforce `code-executing` approval gating at Level 3, and
  report `last-reviewed` age as info with no expiry threshold. Add the matching
  approval-gate and staleness fixtures.
- Keep `scripts/eval_guidecheck.py` as a regression harness and reference map,
  not the verifier implementation.
- Continue separating the reference verifier from repository regression checks
  while preserving the same normalized fixture expectation contract.
- Emit machine-readable verifier output and the compact human-readable report
  from the same evidence model.
- Extend schema and fixture coverage as the local-file CLI contract evolves.
- Add exact JSON Schema validation for manifest, verifier output, and fixture
  expected files using a pinned portable tool.
- Add public-web replay fixtures through local HTTP servers for redirects,
  content-type headers, response size limits, and content variation.
- Add deterministic tests for manifest parsing and cross-channel hash anchor
  handling.
- Add tests for registry-url parsing across npm, PyPI, Cargo, and generic
  registry records.

## Release readiness

- Public repository URL configured and documented.
- Default branch and remote publishing flow verified.
- Canonical site serves `/.well-known/assistant-guide.txt`.
- Canonical site serves schemas at `https://guidecheck.org/schemas/`.
- Canonical site serves or links machine-readable verifier output.
- Guide hash is published through at least one independent channel.
- `security.txt` expiration and contact ownership are reviewed.
- Profile 0.2.0 changelog is complete.
- All static fixtures and generated evals pass in CI.
