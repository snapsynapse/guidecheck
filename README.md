# GuideCheck

Check an assistant setup guide before authorizing its actions.

GuideCheck reports the exact guide hash, achieved conformance level, and blocking findings without executing the guide. Here is a guide rejected because an action invokes repository code outside the bounded instruction surface.

The guide is the released fixture `fixtures/profiles/2.0.0/corrected-bound-unpinned/guide.txt`. This is its only action block:
```text
[action]
id: check-version
class: code-executing
approval: required
command: npm --prefix subdir run check
runner: argv
cwd: .
notes: Prints local version information only.
[/action]
```
The action asks for approval, but nothing bounds the code it runs: no inline commands replace it and no valid `exec-sha256` is declared. This is the local reference verifier's compact report for that guide, with a requested gate of Level 3 (the process exited 1):
```text
Verifier: guidecheck-reference-local 2.0.0
Guide: fixtures/profiles/2.0.0/corrected-bound-unpinned/guide.txt
Profile: 2.0.0 (declared 2.0.0)
Content policy: corrected-content-1
Anchor policy: 1.0.0-strict
Qualifying anchors: 0
Level: 2
SHA-256: 980af0ed73303120f7a9a5d643630b1b02e21579d1578c733174c1445518545c
Blocking findings: 2
Warnings: 0
Hash pinned: no
Proceed? no
```

| Result field | Value |
|---|---|
| Blocking finding | `action.exec-unbounded` (evidence: action `check-version`) |
| Meaning | Repository script dispatch is not bounded by inline commands or a valid declared pin |
| Requested gate | Level 3 |
| Achieved level | Level 2 |
| Exit code | 1 |

The fixture also reports a second blocking finding, `anchor.independent.missing`. It declares a `manifest-url`, which claims Level 4, and a local check cannot fetch the independent evidence Level 4 needs. That is why the report counts 2 blocking findings. Review and bound the invoked repository code before treating this guide as meeting Level 3.

Conformance checks do not establish that the instructions are safe, the publisher is trustworthy, or a runtime will execute only approved instructions.

## Try it

You need Python 3.10 or later and Git. The core verifier uses only the standard library. This path is a source checkout; it does not assume GuideCheck is published to a package index. Cloning contacts GitHub. Local evaluation reads the named guide as data. It does not execute the guide's actions and does not fetch provenance evidence. The `npm` command in the failing fixture is input data and is never run.

The complete JSON reports behind this section, with the exact tag, commit, and Python version, are in [docs/readme-trial-evidence-2026-10-21.md](docs/readme-trial-evidence-2026-10-21.md). Your output will differ slightly: `local_evaluation.evaluated_at` is the evaluation time, and the `metadata.last-reviewed.age` info finding counts days from each guide's `last-reviewed` date.

Step 1. From an empty working directory, clone the released source and enter the checkout. The directory `guidecheck-trial` must not already exist there.

Literal
```bash
git clone --branch v2.0.0 --depth 1 https://github.com/snapsynapse/guidecheck.git guidecheck-trial
cd guidecheck-trial
```
Step 2. Reproduce the known failure. Expect `action.exec-unbounded` as a blocking finding, achieved Level 2, and exit code 1.

Literal
```bash
python3 scripts/guidecheck_verify.py fixtures/profiles/2.0.0/corrected-bound-unpinned/guide.txt --level 3 --pretty
```
Step 3. Run a positive control. This is a known-valid example guide under the legacy 0.7.1 profile. It is a different guide, not a repaired version of the failing one, and the guide's own bytes make the verifier select the frozen legacy evaluator, so the report shows verifier version 0.7.1. Expect achieved Level 3, no blocking findings, `Proceed? yes`, and exit code 0.

Literal
```bash
python3 scripts/guidecheck_verify.py examples/level-3-assistant-guide.txt --level 3 --pretty
```
Step 4. Check your own local `assistant-guide.txt` from the same checkout. You do not need to change its profile declarations to run the check.

Replace: GUIDE_PATH -> the absolute path to the local assistant-guide.txt to inspect.

