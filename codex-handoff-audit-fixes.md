# Codex Handoff: Audit Fixes

Date: 2026-05-21
Scope: Standards-level repo `guidecheck`

## Current state

The repo was bootstrapped after a long design session for the Human-Verifiable Assistant Guide profile and its companion Verifier Conformance Profile.

The core artifacts are:

- `spec.md`: normative Human-Verifiable Assistant Guide profile.
- `verifier-conformance.md`: normative verifier conformance profile.
- `schemas/`: JSON Schemas for manifest and verifier output.
- `examples/`: illustrative guide and manifest examples.
- `fixtures/`: verifier conformance fixtures.
- `design-rationale.md`: rationale and known security risks.
- `threat-register.md`: operational risk register.
- `.well-known/security.txt`: published security metadata.

The repo was initialized clean at the audit pass. Current working directory after rename: `/Users/snap/Git/guidecheck`. The working tree now has uncommitted audit-fix and branding changes. `codex-handoff-audit-fixes.md` is still untracked unless added explicitly.

## Important context from the prior session

### Naming and canonical domain

The chosen public home is GuideCheck:

- Canonical site: `https://guidecheck.org/`
- Standard primary verifier: `https://guidecheck.org/verify`

`GuideCheck` was selected because it reads like "gut check" and fits the standard's purpose without overclaiming safety. `assistant.guide` was considered but rejected as too expensive.

### Core standard posture

Key design invariants:

- Conformance is not safety.
- Human-verifiable means actually reviewable.
- ASCII-only at Level 2 and above.
- No chained guides.
- No central registry, no oracle.
- The human stays in the control loop.

The standard intentionally avoids a central registry. A conformant verifier is a testable implementation claim, not a trust claim. The fixture suite is the conformance target.

### Level model

The spec now uses a five-level ladder:

- Level 0: not conformant.
- Level 1: plain text available with compact verification instruction.
- Level 2: byte profile and size limits.
- Level 3: assistant safety contract and action blocks.
- Level 4: verifiable provenance with sidecar manifest and independent cross-channel hash anchor.
- Level 5: guide plus conformant assistant runtime enforcement.

Level 5 is not guide-only. A verifier must not report achieved Level 5 for a guide alone. It may report `level5_ready`.

### Verifier and runtime hardening added

Recently added mitigations:

- Compact verification ceremony before actions.
- Recommended hosted verifier allowed, but no verifier is authoritative.
- `recommended-verifier` same-domain guidance with an exception for the standard primary verifier.
- Public guide fetches must not send ambient credentials.
- Compact reports include guide SHA-256.
- Level 5 runtimes compare agent-used guide bytes against verifier-reported SHA-256.
- Level 5 approval ledger is keyed by guide URL, guide hash, verifier name, verifier version, achieved level, and action id.
- Verifier conformance includes SSRF defenses, content variation checks, domain mismatch warnings, and output schema requirements.

### Canonical URL conventions from AGENTS.md

Use bare `https` domains. Never `www`. Never `http`.

Correct:

```text
https://guidecheck.org/
```

## Session update

Completed in the follow-up session:

- Renamed the local repo directory from `/Users/snap/Git/assistant-guide` to `/Users/snap/Git/guidecheck`.
- Updated visible project branding outside `archive/` so the standards project is GuideCheck while preserving protocol names such as `assistant-guide.txt` and `human-verifiable-assistant-guide`.
- Added the naming model to `README.md` and `design-rationale.md`: GuideCheck is the standards project, public checker, ecosystem, and site; `assistant-guide.txt` is the artifact; the Human-Verifiable Assistant Guide profile defines artifact conformance; a GuideCheck conformance claim requires verifier output, guide hash, achieved level, and findings.
- Fixed the valid Level 3 example/fixture action block issue and kept the example and fixture byte-identical.
- Updated the Level 3 guide hash to `daba306746a7c4f0d6fe9c4667b692c031c7c62150b3f9990aba9ffee752c0d4` and byte count to `5135` in manifests and expected JSON.
- Made the invalid byte-profile fixtures Level 1-complete while preserving their intended defects: tab, CRLF, and non-ASCII byte.
- Aligned `spec.md` section 26 with the nested verifier output shape in `verifier-conformance.md` and `schemas/verifier-output.schema.json`.
- Added `registry-url` to verifier metadata parsing and Level 4 package-registry anchor requirements.
- Added `schemas/fixture-expected.schema.json` and documented it in `schemas/README.md` and `fixtures/README.md`.
- Added `finding-ids.md` for the starter fixture finding ids and linked it from `README.md` and `fixtures/README.md`.
- Renamed the local branch from `master` to `main`.

