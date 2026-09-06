# GuideCheck 1.0.0 delivery procedure

Scope: this repository's approved version-aware dispatcher, public contracts,
signed GitHub source/conformance assets, and Vercel deployment. Sam explicitly
authorized staging, commit, push, release, and deployment after reviewing the
local compatibility evidence. Dependent repository and anchor bytes stay intact.

The [pre-publication validation](anchor-dispatch-validation.md) is a dated
snapshot. Live completion is established by the exact-commit GitHub checks,
[tag and release](https://github.com/snapsynapse/guidecheck/releases/tag/v1.0.0),
Vercel deployment status, and [production manifest](https://guidecheck.org/deploy-manifest.json).
The local execution receipt is `build/release-state-1.0.0.json`.

## Delivery gates

1. Prepare version 1.0.0, versioned public contracts, release notes, and an
   independently pinned 0.7.1 legacy engine and self-guide. Run all local gates,
   build and smoke the installed package, and check preserved artifact digests.
2. Commit the scoped release on `codex/release-1.0.0`. Push and open a release
   pull request to run CI and Vercel preview. Verify preview source identity,
   existing adopter levels/hashes, strict dispatch, and caller rejection.
3. Once checks pass, fast-forward the same commit to main and verify exact-commit
   main CI and Vercel production. The Git integration deploys main automatically;
   main publication and production deployment are one authorized transition.
4. Tag the verified commit `v1.0.0`. Let the existing release workflow run tests,
   build archives, sign them, and create the GitHub Release from the tracked notes.
5. Download every published artifact; compare provider digests, SHA256SUMS,
   archive contents, and signing evidence. Install the released source outside
   the checkout. Recheck immutable profile links and production identity.

## Deployment guard and recovery

The pre-release production commit is
`3ceb30a58488f925844c51c5aad0bc0f94633ff7`; its successful Vercel deployment is
`https://guidecheck-7awy2ng36-subscriptions-8034s-projects.vercel.app`.
No deployment deletion or retention change is part of this release.

A candidate regression in a known legacy adopter blocks main publication.
Production must match the released commit, report dispatcher version 1.0.0, and
preserve current legacy guide hashes and levels. A failed deployment or mismatched
identity is incomplete delivery, even if CI is green. Strict test-guide fetch
failures must never produce a false conformance success.

If production introduces a regression, preserve the failing response and compare
it to preview and the recorded baseline. Stop further publication. Recovery is
promotion of the known prior Vercel deployment or a reviewed revert commit;
choose based on live provider access and the failure. Do not force-push main,
move a published tag, change adopter declarations, or rotate anchors to mask it.

A real-browser UI smoke is not included in the deterministic DOM test evidence.
Package registries, account signing configuration, OpenSSF, and search-console
submissions are outside this release.
