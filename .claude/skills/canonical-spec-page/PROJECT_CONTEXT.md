# PROJECT_CONTEXT.md — canonical-spec-page

This file lives at `.claude/skills/canonical-spec-page/PROJECT_CONTEXT.md` in the target project. The skill reads it during Phase 0 and skips any questions whose answers it finds here.

```yaml
# Identity
project_name: GuideCheck
canonical_url: https://guidecheck.org/
repo_slug: snapsynapse/guidecheck

# Hero
tagline: The Human-Verifiable Assistant Guide standard
hero_h1: Every instruction, in plain sight.
hero_subtitle: >
  GuideCheck defines the Human-Verifiable Assistant Guide profile — a
  constrained plain-text artifact for the install, setup, and remediation
  instructions an AI assistant will act on.
hero_hook: >
  AI-assisted setup guidance reaches assistants through HTML, rendered
  Markdown, PDFs, and copied terminal output. Those surfaces can carry
  text a model ingests but a human never sees. For high-consequence tasks,
  the instruction surface should be something a human can read in full first.

# SEO
keywords:
  - guidecheck
  - assistant-guide.txt
  - human-verifiable assistant guide
  - AI setup guide
  - prompt injection defense
  - well-known assistant guide
  - conformance verifier

# Authorship
author_name: Sam Rogers
author_url: https://linkedin.com/in/samrogers
publisher_name: PAICE.work PBC
publisher_url: https://paice.work/
twitter_handle: "@snapsynapse"

# Dates
date_published: "2026-05-21"
date_modified: "2026-05-21"

# Versioning
version: v0.1.0
canonical_file: spec.md

# Theme
theme_accent: "#0b6a62"
dark_mode_default: false

# Publish layout
publish_root: "docs/"
mode: generate

# JSON-LD relationships
defined_term_alternate_names:
  - guidecheck
  - Human-Verifiable Assistant Guide
  - assistant-guide.txt
defined_term_description: >
  GuideCheck is a constrained plain-text profile for assistant-guide.txt,
  an assistant-facing instruction artifact. It is strict ASCII, capped at
  8 KiB, and structured into explicit action blocks so a human can review
  the entire instruction surface in one sitting before an assistant acts.
citations:
  - { name: "Graceful Boundaries", url: "https://gracefulboundaries.dev/" }
  - { name: "Knowledge as Code",   url: "https://knowledge-as-code.com/" }
  - { name: "Skill Provenance",    url: "https://skillprovenance.dev/" }
  - { name: "HardGuard25",         url: "https://hardguard25.com/" }
same_as:
  - https://github.com/snapsynapse/guidecheck

# Secondary page
secondary_demo:
  path: /verify/
  label: Verify a guide
  source_html: docs/verify/index.html   # generated placeholder, not a moved page

# OG image
og_image_source: imgs/og.png   # light variant; imgs/og-darkmode.png is the dark variant

# Logo concept
logo_concept: |
  Bracket-check mark. Two square brackets with a checkmark between them.
  The brackets are literal: the artifact format delimits executable
  instructions in [action] blocks. The checkmark is GuideCheck verification.
  32x32 viewBox, stroke 2.8, round caps. Favicon variant: same mark in
  teal #2dd4bf on a dark #0f1117 rounded square for tab contrast.
```

## Notes from this build

- `og.png` and `og-darkmode.png` exist at `imgs/`; light variant chosen as the page default and OG image. Both are 1200x634 (4px taller than the 1200x630 OG ideal — acceptable, regenerate at 630 if a validator complains).
- The repo dogfoods its own spec: `assistant-guide.txt` and `security.txt` are served from `docs/.well-known/`. Keep that directory in sync with the repo-root copies, or treat `docs/.well-known/` as canonical.
- The `/verify/` page is a generated placeholder. Replace `docs/verify/index.html` with the real interactive verifier when it ships.
