# Pre-Level-5 Readiness

Status: repo-local readiness note.

This note lists the work GuideCheck should finish before taking on executable
Level 5 runtime conformance work. It is not a Level 5 profile and does not
create a runtime conformance claim.

## Current boundary

GuideCheck can prepare for Level 5, but it must not claim Level 5 yet.

Valid current language:

- `Guide score: Level 4 of 4`
- `Runtime readiness: Level 5-ready`
- `Runtime: Level 5 evaluated for guide <sha256>` as future claim language

Invalid current language:

- `Level 4 of 5`
- `almost Level 5`
- statements that a conforming guide is safe to follow
- statements that a conforming guide or verifier makes the publisher trusted

The guide-only verifier remains capped at achieved Level 4. It may report
`level5_ready`, but that signal is guide-side preparation only.

## Ordered blockers

1. Finish the Level 1 through Level 4 fixture contract.
2. Validate fixture expectations, verifier output, and manifests against the
   published schemas in the repo-local test path.
3. Keep hosted verifier claim language conservative until it passes the
   applicable fixture suite.
4. Add GuideCheck's own Level 4 manifest and independent anchor only after the
   external publication path is ready.
5. Keep Level 5 runtime docs as design drafts until the runtime fixture suite
   and evaluator profile exist.

## Repo-local work

Repo-local work can be done without DNS, release signing, or external
publication:

- add static verifier fixtures for known generated or documented gaps
- validate schemas and schema-shaped outputs in `make validate-contracts`
- publish examples of correct and incorrect conformance claim language
- document the Level 5 runtime profile as a non-normative draft
- document the future implementation sequence for runtime conformance

## Externally blocked work

The following work needs external systems or release decisions and should not
be treated as part of repo-local readiness:

- publishing signed `security.txt` evidence
- signing verifier reports
- claiming any runtime reaches Level 5

### Resolved in 0.6.0

- publishing a DNS TXT hash anchor: the hosted verifier resolves
  `_assistant-guide.<canonical-host>` over DNS-over-HTTPS, and
  GuideCheck's own guide publishes the record at
  `_assistant-guide.guidecheck.org`
- creating immutable release URLs for GuideCheck's own guide: each
  release tags `v<version>` so the GitHub release page is the immutable
  reference recorded in `assistant-guide-manifest.txt`
- signing fixture-suite releases: 0.6.0 onward signs the release archive,
  the conformance kit, and `SHA256SUMS` with Sigstore cosign keyless from
  the `.github/workflows/release.yml` tag workflow
- claiming GuideCheck's own guide reaches Level 4: in scope; the manifest
  at `docs/.well-known/assistant-guide-manifest.txt` plus the DNS TXT
  anchor plus the github.com repository-file anchor support a Level 4
  claim for guidecheck.org's own guide once the DNS record is in place

## Recommended next implementation slice

The next repo-local slice before Level 5 should:

1. Add schema-backed validation to the existing contract checks.
2. Promote small generated or documented gaps into static fixtures.
3. Update fixture documentation so current coverage and remaining gaps are
   explicit.
4. Link Level 5 design drafts from planning docs only.
5. Run the full local suite and keep Level 5 out of the verifier claim path.
