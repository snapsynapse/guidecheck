# repo-polish project context

Persisted decisions for the GuideCheck repo. A re-run of repo-polish reads
this and skips the questions it answers.

## Fields

- canonical_domain: guidecheck.org
- brand: paice
- is_fork: false
- upstream_url: none
- license: CC-BY-4.0 for specification text and documentation, MIT for code and schemas
- primary_signal: AI setup guides can hide instructions a model reads but a human never sees. GuideCheck is the plain-text standard that makes an assistant's instruction surface reviewable before it acts.
- differentiator: A constrained ASCII `assistant-guide.txt` profile with a five-level conformance ladder and a companion verifier conformance profile, instead of unconstrained HTML, Markdown, or PDF instruction surfaces.
- target_audience: Developers and maintainers who publish AI-assisted setup, install, or operational guides, and authors building conformant verifiers.

## Decisions

- GitHub Issues: enabled.
- GitHub Discussions: enabled. Issue config routes questions there.
- GitHub Wiki: disabled, not used.
- Release scheme: git tag `vX.Y.Z` tracks the profile version in `spec.md`. First release `v0.1.0`.
- Hosting: Vercel. GitHub Pages retired. Static site under `docs/`, hosted verifier API under `api/`.
- Not a binary product. Release assets are skipped; this is a specification and reference-tooling repo.

## Run history

- 2026-05-21: first repo-polish run. README, CHANGELOG, `.github/` templates, GitHub metadata, topics, release `v0.1.0`.
