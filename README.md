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

The trial is one lesson under one released profile: reproduce a rejected 2.0.0 guide, read the repair, verify the repaired guide under the same gate, then check your own. The complete JSON reports behind this section, with the exact commit and Python version, are in [docs/readme-trial-evidence-2026-11-24.md](docs/readme-trial-evidence-2026-11-24.md). Your output will differ slightly: `local_evaluation.evaluated_at` is the evaluation time, and the `metadata.last-reviewed.age` info finding counts days from each guide's `last-reviewed` date.

Step 1. From an empty working directory, clone the source and check out the pinned commit that adds the repaired example. That commit follows the v2.0.0 release; its verifier reports version 2.0.0 and evaluates released profile 2.0.0. The directory `guidecheck-trial` must not already exist there.

Literal
```bash
git clone https://github.com/snapsynapse/guidecheck.git guidecheck-trial
```
Literal
```bash
cd guidecheck-trial
```
Literal
```bash
git checkout --detach 3feb5e0043b224379d59782a8700bc795ede9a0d
```
Step 2. Reproduce the known failure. Expect `action.exec-unbounded` as a blocking finding, achieved Level 2, and exit code 1.

Literal
```bash
python3 scripts/guidecheck_verify.py fixtures/profiles/2.0.0/corrected-bound-unpinned/guide.txt --require-profile-version 2.0.0 --level 3 --pretty
```
Step 3. Read the repair. `examples/2.0.0-corrected-bound-inline/guide.txt` is the same guide with the action bounded: `npm --prefix subdir run check`, which runs repository code the guide does not show, becomes `example-verifier --version`, which a reviewer can read in full, and the class and approval follow. It also drops `manifest-url`, so a local check is not asked for Level 4 evidence it cannot fetch, and updates the version, review date, checklist and threat model lines to match. `diff` exits 1 because the files differ; that is expected.

Literal
```bash
diff fixtures/profiles/2.0.0/corrected-bound-unpinned/guide.txt examples/2.0.0-corrected-bound-inline/guide.txt
```
Step 4. Verify the repaired guide under the same gate. Expect verifier version 2.0.0, achieved Level 3, no blocking findings, `Proceed? yes`, and exit code 0.

Literal
```bash
python3 scripts/guidecheck_verify.py examples/2.0.0-corrected-bound-inline/guide.txt --require-profile-version 2.0.0 --level 3 --pretty
```
Step 5. Check your own local `assistant-guide.txt` from the same checkout. You do not need to change its profile declarations to run the check.

Replace: GUIDE_PATH -> the absolute path to the local assistant-guide.txt to inspect.

Customize
```bash
python3 scripts/guidecheck_verify.py 'GUIDE_PATH' --level 3 --pretty
```
Native exit codes are 0 when the requested gate is accepted, 1 for blocking findings or a result below the requested level, and 2 for handled missing-input or profile-selection errors. Treat operational failures separately from conformance rejection. The experimental `--contract posix-json-v1` selector has different exit semantics; see [docs/cli-contract.md](docs/cli-contract.md) if you are integrating the verifier into another tool.

If a result gates anything, state the gate: `--require-profile-version 2.0.0 --level 3`. Without `--require-profile-version`, the guide's own declaration selects the evaluator, so its author decides which checks run. Without `--level`, exit code 0 means only that no blocking finding was raised, at whatever level was achieved. The verifier prints a note on stderr in both cases; the report on stdout is unchanged. The report's `Proceed?` line counts blocking findings only and does not reflect `--level` or `--fail-on-warning`, so do not gate on it.

Read `guide.achieved_level` and the finding list, not the exit code alone, when your guide declares profile 2.0.0 or 1.0.0 and includes a `manifest-url`. Declaring `manifest-url` claims Level 4. Level 4 provenance requires fetched evidence, which the local check cannot supply, so it reports blocking `anchor.independent.missing` and exits 1 even when `achieved_level` is 3. The hosted verifier, which is a preview, fetches and reports declared anchor evidence but does not verify it, so it also caps at Level 3. No GuideCheck verifier currently awards Level 4. This is current behavior of both verifiers.

