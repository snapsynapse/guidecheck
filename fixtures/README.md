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

- valid Level 2 and Level 3 examples
- a real-world PrompterKit Level 3 guide captured from
  `https://prompterkit.app/.well-known/assistant-guide.txt`
- byte-profile failures for tabs, CRLF, non-ASCII, overlong lines, and oversize guides
- compact verification instruction failure
- metadata URL failure and revoked status
- missing required section
- malformed or incomplete action block
- missing approval gate
- networked action missing egress
- shell runner warning
- chained-guide and encoded-execution prohibitions
- manifest hash mismatch

Cases still to add:

- valid Level 4
- valid Level 1
- additional metadata parser-confusion cases
- duplicate action ids and invalid action enum values
- code-executing action omitted
- environment variable and cwd failures
- command chaining, substitution, pipes, redirection, and destructive glob failures
- guide with cross-channel hash divergence
- guide with stale or malformed dates
- hosted-fetch SSRF cases
- redirect chain cases
- TLS failure cases

Many of these cases are already covered as generated local evals in
`scripts/eval_guidecheck.py`. They remain on this list until they are promoted
into static fixture directories with `guide.txt` and `expected.json`.

Contributions that add a fixture must include `guide.txt` and `expected.json` and update this list.

## Finding ids

The finding ids used in `expected.json` files are defined in `finding-ids.md`.
The current registry covers the starter fixture suite. New fixtures that
introduce new required finding ids must update the registry in the same change.
