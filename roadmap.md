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

Candidates for 0.3.0 and later. Not commitments.

- A higher provenance tier above Level 5 requiring a code signature and a
  transparency-log entry. The conformance ladder stays 0 to 5 for now;
  provenance hardening would land within the existing tiers, not as a numbered
  Level 6.
- An optional signed verifier-report envelope for hosted checkers, CI, and
  assistant-runtime consumption.
- A future Level 5 runtime conformance profile. Detailed sequencing lives in
  `docs/level-5-implementation-plan.md`; roadmap entries here stay at the
  milestone level.
- A requirement that Level 5 runtimes publish an attestation or conformance
  report.
- A self-verification report published by hosted verifiers.
- Draft Level 5 planning lives in `docs/level-5-runtime-conformance.md` and
  `docs/level-5-implementation-plan.md`. Keep these as non-normative design
  notes until the Level 1-4 fixture and validation base is stronger.
- Signing fixture-suite releases once `verifier-conformance.md` reaches a
  stable conformance target; tracked also in `CONTRIBUTING.md`.

## Near-term actions

- The reference verifier CLI covers Level 1 through Level 3 in local-file mode;
  it checks supplied sidecar manifest and independent-anchor evidence for
  consistency but caps at Level 3 (reporting `level4.requires-fetch`), since
  Level 4 requires fetched provenance. The hosted public-web verifier covers
  Level 1 through Level 4 for supported
  public-web anchors: package-registry metadata and transparency-log entries.
  The hosted verifier is live as a preview at https://guidecheck.org/verify;
  do not present it as fully conformant, and do not claim Level 5 conformance,
  until the supporting runtime fixture suites are complete.
- Add a Level 4 manifest for GuideCheck's own guide after an independent hash
  anchor is published.
- Add a signed or otherwise independently anchored `security.txt` plan before
  claiming it as a Level 4 channel.
- Add immutable release URLs and a static fixture for the tagged 0.2.0 release.
- Add signed verifier-report envelopes for hosted checker and CI consumption.
- Track repo-local blockers before executable Level 5 work in
  `docs/pre-level-5-readiness.md`.

## Documentation work

- Extend the contents-with-anchor-links approach added to `spec.md` to
  `verifier-conformance.md` so both docs are navigable without depending on
  section numbers.
- Expand verifier author guidance with examples of compact reports and full
  machine-readable output.
- Add a non-normative AOS integration note describing how GuideCheck verifier
  output, guide hashes, action ids, approval decisions, and stop conditions
  can feed OWASP Agent Observability Standard trace, guardian, and AgBOM
  surfaces. The note must not make AOS a GuideCheck conformance dependency or
  imply OWASP endorsement.

The three integration notes below were added in the 0.3.x cycle and are
advisory perimeter documents, not core roadmap commitments. "Keep in sync"
means they track the normative documents; each may be restructured or
withdrawn without a profile version change.

- Keep the non-normative ACS integration note in `docs/acs-integration.md`
  describing how GuideCheck verifier output, action ids, approval gates,
  egress declarations, and stop conditions can feed Agent Control Standard
  runtime hooks, Guardian Agent verdicts, trace records, and AgBOM inventory.
  Keep ACS as a runtime-control integration surface, not a GuideCheck
  conformance dependency.
- Keep the non-normative MCP integration note in `docs/mcp-integration.md`
  describing where `assistant-guide.txt` can add value for MCP server
  installation guides, server manifests, tool permission review, resource
  exposure review, and MCP-host runtime enforcement. Keep the profile
  vendor-neutral and avoid making MCP a required transport or discovery
  mechanism.
- Keep the non-normative A2A integration note in `docs/a2a-integration.md`
  describing where GuideCheck can add value for Agent Card review,
  delegated-task instructions, remote-agent provenance, approval boundaries,
  and A2A task artifacts that instruct an assistant to act.
- Add an ecosystem relationship map showing how GuideCheck fits with
  Graceful Boundaries, Skill Provenance, Turnfile, Siteline, AI Posture, ACS,
  MCP, A2A, and AOS as delegated-agent trust infrastructure.
- Add a machine-onboarding page that summarizes GuideCheck's purpose,
  conformance limits, integration surfaces, and canonical docs for assistants
  and search systems without changing normative requirements.
- Add or refine a compact comparison of rendered review, raw-source review,
  and GuideCheck review integrity for public-facing education.
- Add a short threat-model primer for maintainers adding new finding ids.
- Expand the verifier examples page with full passing, failing, `not-found`,
  and warning-bearing JSON reports generated from current fixtures.

## Implementation work

- Maintain the local-file reference verifier CLI for Levels 1 through 3 and
  the hosted public-web verifier for Levels 1 through 4 on shared content and
  provenance checks. Do not extend either verifier to Level 5 runtime
  conformance until the supporting fixtures exist.
- Keep `scripts/eval_guidecheck.py` as a regression harness and reference map,
  not the verifier implementation.
- Continue separating the reference verifier from repository regression checks
  while preserving the same normalized fixture expectation contract.
- Emit machine-readable verifier output and the compact human-readable report
  from the same evidence model.
- Extend schema and fixture coverage as the local-file CLI contract evolves.
- Add exact JSON Schema validation for manifest, verifier output, and fixture
  expected files using a pinned portable tool.
- Add public-web replay fixtures through local HTTP servers for TLS edge cases
  and additional header variants.
- Replace modeled public-fetch scenarios with replayable public-web fixtures
  where practical, while keeping non-network deterministic tests as the default
  CI path.
- Add deterministic tests for the remaining cross-channel hash anchor types.
- Add tests for registry-url parsing across npm, PyPI, Cargo, and generic
  registry records.
- Treat runtime-policy mapping for tool calls, MCP tool invocations, and
  delegated A2A tasks as optional Level 5 enforced-surface design research.
  Do not make those surfaces core conformance dependencies without a future
  profile decision.
- Add example machine-readable event records for guide verification, action
  selection, approval prompts, approval results, command execution, egress
  checks, and stop-condition denials so AOS-compatible or other observability
  systems can consume GuideCheck evidence without treating the hosted verifier
  as a central oracle.

## Release readiness

- Public repository URL configured and documented.
- Default branch and remote publishing flow verified.
- Canonical site serves `/.well-known/assistant-guide.txt`.
- Canonical site serves schemas at `https://guidecheck.org/schemas/`.
- Canonical site serves or links machine-readable verifier output.
- Guide hash is published through at least one independent channel.
- `security.txt` expiration and contact ownership are reviewed.
- The changelog for the current profile version is complete.
- All static fixtures and generated evals pass in CI.
- Each release packages the fixture suite and schemas as a standalone
  conformance kit with a `SHA256SUMS` file, so independent verifier authors
  can target a pinned corpus. Cryptographic signing of the kit is planned
  once a signing mechanism is chosen (minisign or Sigstore are the
  candidates); until then the SHA256SUMS file published with the GitHub
  release is the integrity reference.
