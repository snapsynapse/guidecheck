# Version-aware anchor dispatch validation

Date: 2026-09-05 America/Denver; public observations occurred on September 6 UTC.
State: pre-publication validation snapshot. Subsequent release and deployment
authority is recorded in `release-1.0.0.md`; this snapshot is not a live deployment receipt.
Release package: 1.0.0. Self-guide and legacy engine: 0.7.1.

## Result

Supported legacy declarations select the preserved 0.7.1 evaluator. Explicit
1.0.0 declarations select the strict evaluator, where repository-file hashes
remain visible but do not qualify toward Level 4. Caller profile assertions
reject incompatible declarations instead of reinterpreting guide bytes.
No observed legacy result was downgraded by the candidate.

The [approved compatibility contract](anchor-policy-compatibility.md) defines
the boundary. New-profile normative candidates and example output are in
`profiles/1.0.0/`; the separate schemas are in `schemas/1.0.0/`.

## Baseline provenance

The reference baseline is commit
`3ceb30a58488f925844c51c5aad0bc0f94633ff7`. On session entry, local and remote main
matched that commit, GitHub reported its signature valid, and
[the exact-commit test run](https://github.com/snapsynapse/guidecheck/actions/runs/33986766432)
had completed successfully. Those observations concern the baseline, not the
uncommitted candidate. No signing or account configuration was changed.

The legacy evaluator is copied from that baseline with only its constants import
redirected to the frozen legacy constants module. Preserved artifact digests
cover both modules, transport/anchor helpers, root normative documents, the
legacy output schema, and published self-guide/manifest files. The previously
confirmed July DNS rotation is still recorded in the roadmap; no new rotation
has been performed or assumed necessary.

## Local verification

| Gate | Result |
|---|---|
| `make test` | Passed, including all prior suites and new profile/compatibility checks |
| Existing regression corpus | 138 evals, 74 reference fixtures, 84 contract fixtures passed |
| Full legacy report replay | All 74 local reports and 25 hosted responses equal the captured baseline |
| Legacy version scenarios | 54 checks across nine pinned legacy versions passed |
| Strict profile tests | 11 test methods, including six static fixture cases, selector rejection, caller assertions, manifest binding, unknown channels, CLI behavior, and mixed-request execution passed |
| `make test-verify-ui` | Actual form/render/copy/download JavaScript passed in a deterministic DOM adapter, including alternating legacy/new reports |
| Preserved artifact checks | Frozen engine, normative legacy files, schema, transport, self-guide, and manifest digests unchanged |
| Installed wheel | Built 1.0.0 wheel, installed only into a temporary directory, and exercised its actual console entry point outside the repository |
| AIDR lint and `git diff --check` | Passed |

The [package receipt](anchor-dispatch-package-check.json) records its digest and
entry-point checks: package version, legacy success, strict conformance result,
and profile-requirement rejection. Nothing was installed globally or published.
Core verification remains dependency-free Python; the separate UI contract uses
Node 18+. The established `make test` entry point does not acquire a Node
requirement. CI is configured to run both targets after an authorized push.

The UI test is not a real-browser smoke test. Hosted CI, source/conformance-kit
release assets, and a deployed candidate have not been verified in this session.

## Adopter comparisons

[Machine-readable receipts](anchor-dispatch-adopters.json) contain paths,
declarations, hashes, verifier ranges, observed CI references, and results.

- All 25 discovered local guide paths across 16 repositories produced identical
  complete reports under baseline and candidate at the same fixed time.
- For all 16 distinct public guide URLs, the baseline hosted evaluator fetched
  the current public guide and available evidence. The candidate replayed those
  exact responses, including fetch failures, at the same evaluation time.
  Every complete response and fetch-set comparison matched.
- The current public verifier was separately queried for all nine adopters with
  manifest declarations. Production and candidate had the same guide hash and
  achieved level in every case. This comparison establishes level/hash parity;
  it is not a claim that the deployed source commit was identified.

| Currently observed Level 4 adopter | Production | Candidate |
|---|---|---|
| Agentlink | 4 | 4 |
| AI Incident Law | 4 | 4 |
| Knowledge-as-Code | 4 | 4 |
| PrompterKit | 4 | 4 |

Existing production findings were unchanged: AI Posture reports missing manifest
fields; GuideCheck and Harnessie report an anchor hash mismatch; Obligation First
reports an encoded-execution finding; A11y Audit reports a malformed action block.
These are inherited observations, not newly introduced failures or a diagnosis
of their causes. Investigating them is a separate maintenance queue. In
particular, an anchor mismatch alone does not identify DNS as the cause or
authorize repeating the completed DNS rotation.

Known first-party evidence cannot establish zero regressions for unknown external
users. The legacy path, unchanged public artifacts, preserved response contract,
and lack of an automatic migration/sunset policy protect that compatibility
boundary. Any future unsupported adopter declaration is a rollout stop for
explicit assessment, not permission to silently downgrade or rewrite it.

## Delivery gates at the pre-publication snapshot

1. Stage and commit the authorized release; push and verify CI against
   that exact commit. No current CI result covers the uncommitted candidate.
2. Prepare the major release with explicit version/status updates, versioned
   public documentation, and source/conformance-kit artifact verification.
   Preserve legacy references and the self-guide's existing anchored bytes.
3. Review staging and rollback steps before the authorized deployment.
   Recheck the candidate on staging against the known adopters before changing
   the public endpoint. Do not treat these local checks as deployed verification.
4. Keep existing adopter findings separate from release migration. No dependent
   repository, DNS record, hosted guide, manifest, or existing release is changed
   by the candidate. Subsequent delivery is covered by `release-1.0.0.md`.

The September 5 anchor handoff is processed: its durable decision and evidence
are in the AIDR, compatibility contract, this report, receipts, and roadmap.
The separate September 1 signing/OpenSSF/citation handoff remains unprocessed.
