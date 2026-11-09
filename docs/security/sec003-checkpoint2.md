# SEC-003 checkpoint 2: local worker candidate

Scope: first local implementation slice after re-reviewing the corrected
checkpoint-1 proof. No activation, deployment, release, or profile change.
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

- Fourteen worker tests pass on Python 3.12 and 3.15, including binary data,
  profile/Accept forwarding, 60 KiB request writes, protocol/body limits, deadline
  expiry during validation, shared admission, cancellation, and cleanup faults.
- The checkpoint-2 cancellation review finding is fixed: incomplete cleanup
  preserves a propagating caller exception while retaining resources/admission
  for recovery. A regression proves KeyboardInterrupt identity, reaping,
  retained admission, pipe recovery and subsequent success. The focused suites
  pass after this fix; the wider gates below describe the earlier candidate.
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

## Remaining implementation and validation

1. Run corrected proof and candidate tests on Linux Python 3.10/3.12. Verify
   actual Vercel worker execution, imports, signal/reaping behavior, concurrency,
   memory/descriptor costs and effective duration in a separately authorized
   isolated preview. No VM, CI dispatch, preview or production deployment has
   been performed for this work.
2. Before wiring active callers, give the synchronous transport an explicit
   private in-process entrypoint and point the child at it. The current child
   delegates to the still-synchronous public safe_fetch; simply replacing that
   function with the supervisor would recurse and must not be done.
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
