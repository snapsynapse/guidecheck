# GuideCheck 2.0.0 candidate

Candidate version: 2.0.0

Status: Unpublished candidate. No tag, package, GitHub Release, deployment, or
hosted-service update is claimed.

The candidate introduces the opt-in `corrected-content-1` policy for explicitly
declared 2.0.0 guides and retains the `1.0.0-strict` anchor policy. Legacy
0.7.1 behavior, published 1.0.0 behavior, the self-guide, and frozen reports
remain unchanged.

The experimental POSIX JSON CLI selector `--contract posix-json-v1` is
independent of guide-declared profile selection. See [the CLI contract](cli-contract.md).

Read the repository [candidate release notes](../RELEASE_NOTES-2.0.0.md) and
[corrected-content policy](corrected-content-policy-2026-09-07.md) for scope.

## Delivery order and authority

Local implementation, testing, and checkpoint commits are authorized. The
candidate pull request provides review and exact-commit CI. Main integration
automatically deploys through the existing Vercel Git integration. Main
integration, final publication wording, tag, GitHub Release, and production
verification form the next delivery tranche and require explicit approval.

1. Validate `make test test-verify-ui`, the public-contract build, and the
   isolated installed-wheel consumer. Preserve the full legacy and strict
   report baselines and all anchored self-guide bytes.
2. Push the candidate branch and open a draft pull request. Require green CI
   on both Python 3.10 and 3.12. Inspect Vercel preview status and compare its
   deployment manifest with the exact candidate commit and local digests.
   Exercise hosted legacy, strict, and corrected selection against controlled
   evidence. A successful build alone does not establish hosted acceptance.
3. After delivery approval, finalize candidate wording and release metadata
   together, including `LATEST_RELEASED_PROFILE_VERSION`, version/date checks,
   normative profile status, release notes, and public surfaces. Rerun relevant
   gates on that final content and require exact-commit CI before merging.
4. Merge through the normal pull request path, without administrator bypass.
   Verify main CI, Vercel production source identity, published contract bytes,
   existing legacy adopter results, strict anchor qualification, and corrected
   profile selection. Do not migrate adopter guides or rotate anchors.
5. Tag the verified release commit `v2.0.0`. The existing release workflow
   builds source tar/zip and a conformance-kit tarball, signs them and the
   combined SHA256SUMS with Sigstore, and publishes the GitHub Release using
   `RELEASE_NOTES-2.0.0.md`. No package-index publication is configured.
6. Download every asset, verify digests/signing identity and archive contents,
   install the released source in an isolated consumer, and record final
   provider evidence. Close issue 2 and advance its portfolio item only when
   its recorded completion boundary has been satisfied.

## Recovery and deferred work

The baseline for this preparation is main commit
`1bd5f3d6e31f79ca6125e7da03ec1746934eb6b5`. Reconcile production and origin
again before publication; this recorded commit is not a live deployment
receipt. A compatibility regression or mismatched manifest blocks delivery.
Preserve failing evidence and choose a reviewed revert or promotion of the
verified prior deployment. Do not move published tags or rewrite main.

Real-browser UI acceptance is separate from the deterministic DOM tests.
Signing/account configuration, OpenSSF/citation maintenance, Level 5, hosted
execution-artifact fetching, and adopter migrations remain separate work.
Portfolio CLI standardization can reuse this pilot's documented result
semantics after delivery; it is not a prerequisite for GuideCheck.
