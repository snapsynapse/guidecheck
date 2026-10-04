# DNS anchor parsing characterization

Status: diagnostic evidence and correction proposal. No released behavior changed.
Date: 2026-10-03 America/Denver. Evaluator source baseline: `48848bf1b5b48b5ca369a48e1162e7d9b0c1daec`.

## Reproduction and findings

The [offline diagnostic](../scripts/diagnose_dns_anchor_parsing.py) exercises DNS record selection and the evaluator for all 11 supported profile declarations, using the released corrected-profile DNS fixture with consistent version and hash substitutions. It supplies DNS evidence in memory with `evidence_fetched=True`; this models fetched evidence and does not establish a public-web result. Evaluation time is fixed. The [110-case result](evidence/dns-anchor-parsing-2026-10-03.json) includes exact records, source digests, selected record, extracted hash, level and blocking findings.

Run from the repository root. Output goes to stdout; the command changes no source or evidence file.
Literal
```sh
python3 scripts/diagnose_dns_anchor_parsing.py
```

All supported declarations produced the same outcomes below. Each profile's valid control reached Level 4 with no blocking findings.

| Case | Observed level | Blocking finding |
|---|---|---|
| One valid hash and matching URL | 4 | None |
| One wrong hash | 3 | `anchor.independent.mismatch` |
| Doubled `sha256=sha256=` prefix | 4 | None |
| Two identical hash fields | 4 | None |
| Conflicting hashes, matching hash first | 4 | None |
| Conflicting hashes, wrong hash first | 3 | `anchor.independent.mismatch` |
| Matching hash embedded in `note=sha256=` | 4 | None |
| Valid hash with a different canonical URL | 3 | `anchor.independent.missing` |
| Two URL-matching TXT records, correct record first | 4 | None |
| Two URL-matching TXT records, wrong record first | 3 | `anchor.independent.mismatch` |

The extractor in `scripts/guidecheck_legacy.py::extract_anchor_sha256` searches for a hash substring instead of parsing the DNS wire fields. Both newer evaluators call that same function. `scripts/guidecheck_hosted_anchors.py::select_dns_txt_record` selects the first URL-matching record, so conflicting RRsets are order-sensitive too. This is ambiguous input acceptance, not evidence that an attacker can forge an arbitrary guide digest or bypass control of the DNS publication channel.

## Bounded correction proposal

Recommend a future explicitly selected policy with field-aware DNS parsing: exactly one version, hash and canonical URL field; a complete 64-hex hash value; no embedded or conflicting values. Define the disposition of unknown fields, identical duplicates and multiple matching TXT records in the normative text and fixtures. Conflicting matching records should not silently depend on resolver ordering.

| Option | Consequence | Recommendation |
|---|---|---|
| Patch the shared legacy extractor | Changes results for every supported profile and breaks the frozen behavior commitment | Do not apply within this maintenance tranche |
| Reject malformed DNS in the shared hosted fetch path | Changes hosted results even when the guide selects an old profile | Requires the same explicit compatibility decision |
| Add a version-selected parser and conflict policy | Preserves old results while providing an opt-in corrected contract | Preferred proposal; version and semantics remain owner decisions |

This diagnostic is intentionally outside `make test` and the normative fixture corpus. Its permissive results characterize a gap; they are not new acceptance requirements. A future correction needs profile-specific positive and negative fixtures, complete legacy/strict replay preservation, and hosted record-selection tests. Keep the now-correct self-guide DNS record and all anchored guide bytes unchanged.
