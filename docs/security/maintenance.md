# Security maintenance

Scope: GuideCheck repository security remediation and its remaining work queue.
Updated: 2026-11-08, America/Denver.

## Baseline and delivery state

The 2026-10-26 audit reviewed commit `9b39a46` and recorded fourteen findings:
one high, eight medium, and five low. The original audit remains local and
untracked at `docs/security/audits/audit-2026-10-26.md`; its evidence dates and
historical local-only follow-up are preserved. This record tracks later state
without rewriting that audit.

- SEC-001's hosted-path mitigation was committed and pushed as `08de124`.
  Arbitrary transparency-log URLs are neither fetched nor qualified. The hosted
  handler reports `anchor.transparency-log.unverified`; supported DNS and
  package-registry anchors remain available. Twenty-eight offline regression
  cases cover all eleven supported profiles and positive controls. The trusted
  in-process evaluator interface retains its historical evidence contract.
- Fixture commit `fad7f72` added two static files without changing verifier
  logic. The public deployment manifest still identifies that commit on
  2026-11-08. SEC-002's local changes have not been deployed.
- The retained 2026-10-26 registry receipt records publication of
  `@snapsynapse/guidecheck-registry-fixture@0.0.1`, matching `latest` and
  `verification` tags, and tarball SHA-256
  `42dc42e8415ac2b6b0b95bc16f180f998f2c52b23bfcc3306ea05fb6fcca9d00`.
  At 23:43 MDT, production returned Level 4 with zero blockers and package-registry
  as the sole qualifying anchor. Guide/manifest/registry evidence matched guide
  SHA-256 `3566a9b52bc4549bc40660211fbd13cebf2abc10fc091a047dcd885207ad1afe`.
  Repository evidence matched but did not qualify. The fixture retains its
  disclosed nonstandard path and inherited review date. This is dated evidence,
  not a fresh registry verification or human attestation.
- Detailed local receipts remain in
  `out/registry-anchor-verification-plan/live-verification.md` and its
  `live-evidence/` directory. The earlier mocked SEC-002/SEC-003 observations
  remain in `out/security-followup-2026-10-26/fetch-probe.json`.
- As of 2026-11-08, GitHub has no open issues or PRs and thirteen open
  code-scanning alerts. Those alerts are separate from the audit findings.
  Successful CodeQL/Scorecard runs do not close either inventory.

## SEC-002 local containment

Status: implemented and locally reviewed on base `fad7f72`; local commit
authorized after review. Unpushed and undeployed. No software/profile version
or dependency change.

`safe_fetch` captures each redirect's Location and closes the response without
reading its body. Every hop already opens a fresh connection and sends
`Connection: close`; draining an unused body serves no reuse purpose. Explicit
response closure also covers streams detached from the connection by
`http.client`. The existing `finally` still closes the connection.

The patch retains missing-target errors, relative URL resolution, redirect
history/count limits, scheme/domain/IP checks, TLS validation, variation
headers, sanitized errors, and final-response Content-Length/MAX_BYTES checks.

Regression coverage in `scripts/test_fetch_replay.py` includes:

- All five statuses (301, 302, 303, 307, 308) with body-read traps under oversized
  Content-Length, absent Content-Length, and chunked framing.
- Missing/empty Location for every status, with no body reads or next request.
- Scheme/domain/private-address rejection, including real per-hop IP validation
  against mocked DNS; maximum-length chains and redirect exhaustion.
- Response and connection closure before the next connection; cleanup on final
  read timeout/error and next-hop DNS failure.
- Real standard-library HTTPResponse parsing over in-memory streams for all
  three framing variants, including chunk-header and body-read traps.
- Final bodies at MAX_BYTES and MAX_BYTES+1 with absent, malformed, or
  underreported Content-Length; existing declared-length rejection remains.

The historical `fixtures/compatibility/preserved-artifacts.json` is unchanged.
It includes the old fetch-source digest, so `test_profile_dispatch.py` explicitly
asserts that historical value and pins the reviewed SEC-002 replacement digest.
All other preserved-artifact checks and full report replays remain unchanged.
This exception permits this transport correction, not profile reinterpretation.

Validation on 2026-11-08:

