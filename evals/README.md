# GuideCheck Evals

The local eval suite is dependency-free and runs against both the static
fixture corpus and generated edge cases derived from the profile.

## Quick run
```text
make eval
```

Direct script invocation is also supported:
```text
python3 scripts/eval_guidecheck.py
```

Run the complete local test set with:
```text
make test
```

## Status

The eval runner is not the normative verifier. It is a regression harness
for this repository and a reference map for verifier authors. It covers:

- valid Level 1/2, Level 3, and Level 4 local-file guides
- byte-profile failures
- disallowed constructs
- compact verification instruction checks
- metadata parsing and URL checks
- required Level 3 section checks
- action block parsing and approval gates
- command, cwd, env, and egress checks
- prohibited chaining and encoded-execution patterns
- manifest hash, byte-count mismatch, missing-anchor, and anchor-divergence checks
- local public-fetch safety scenarios for HTTP, SSRF, TLS, and redirects

The authoritative conformance target remains the fixture suite described in
`fixtures/README.md` and `verifier-conformance.md`.

## What the eval runner checks

The runner has three inputs:

- static fixture directories under `fixtures/`
- generated local-file guide mutations derived from the valid Level 3 fixture
- generated public-fetch scenarios that model URL, TLS, redirect, and SSRF risks

Additional Makefile targets check the reference verifier fixture contract,
fixture and verifier-output structure, hosted API behavior with stubbed fetches,
repository guide artifact byte profiles, and deterministic fetch replay cases
for redirects, response size limits, headers, and content variation.

The static fixture checks assert the normalized `expected.json` contract:

- achieved level
- blocking finding ids
- required warning ids
- guide hash and byte count where present
- Level 5 readiness

The generated local-file cases are intentionally broader than the starter
fixture corpus. They check edge cases that should eventually become static
fixtures, but are kept generated for now so the repository can move quickly
without hundreds of copied guide files.

The generated public-fetch cases do not perform network access. They model
fetch safety decisions, including HTTP rejection, localhost and private-IP
blocking, cloud metadata address blocking, TLS failure, and cross-domain
redirect findings.

## Normative boundaries

Use the eval runner to catch regressions in this repository. Do not cite
`scripts/eval_guidecheck.py` as the standard. Normative requirements live in:

- `spec.md`
- `verifier-conformance.md`
- `schemas/`
- static fixtures under `fixtures/`

When the script and the normative documents disagree, update the script or
open a standards issue. Do not silently reinterpret the standard through the
script.

## Promotion path

Generated eval cases should be promoted into static fixtures when:

- a finding id becomes part of verifier conformance expectations
- an edge case is security-critical enough to be a hard conformance gate
- a verifier implementation needs a stable corpus file for interoperability
- the generated mutation is too subtle to remain embedded in script code

Promotion means creating a fixture directory with `guide.txt`, optional
`manifest.txt`, optional `anchors/` evidence files, and `expected.json`, then
updating `fixtures/README.md` and `finding-ids.md` in the same change.

## Maintenance rules

Changes to any of the following should run `make eval`:

- guide profile rules
- verifier profile rules
- schemas
- examples
- fixtures
- finding ids
- `assistant-guide.txt`

If an eval expectation changes, document why in the commit message or PR
description. For normative changes, update `CHANGELOG.md` as required by
`CONTRIBUTING.md`.