Customize
```bash
python3 scripts/guidecheck_verify.py 'GUIDE_PATH' --level 3 --pretty
```
Native exit codes are 0 when the requested gate is accepted, 1 for blocking findings or a result below the requested level, and 2 for handled missing-input or profile-selection errors. Treat operational failures separately from conformance rejection. The experimental `--contract posix-json-v1` selector has different exit semantics; see [docs/cli-contract.md](docs/cli-contract.md) if you are integrating the verifier into another tool.

Read `guide.achieved_level` and the finding list, not the exit code alone, when your guide declares profile 2.0.0 or 1.0.0 and includes a `manifest-url`. Declaring `manifest-url` claims Level 4. Level 4 provenance requires fetched evidence, which the local check cannot supply, so it reports blocking `anchor.independent.missing` and exits 1 even when `achieved_level` is 3. The hosted verifier, which is a preview, is where fetched evidence is checked. This is current behavior of the local verifier.

## Have an instruction file rather than a guide?

If you have an `AGENTS.md`, `CLAUDE.md`, README, or skill file rather than an `assistant-guide.txt`, scan that existing file for supported hidden-instruction channels. This does not require adopting the profile and is separate from guide verification. Run it from the same checkout.

Replace: INSTRUCTION_FILE -> the absolute path to one local instruction file to inspect.

Customize
```bash
python3 scripts/guidecheck_scan.py 'INSTRUCTION_FILE' --json
```
The scanner reports findings such as `surface.hidden-html-comment`, invisible Unicode, supported CSS-hidden text, and ANSI escapes. It does not award a conformance level. Run against this repository's own `CLAUDE.md` it reported 0 findings (exit 0). Detection favors precision over recall: no findings means no supported channel was detected in that input, not that the file is safe or that all prompt injection was excluded.

## What to do with a blocking finding

1. Inspect the implicated bytes. The `evidence` field of `action.exec-unbounded` names the action id (`check-version` above).
2. Bound the execution. Replace the repository script dispatch with inline actions that a reviewer can read in the guide, or declare a valid `exec-sha256` for the invoked code. The corrected-content policy covers dispatch and pinning limits: [docs/corrected-content-policy-2026-09-07.md](docs/corrected-content-policy-2026-09-07.md). Finding ids are registered in `finding-ids.md`.
3. Rerun the check without executing the guide.

Keep these claims distinct:
- Human approval being requested (`approval: required`) does not bound the command.
- A pin declaration is not pin verification. A declared `exec-sha256` is not evidence that the verifier read the target bytes. The local verifier does not read the invoked artifact and reports the pin as `exec-sha256.unverified`.
- Fetched provenance (Level 4) is not runtime enforcement (Level 5), and neither is a statement that the guide is safe.

## Verification and scanning

- Verification (`scripts/guidecheck_verify.py`) evaluates one `assistant-guide.txt` against the Human-Verifiable Assistant Guide profile and reports a hash, achieved level, and findings.
- Scanning (`scripts/guidecheck_scan.py`) inspects existing instruction files for supported hidden-instruction channels and reports scanner findings. It does not evaluate the conformance ladder.

Neither guarantees that attacks are prevented or that every hidden-instruction channel is detected.

## About GuideCheck

GuideCheck is a trust boundary protocol for agent instruction surfaces. It
helps ensure the instructions humans approve are the same instructions agents
execute.

AI setup guides can hide instructions a model reads but a human never sees. A
tool-using assistant may then run those hidden instructions with delegated
authority: credentials exposed, destructive commands run, malicious
dependencies installed, or safeguards disabled while the human believes the
guide was reviewed.

GuideCheck is the standards project for the Human-Verifiable Assistant Guide
profile: a constrained plain-text profile for `assistant-guide.txt`, covering
assistant-facing install, implementation, remediation, migration, and
operational instructions that a human can review in full before an assistant
acts on them. The core claim is review integrity: the reviewed instruction
surface and the executed instruction surface should be one bounded artifact.

