# SEC-003 checkpoint 2: local worker candidate

Scope: worker candidate and private synchronous transport extraction after
re-reviewing the corrected checkpoint-1 proof. No activation, release, or profile
change. Commit, CI and inactive deployment identity are separate delivery checks.
Review base: `96c648e`. The reviewed candidate remains inactive; delivery is
recorded in git history separately from activation and SEC-003 closure.

## Checkpoint 1 re-review

All three proof findings are resolved: deadline expiry after result validation
is rejected, cleanup failures do not skip independent recovery/pipe closure,
and ready/result frame schemas and PIDs are checked. The eight regressions
passed again on Python 3.12.16 and 3.15.2. The retained 196-check proof receipts
and corrected source hashes match. No new finding in that focused re-review.

Detailed local evidence remains in
`out/security-sec003-worker-proof-2026-11-08/`; the original review baseline
and its earlier receipts are preserved there as well.

## Candidate implemented

`scripts/guidecheck_fetch_worker.py` provides an experimental `supervised_fetch`
entrypoint. A fixed isolated child runs the existing synchronous transport.
The API and scanner still call their original `safe_fetch` path; this candidate
does not mitigate the deployed SEC-003 path yet.

- One absolute deadline covers admission, process startup, nonblocking request
  writes, response reads, child completion, and result validation. A caller can
  shorten the existing 12-second local budget. Late results are rejected.
- The parent caps input at 64 KiB and output at 2 MiB, using nonblocking pipe I/O.
  The output cap accommodates base64 for the 256 KiB body plus bounded metadata;
  decoded bodies remain capped at 256 KiB. These are candidate IPC resource
  limits, not changes to normative profiles or anchored artifacts.
- Ready/result frames bind to the child PID. Results validate status, body,
  headers, redirect structure/count and TLS-result type. The parent owns error
  messages; child diagnostics and tracebacks are not relayed.
- A warm parent supervisor admits at most two child processes. Cancellation
  attempts terminate, then kill/reap, with 50 ms and 500 ms cleanup grace values.
  Incomplete cleanup retains admission until explicit recovery. These candidate
  settings still need target-runtime validation.
- No shell or guide command is executed. URLs travel through bounded stdin,
  not argv. The child environment carries PATH and optional SSL_CERT_FILE/DIR;
  it does not copy arbitrary parent credentials or diagnostic settings.
- The isolated child bootstraps only its fixed module's sibling directory,
  allowing the packaged module to import the transport outside the checkout.
- The candidate is POSIX-only and fails closed on unsupported platforms. Active
  public callers are unchanged, including their existing platform behavior.

## Local validation

- Nineteen worker/boundary tests pass on Python 3.12 and 3.15, including binary data,
  profile/Accept forwarding, 60 KiB request writes, protocol/body limits, deadline
  expiry during validation, shared admission, cancellation, and cleanup faults.
- The checkpoint-2 cancellation review finding is fixed: incomplete cleanup
  preserves a propagating caller exception while retaining resources/admission
  for recovery. A regression proves KeyboardInterrupt identity, reaping,
  retained admission, pipe recovery and subsequent success.
- Test-only fixed child fixtures drive the actual transport into blocked DNS,
  TLS/connect, write, headers, body and real HTTPResponse chunk-parser stages.
  Each stage writes a temporary marker before blocking, so timeout assertions
  cannot pass merely because interpreter startup was slow. No external DNS or
  network requests are made; these remain controlled operation surrogates.
- Full Python/UI gates pass on Python 3.12, including compatibility replays and
  preserved-artifact checks. Focused worker gates also run on Python 3.15.
- Installed-wheel tests pass outside the checkout: the isolated candidate worker
  imports correctly and rejects a plaintext scheme with a sanitized error.
  Existing profile, CLI and scanner consumer checks pass. The wheel was built
  and installed only in a temporary test environment; it was not published.
- The pushed `dd15e8b` candidate passed Linux CI on Python 3.10 and 3.12, plus
  CodeQL and Scorecard. This is evidence for that candidate; subsequent extraction
  CI is recorded separately. The standalone checkpoint-1 proof has not run on Linux.

## Private transport extraction

The reviewed inactive candidate was committed and pushed as `dd15e8b`. The
subsequent extraction was implemented and locally validated against that baseline.

- Public `safe_fetch` keeps its original synchronous signature and delegates to
  `_fetch_in_process`. The extracted transport body matches the previous body's
  AST; socket timeouts, redirect ordering and all network policies are unchanged.
- The default worker calls `_fetch_in_process` directly, removing its dependency
  on public `safe_fetch` before any later supervisor integration. Active API and
  scanner callers still use the public synchronous path.
- Five new regressions prove argument/result forwarding, original FetchError
  identity, unchanged synchronous interface without spawning, private child
  binding when public fetch is poisoned, and sanitized private error categories.
  They failed before extraction; all nineteen tests pass afterward. Full Python
  3.12/UI and temporary installed-wheel gates also pass on this extraction.
- Only the explicit transport digest expectation changed. The historical
  preserved-artifacts record and evaluator/profile/guide bytes remain intact.

## Remaining implementation and validation

1. Retain Linux Python 3.10/3.12 CI coverage for the extracted candidate and run
   the corrected standalone proof on those runtimes. Verify
   actual Vercel worker execution, imports, signal/reaping behavior, concurrency,
   memory/descriptor costs and effective duration in a separately authorized
   isolated preview. The standalone worker-capability proof has not been deployed
   or exercised on Vercel. Inactive production source identity and benign controls
   are verified separately from worker execution capability.
2. Active public-fetch wiring remains a separate slice after platform validation.
   Preserve direct private transport binding in the child and prevent recursive
   supervision when introducing any public deadline/supervisor interface.
3. Apply remaining-budget timeouts to the actual raw/TLS sockets. Add the shared
   hosted outbound-I/O deadline, preserve cache keys and the seven-fetch cap,
   and replace TypeError fallback retries with explicit test adapters.
4. Add the remaining real loopback TLS/status/header/body/trailer and hosted
   budget/error-contract tests. Preserve SEC-002 unread redirect cleanup, SSRF,
   TLS validation, frozen reports and guide/manifest/anchor bytes.

The proposed aggregate hosted budget remains 30 seconds pending runtime evidence.
No hard end-to-end handler deadline or Level 5 runtime claim is made. SEC-003 and
the platform gate remain open. The audit stays untracked and the sponsors handoff
is unchanged. Activation and deployment validation remain separate from this slice.