## Have an instruction file rather than a guide?

If you have an `AGENTS.md`, `CLAUDE.md`, README, or skill file rather than an `assistant-guide.txt`, scan that existing file for supported hidden-instruction channels. This does not require adopting the profile and is separate from guide verification. Run it from the same checkout.

Replace: INSTRUCTION_FILE -> the absolute path to one local instruction file to inspect.

Customize
```bash
python3 scripts/guidecheck_scan.py 'INSTRUCTION_FILE' --json
```
The scanner reports findings such as `surface.hidden-html-comment`, invisible Unicode, supported CSS-hidden text, and ANSI escapes. It does not award a conformance level. Run against this repository's own `CLAUDE.md` it reported 0 findings (exit 0). Detection favors precision over recall: no findings means no supported channel was detected in that input, not that the file is safe or that all prompt injection was excluded. In directory mode the scanner does not follow symbolic links and reads at most 2 MiB of each file; `summary.surfaces_incomplete` in the JSON output counts surfaces that were skipped, truncated or not followed, and the exit code does not reflect them, so check that field when a clean result has to mean every surface was read.

## What to do with a blocking finding

1. Inspect the implicated bytes. The `evidence` field of `action.exec-unbounded` names the action id (`check-version` above).
2. Bound the execution. Replace the repository script dispatch with inline actions that a reviewer can read in the guide, or declare a valid `exec-sha256` for the invoked code. The corrected-content policy covers dispatch and pinning limits: [docs/corrected-content-policy-2026-09-07.md](docs/corrected-content-policy-2026-09-07.md). Finding ids are registered in `finding-ids.md`.
3. Rerun the check without executing the guide. Steps 3 and 4 of "Try it" show this repair on the fixture above.

Keep these claims distinct:
- Human approval being requested (`approval: required`) does not bound the command.
- A pin declaration is not pin verification. A declared `exec-sha256` is not evidence that the verifier read the target bytes. The local verifier does not read the invoked artifact and reports the pin as `exec-sha256.unverified`.
- Fetched provenance (Level 4) is not runtime enforcement (Level 5), and neither is a statement that the guide is safe.

## Learning path

Pages grouped by what they are for. Each page is listed once.

- Tutorial: [Try it](#try-it), the fail, repair, pass lesson above.
- How-to: [ADOPTION.md](ADOPTION.md) for the level-by-level path to a conforming guide, and [Have an instruction file rather than a guide?](#have-an-instruction-file-rather-than-a-guide) for scanning existing files.
- Reference: [profiles/2.0.0/spec.md](profiles/2.0.0/spec.md), [profiles/2.0.0/verifier-conformance.md](profiles/2.0.0/verifier-conformance.md), [finding-ids.md](finding-ids.md), [docs/cli-contract.md](docs/cli-contract.md), and [docs/verifier-scope.md](docs/verifier-scope.md).
- Explanation: [design-rationale.md](design-rationale.md), [threat-register.md](threat-register.md), and [operator-guide.md](operator-guide.md).

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

- The local reference CLI (`scripts/guidecheck_verify.py`, or `guidecheck verify` from Homebrew) evaluates Levels 1 through 3 from local bytes and never executes guide content.
- The hosted verifier at https://guidecheck.org/verify is a preview that fetches a guide by URL and applies the same Level 1 to 3 checks.
- Neither verifier awards Level 4 today: the local CLI cannot fetch independent evidence, and the hosted verifier reports declared anchors as unverified.
- Neither claims Level 5, which needs a conformant assistant runtime.
- Installation, Level 4 evidence checks, hosted limits and telemetry, and the local eval suite are in [docs/verifier-scope.md](docs/verifier-scope.md).

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
- `docs/verifier-scope.md` - what each verifier checks, how to run it, current hosted limits, and the local eval suite
- `docs/readme-trial-evidence-2026-11-24.md` - captured output behind the "Try it" section (supersedes `docs/readme-trial-evidence-2026-10-21.md`)
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