Still open:

- `.well-known/assistant-guide.txt` for GuideCheck itself has not been created. Blocker: there is still no configured public repository URL (`git remote -v` is empty), and the guide should not invent one.
- `.well-known/security.txt` extension fields `Assistant-Guide` and `Assistant-Guide-SHA256` should wait until `.well-known/assistant-guide.txt` is finalized.
- Optional cleanup remains: stable section anchors or named references.

Verification run after fixes:

```text
jq empty schemas/*.json fixtures/*/*/expected.json
shasum -a 256 examples/level-3-assistant-guide.txt fixtures/valid/level-3/guide.txt
wc -c examples/level-3-assistant-guide.txt fixtures/valid/level-3/guide.txt examples/manifest.txt fixtures/valid/level-3/manifest.txt
file fixtures/invalid/crlf-line-endings/guide.txt fixtures/invalid/non-ascii-byte/guide.txt fixtures/invalid/tab-character/guide.txt
```

Observed after fixes:

- JSON files parse successfully.
- `examples/level-3-assistant-guide.txt` and `fixtures/valid/level-3/guide.txt` are byte-identical.
- Current SHA-256 for both Level 3 guide copies: `daba306746a7c4f0d6fe9c4667b692c031c7c62150b3f9990aba9ffee752c0d4`.
- Current byte count for both Level 3 guide copies: `5135`.
- CRLF invalid fixture still reports `ASCII text, with CRLF line terminators`.
- Non-ASCII invalid fixture still reports UTF-8 text.
- `git diff --check` reports only the intentional CRLF fixture as trailing whitespace because Git sees carriage returns that way.

## Audit findings to fix

These were found in the review pass. Completion status is marked in each heading.

### DONE P1: Valid Level 3 fixture is not valid under action block rules

Files:

- `fixtures/valid/level-3/guide.txt`
- `examples/level-3-assistant-guide.txt`
- `fixtures/valid/level-3/expected.json`
- `examples/manifest.txt`
- `fixtures/valid/level-3/manifest.txt`

Problem:

The `install` action in `fixtures/valid/level-3/guide.txt` and `examples/level-3-assistant-guide.txt` violates the spec:

- It writes filesystem state via `npm install --global`, but has no `cwd`.
- Its `notes` value wraps to a continuation line, but `notes` is defined as single-line.

Relevant spec text:

- `spec.md` section 12 says any action that reads or writes the filesystem must include `cwd`.
- `spec.md` section 12 defines `notes` as optional, single-line rationale.
- `verifier-conformance.md` expects action blocks to use `key: value` lines and reject malformed values.

Suggested fix:

Add `cwd: .` or a clearer approved absolute/path placeholder to the `install` action, and rewrite `notes` to one line under the 120-byte line limit.

After editing, recompute:

- SHA-256 of `examples/level-3-assistant-guide.txt`
- SHA-256 of `fixtures/valid/level-3/guide.txt`
- byte counts for both

Then update:

- `examples/manifest.txt`
- `fixtures/valid/level-3/manifest.txt`
- `fixtures/valid/level-3/expected.json`

Also ensure examples and fixtures stay byte-identical if that remains the intended setup.

Useful checks:

```text
shasum -a 256 examples/level-3-assistant-guide.txt fixtures/valid/level-3/guide.txt
wc -c examples/level-3-assistant-guide.txt fixtures/valid/level-3/guide.txt examples/manifest.txt fixtures/valid/level-3/manifest.txt
awk 'length($0)>120 {print FILENAME ":" FNR ":" length($0) ":" $0}' examples/*.txt fixtures/valid/level-3/guide.txt
```

### DONE P1: Invalid fixtures claim Level 1 even when Level 1 requirements are absent

Files:

- `fixtures/invalid/tab-character/guide.txt`
- `fixtures/invalid/tab-character/expected.json`
- `fixtures/invalid/crlf-line-endings/guide.txt`
- `fixtures/invalid/crlf-line-endings/expected.json`
- `fixtures/invalid/non-ascii-byte/guide.txt`
- `fixtures/invalid/non-ascii-byte/expected.json`

Problem:

The expected outputs currently claim `achieved_level: 1` for invalid byte-profile fixtures. But the fixture guide files do not consistently satisfy Level 1.

Examples:

- `fixtures/invalid/crlf-line-endings/guide.txt` has no canonical URL, repository/project URL, task scope, or compact verification instruction.
- `fixtures/invalid/non-ascii-byte/guide.txt` has no canonical URL, repository/project URL, task scope, or compact verification instruction.
- `fixtures/invalid/tab-character/guide.txt` has a task scope heading but no canonical URL or repository/project URL and only a minimal verification sentence.

Relevant verifier level calculation:

- `verifier-conformance.md` section 25 says Level 1 requires HTTPS public-web fetch evidence, readable `.txt`, canonical project or repository URL, task scope, and compact verification instruction.

Potential fix options:

1. Make each invalid fixture satisfy Level 1 except for the intended Level 2 byte-profile defect, then keep `achieved_level: 1`.
2. Or update expected results to `achieved_level: 0` where Level 1 is not actually satisfied.

Recommended fix:

Use option 1 for byte-profile fixtures. These fixtures are meant to isolate Level 2 failures, so their contents should satisfy Level 1 and fail exactly one byte-profile rule.

Be careful:

- The non-ASCII fixture must intentionally contain one non-ASCII byte.
- The CRLF fixture must intentionally use CRLF line endings.
- The tab fixture must intentionally contain a tab.

Expected finding ids may remain:

- `byte-profile.no-tabs`
- `byte-profile.no-carriage-returns`
- `byte-profile.non-ascii-byte`

But recompute any `guide_sha256` if expected files begin including hashes.

### DONE P1: Verifier output schema conflicts with normative output examples

Files:

- `spec.md`
- `verifier-conformance.md`
- `schemas/verifier-output.schema.json`
- `schemas/README.md`

Problem:

`spec.md` section 26 currently shows a flat minimum output shape:

```text
guide_url
final_url
fetched_at
http_status
headers
bytes
sha256
profile_version
claimed_level
achieved_level
findings
```

But `verifier-conformance.md` section 27 and `schemas/verifier-output.schema.json` use the newer nested shape:

```text
verifier
input
fetch
guide
summary
findings
```

This creates conflicting normative guidance.

Suggested fix:

Make `spec.md` section 26 defer to `verifier-conformance.md` and/or update its example to the nested shape. Since `verifier-conformance.md` is the dedicated verifier spec, prefer making `spec.md` lighter:

- Keep compact report language if needed.
- State that machine-readable verifier output is defined normatively by `verifier-conformance.md` section 27 and `schemas/verifier-output.schema.json`.
- Remove or replace the flat JSON example.

Then verify:

- `schemas/README.md` references still make sense.
- `README.md` does not imply the schema follows the flat shape.

### DONE P2: `registry-url` is normative in spec but missing from verifier metadata parsing

Files:

- `spec.md`
- `verifier-conformance.md`
- possibly `schemas/manifest.schema.json`
- possibly future examples/fixtures

Problem:

`spec.md` section 11 lists `registry-url` as optional metadata and says it is required when package registry metadata is the publisher's chosen independent anchor. `spec.md` section 11 also says verifiers discover the registry record through `registry-url`.

But `verifier-conformance.md` section 14 optional metadata checks omit `registry-url`.

Suggested fix:

Add `registry-url` to optional metadata fields in `verifier-conformance.md`.

Consider adding verifier requirements:

- validate it as an ASCII URL
- require it when the package-registry channel is used as an independent anchor
- warn when it is absent and no other Level 4 independent anchor is available

Consider adding a future fixture for package-registry anchors, but this likely does not need to happen in the immediate cleanup unless you want full coverage now.

### OPEN P2: Repo does not dogfood its own canonical well-known artifact

Files:

- `.well-known/assistant-guide.txt` does not exist
- `README.md`
- `.well-known/security.txt`
- possibly `examples/level-3-assistant-guide.txt`

Problem:

`README.md` says the canonical artifact is served at `/.well-known/assistant-guide.txt`, and the repo includes `.well-known/security.txt`, but it does not include `.well-known/assistant-guide.txt`.

If this repo is deployed as `https://guidecheck.org/`, the standard's own site will not satisfy its primary discovery convention.

Suggested fix:

Create `.well-known/assistant-guide.txt` for the GuideCheck standard itself.

Important: This file must satisfy the profile it claims.

Recommended target:

