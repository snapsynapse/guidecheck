# Security maintenance

Scope: GuideCheck repository security remediation and its remaining work queue.
Updated: 2026-11-12, America/Denver.

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
  logic. SEC-002 was subsequently committed and pushed as `96c648e`; exact-commit
  CI and production verification passed on 2026-11-08. The production receipt
  matched all fourteen source hashes and six served files, with benign DNS,
  registry and redirect controls passing. This is dated delivery evidence;
  later SEC-003 candidate delivery is separate from worker activation.
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
- A second local audit, dated 2026-11-11, is untracked at
  `docs/security/audits/audit-2026-11-11.md`. This record tracks SEC-015 from
  it, below. Reconciling the rest of that audit into this record is a separate
  decision.
- As of 2026-11-08, GitHub has no open issues or PRs and thirteen open
  code-scanning alerts. Those alerts are separate from the audit findings.
  Successful CodeQL/Scorecard runs do not close either inventory.

## SEC-002 containment and delivery

Status: committed, pushed and verified live as `96c648e` on 2026-11-08 after
local review on base `fad7f72`. Linux Python 3.10/3.12, CodeQL and Scorecard CI
passed at that commit. Retained evidence: `out/security-sec002-live-2026-11-08/`.
No software/profile version or dependency change.

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
asserts that historical value and pins the current reviewed transport digest.
The subsequent SEC-003 private extraction preserves the transport body while
changing its function boundary; its explicit digest expectation is separate.
All other preserved-artifact checks and full report replays remain unchanged.
This exception permits this transport correction, not profile reinterpretation.

Historical local validation on 2026-11-08, before the delivery checks above:

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
No packages or release archives were built during this SEC-002 proof, and no live
malicious probes ran.

## SEC-015 containment

Status: committed locally on 2026-11-12, not pushed or deployed. Production
still awards hosted Level 4 until this change is pushed and deployed. No
software/profile version or dependency change.

Finding: the hosted handler derived every anchor location from fields in the
guide bytes (DNS name from `canonical-url`, registry record from
`registry-url`, repository file from `repository-url`). Nothing compared them
with the checked URL, so whoever writes the guide chooses where its
"independent" evidence comes from. The audit reproduced Level 4 with zero
blockers from a foreign-domain DNS anchor, an attacker-named npm package, and
a legacy-profile attacker repository.

Containment by removal, as decided by Sam on 2026-11-11: the hosted verifier
no longer awards Level 4. Binding anchors to the checked host was the
alternative and was not chosen. In `api/verify.py`:

- every hosted result is capped at Level 3 and `level5_ready` is false, under
  every supported profile;
- declared anchors are still fetched and reported; each reported anchor
  carries `hosted_verification: unverified`, and under 1.0.0 and 2.0.0
  `qualifies_for_level4` is false and `qualifying_anchor_count` is 0;
- a guide that declares `manifest-url` receives the info finding
  `anchor.hosted.unverified`; by Sam's 2026-11-12 choice it is not blocking,
  so the compact report reads `Hash pinned: no` and `Proceed?` follows the
  remaining blocking findings;
- Level 5 readiness findings, evaluated only for Level 4 results, are dropped
  with the level.

The existing `qualification_reason` value is left as the profile policy
computed it, because the released schemas fix that enum. A reason value for
hosted non-qualification belongs to a future profile, not this containment.

Unchanged: the local CLI, the in-process evaluator interface, frozen engines,
released profiles, schemas, fixtures, snapshots, `preserved-artifacts.json`,
and published guide, manifest and anchor bytes. Replay tests
(`test_dispatch_compatibility.py`, `test_strict_compatibility.py`) apply an
explicit SEC-015 delta to the frozen snapshots and assert how many results it
caps: eight legacy hosted results and none of the released 1.0.0 results. The
expected `anchor.hosted.unverified` finding is derived from whether each
replayed guide declares `manifest-url`, never from the response under test.

Known consequence: the hosted report for guidecheck.org's own guide drops from
Level 4 to Level 3. Public copy on the landing page, verify page, verifier
examples, `llms.txt`, README, operator guide and examples README now states the
Level 1 to 3 scope.

Regression and adversarial coverage, all with mocked fetches, in
`scripts/test_hosted_level4_containment.py` (8 tests, 110 subtests across all
eleven supported profiles):

| Route back to hosted Level 4 | Before (HEAD handler) | After |
|---|---|---|
| Foreign-domain DNS anchor (audit reproduction 1) | Level 4, all 11 profiles | Level 3 |
| Attacker-named registry package (reproduction 2) | Level 4, all 11 profiles | Level 3 |
| Attacker repository (reproduction 3) | Level 4 for 9 legacy profiles; already Level 3 under 1.0.0 and 2.0.0 | Level 3 |
| DNS, registry and repository anchors together | Level 4, all 11 profiles | Level 3 |
| Redirect that lands on the canonical host | Level 4, all 11 profiles | Level 3 |
| DNS anchor on the checked host itself | Level 4, all 11 profiles | Level 3, no blockers |
| Anchor fields placed in the manifest | Not fetched; Level 3 | Not fetched; Level 3 |
| Caller `required_profile_version` assertion | Level 4 in 3 of 33 cases; others 400 | Level 3 or 400 |

Local validation on 2026-11-12:

| Check | Result |
|---|---|
| New suite against the unmodified HEAD handler | 67 subtests reached Level 4; 2 errored on the missing finding; exit 1. No network. |
| New suite, patched | 8 tests passed. |
| `make test test-verify-ui`, Python 3.15.2 | Passed, including frozen report replays with the counted delta, preserved-artifact checks, hosted API, transparency-log and UI contract suites. |
| `make test`, Python 3.12.16 | Passed. Python 3.10 was not available locally. |
| `build_public_contracts.py`, `check_version_sync.py`, `validate_contracts.py` | Passed; `anchor.hosted.unverified` is registered in `finding-ids.md`. |
| `git diff --check` | Passed. No frozen evaluator, profile, schema, fixture, snapshot or published guide byte changed. |

No live probe ran. Pushing, exact-commit CI, deployment and a production
check of the self-guide need Sam's go.

## Remaining remediation queue

SEC-003 checkpoint 2 has begun as a reviewed, unactivated worker
candidate. The three checkpoint-1 proof findings passed re-review. The reviewed
candidate passed Linux CI on Python 3.10/3.12; standalone-proof Linux validation,
Vercel worker capability, active-path integration and the shared hosted budget
remain open. The private extraction preserves public synchronous behavior.
See [checkpoint-2 scope and validation](sec003-checkpoint2.md). This does not
change the deployed SEC-003 disposition below.

These are the twelve findings remaining after delivered SEC-002 containment. They
retain their 2026-10-26 severity and evidence scope; no new full audit is claimed.

| Order | Finding | Severity | Next bounded work |
|---|---|---|---|
| 1 | SEC-003: total deadline during I/O | Medium | Validate the supervised candidate on target runtimes, cover real socket/parser behavior, and implement the shared hosted budget before activation. Separate from SEC-002. |
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

SEC-002 delivery and later SEC-003 proof/candidate work are separate tranches.
Sam authorized the reviewed candidate and private extraction, status reconciliation,
commits/pushes, exact-commit CI checks and inactive deployment verification. Worker
activation, a worker-capability preview, tagging/releases, DNS/registry mutations
and provider-setting changes remain outside this tranche. Prior fixture publication
authority was consumed by that completed work. Preserve frozen evaluators, normative profiles, schemas,
snapshots, guide/manifest/anchor bytes, and the published npm fixture version.