The current release is 2.0.0. It adds an opt-in corrected-content policy while
preserving legacy and 1.0.0 evaluations; GuideCheck's own self-guide and frozen
legacy reports remain 0.7.1. See the [2.0.0 profile](https://github.com/snapsynapse/guidecheck/blob/v2.0.0/profiles/2.0.0/spec.md),
[corrected-content policy](docs/corrected-content-policy-2026-09-07.md), and
[release notes](RELEASE_NOTES-2.0.0.md).

Canonical site: https://guidecheck.org/
Verifier: https://guidecheck.org/verify

New here: `ADOPTION.md` is the practical on-ramp. It explains the conformance
ladder, gives a level-by-level path, and carries the guide-author checklist.

## Conformance is not safety

Conformance to this profile, at any level, does not mean a guide is safe to
follow, that the publisher is trustworthy, or that the assistant may proceed
without the security practices a competent operator would already apply. A
verifier confirms form. The human confirms meaning. Read `spec.md` section 1
and `operator-guide.md` before adopting.

## What problem it solves

AI-assisted setup guides are distributed through HTML, rendered Markdown, PDFs,
docs sites, copied issue comments, terminal output, and screenshots. Those
surfaces can carry content a model ingests but a human does not see: hidden
HTML comments, offscreen CSS, white-on-white text, script-inserted content,
invisible Unicode controls, terminal escape sequences, long buried instruction
blocks.

For high-consequence tasks, projects need a constrained instruction surface
that a human can review in full before authorizing an assistant to follow it.
The problem is a trust-boundary failure: humans approve one surface while
agents may execute another.

## Who this is for

- AI governance practitioners who need evidence that guidance was reviewable
  before an assistant acted on it.
- Security engineers concerned with prompt injection and hidden instruction
  channels.
- AI platform and MLOps engineers who operationalize assistant workflows.
- MCP server authors and host implementers who need reviewable install,
  configuration, tool, resource, and approval boundaries.
- A2A implementers evaluating how delegated tasks, returned artifacts, and
  remote-agent instructions should cross trust boundaries.
- Technical policy and compliance professionals working on evidence,
  reviewability, and control design.
- Anyone who wants to take basic precautions against prompt injection and other
  well-known security issues when using AI agents to install software or take
  other autonomous actions.

## What this profile defines

- a `.txt` artifact named `assistant-guide.txt`, served at `/.well-known/assistant-guide.txt`
- a strict ASCII byte profile and an 8 KiB size cap, so the whole instruction
  surface is reviewable in one sitting
- structured `[action]` blocks with explicit classes, approval gates, and command restrictions
- a five-level conformance ladder, from plain-text availability through
  verifiable provenance to runtime-enforced execution
- a sidecar manifest plus cross-channel hash publication for provenance
- a companion verifier conformance profile so independent verifiers agree on results
- this repo's own `assistant-guide.txt`, for drafting or reviewing a target repo guide

## Conformance levels

- Level 0: instructions only available through surfaces that can hide or
  transform text
- Level 1: a plain-text guide exists, is reachable, and carries the compact
  verification instruction
- Level 2: strict ASCII byte profile, size limits, no disallowed constructs
- Level 3: assistant safety contract, all required sections, explicit approval
  gates; from 0.7.0, an invoked in-repo script or entry point must be inlined or
  hash-pinned so the executed surface stays inside the reviewed guide
- Level 4: verifiable provenance, sidecar manifest, cross-channel hash on an
  independent control plane
- Level 5: a guide plus a conformant assistant runtime that mechanically
  enforces the execution contract

Level 4 is the highest score for the guide file itself. Level 5 is not a
higher guide-file score; it is a separate runtime enforcement claim for a
deployment that executes a Level 4 guide.

## Verifier scope

Verifier work is split by evaluation mode. Two verifiers exist:

- a local-file reference CLI, `scripts/guidecheck_verify.py`, which evaluates
  Levels 1 through 3. It also checks that any supplied sidecar manifest and
  independent-anchor evidence is internally consistent, but caps the achieved
  level at 3 and reports `level4.requires-fetch`: Level 4 asserts independent
  provenance, which can only be established by fetching the evidence from its
  real location
- a hosted public-web verifier at https://guidecheck.org/verify, which fetches
  a guide by URL and applies Level 1-4 checks when supported public-web
  provenance evidence is available. The hosted verifier also accepts optional
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
bytes (it caps at Level 3); only the hosted verifier, which fetches supported
public-web anchors (package-registry metadata and transparency-log entries),
asserts Level 4.

The hosted verifier may report `level5_ready: true` for a Level 4 guide that
also passes the guide-side preparation checks for runtime enforcement (Level 5
readiness is evaluated only once Level 4 is achieved, so it does not apply in
local-file mode). This is not an achieved Level 5 claim; Level 5 still requires
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
reporting `level4.requires-fetch`; use the hosted verifier to assert Level 4):

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

