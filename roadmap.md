# Roadmap

Status: planning notes for actions not yet executed and decisions not yet made.

This roadmap is not normative. It records likely future work so unresolved
items are visible without being treated as commitments.

## Near-term actions

- Treat the first reference verifier milestone as Level 1 through Level 3 only.
  Do not claim Level 4, hosted verifier, or Level 5 conformance from this
  milestone.
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
- Add release tags and immutable release URLs for profile version 0.1.0.

## Documentation work

- Add stable named anchors or reference labels so docs are less dependent on
  section numbers.
- Expand verifier author guidance with examples of compact reports and full
  machine-readable output.
- Add an adoption guide for projects that want only Level 1 or Level 2 before
  committing to full Level 3 action blocks.
- Add a guide-author checklist separate from the normative spec.
- Add examples for package registry metadata in npm, PyPI, Cargo, and generic
  registries.
- Document how generated evals map to future static fixture names.
- Add a short threat-model primer for maintainers adding new finding ids.

## Implementation work

- Maintain the local-file reference verifier CLI for Levels 1 through 3 before
  attempting Level 4 provenance or hosted public-web verification.
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

## Open decisions

- Which CLI name, output flags, and exit-code contract the Level 1-3 reference
  verifier should expose.
- Whether local-file verifier output should require `input.path`, keep
  `input.url` optional, or use separate input object variants by mode.
- What default staleness threshold, metadata value length threshold, approval
  count warning threshold, and request/fetch limits should be pinned for the
  reference implementation.
- Whether GuideCheck's own `repository-url` should be a repository URL, a
  project page URL, or both through separate metadata fields.
- Whether root `assistant-guide.txt` and `/.well-known/assistant-guide.txt`
  must remain byte-identical for all publishers or only for GuideCheck.
- Exact Level 4 anchor wire formats for DNS TXT, package registry metadata,
  repository-file hash publication, and signed `security.txt` fields.
- Whether signed `security.txt` should be promoted from optional evidence to a
  stronger recommended path for Level 4.
- Whether `code-executing` should require approval at Level 3, not only as a
  Level 4 recommendation and Level 5 requirement.
- Whether `networked` actions should require approval at Level 3.
- Whether finding ids should become fully normative before profile 0.1.0 or
  remain fixture-contract identifiers until 0.2.0.
- Whether generated evals are acceptable for interim conformance work or all
  conformance-relevant cases must be static fixtures before public release.
- Whether hosted verifier UX should be specified more tightly or remain mostly
  implementation guidance.
- Whether Level 5 runtime conformance needs a separate fixture suite.
- Whether public-fetch SSRF cases should be represented as data fixtures,
  local server tests, or both.

## Release readiness

- Public repository URL configured and documented.
- Default branch and remote publishing flow verified.
- Canonical site serves `/.well-known/assistant-guide.txt`.
- Canonical site serves schemas at `https://guidecheck.org/schemas/`.
- Canonical site serves or links machine-readable verifier output.
- Guide hash is published through at least one independent channel.
- `security.txt` expiration and contact ownership are reviewed.
- Profile 0.1.0 changelog is complete.
- All static fixtures and generated evals pass in CI.
