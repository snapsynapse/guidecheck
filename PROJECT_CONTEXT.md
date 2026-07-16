# Project Context

## What this project is

GuideCheck is a PAICE Foundation open standard: the Human-Verifiable
Assistant Guide profile. It defines `assistant-guide.txt`, a constrained,
ASCII-only, size-capped plain-text artifact for assistant-facing install,
implementation, remediation, migration, and operational instructions — one
that a human can review in full before an AI agent is allowed to act on it.
The core claim is "review integrity": the instruction surface a human
approves and the instruction surface an agent executes should be one bounded
artifact, closing the gap that hidden HTML comments, invisible Unicode,
CSS-hidden text, or runtime-fetched payloads can otherwise exploit.

Companion tooling: a reference verifier (Levels 1-3 locally, Levels 1-4 via
the hosted checker) and, as of 0.7.x, `guidecheck scan`, a standalone
instruction-surface scanner that checks existing files people already
publish (AGENTS.md, CLAUDE.md, README, SKILL files, llms.txt,
assistant-guide.txt) for hidden-instruction channels — designed as a
zero-adoption-cost front door into the standard.

Explicitly out of scope / not claimed: conformance to the profile does not
mean a guide is safe, that its publisher is trustworthy, or that an assistant
may skip ordinary security practice. The profile verifies form; a human
still verifies meaning.

## Audience

- AI governance practitioners needing evidence guidance was reviewable
  before an assistant acted on it.
- Security engineers working on prompt injection and hidden-instruction
  channels.
- AI platform / MLOps engineers operationalizing assistant workflows.
- MCP server authors and host implementers needing reviewable install,
  configuration, tool, resource, and approval boundaries.
- A2A implementers evaluating trust boundaries for delegated tasks and
  remote-agent instructions.
- Technical policy / compliance professionals working on evidence and
  control design.
- Anyone taking basic precautions against prompt injection when using AI
  agents to install software or take autonomous action.

## Style / tone

Formal, precise, standards-document register throughout README and the
normative specs — dense, declarative sentences, minimal hedging, heavy use of
defined terms ("conformance," "profile," "anchor," "finding id"). Explanatory
docs (design-rationale, operator-guide, roadmap) are more discursive but stay
technical and unembellished. No marketing language; claims are consistently
qualified ("Conformance is not safety," "preview," "not a commitment").
Changelog and commit messages favor full sentences explaining rationale, not
just what changed. This is house style for GuideCheck specifically — treat it
as the model for any new content in this repo (site copy, docs, release
notes), rather than a general PAICE-wide default.

## Key URLs

- Canonical site: https://guidecheck.org/
- Hosted verifier: https://guidecheck.org/verify
- Repository: https://github.com/snapsynapse/guidecheck
- Portfolio: https://paice.foundation/
- Referenced external incident write-up (motivates the 0.7.0 bounded-execution
  work): https://0din.ai/blog/clone-this-repo-and-i-own-your-machine

## Current status

Released, profile version 0.7.0 (see `CHANGELOG.md`). `main` is clean and in
sync with `origin/main`. Most recent shipped work: `guidecheck scan`, an
instruction-surface scanner for pre-existing AGENTS.md/CLAUDE.md/README/
SKILL/llms.txt-style files (2026-07-07). Undecided/open items live in
`roadmap.md` and `INTENT.md`: conformance-kit signing mechanism, a possible
second independent verifier implementation (language undecided), and the
Level 5 runtime-conformance fixture suite design. See `CLAUDE.md` for
technical/agent-facing detail.
