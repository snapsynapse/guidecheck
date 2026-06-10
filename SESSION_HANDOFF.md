# Session handoff

Date: 2026-06-09

Scope: Full-repo audit mitigation and the 0.5.0 release.

## Completed

- Released 0.5.0: folded the post-0.4.0 hosted hardening (fetch budget,
  content-variation probe, off-domain recommended-verifier warning,
  registry-anchor hash binding) out of Unreleased into a tagged release.
- Added `scripts/check_version_sync.py` to `make test`: asserts every
  version-bearing surface against `guidecheck_constants.py` and checks the
  published `docs/.well-known/assistant-guide.txt` byte-for-byte against the
  repository guide. It caught a second .well-known drift on its first run.
- Tightened the fixture warning contract: optional `warnings_exact` and
  `forbidden_warning_ids` fields; all 68 local-file fixtures now pin their
  warning sets exactly, so false-positive warnings fail tests.
- Added deterministic anchor-channel tests for dns-txt, repository-file,
  signed-security-txt, and transparency-log (extraction, agreement, mismatch
  blocking, absent evidence).
- Recorded the Level 5 ownership decision in `INTENT.md`: GuideCheck owns the
  runtime fixture suite and evaluator, gated by pre-level-5 readiness.
- Reframed `ADOPTION.md` so MCP/A2A are ecosystem integrations, not primary
  audiences; added explicit advisory status statements to the three
  integration notes; fixed roadmap "Maintain" framing and gave fixture-suite
  signing a stated path (SHA256SUMS now, minisign or Sigstore later).
- Marked `finding-ids.md` normative in `CONTRIBUTING.md`; documented `valid`
  and `guide_sha256` in the verifier-output schema.
- Added `make release-archive` and `make conformance-kit` targets.

## Verification

- `make test` passes at 0.5.0: 132 evals, 68 fixtures, 78 contract
  validations, version sync, and all network-safety suites.

## Open decisions

- Conformance-kit signing mechanism: minisign vs Sigstore. SHA256SUMS
  published with the release is the integrity reference until chosen.
- Second independent verifier implementation: kit packaging done; whether to
  write a minimal independent (for example JavaScript) engine or recruit an
  external implementation is undecided.

## Next candidates

- Publish the 0.5.0 GitHub release with the source archive and the first
  conformance-kit artifact.
- Design the Level 5 runtime-conformance fixture suite per the implementation
  plan, now that ownership is recorded.
- Add replay fixtures for TLS edge cases and additional public-web header
  variants.
- Promote generated metadata parser-confusion cases into static fixtures.
