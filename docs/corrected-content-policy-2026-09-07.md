# Corrected content policy contract

Status: implemented local candidate contract, 2026-09-07. The profile documents,
schemas, fixtures, selectors, and callers named below agree; profile 2.0.0 remains
unreleased and undeployed.

## Decision

Add the corrected checks as profile `2.0.0`. A guide selects them only by
declaring exactly one `profile: human-verifiable-assistant-guide` and exactly
one `profile-version: 2.0.0` in its metadata block. Build metadata MAY identify
an equivalent build, such as `2.0.0+build.1`, and MUST resolve to policy
`2.0.0` as existing selectors do.

This is the smallest honest selector. The corrected checks tighten some cases
and relax false-positive cases, so the repository's SemVer rule requires a
major profile version. A CLI flag, hosted request field, manifest assertion,
or caller-supplied `ProfileSelection` MUST NOT reinterpret guide bytes as
`2.0.0`. `--require-profile-version 2.0.0` and the hosted equivalent remain
assertions that fail when the guide does not declare the required profile.

Profile `2.0.0` has these policy identities:

- content policy: `corrected-content-1`
- anchor policy: `1.0.0-strict`
- evaluated policy: `2.0.0`

Supported legacy declarations through `0.7.1` continue to select the frozen
legacy engine. A `1.0.0` declaration continues to select the released strict
anchor policy with frozen content checks. Neither path gains corrected checks,
new findings, changed levels, changed report fields, or changed exit behavior.

## Anchor composition

Profile `2.0.0` inherits the complete `1.0.0-strict` anchor contract:

- repository-file evidence is corroboration and never establishes independent
  provenance or qualifies for Level 4
- a fetched matching non-repository qualifying channel is required for Level 4
- matching local evidence cannot establish independence and local-file mode is
  capped at Level 3
- manifest `profile` and `profile-version` must match the selected guide profile
  exactly, so a `2.0.0` guide requires a `2.0.0` manifest
- mismatches, unsupported channels, qualification reasons, and Level 5
  readiness retain the released strict semantics

Content and anchor policy are composed after one request-local selection from
the guide bytes. Content findings may limit the achieved level, but they do not
change which anchor channels qualify. Anchor evidence does not suppress or
reinterpret content findings. The implementation MUST NOT mutate global
policy state, monkey-patch the legacy evaluator, or modify
`scripts/guidecheck_legacy.py`.

## Corrected content behavior

The new content engine segments prose before matching. Sentence punctuation,
semicolons, blank lines, action markers, metadata and structured fields, list
items, and headings terminate negation scope. One ordinary LF or CRLF prose
wrap does not terminate a directly governing phrase.

Each prohibited instruction occurrence is matched independently using token
boundaries and bounded, non-greedy spans. A later affirmative instruction is
reported even when an earlier occurrence in the same prose unit is prohibited.
A direct negation may suppress its governed phrase across one prose wrap. A
comma-coordinated prohibition is recognized only for a narrow verb-phrase list
with an explicit conjunction. An intervening subject, contrast, temporal or
conditional term, sentence, structured boundary, or unrelated reassurance
ends governance. Ambiguous grammar does not suppress a finding.

The 29 cases in the September 7 reproducer define the initial direct detector
contract. In particular:

| Case | Corrected result |
|---|---|
| `Do not` plus one wrapped encoded-execution phrase | no encoded-execution finding |
| coordinated `Do not broaden ..., disable ..., or persist ...` | no skip-approval finding |
| affirmative encoded-execution phrase across one wrap | `prohibited.encoded-execution` error |
| negated occurrence followed by an affirmative occurrence | `prohibited.encoded-execution` error |
| sentence, paragraph, field, list, heading, action, contrast, subject, or temporal boundary | affirmative occurrence remains an error |

No new prohibited-instruction finding ID is required for these cases. Existing
IDs retain their meanings and severities on the corrected path.

## Bounded execution behavior

The corrected path distinguishes syntax-proven repository dispatch from cases
whose ownership cannot be decided from the command. It MUST emit the new
`action.exec-target-unresolved` finding for an unresolved code-executing
target. `ambiguous` is an explicit review result, not a clean result.

Sam decided on 2026-09-07 that `action.exec-target-unresolved` is an error. It
blocks Level 3 because the verifier cannot establish which bytes the action
executes. A declared hash cannot clear the finding by itself: until the target
is identified, the verifier cannot establish what those declared hash bytes
would bind.

