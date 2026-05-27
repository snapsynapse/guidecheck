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

- publishing a DNS TXT hash anchor
- publishing signed `security.txt` evidence
- creating immutable release URLs for GuideCheck's own guide
- signing verifier reports or fixture-suite releases
- claiming GuideCheck's own guide reaches Level 4
- claiming any runtime reaches Level 5

## Recommended next implementation slice

The next repo-local slice before Level 5 should:

1. Add schema-backed validation to the existing contract checks.
2. Promote small generated or documented gaps into static fixtures.
3. Update fixture documentation so current coverage and remaining gaps are
   explicit.
4. Link Level 5 design drafts from planning docs only.
5. Run the full local suite and keep Level 5 out of the verifier claim path.
