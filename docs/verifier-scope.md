# Verifier scope

What each GuideCheck verifier checks, how to run it, and its current limits. Moved from `README.md` on 2026-11-24; the README keeps a summary.

Verifier work is split by evaluation mode. Two verifiers exist:

- a local-file reference CLI, `scripts/guidecheck_verify.py`, which evaluates
  Levels 1 through 3. It also checks that any supplied sidecar manifest and
  independent-anchor evidence is internally consistent, but caps the achieved
  level at 3 and reports `level4.requires-fetch`: Level 4 asserts independent
  provenance, which can only be established by fetching the evidence from its
  real location
- a hosted public-web verifier at https://guidecheck.org/verify, which fetches
  a guide by URL and applies Level 1-3 checks. It fetches and reports declared
  Level 4 evidence but does not verify it, because the guide names where its
  anchors live and nothing binds them to the checked host, so it caps the
  achieved level at 3 and reports `anchor.hosted.unverified`. The hosted
  verifier also accepts optional
  agent category and expected-level inputs so product telemetry can show where
  specific agent families routinely miss expected conformance levels.

Both verifiers:

- evaluate `assistant-guide.txt` bytes without executing guide content
- compute and report the guide SHA-256
- check Level 1 compact verification instructions and basic source metadata
- check the Level 2 byte profile and disallowed constructs
- check Level 3 metadata, required sections, action blocks, approval gates,
  command restrictions, prohibited patterns, status, and staleness
- emit machine-readable verifier output plus the compact human-readable report

Both verifiers check Level 4 sidecar manifests plus guide hash and byte-count
matches. The local reference CLI accepts local independent-anchor evidence with
`--anchor` and confirms it is consistent, but does not assert Level 4 on local
bytes (it caps at Level 3). The hosted verifier fetches declared public-web
anchors (package-registry metadata, DNS TXT, github.com repository files) and
reports them as unverified evidence; it also caps at Level 3. Neither verifier
currently asserts Level 4.

A verifier may report `level5_ready: true` for a Level 4 guide that also
passes the guide-side preparation checks for runtime enforcement. Level 5
readiness is evaluated only once Level 4 is achieved, so neither the local CLI
nor the hosted verifier reports it as true today. This is not an achieved Level 5 claim; Level 5 still requires
a conformant assistant runtime.

User-facing score language should treat this as `Guide score: Level 4 of 4`
plus `Runtime readiness: Level 5-ready`. Avoid `Level 4 of 5`, `almost Level
5`, or similar phrasing that implies the guide file is missing a final point.

Version selection: the software version is separate from a guide's declared
profile version. The guide's own bytes select the evaluation policy, and
`--require-profile-version` only asserts compatibility; it never reinterprets
legacy bytes. Frozen legacy and 1.0.0 evaluations and the 0.7.1 self-guide stay
intact.

Run the local reference verifier from a checkout with:

Literal
```bash
python3 scripts/guidecheck_verify.py assistant-guide.txt --pretty
```
Or install it via Homebrew (macOS and Linux). The formula provides
`guidecheck` (the `verify` and `scan` commands) and keeps the earlier
`guidecheck-verify` command name:

Literal
```bash
brew install snapsynapse/tap/guidecheck
```
Then verify a guide:

Replace: GUIDE_PATH -> the path to the assistant-guide.txt to verify.

Customize
```bash
guidecheck verify 'GUIDE_PATH' --pretty
```
Check Level 4 sidecar evidence for consistency (still caps at Level 3 locally,
reporting `level4.requires-fetch`):

Replace: GUIDE_PATH -> the path to the assistant-guide.txt to verify.
Replace: MANIFEST_PATH -> the path to the guide's sidecar manifest file.
Replace: ANCHOR_PATH -> the path to the local independent-anchor evidence file.

Customize
```bash
python3 scripts/guidecheck_verify.py 'GUIDE_PATH' --manifest 'MANIFEST_PATH' --anchor dns-txt='ANCHOR_PATH' --pretty
```
Run the static fixture check for the reference verifier with:

Literal
```bash
make verify-fixtures
```
The hosted verifier is a preview. It is live and usable, but it is not
presented as fully conformant: the verifier conformance fixture suite is not
yet complete, and the hosted implementation has not been shown to pass it.

Temporary limitations:

- the hosted verifier does not award Level 4. It fetches declared
  package-registry, DNS TXT, and github.com repository-file anchors and reports
  them as unverified, because the guide names their locations and nothing binds
  them to the checked host. Transparency-log and signed `security.txt` anchors
  are not fetched. Log identity, independence, and append-only evidence are not
  verified, so a declared transparency log is reported but never fetched
- the hosted verifier refuses, without evaluating it, a file larger than the
  8192-byte guide limit (`too-large`) and a submitted URL that contains a
  fragment, userinfo, whitespace, a backslash, or non-ASCII characters
  (`invalid-url`); it runs under a 30 second function limit
- the hosted endpoint accepts only `Content-Type: application/json`
  (`unsupported-media-type` otherwise) and refuses a browser request whose
  `Origin` is another site (`origin-not-allowed`); its best-effort rate limit
  counts an IPv6 client by /64
- the hosted verifier is a Level 1-3 preview; its SSRF and abuse controls are
  covered by unit tests in `scripts/test_fetch_safety.py`; replay tests cover
  redirects, response size limits, header capture, and content variation; each
  hosted request is capped by a seven-fetch outbound budget
- no Level 5 runtime conformance claim; Level 5 remains out of scope for the
  reference verifier

Hosted verifier product telemetry is intentionally limited. It records target
host, whether the path was the standard well-known path or a custom path,
selected agent category, expected level, achieved level, outcome, failure
category, and coarse duration. It does not store full submitted URLs, query
strings, prompts, model responses, IP addresses, or stable visitor identifiers
as product telemetry. Vercel may keep standard short-lived request logs for
abuse prevention; those request logs do not include the submitted guide URL.

The current `scripts/eval_guidecheck.py` remains a regression harness and
reference map, not the verifier itself. The reference verifier lives in
`scripts/guidecheck_verify.py` and is checked against the same static fixture
expectation contract by `scripts/check_reference_verifier.py`.

## Local evals

Run the local regression suite with:

Literal
```bash
make eval
```
Run the full local verification suite with:

Literal
```bash
make test
```
The eval runner checks the static fixture corpus plus generated edge cases
for byte profile, metadata, action blocks, command restrictions, prohibited
patterns, Level 4 manifest and anchor evidence, and public-fetch safety. It is
a repository regression harness, not the normative verifier. See
`evals/README.md`.

CI runs the same `make test` target on pushes to `main` and pull requests.
