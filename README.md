# GuideCheck

AI setup guides can hide instructions a model reads but a human never sees.
GuideCheck is the standards project for the Human-Verifiable Assistant Guide
profile: a constrained plain-text profile for `assistant-guide.txt`, covering
assistant-facing install, implementation, remediation, migration, and
operational instructions that a human can review in full before an assistant
acts on them.

Canonical site: https://guidecheck.org/
Verifier: https://guidecheck.org/verify

New here: `ADOPTION.md` is the practical on-ramp. It explains the conformance
ladder, gives a level-by-level path, and carries the guide-author checklist.

## Naming model

- The standards project, public checker, ecosystem, and site are GuideCheck.
- The artifact is `assistant-guide.txt`.
- The profile is the Human-Verifiable Assistant Guide profile.
- A conformant file is an `assistant-guide.txt` artifact that satisfies a
  specific profile version.
- A GuideCheck conformance claim is valid only when backed by verifier output,
  guide hash, achieved level, and findings.

## Conformance is not safety

Conformance to this profile, at any level, does not mean a guide is safe to
follow, that the publisher is trustworthy, or that the assistant may proceed
without the security practices a competent operator would already apply. A
verifier confirms form. The human confirms meaning. Read `spec.md` section 1
and `operator-guide.md` before adopting.

## The problem

AI-assisted setup guides are distributed through HTML, rendered Markdown, PDFs,
docs sites, copied issue comments, terminal output, and screenshots. Those
surfaces can carry content a model ingests but a human does not see: hidden
HTML comments, offscreen CSS, white-on-white text, script-inserted content,
invisible Unicode controls, terminal escape sequences, long buried instruction
blocks.

For high-consequence tasks, projects need a constrained instruction surface
that a human can review in full before authorizing an assistant to follow it.

## Who this is for

- AI governance practitioners who need evidence that guidance was reviewable
  before an assistant acted on it.
- Security engineers concerned with prompt injection and hidden instruction
  channels.
- AI platform and MLOps engineers who operationalize assistant workflows.
- Technical policy and compliance professionals working on evidence,
  reviewability, and control design.

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

## Documents

- `ADOPTION.md` - the practical on-ramp: conformance ladder, level-by-level path, guide-author checklist
- `spec.md` - the normative Human-Verifiable Assistant Guide profile
- `verifier-conformance.md` - the normative profile for tools that verify guides
- `design-rationale.md` - why the design choices were made
- `operator-guide.md` - non-normative defense-in-depth practices for operators
- `threat-register.md` - known risk classes for fixture, verifier, and runtime authors
- `schemas/` - JSON Schema for the manifest, verifier output, and fixture expectations
- `finding-ids.md` - registry for fixture-required verifier finding ids
- `assistant-guide.txt` - repository copy of the GuideCheck adoption guide
- `.well-known/assistant-guide.txt` - canonical public copy of the adoption guide
- `evals/` - local eval documentation for fixture and generated checks
- `scripts/eval_guidecheck.py` - dependency-free local eval runner
- `roadmap.md` - future actions and undecided questions
- `CHANGELOG.md` - profile and companion-document change history
- `CONTRIBUTING.md` - how to propose a profile change
- `SECURITY.md` - how to report a security weakness privately
- `examples/` - sample conforming guides and a sample manifest
- `fixtures/` - verifier conformance test corpus
- `INTENT.md` - standards-level strategy, invariants, and recalibration gates
- `archive/` - genesis documents, non-normative

## Conformance levels

- Level 0: instructions only available through surfaces that can hide or
  transform text
- Level 1: a plain-text guide exists, is reachable, and carries the compact
  verification instruction
- Level 2: strict ASCII byte profile, size limits, no disallowed constructs
- Level 3: assistant safety contract, all required sections, explicit approval gates
- Level 4: verifiable provenance, sidecar manifest, cross-channel hash on an
  independent control plane
- Level 5: a guide plus a conformant assistant runtime that mechanically
  enforces the execution contract

## Local Evals

Run the local regression suite with:
```text
make eval
```

Run the full local verification suite with:
```text
make test
```

The eval runner checks the static fixture corpus plus generated edge cases
for byte profile, metadata, action blocks, command restrictions, prohibited
patterns, manifest mismatch, and public-fetch safety. It is a repository
regression harness, not the normative verifier. See `evals/README.md`.

## Verifier scope

Verifier work is intentionally scoped to Levels 1 through 3. Two verifiers
exist, and both run the same check logic:

- a local-file reference CLI, `scripts/guidecheck_verify.py`
- a hosted public-web verifier at https://guidecheck.org/verify, which fetches
  a guide by URL and applies the same Level 1-3 checks

Both verifiers:

- evaluate `assistant-guide.txt` bytes without executing guide content
- compute and report the guide SHA-256
- check Level 1 compact verification instructions and basic source metadata
- check the Level 2 byte profile and disallowed constructs
- check Level 3 metadata, required sections, action blocks, approval gates,
  command restrictions, prohibited patterns, status, and staleness
- emit machine-readable verifier output plus the compact human-readable report

Run the local reference verifier with:
```text
python3 scripts/guidecheck_verify.py assistant-guide.txt --pretty
```

Run the static fixture check for the reference verifier with:
```text
make verify-fixtures
```

The hosted verifier is a preview. It is live and usable, but it is not
presented as fully conformant: the verifier conformance fixture suite is not
yet complete, and the hosted implementation has not been shown to pass it.

Temporary limitations:

- no public conformance claim beyond Level 3
- no Level 4 provenance claim until manifest and independent-anchor fixtures
  are complete
- the hosted verifier is a Level 1-3 preview; its SSRF and abuse controls are
  covered by unit tests in `scripts/test_fetch_safety.py`, but public-web
  fetch replay fixtures, redirect cases, and TLS cases are still outstanding
- no Level 5 runtime conformance claim; Level 5 remains out of scope for the
  reference verifier

The current `scripts/eval_guidecheck.py` remains a regression harness and
reference map, not the verifier itself. The reference verifier lives in
`scripts/guidecheck_verify.py` and is checked against the same static fixture
expectation contract by `scripts/check_reference_verifier.py`.

## Status

Draft for review, profile version 0.2.0. See `CHANGELOG.md`.

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
