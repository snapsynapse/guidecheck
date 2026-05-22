# Fixture Suite

The conformance test corpus for the Human-Verifiable Assistant Guide Verifier Conformance Profile. A verifier is conformant for a verifier-profile version only if it passes the fixture suite for that version (verifier-conformance section 29).

## Layout

Each fixture is a directory containing:

- the input artifact, named `guide.txt`, and optionally `manifest.txt`
- `expected.json`, the normalized expected result

Fixtures live under `valid/` or `invalid/` by whether the input is a conforming guide.

## Expected result format

`expected.json` specifies normalized expectations, not a byte-for-byte full report. Conformant verifiers may differ in wording but MUST agree on:

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

This is the v0.1.0 starter set. The full suite enumerated in verifier-conformance section 29 is in progress. Cases still to add:

- valid Level 1, Level 4
- guide over 8192 bytes
- guide with overlong lines
- guide missing the compact verification instruction
- guide with metadata errors
- guide with missing required sections
- guide with malformed action blocks
- guide with missing approval gates
- guide with networked action missing egress
- guide with code-executing action omitted
- guide with shell runner lacking rationale
- guide with chained-guide instruction
- guide with encoded execution instruction
- guide with manifest hash mismatch
- guide with cross-channel hash divergence
- guide with revoked status
- guide with stale last-reviewed
- hosted-fetch SSRF cases
- redirect chain cases
- TLS failure cases

Contributions that add a fixture must include `guide.txt` and `expected.json` and update this list.

## Finding ids

The finding ids used in `expected.json` files (for example `byte-profile.no-tabs`) are provisional for v0.1.0. A canonical finding-id registry, mapping every blocking check to a stable id, is planned before the fixture suite becomes a hard conformance gate. Until then, treat the ids in this suite as the working set.