| Command shape | Classification | Reason or counterexample |
|---|---|---|
| `npm run <script>`, `npm test`, or `npm --prefix subdir run <script>` | `bound-script` | dispatches through the `package.json` selected from the effective working directory |
| `npm --workspace app run <script>` or `npm exec` | `ambiguous` | this candidate does not prove workspace dispatch or executable ownership from those forms |
| `make`, `make <target>`, `make -C subdir <target>`, or `make -f alternate.mk <target>` | `bound-script` | dispatches through the default or explicitly selected makefile in the effective working directory |
| `just`, `just <recipe>`, `just --justfile alternate.just <recipe>`, or `just --working-directory subdir <recipe>` | `bound-script` | dispatches the default or named recipe through the selected justfile and effective working directory |
| `pip install .`, `pip install -e .`, or another local path | `bound-script` | names local publisher-controlled package and build bytes |
| `go generate` | `bound-script` | dispatches commands declared in repository source |
| `docker build .` or `docker build --file Dockerfile .` | `bound-script` | names a local build context and its default or explicit local Dockerfile |
| `python -m <module>` | `ambiguous` | syntax does not establish first-party, standard-library, or dependency ownership |
| `cargo build` or `go build` | `ambiguous` | a repository hook requires repository inspection |
| `docker build` with remote or omitted ownership evidence | `ambiguous` | syntax does not establish a publisher-controlled local artifact |
| any `npx` form, including `--package`, `--no-install`, local paths, or custom prefixes | `ambiguous` | package selection alone does not prove that the effective binary belongs to that package; local and fetched resolution remain possible |
| a known wrapper with unsupported options, or an unsupported dispatch option such as `docker build --tag app .` | `ambiguous` | the candidate does not guess through options that may change the effective command, working directory, or dispatch file |
| `npm --version`, `make -C subdir --help`, `just --justfile alternate.just --list`, or `docker build --file Dockerfile --help` | `none` | recognized query-only forms do not execute the selected project recipe |

Equivalent option ordering MAY be recognized only after tokenization proves the
same shape. A program-name allowlist MUST NOT classify all `docker`, `pip`,
`cargo`, `go`, `make`, or `just` commands alike. Query-only commands do not
become bound merely because their program can execute code in other forms.
No `npx` form qualifies as `exempt-installer` from command syntax alone. A
future binding rule would need to establish the effective binary-to-package
mapping and the executed package identity, not merely parse a package option.

An unpinned corrected-path `bound-script` emits the existing blocking
`action.exec-unbounded`. `exec-opaque` cannot exempt it. A valid
`exec-sha256` suppresses that blocker but remains declared and unverified when
the evaluator has not read the dispatched artifact bytes. For `npm` and
`make`, the pin binds the dispatch file selected from the effective working
directory after recognized `--prefix` or `-C` handling (`package.json` or the
selected makefile); invoked repository files remain
subject to the existing transitive pin rule when their bytes can be read. The
same rule binds the justfile, local package metadata, source file containing a
`go generate` directive, or Dockerfile for the corresponding syntax-proven
forms. An acknowledged `exec-opaque` with a same-action `notes` rationale on an
`exempt-installer` emits the existing `action.exec-opaque` warning.

An unresolved target with `exec-opaque` remains malformed because opacity is
permitted only after syntax establishes the exempt external-dependency class.
An unresolved target with `exec-sha256` reports both the declared-but-unverified
pin and `action.exec-target-unresolved`; the verifier cannot claim the hash
binds the effective entry point until target ownership is established.

This resolves the A11y guide discrepancy without rewriting an old report. Its
workflow pins GuideCheck commit `3a5cbb5e880db00e0a8f44b68d89df0a73e53a45`,
whose 0.7.0 verifier ignores bounded-execution fields and reports Level 3 with
no blockers for guide SHA-256
`81fed93eac293f63897daf3c4ebc283cf9ad9efa194893fe93ddae58c5da3c78`.
The current frozen 0.7.1 legacy engine selects legacy policy for the same
declared 0.7.0 bytes, classifies `npx skills add ...` as `none`, and reports
`action-block.malformed`, Level 2, and exit 1. Both results remain historical
facts. If the guide and manifest explicitly migrate to `2.0.0`, the same
bare `install-skill` command remains unresolved and its `exec-opaque` remains
malformed. Removing `exec-opaque` would leave
blocking `action.exec-target-unresolved`, so the guide cannot reach Level 3.
No command-only `npx` rewrite is
claimed to establish an exempt installer. This policy does not depart from the
executable-ownership rule merely to reproduce the pinned 0.7.0 result.