| Check | Result |
|---|---|
| New regression cases against the unmodified HEAD fetch module | 105 failed assertions; exit 1. Body reads and missing stream closure reproduced without network traffic. |
| Patched fetch replay suite | 187 passed, 0 failed. |
| Fetch-safety suite | 36 passed, 0 failed. |
| `make test test-verify-ui`, Python 3.15.2 | Passed, including frozen report replays, preserved-artifact checks, hosted anchor/API positives, and UI contract. |
| `make test test-verify-ui`, Python 3.12.16 | Passed on a supported runtime. Python 3.10 was not available locally; no new CI run was triggered. |
| Additional offline review probes, Python 3.12.16 | 90 cases passed through real HTTPSConnection/HTTPResponse classes across all five redirect statuses, three framing variants, close/keep-alive responses, missing targets, and rejected destinations. No actionable review findings. |
| Original audit and sponsors handoff | SHA-256 values match the pre-edit baseline; both remain untouched. |
| `git diff --check` | Passed. Frozen evaluator/profile/schema/fixture and published guide bytes have no diff. |

Local logs: `/private/tmp/guidecheck-sec002-red-final.log`,
`/private/tmp/guidecheck-sec002-green.log`,
`/private/tmp/guidecheck-sec002-safety.log`,
`/private/tmp/guidecheck-sec002-full-tests.log`, and
`/private/tmp/guidecheck-sec002-python312-tests.log`. These temporary logs are
supporting receipts; the results above remain here if temporary files expire.
No packages or release archives were built and no live malicious probes ran.

## Remaining remediation queue

SEC-003 checkpoint 2 has begun as a reviewed, unactivated worker
candidate. The three checkpoint-1 proof findings passed re-review; Linux/Vercel
platform gates, active-path integration and the shared hosted budget remain open.
See [checkpoint-2 scope and validation](sec003-checkpoint2.md). This does not
change the deployed SEC-003 disposition below.

These are the twelve findings remaining after local SEC-002 containment. They
retain their 2026-10-26 severity and evidence scope; no new full audit is claimed.
Production also retains SEC-002 until a separately authorized delivery.

| Order | Finding | Severity | Next bounded work |
|---|---|---|---|
| 1 | SEC-003: total deadline during I/O | Medium | Bound DNS and remaining-budget socket operations, use incremental reads, and design the hosted overall budget. Separate from SEC-002. |
| 2 | SEC-007: nonlinear scanner CPU cost | Medium | Replace styled-element/comment regexes and repeated neighbor scans with bounded tokenization and linear passes. Scanner scope, not attributed to the hosted verifier. |
| 3 | SEC-008: clean result for truncated local prefix | Medium | Limit-plus-one local reads and an incomplete, nonzero result. |
| 3 | SEC-009: skipped NUL input returns success | Medium | Define skipped/incomplete counters and exit semantics with compatibility review. |
| 3 | SEC-010: directory inventory omits llms.txt | Low | Reconcile directory inventory with URL discovery alongside scanner completeness. |
| 4 | SEC-005: unknown execution wrappers | Medium | Select a modern-policy correction while preserving frozen reports and known-query positive controls. |
| 4 | SEC-006: redirection target escapes cwd | Medium | Reject outside/unresolved targets in an explicitly selected static policy; runtime symlinks remain separate. |
| 4 | SEC-013: empty manifest release fields | Low | Resolve modern value validation and release-reference reachability separately from frozen behavior and fetch-budget design. |
| 5 | SEC-004: cross-tenant redirect boundary | Medium | Decide exact-host redirects versus a maintained PSL including private suffixes. No private-network SSRF bypass was demonstrated. |
| 6 | SEC-011: unsanitized surface labels | Low | Escape controls in text output while retaining identities through JSON escaping. |
| 6 | SEC-012: malformed API input | Low | Normalize expected encoding/URL parse failures to sanitized 400 responses. |
| 6 | SEC-014: release tag/version mismatch | Low | Require exact tag/software-version equality before build/signing. No existing mislabeled release is asserted. |

SEC-003 remains open: removing redirect-body draining does not bound DNS, TLS,
headers, or final-body I/O by an absolute deadline. SEC-004's approximate domain
helper is also unchanged; this patch establishes no exact tenant boundary.

Governance observations, DNS-parser ambiguity, in-memory abuse controls, and
optional response-header hardening remain separate follow-up in the original
audit and roadmap. Provider configuration was not re-audited in this tranche.
Supported transparency-log adapters still need log identity, independence,
append-only evidence, and guide-entry binding before that channel can qualify.

## Queue ownership and authority

The processed 2026-10-26 security handoff is replaced by this durable record and
the current roadmap. The unrelated 2026-10-23 sponsors handoff remains pending
and unchanged; owning-entity wording still needs Sam's decision.

The authorized tranche is SEC-002, regression tests, and queue reconciliation.
Sam authorized a local commit after review. SEC-003 implementation, pushes,
publication, deployment, DNS/registry mutations, and GitHub/provider-setting changes are not
part of this tranche. Prior fixture publication authority was consumed by that
completed work. Preserve frozen evaluators, normative profiles, schemas,
snapshots, guide/manifest/anchor bytes, and the published npm fixture version.