- Level 3 initially, because Level 4 requires manifest plus independent cross-channel anchor.
- Keep under 8192 bytes and 120 bytes per line.
- Use `canonical-url: https://guidecheck.org/.well-known/assistant-guide.txt`
- Use `repository-url` once the public repo URL is known. If the repo URL is not public yet, choose a placeholder carefully or wait.
- Use `recommended-verifier: https://guidecheck.org/verify`
- Use `verifier-conformance: human-verifiable-assistant-guide-verifier >=0.1.0, <0.2.0`

Possible scope:

```text
This guide helps an assistant verify and read the GuideCheck standard. It does not install software, run code, or change local files.
```

Actions may be minimal/read-only, or the guide may declare that there are no executable actions. If using no actions, confirm the spec supports Level 3 with no substantive actions. If not, include read-only `normal` actions such as verifying local checksums only if they are meaningful and safe.

Also consider whether `.well-known/security.txt` should add extension fields:

```text
Assistant-Guide: https://guidecheck.org/.well-known/assistant-guide.txt
Assistant-Guide-SHA256: <64-hex>
```

Only add the hash once the guide is finalized.

## Additional cleanup candidates noticed during audit

These were not primary findings, but are worth considering.

### OPEN: Section reference fragility

Many docs cite section numbers directly:

- `README.md`
- `CHANGELOG.md`
- `CONTRIBUTING.md`
- `schemas/README.md`
- `fixtures/README.md`
- `design-rationale.md`
- `INTENT.md`
- `SECURITY.md`

The current section numbering appears mostly coherent, but section-number references will drift as the spec changes. Consider adding stable anchors or using names alongside numbers.

### DONE: Fixture expected format lacks JSON Schema

`schemas/fixture-expected.schema.json` now defines the normalized `expected.json` contract for conformance fixtures.

### DONE: Finding-id registry is planned but not present

`finding-ids.md` now defines the fixture-required finding ids used by the starter suite, and `fixtures/README.md` points fixture authors there.

### DONE: Current branch name

The local branch was renamed from `master` to `main`.

## Commands already run during audit

These checks passed:

```text
git status --short
jq empty schemas/verifier-output.schema.json schemas/manifest.schema.json fixtures/valid/level-3/expected.json fixtures/invalid/tab-character/expected.json fixtures/invalid/crlf-line-endings/expected.json fixtures/invalid/non-ascii-byte/expected.json
shasum -a 256 examples/level-3-assistant-guide.txt fixtures/valid/level-3/guide.txt
wc -c examples/level-3-assistant-guide.txt fixtures/valid/level-3/guide.txt examples/manifest.txt fixtures/valid/level-3/manifest.txt
awk 'length($0)>120 {print FILENAME ":" FNR ":" length($0) ":" $0}' examples/*.txt fixtures/valid/level-3/guide.txt
```

Observed:

- `examples/level-3-assistant-guide.txt` and `fixtures/valid/level-3/guide.txt` are byte-identical.
- Their current SHA-256 is `084ec8df929052d176d25984e5ec3443ef195ac8be4e1fd27e7350192a29781d`.
- Their current byte count is `5156`.
- JSON files parsed successfully.
- Line-length check found no lines over 120 bytes in examples/fixtures checked.
- Non-ASCII scan found expected non-ASCII in `fixtures/invalid/non-ascii-byte/guide.txt` and an intentional homoglyph example in `design-rationale.md`.

## Recommended repair order

1. Fix the Level 3 valid example/fixture action block issue.
2. Recompute hashes and byte counts; update manifests and expected JSON.
3. Fix invalid fixtures so expected levels match the actual Level 1 requirements.
4. Align `spec.md` section 26 with `verifier-conformance.md` and `schemas/verifier-output.schema.json`.
5. Add `registry-url` to verifier metadata parsing.
6. Add `.well-known/assistant-guide.txt` for GuideCheck itself, if enough canonical repository information is available.
7. Run full consistency checks again:

```text
rg -n "[^\\n\\r\\t -~]" README.md spec.md verifier-conformance.md examples fixtures schemas .well-known robots.txt SECURITY.md CONTRIBUTING.md CHANGELOG.md INTENT.md threat-register.md archive
jq empty schemas/*.json fixtures/*/*/expected.json
shasum -a 256 examples/level-3-assistant-guide.txt fixtures/valid/level-3/guide.txt
wc -c examples/level-3-assistant-guide.txt fixtures/valid/level-3/guide.txt
awk 'length($0)>120 {print FILENAME ":" FNR ":" length($0) ":" $0}' examples/*.txt fixtures/valid/level-3/guide.txt .well-known/assistant-guide.txt
```

Expect the non-ASCII check to report intentional cases unless the command is narrowed or exceptions are documented.
