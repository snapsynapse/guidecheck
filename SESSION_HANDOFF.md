# Session handoff

Date: 2026-07-21

Scope: Handoff disposition review and adopter-friction fixes validated against
the Harnessie GuideCheck adoption.

## Completed

- Reviewed the root handoff, four gitignored working handoffs, and two archived
  genesis/migration handoffs against the 0.7.0 repository state, then prepared
  the resulting fixes for the 0.7.1 patch release.
- Confirmed that release signing, additional Level 4 anchors, GuideCheck's own
  Level 4 posture, and the Vercel migration are complete. Sigstore cosign
  keyless is the release and conformance-kit signing mechanism from 0.6.0.
- Validated the Harnessie field report against `/Users/snap/Git/harnessie`, its
  adoption commits, current guide, manifest, artifact-sync tests, and release
  record.
- Fixed compact verification-instruction matching when a concept pair such as
  `blocking findings` wraps across lines.
- Narrowly exempted CLI result prose such as `tool eval (expect ...)` from the
  JavaScript detector while retaining blocking coverage for `eval` calls with
  no space, spaces, newlines, and mixed case.
- Added regression tests for both false blockers, normalized the wrapped
  single-authority check, and promoted wrapped verification wording into the
  static Level 1 fixture contract.
- Added GitHub Pages `.nojekyll` and response-header guidance, clarified
  `immutable-release-url` authoring order, and documented Level 4 rotation.
- Documented that volatile facts such as current test counts create rotation
  liabilities and require semantic checks beyond byte/hash synchronization.
- Corrected `CLAUDE.md` and `PROJECT_CONTEXT.md` where they described the
  already-resolved signing mechanism as undecided.
- Cached repeated per-action command classification, simplified the Level 5
  readiness scan, and refreshed public hosted-verifier copy from the stale
  five-fetch scope to the current seven-fetch and four-anchor scope.
- Published the 0.7.1 release from annotated tag `v0.7.1`, with reviewed release
  notes, three downloadable bundles, combined checksums, and Sigstore signing
  material. The public release workflow completed successfully.
- Narrowed the release workflow's archive glob after publication so future
  checksum and signing passes process the conformance kit exactly once. The
  duplicate 0.7.1 checksum line is harmless and both entries carry the same
  verified digest.

## Handoff disposition

- `archive/human-verifiable-plain-text-handoff.md`: historical genesis;
  superseded by the GuideCheck standard.
- `archive/vercel-migration-handoff.md`: historical migration plan; completed.
- `handoffs/2026-06-09-disposition-note.md`: demand-gating context, not a work
  order; subsequent scanner and adoption work partially overtook the park.
- `handoffs/2026-06-09-post-0.5.0-open-decisions.md`: mostly resolved; retain
  the second-verifier, signed-security.txt, replay/UI/fuzz, and Level 5 items.
- `handoffs/2026-07-02-0.7.0-transitive-execution-proposal.md`: normative work
  applied in 0.7.0; verifier enforcement remains active 0.7.x work.
- `handoffs/2026-07-07-harnessie-adoption-field-report.md`: adopter-friction
  fixes applied here; same-control-plane anchor handling remains open.

## Next candidates

1. Rotate `_assistant-guide.guidecheck.org` to the 0.7.1 guide digest:
   `v=1; sha256=4b30202c809a3db037290371da8fed6a9681255199e0e19cfe1a0a7fc1d5df9e; url=https://guidecheck.org/.well-known/assistant-guide.txt`.
2. Resolve repository-file anchors that share a control plane with a Pages
   deployment. This needs a normative independence decision, finding id,
   detection design, hosted tests, and fixtures. Harnessie's independent DNS
   TXT anchor keeps its own Level 4 claim valid despite this general gap.
3. Implement local bounded-execution enforcement phases 1 through 3 and 5 in
   `docs/0.7-verifier-enforcement-plan.md` as a dedicated 0.7.x slice.
4. Implement hosted `exec-sha256` verification and transitive scanning only
   after resolving artifact-fetch limits and the outbound-fetch budget.
5. Keep the second verifier and Level 5 runtime work demand/readiness-gated.

## Verification

- `make test` passes: 134 eval cases, 70 reference-verifier fixtures, 80
  contract validations, the two new parser regressions, version and guide-copy
  sync, fetch safety, hosted anchors and API, fetch replay, CLI contract, and
  58 scanner tests.
- GuideCheck and Harnessie both pass the 0.7.1 local verifier with zero blockers
  and zero warnings. The maximum-size adversarial regex check completed 2,000
  scans in 0.397 seconds while retaining real JavaScript `eval` detection.
- The public release contains 12 assets. All three bundle hashes match the
  published `SHA256SUMS`, and all four signed artifacts verify against the
  release workflow's GitHub Actions OIDC identity.
- The live guide and manifest serve the 0.7.1 digest. The independent DNS TXT
  anchor still serves the prior digest and is the only outstanding release
  rotation step.
