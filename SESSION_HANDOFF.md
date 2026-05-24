# Session handoff

Date: 2026-05-24

Scope: GuideCheck verifier and adoption documentation.

## Completed

- Added local and hosted Level 4 validation coverage for sidecar manifests and supported independent anchors.
- Added `level5_ready` reporting for Level 4 guides that satisfy guide-side runtime preparation checks.
- Updated user-facing score language so guide files are described as scoring up to Level 4 of 4, with Level 5 framed as separate runtime enforcement.
- Added hosted public-web warnings for missing or incompatible reportable response headers and for guide bytes that vary across harmless request profiles.
- Added Level 4 package registry metadata examples for npm, PyPI, Cargo, and generic registries.
- Updated roadmap, README, verifier page copy, fixtures notes, and changelog to match the implemented scope.

## Verification

- `make test` passes after the hosted hardening and documentation updates.

## Lessons learned

- Avoid presenting Level 5 as a missing point in a guide-file score. The clearest user model is `Guide score: Level 4 of 4` plus a separate runtime-readiness or runtime-conformance status.
- Hosted verifier output should report only conformance-relevant response headers. Capturing every header risks exposing cookies or other operational details in public verifier output.
- Public-web hardening can advance safely as advisory findings while preserving current achieved-level semantics.
- Level 5 runtime conformance should not be implemented until a separate runtime fixture suite and runtime adapter model are designed.

## Next candidates

- Design the Level 5 runtime-conformance fixture suite separately from guide-file validation.
- Add deterministic tests for remaining cross-channel anchor types.
- Add replay fixtures for TLS edge cases and additional public-web header variants.
- Expand verifier examples with full passing, failing, not-found, and warning-bearing JSON reports.