## Report and exit contract

The `2.0.0` JSON schema requires `profile_selection` with these exact values:
```json
{
  "declared_version": "2.0.0",
  "evaluated_policy": "2.0.0",
  "content_policy": "corrected-content-1",
  "anchor_policy": "1.0.0-strict"
}
```
The compact report includes the selected profile, content policy, and anchor
policy before the level and finding counts. `verifier.guide_profile_version`
and `verifier.verifier_profile_version` identify `2.0.0`; the software version
continues to identify the actual verifier release.

Exit semantics do not gain a new code:

- `0`: no blocking findings and requested level or warning threshold satisfied
- `1`: one or more blocking findings, unmet `--level`, or warnings with
  `--fail-on-warning`
- `2`: input, parsing, unsupported-selector, or selector-assertion failure

Local and hosted callers MUST emit the same content findings, policy identity,
level, and default pass/fail result for the same guide bytes and equivalent
evidence. Hosted fetch findings may differ only where the public-web contract
requires live fetch evidence.

## Implementation scope

The implementation change is limited to:

- new normative `profiles/2.0.0/spec.md` and
  `profiles/2.0.0/verifier-conformance.md`
- new `schemas/2.0.0/` manifest, verifier-output, and fixture contracts
- new `fixtures/profiles/2.0.0/` corrected-content and anchor-composition cases
- a new isolated corrected evaluator module, with no edits to the frozen legacy
  evaluator or legacy constants
- request-local `2.0.0` selection and dispatch in
  `scripts/guidecheck_profiles.py` and `scripts/guidecheck_verify.py`
- matching hosted dispatch, report construction, and verifier UI handling
- corrected detector and bounded-dispatch unit tests, profile-dispatch tests,
  hosted parity tests, registration of `action.exec-target-unresolved`, version
  synchronization, and release notes

Refactoring `1.0.0` anchor code for reuse is allowed only if exact strict
fixtures prove byte-for-byte report compatibility. Copying the small strict
qualification step into the isolated corrected module is preferable when a
shared refactor would enlarge the compatibility surface.

## Acceptance contract

Implementation is complete only when all of the following hold:

1. Frozen legacy module digests and complete legacy replay JSON are unchanged.
2. Every released `1.0.0` fixture and complete report is unchanged.
3. Unsupported or caller-forced `2.0.0` selection fails with exit 2 before
   evaluation; changing only a manifest cannot select the policy.
4. All 29 direct detector cases pass under `corrected-content-1`, while every
   existing supported profile retains its current result for those bytes.
5. Static `2.0.0` fixtures cover both corrected false positives, both corrected
   false negatives, boundaries, multiple occurrences, LF and CRLF, and exact
   warning sets.
6. Syntax-proven `npm`, `make`, `just`, local `pip install`, `go generate`, and
   local Docker build forms block without a valid pin only on `2.0.0`; pinned
   forms report declared-but-unverified status where applicable.
7. `python -m`, build-hook-dependent Cargo or Go commands, remote Docker builds,
   and every command-only `npx` form emit blocking
   `action.exec-target-unresolved` rather than passing silently. A declared hash
   also reports unverified status and does not clear the blocker.
8. Bare `npx skills add ...` with `exec-opaque` remains malformed on `2.0.0`.
   Removing `exec-opaque` leaves the unresolved-target finding; pinned 0.7.0
   and current frozen legacy results remain unchanged as explicit regressions.
9. A repository-file-only `2.0.0` guide cannot reach Level 4. A matching
   fetched DNS or other qualifying strict channel can reach Level 4 when all
   content requirements pass.
10. JSON schemas, compact reports, CLI, hosted API, and UI identify all three
   policy dimensions consistently, including mixed concurrent requests.
11. `make test`, the deterministic verifier UI suite, contract validation,
    version synchronization, and `git diff --check` pass.

No adopter's existing report becomes corrected automatically. Obligation First,
substack2md, A11y Audit, and other adopters require an explicit guide and
manifest migration followed by a new report under `2.0.0`.