- hosted Level 4 supports package-registry, transparency-log, DNS TXT, and
  github.com repository-file anchors; signed `security.txt` anchors are not
  fetched yet. Repository-file matches qualify only under legacy profiles;
  1.0.0 requires another qualifying channel
- the hosted verifier is a Level 1-4 preview; its SSRF and abuse controls are
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

## Local Evals

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

## Documents

- `ADOPTION.md` - the practical on-ramp: conformance ladder, level-by-level path, guide-author checklist
- `profiles/2.0.0/spec.md` and `profiles/2.0.0/verifier-conformance.md` - the current released guide and verifier profiles
- `profiles/1.0.0/spec.md` and `profiles/1.0.0/verifier-conformance.md` - the prior released guide and verifier profiles
- `spec.md` and `verifier-conformance.md` - preserved normative legacy profiles
- `design-rationale.md` - why the design choices were made
- `operator-guide.md` - non-normative defense-in-depth practices for operators
- `threat-register.md` - known risk classes for fixture, verifier, and runtime authors
- `docs/acs-integration.md` - non-normative ACS runtime control patterns
- `docs/owasp-crosswalk.md` - non-normative map to the OWASP Agentic Top 10 and ACS v0.1.0 hooks
- `docs/mcp-integration.md` - non-normative MCP integration patterns
- `docs/a2a-integration.md` - non-normative A2A integration patterns
- `docs/readme-trial-evidence-2026-10-21.md` - captured output behind the "Try it" section
- `schemas/` - JSON Schema for the manifest, verifier output, and fixture expectations
- `finding-ids.md` - registry for fixture-required and emitted verifier finding ids
- `assistant-guide.txt` - repository copy of the GuideCheck adoption guide
- `.well-known/assistant-guide.txt` - canonical public copy of the adoption guide
- `evals/` - local eval documentation for fixture and generated checks
- `scripts/eval_guidecheck.py` - eval runner over the primary engine (static fixtures plus generated edge cases); not a separate verifier
- `roadmap.md` - future actions and undecided questions
- `CHANGELOG.md` - profile and companion-document change history
- `CONTRIBUTING.md` - how to propose a profile change
- `SECURITY.md` - how to report a security weakness privately
- `examples/` - sample conforming guides and a sample manifest
- `fixtures/` - verifier conformance test corpus
- `INTENT.md` - standards-level strategy, invariants, and recalibration gates
- `archive/` - genesis documents, non-normative

## Naming model

- The standards project, public checker, ecosystem, and site are GuideCheck.
- The artifact is `assistant-guide.txt`.
- The profile is the Human-Verifiable Assistant Guide profile.
- A conformant file is an `assistant-guide.txt` artifact that satisfies a
  specific profile version.
- A GuideCheck conformance claim is valid only when backed by verifier output,
  guide hash, achieved level, and findings.

## Canonical URL

https://guidecheck.org/

## Status

The current release is 2.0.0. Profile 1.0.0 remains supported as a prior
release, and legacy profiles remain supported. See
`RELEASE_NOTES-2.0.0.md` and `CHANGELOG.md`.

This is an early-stage open standard. The most useful feedback right now is
whether the hidden-instruction problem maps to real operational risk in your
environment, whether `assistant-guide.txt` and the conformance ladder are the
right abstraction, and what is missing before you could reference a standard
like this in internal policy or architecture. Open an issue or start a
discussion.

If the direction is useful to your AI governance, security, or platform work,
a GitHub star helps the project reach other practitioners working on the same
problem.

## Contributing

GuideCheck is a security-relevant standards project. See `CONTRIBUTING.md` for
how to propose a profile change, and `SECURITY.md` to report a weakness
privately.

## License

Specification text and documentation: Creative Commons Attribution 4.0
International (`LICENSE`).
Reference code and schemas: MIT (`LICENSE-MIT`).
Copyright 2026 PAICE.work PBC.

## Project

A PAICE Foundation standard. See https://paice.foundation/ for the portfolio.
