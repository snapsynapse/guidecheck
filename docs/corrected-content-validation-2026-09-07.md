# Corrected Profile 2.0.0 Local Validation
Date: 2026-09-07

Scope: historical local evidence for corrected-profile checkpoint `20fd911`,
before the CLI adapter and software 2.0.0 candidate preparation. Version and
fingerprint statements below describe that checkpoint. Current release
preparation is tracked in `docs/release-2.0.0.md`.

## Result

The explicitly selected profile 2.0.0 candidate is implemented and passes the
local contract suite. It combines `corrected-content-1` with
`1.0.0-strict` anchor qualification. The guide bytes select the policy; a
caller-supplied selection or manifest cannot reinterpret other guide bytes.

Unresolved execution emits blocking `action.exec-target-unresolved`. Every
`npx` form remains unresolved because command syntax does not establish the
effective binary's package ownership. A declared `exec-sha256` does not clear
that ambiguity. Known npm, make, just, local pip, Go generate, and local Docker
dispatch forms are bound only where tokenized syntax establishes the effective
working directory and dispatch file. Unsupported options and wrappers fail
closed as unresolved; recognized query-only forms remain non-executing.

## Identity and fingerprints

- Base repository HEAD: `1bd5f3d6e31f79ca6125e7da03ec1746934eb6b5`.
- This record describes the corrected-profile implementation checkpoint. Its
  local commit is identified by Git history; it has no published tag, release,
  deployment, or hosted acceptance identity.
- Corrected evaluator SHA-256: `3ef35978de1b4c6ddf60b21c0a2e87f52f8f7483cde2ccdcab0d8cd34b59ac05`.
- Schema-valid hosted example SHA-256: `7ab29cbf11cab395ada8b5f63bc18d2338c7b934fcc574ebf66a7302ef743c04`.
- Preserved-artifact record SHA-256: `ee54d3e6589eb3b5f2ea1e4160e1228b1c37373739eaf38d8c21ed2cac70fdf4`.
- Frozen legacy evaluator SHA-256 remains
  `b2f2e5afefaf949cdc50846ff1ad97d5f506da50fc787afa17e26e019963efda`,
  exactly the digest in the preserved-artifact record.
- Root and served manifest copies are byte-identical at SHA-256
  `b8d0cfdddc7ddc134ca86a40365a0aa84b75dd0c6031a6d19a88e7b0e4cfd923`.

## Validation evidence

`make test` exits 0. Its component evidence is:

- 2 legacy-anchor compatibility tests, 1 complete dispatch replay test, and 14
  mixed profile dispatch/schema/hosted/CLI tests pass.
- The preserved-artifact check covers all 10 frozen implementation, schema,
  normative, self-guide, and served-manifest digests in its record.
- 6 released bounded-execution tests and 5 corrected content/execution test
  groups pass.
- 138 generated evaluator cases and 74 reference-verifier fixtures pass.
- Contract validation accepts 84 fixtures, including 11 static 2.0.0 cases
  with exact blocking and warning sets.
- The contract-schema checks, parser edge cases, 6 guide byte-profile checks,
  36 fetch-safety cases, 30 hosted-anchor cases, 101 hosted API cases, 12 fetch
  replay cases, 10 CLI cases, and 58 scanner cases pass.
- Version synchronization passes 28 pattern checks and 2 byte-identity checks.
- `make test-verify-ui` passes legacy, strict, and corrected rendering, including
  all corrected policy identities, copy, download, and repeated requests.
- Python compilation and `git diff --check` pass.

The 2.0.0 example report was generated through the hosted handler with replayed
guide, manifest, repository, and DNS evidence, then normalized to the fixed
fixture timestamp. It validates against the 2.0.0 output schema. Its software
version is the actual current release, 1.0.0; its guide/verifier profile version
is 2.0.0; and `profile_selection` identifies all four selection dimensions.

## Compatibility and delivery boundary

Legacy and released 1.0.0 guides retain their existing engines and complete
report shapes. `LATEST_RELEASED_PROFILE_VERSION` and `GUIDECHECK_VERSION`
remain 1.0.0. The root self-guide remains profile 0.7.1, and no existing guide,
manifest, anchor, or adopter report was migrated.

The A11y guide's pinned 0.7.0 report and current frozen 0.7.1 result remain
historical facts. A future explicit 2.0.0 migration would classify its
`npx skills add ...` command as unresolved; this candidate does not create an
installer exemption to make that guide pass.

Release review and delivery remain separate. The public tracker is
[GuideCheck issue 2](https://github.com/snapsynapse/guidecheck/issues/2).
Signing, OpenSSF scorecards, and citations remain in their separate handoff.

## Resumed preparation verification

On 2026-09-07, `make test` and `make test-verify-ui` passed again on the resumed candidate. The public-contract build and its complete source/public digest inventory passed local readback. These checks do not establish hosted deployment.

An isolated installed-wheel check found that `guidecheck_corrected` was absent from `pyproject.toml` package modules. The package inventory now includes it. `scripts/test_package_consumer.py` builds and installs a wheel outside the checkout, then exercises legacy, strict, corrected and scanner dispatch. All four scenarios passed; CI now runs this check separately from the offline Python suite. Build-dependency retrieval initially failed under sandbox DNS restrictions; the unchanged test passed with network access. No legacy or released-profile report changed for this packaging correction.

The released strict profile now has an additional complete-report replay guard: six local fixture reports and two hosted anchor responses were captured from the unchanged released commit `1bd5f3d6e31f79ca6125e7da03ec1746934eb6b5`, with fixed evaluation time and only checkout paths normalized. The current candidate matches that independent baseline exactly. The preserved legacy replay remains unchanged. CI exercises the declared Python 3.10 floor as well as Python 3.12.

The resumed independent review found and repaired normative phrase false passes, npm workspace options after the subcommand, and pip destination/source confusion. Eleven focused test groups now cover these paths, including complete Level 3 evaluations and negative counterparts. Narrow direct permission prohibitions and recognized external npm installer flags remain accepted; unsupported dispatch options stay unresolved. The complete repository and UI suites pass after these repairs.
