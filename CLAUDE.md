# CLAUDE.md

Agent guidance for working in this repository.

## Purpose

GuideCheck is a trust-boundary standards project: the Human-Verifiable
Assistant Guide profile for `assistant-guide.txt`. It defines a constrained,
plain-text, ASCII-only instruction surface that a human can fully review
before an AI assistant acts on it, closing the gap between "instructions a
human approved" and "instructions an agent actually executes." It also ships
a reference verifier and (new, 0.7.x) an instruction-surface scanner that
checks existing files (AGENTS.md, CLAUDE.md, README, SKILL, llms.txt,
assistant-guide.txt) for hidden-instruction channels (HTML comments,
invisible Unicode, CSS-hidden text, ANSI escapes).

Canonical site: https://guidecheck.org/ · Verifier: https://guidecheck.org/verify

## Tech stack

- Python 3.10+ (reference verifier, scanner, CLI, eval/test harness) — no
  external runtime dependencies beyond the standard library for the core
  tools; packaging uses `setuptools` via `pyproject.toml`.
- Plain-text/Markdown for the normative spec and companion docs.
- JSON Schema (`schemas/`) for the manifest, verifier output, and fixture
  contracts.
- Static HTML/CSS for the public site under `docs/` (served, not built by a
  framework).
- GitHub Actions for CI/CD; Sigstore/cosign for release artifact signing.

## Directory layout

- `spec.md` — normative Human-Verifiable Assistant Guide profile.
- `verifier-conformance.md` — normative profile for tools that verify guides.
- `design-rationale.md`, `operator-guide.md`, `threat-register.md` — explanatory/
  non-normative companions that must stay consistent with the normative docs.
- `ADOPTION.md` — practical on-ramp: conformance ladder, level-by-level path,
  guide-author checklist.
- `INTENT.md` — standards-level strategy, invariants, recalibration gates.
- `roadmap.md` — future actions and undecided questions (not normative).
- `finding-ids.md` — registry for fixture-required and emitted verifier
  finding ids (normative per `CONTRIBUTING.md`).
- `CHANGELOG.md` — profile and companion-document change history (Keep a
  Changelog format, SemVer).
- `docs/` — public site (`index.html`, `.well-known/` surface, integration
  notes: `acs-integration.md`, `mcp-integration.md`, `a2a-integration.md`;
  Level 5 planning notes: `level-5-runtime-conformance.md`,
  `level-5-implementation-plan.md`, `pre-level-5-readiness.md`).
- `scripts/` — Python tools:
  - `guidecheck_profiles.py` selects an explicitly supported policy from guide
    bytes; caller profile assertions never reinterpret those bytes.
  - `guidecheck_legacy.py` and `guidecheck_legacy_constants.py` preserve the
    3ceb30a evaluator and 0.7.1 report contract; frozen artifact digests and full
    report replays guard compatibility.
  - `guidecheck_strict.py` implements the opt-in 1.0.0 provenance policy.
  - `guidecheck_corrected.py` implements the opt-in 2.0.0 corrected-content policy.
  - `guidecheck_verify.py` — local-file reference verifier CLI (Levels 1-3,
    plus internal-consistency checks on Level 4 sidecar manifests/anchors).
  - `guidecheck_scan.py` / `guidecheck_cli.py` — instruction-surface scanner
    (`guidecheck scan <url-or-file-or-dir>`), new in 0.7.x.
  - `guidecheck_fetch.py`, `guidecheck_hosted_anchors.py` — fetch/anchor
    support for hosted verifier checks.
  - `guidecheck_constants.py` — single source of truth for the version
    string; checked by `check_version_sync.py`.
  - `eval_guidecheck.py` — regression harness over fixtures + generated edge
    cases (not the normative verifier).
  - `check_reference_verifier.py`, `validate_contracts.py`,
    `check_guide_artifacts.py`, `check_version_sync.py`, and the
    `test_*.py` files — CI-run checks invoked via `make test`.
- `fixtures/` — verifier conformance test corpus (static, pinned).
- `schemas/` — JSON Schema for manifest / verifier output / fixture contracts.
- `examples/` — sample conforming guides and a sample manifest.
- `evals/` — local eval documentation.
- `assistant-guide.txt` — this repo's own guide (dogfooding); a canonical
  copy is published at `docs/.well-known/assistant-guide.txt` and must stay
  byte-identical to the repo root copy.
- `archive/` — historical/genesis documents; not edited.
- `.github/workflows/` — `test.yml` (CI on push/PR to `main`), `release.yml`
  (tag-triggered release build + Sigstore signing).

## Conventions

- Normative documents (`spec.md`, `verifier-conformance.md`) drive behavior;
  explanatory docs (`design-rationale.md`, `threat-register.md`) must be kept
  consistent with them, not the other way around.
