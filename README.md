# GuideCheck

GuideCheck is the standards project for the Human-Verifiable Assistant Guide profile: a constrained plain-text profile for `assistant-guide.txt`, covering assistant-facing install, implementation, remediation, migration, and operational instructions that a human can review in full before an assistant acts on them.

Canonical site: https://guidecheck.org/
Verifier: https://guidecheck.org/verify

## Naming model

- The standards project, public checker, ecosystem, and site are GuideCheck.
- The artifact is `assistant-guide.txt`.
- The profile is the Human-Verifiable Assistant Guide profile.
- A conformant file is an `assistant-guide.txt` artifact that satisfies a specific profile version.
- A GuideCheck conformance claim is valid only when backed by verifier output, guide hash, achieved level, and findings.

## Conformance is not safety

Conformance to this profile, at any level, does not mean a guide is safe to follow, that the publisher is trustworthy, or that the assistant may proceed without the security practices a competent operator would already apply. A verifier confirms form. The human confirms meaning. Read `spec.md` section 1 and section 28 before adopting.

## The problem

AI-assisted setup guides are distributed through HTML, rendered Markdown, PDFs, docs sites, copied issue comments, terminal output, and screenshots. Those surfaces can carry content a model ingests but a human does not see: hidden HTML comments, offscreen CSS, white-on-white text, script-inserted content, invisible Unicode controls, terminal escape sequences, long buried instruction blocks.

For high-consequence tasks, projects need a constrained instruction surface that a human can review in full before authorizing an assistant to follow it.

## What this profile defines

- a `.txt` artifact named `assistant-guide.txt`, served at `/.well-known/assistant-guide.txt`
- a strict ASCII byte profile and an 8 KiB size cap, so the whole instruction surface is reviewable in one sitting
- structured `[action]` blocks with explicit classes, approval gates, and command restrictions
- a five-level conformance ladder, from plain-text availability through verifiable provenance to runtime-enforced execution
- a sidecar manifest plus cross-channel hash publication for provenance
- a companion verifier conformance profile so independent verifiers agree on results

## Documents

- `spec.md` - the normative Human-Verifiable Assistant Guide profile
- `verifier-conformance.md` - the normative profile for tools that verify guides
- `design-rationale.md` - why the design choices were made
- `threat-register.md` - known risk classes for fixture, verifier, and runtime authors
- `schemas/` - JSON Schema for the manifest, verifier output, and fixture expectations
- `finding-ids.md` - registry for fixture-required verifier finding ids
- `examples/` - sample conforming guides and a sample manifest
- `fixtures/` - verifier conformance test corpus
- `INTENT.md` - standards-level strategy, invariants, and recalibration gates
- `archive/` - genesis documents, non-normative

## Conformance levels

- Level 0: instructions only available through surfaces that can hide or transform text
- Level 1: a plain-text guide exists, is reachable, and carries the compact verification instruction
- Level 2: strict ASCII byte profile, size limits, no disallowed constructs
- Level 3: assistant safety contract, all required sections, explicit approval gates
- Level 4: verifiable provenance, sidecar manifest, cross-channel hash on an independent control plane
- Level 5: a guide plus a conformant assistant runtime that mechanically enforces the execution contract

## Status

Draft for review, profile version 0.1.0. See `CHANGELOG.md`.

## License

Specification text and documentation: Creative Commons Attribution 4.0 International (`LICENSE`).
Reference code and schemas: MIT (`LICENSE-MIT`).
Copyright 2026 PAICE.work PBC.

## Project

A PAICE Foundation standard. See https://paice.foundation/ for the portfolio.
