# Fixture Suite

The conformance test corpus for the GuideCheck Verifier Conformance Profile. A
verifier is conformant for a verifier-profile version only if it passes the
fixture suite for that version (verifier-conformance section 29).

## Layout

Each fixture is a directory containing:

- the input artifact, named `guide.txt`, and optionally `manifest.txt`
- `expected.json`, the normalized expected result

Fixtures live under `valid/` or `invalid/` by whether the input is a conforming guide.

## Expected result format

`expected.json` specifies normalized expectations, not a byte-for-byte full
report. The expected-result schema lives at
`schemas/fixture-expected.schema.json`. Conformant verifiers may differ in
wording but MUST agree on:

- `achieved_level`
- `blocking_finding_ids`: the set of `error`-severity finding ids
- `required_warning_ids`: warning ids the fixture asserts must appear
- `guide_sha256` when the guide bytes are evaluated
- `level5_ready`

Example:
```
{
  "achieved_level": 2,
  "blocking_finding_ids": ["byte-profile.no-tabs"],
  "required_warning_ids": [],
  "level5_ready": false
}
```

## Status

This is the v0.2.0 starter set. The full suite enumerated in
verifier-conformance section 29 is in progress.

The current static corpus includes:

- valid Level 1, Level 2, Level 3, and Level 4 examples
- GuideCheck's own repository guide and a real-world PrompterKit Level 3 guide captured from
  `https://prompterkit.app/.well-known/assistant-guide.txt`
- byte-profile failures for tabs, CRLF, non-ASCII, NUL, ANSI escape, other controls, overlong lines, and oversize guides
- disallowed constructs for HTML, Markdown images, data URLs, and JavaScript
- compact verification instruction failure
- single-authority verifier language
- metadata key, URL, status, date, and revoked-status failures
- missing required section
- malformed or incomplete action blocks, duplicate ids, and invalid enum values
- missing approval gates, including `code-executing`
- networked action missing egress and broad egress wildcard
- shell runner and missing `code-executing` warnings
- command chaining, substitution, non-normal pipes, destructive glob, cwd, and env failures
- chained-guide, next-guide, guide-rewrite, skip-approval, and encoded-execution prohibitions
- manifest hash and byte-count mismatch
- missing independent anchor and cross-channel hash divergence
- Level 5 readiness true and false cases for otherwise valid Level 4 guides
- public-fetch SSRF, TLS, cross-domain redirect, header, and content-variation scenarios

Cases still to add:

- additional metadata parser-confusion cases
- public-fetch redirect-chain details beyond the modeled cross-domain case
- additional replay fixtures for TLS edge cases and public-web header variants
- additional Level 4 anchor scenarios for registry, repository, signed security.txt, and transparency logs

Some additional mutation cases remain covered by generated local evals in
`scripts/eval_guidecheck.py`. Promote a generated case into this static corpus
when it becomes a verifier conformance gate.

Contributions that add a fixture must include `guide.txt` and `expected.json` and update this list.

## Finding ids

The finding ids used in `expected.json` files are defined in `finding-ids.md`.
The current registry covers the starter fixture suite. New fixtures that
introduce new required finding ids must update the registry in the same change.