- Software, engine, released-profile, and self-guide versions are separate in
  `scripts/guidecheck_constants.py`. The legacy engine has frozen constants.
  `scripts/check_version_sync.py` checks the 2.0.0 candidate surfaces while
  legacy/self-guide surfaces remain 0.7.1; candidate work must not rewrite the
  published self-guide or its anchors.
- `finding-ids.md` is the normative registry for finding ids; new finding ids
  used by fixtures or emitted by verifiers/scanner must be registered there
  (see `CONTRIBUTING.md`).
- Root and `.well-known` copies of `assistant-guide.txt` must be byte-
  identical (`spec.md` section 6); `check_version_sync.py` checks this.
- Fixtures pin exact expected findings/warnings (`warnings_exact`,
  `forbidden_warning_ids`) so false positives fail tests, not just true
  negatives.
- Commits in this repo follow Conventional-ish free-text summaries with a
  detailed body explaining rationale; recent commits include a
  `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>` trailer when an
  agent contributed.
- Roadmap/INTENT items are explicitly non-binding until resolved and moved
  into `spec.md`/`verifier-conformance.md`; don't treat roadmap language as
  normative.

## Build / test (from docs — do not execute without explicit instruction)

```text
make eval              # regression suite: fixtures + generated edge cases
make verify-fixtures   # static fixture check for the reference verifier
make validate-contracts
make test              # full local verification suite (everything above plus
                        # contract schema validation, parser edge cases,
                        # guide-artifact checks, version sync, fetch-safety,
                        # hosted-anchor/API tests, fetch-replay, CLI contract,
                        # scanner tests)
make release-archive   # source archive for a GitHub release
make conformance-kit   # standalone fixtures+schemas archive for independent
                        # verifier implementations
```

Reference verifier direct invocation:
```text
python3 scripts/guidecheck_verify.py assistant-guide.txt --pretty
```

CI (`.github/workflows/test.yml`) runs `make test` on every push to `main`
and on pull requests. `release.yml` runs on `v*` tags: `make test`, then
builds and Sigstore-signs release + conformance-kit artifacts.

## Current state

- The current candidate is 2.0.0 and is unpublished. Profile 1.0.0 remains the
  last published profile (see `CHANGELOG.md`).
- Most recent work (2026-07-07): added `guidecheck scan`, a standalone
  instruction-surface scanner for existing files (AGENTS.md/CLAUDE.md/
  README/SKILL/llms.txt/assistant-guide.txt) that flags hidden-instruction
  channels independent of full assistant-guide.txt conformance — framed as
  "adoption steps 1-2," the low-friction front door ahead of full profile
  adoption. Packaged via `pyproject.toml` for `uvx guidecheck scan`.
- `roadmap.md` records current work and disposition; `handoffs/` contains
  only unprocessed temporary queues.
- Release and conformance-kit signing is settled: 0.6.0 and later use Sigstore
  cosign keyless in the tag-triggered release workflow; SHA256SUMS remains the
  integrity reference for 0.5.0 and earlier. Open items tracked in `roadmap.md`
  and `INTENT.md` include whether to build a second independent verifier
  implementation (Go vs Rust undecided) or recruit an external one, Level 5
  runtime-conformance fixture-suite design, and a possible higher provenance
  tier above Level 4/5.
- The hosted verifier at guidecheck.org/verify is explicitly a preview: its
  conformance fixture suite is incomplete and it has not been shown to pass
  it; signed `security.txt` anchors are not yet fetched by the hosted path.

## Version-aware release (2026-09-05)

The approved version-aware dispatcher is released as 1.0.0. Legacy profiles retain the isolated 0.7.1 behavior; explicit
1.0.0 guides use strict repository-anchor exclusion. Current normative text
and examples live in `profiles/1.0.0/`, with new schemas in `schemas/1.0.0/`.
Root normative documents and published guide bytes remain the legacy contract.
See `docs/anchor-dispatch-validation.md` for evidence and remaining release gates.
`make test` remains Python-only; `make test-verify-ui` requires Node 18+ and runs
the deterministic DOM contract separately. CI runs both.

Local bounded-execution findings are implemented in the shared verifier. Pins
remain unverified, including through hosted callers. See roadmap.md for pending
hosted fetching and independence decisions. Legacy profile behavior remains pinned to the pre-dispatch baseline.

## Corrected-content candidate (2026-09-07)

The opt-in 2.0.0 candidate selects `corrected-content-1` while retaining the
`1.0.0-strict` anchor policy. See `docs/corrected-content-policy-2026-09-07.md`
and `RELEASE_NOTES-2.0.0.md`. It does not publish, migrate, or reinterpret
legacy, 1.0.0, or self-guide bytes. The experimental POSIX CLI selector
`--contract posix-json-v1` is independent of the guide-declared profile
selector; see `docs/cli-contract.md`.
