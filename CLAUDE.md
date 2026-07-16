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
- Profile version lives in `scripts/guidecheck_constants.py` and is asserted
  across every version-bearing surface by `scripts/check_version_sync.py` —
  never hand-edit a version number in one place without checking sync.
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

- Released, profile version 0.7.0 (see `CHANGELOG.md`). Working tree is
  clean; `main` is up to date with `origin/main`.
- Most recent work (2026-07-07): added `guidecheck scan`, a standalone
  instruction-surface scanner for existing files (AGENTS.md/CLAUDE.md/
  README/SKILL/llms.txt/assistant-guide.txt) that flags hidden-instruction
  channels independent of full assistant-guide.txt conformance — framed as
  "adoption steps 1-2," the low-friction front door ahead of full profile
  adoption. Packaged via `pyproject.toml` for `uvx guidecheck scan`.
- `SESSION_HANDOFF.md` at the repo root is dated 2026-06-09 (pre-0.7.0,
  pre-scanner) — treat it as historical context, not current status; prefer
  `CHANGELOG.md`, `INTENT.md`, and `roadmap.md` for what's current.
- Open/undecided items tracked in `roadmap.md` and `INTENT.md`: conformance-
  kit signing mechanism (minisign vs Sigstore — SHA256SUMS is the interim
  integrity reference), whether to build a second independent verifier
  implementation (Go vs Rust undecided) or recruit an external one, Level 5
  runtime-conformance fixture suite design, and a possible higher provenance
  tier above Level 4/5.
- The hosted verifier at guidecheck.org/verify is explicitly a preview: its
  conformance fixture suite is incomplete and it has not been shown to pass
  it; signed `security.txt` anchors are not yet fetched by the hosted path.
