# GuideCheck 1.0.0

GuideCheck now selects verification policy from the guide's declared profile
version. Existing supported legacy guides keep their previous anchor eligibility,
report format, and conformance results. A guide that deliberately declares
`1.0.0` uses the stricter repository-anchor policy.

## Changes

- Under profile 1.0.0, a matching repository-file hash remains visible evidence
  but cannot qualify toward Level 4. Another qualifying anchor is required.
  A conflicting repository hash still blocks Level 4 even when DNS matches.
- Exact-profile assertions are available through `--require-profile-version`
  and the hosted API's `required_profile_version`. Incompatible declarations
  are rejected rather than reinterpreted.
- Strict reports identify the selected policy and qualifying evidence. New
  schemas and normative documents live under `schemas/1.0.0/` and `profiles/1.0.0/`.
- Package, engine, profile, and self-guide versions are independent. The
  published self-guide and manifest remain byte-for-byte unchanged at 0.7.1.
- This release also includes the bounded-execution enforcement already present
  in baseline commit 3ceb30a: named script classification, execution-pin checks,
  and opacity rationale. Valid execution pins remain declared but unverified.

## Compatibility and adoption

Legacy declarations 0.1.0, 0.2.0, 0.3.0, 0.3.1, 0.4.0, 0.5.0, 0.6.0, 0.7.0,
and 0.7.1 select the preserved pre-dispatch evaluator. Build metadata is accepted;
prereleases, version ranges, ambiguous declarations, and unsupported versions
are rejected. Legacy support has no automatic sunset. Existing adopters need
no guide, manifest, repository, or DNS changes to retain that behavior.

Consumers requiring 1.0.0 should assert it and validate the strict response
schema and `profile_selection.evaluated_policy`. An old server may ignore an
unknown request field; HTTP 200 or a legacy Level 4 report is insufficient.

The compatibility baseline is the verifier at 3ceb30a, not every historical
verifier release. The included bounded-execution enforcement predates dispatch.

## Validation

- Full Python and UI contract suites pass, including 138 evals, 74 reference
  fixtures, 84 contract fixtures, six strict cases, and mixed-request isolation.
- All 74 captured local reports and 25 captured hosted responses match the
  pre-dispatch baseline exactly. Nine legacy versions have 54 anchor scenarios.
- All 25 discovered local guide paths and 16 public fetch/replay comparisons
  matched. Separate production observations confirmed matching level and guide
  hash for nine manifest-declaring adopters; all four observed Level 4 adopters
  remained Level 4 in the candidate.
- An isolated wheel installation exercised the actual console entry point.

See [validation evidence](https://github.com/snapsynapse/guidecheck/blob/v1.0.0/docs/anchor-dispatch-validation.md)
for methods and limitations. Finite adopter checks do not establish compatibility
with every unknown external integration.

## Artifacts and limits

The source tarball, source ZIP, conformance kit, and SHA256SUMS are signed with
Sigstore keyless in the tag-triggered release workflow. No package registry
publication is part of this release; install the packaged source from this tag.

The hosted verifier remains a preview. Local verification caps at Level 3;
signed security.txt anchors are not fetched; runtime Level 5 conformance,
execution-artifact fetching, and transitive scanning remain out of scope.
Repository exclusion does not establish new administrative-independence proof
for the other retained anchor channels.
