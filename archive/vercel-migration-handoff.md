# Vercel Migration Handoff

Status: planning handoff, not executed.

## Goal

Migrate GuideCheck from a static-only GitHub Pages deployment to a Vercel-hosted site that can serve both:

- the static standards site and documentation
- a hosted `/verify/` experience backed by a verifier API

The first hosted verifier should remain limited to GuideCheck Levels 1 through 3. It must not claim Level 4 provenance, hosted verifier conformance, or Level 5 runtime conformance until those parts of the profile and fixture suite are complete.

## Current State

- Static site output lives under `docs/`.
- GitHub Pages can serve the current site as-is.
- The local reference verifier lives at `scripts/guidecheck_verify.py`.
- The fixture check for the local verifier is `make verify-fixtures`.
- The broader regression harness is `make eval`.
- Verifier output schema is `schemas/verifier-output.schema.json`.
- The verifier is local-file only today. It does not fetch arbitrary public URLs.

## Recommended Target Architecture

Use Vercel for both frontend and verifier API:

- `https://guidecheck.org/` serves the static site.
- `https://guidecheck.org/verify/` serves a static verifier UI.
- `https://guidecheck.org/api/verify` accepts a public guide URL and returns verifier JSON plus a compact report.

This keeps same-origin routing simple and avoids CORS complexity. If the API is later separated, use `https://api.guidecheck.org/verify` with strict CORS for `https://guidecheck.org/`.

## Migration Scope

Phase 1 should migrate hosting and add a Level 1-3 verifier endpoint only.

In scope:

- preserve existing static pages from `docs/`
- preserve canonical URLs under `https://guidecheck.org/`
- add Vercel routing for `/verify/`
- add a serverless verifier API for public URL input
- reuse the existing local verifier evidence model where practical
- cap hosted results at Level 3
- document temporary limitations in the UI and API response

Out of scope:

- Level 4 manifest fetch and independent-anchor verification
- DNS TXT, package registry, repository-file, or signed `security.txt` anchor checks
- Level 5 runtime enforcement
- signed verifier output
- private repository, authenticated, or offline archive verification modes

## Security Requirements For The API

The API fetches user-supplied URLs, so this is the main risk surface.

Required controls:

- accept only HTTPS guide URLs
- reject plaintext HTTP
- send no cookies, authorization headers, or ambient credentials
- do not execute scripts or render fetched content
- enforce response size limit before buffering full responses
- enforce total request timeout and body read timeout
- limit redirects, default 5
- report redirect chain
- reject cross-registered-domain redirects for Level 2 and above
- block localhost, loopback, private, link-local, multicast, unspecified, and cloud metadata IP ranges
- resolve DNS before connecting and reject private targets
- re-check resolved IP after each redirect
- sanitize fetch errors before returning them to users
- rate limit by IP and possibly by target host
- log minimally; submitted URLs may be sensitive
- never log cookies, auth headers, or internal network details

## API Contract

Proposed request:

```text
POST /api/verify
Content-Type: application/json

{
  "url": "https://example.com/.well-known/assistant-guide.txt"
}
```

Proposed successful response:

```text
{
  "verifier": {
    "name": "guidecheck-hosted",
    "version": "0.1.0",
    "verifier_profile": "human-verifiable-assistant-guide-verifier",
    "verifier_profile_version": "0.1.0",
    "guide_profile": "human-verifiable-assistant-guide",
    "guide_profile_version": "0.1.0"
  },
  "input": {
    "evaluation_mode": "public-web",
    "url": "https://example.com/.well-known/assistant-guide.txt"
  },
  "fetch": {
    "final_url": "https://example.com/.well-known/assistant-guide.txt",
    "fetched_at": "2026-05-22T00:00:00Z",
    "http_status": 200,
    "headers": {
      "content-type": "text/plain; charset=utf-8"
    },
    "redirects": [],
    "tls_valid": true
  },
  "guide": {
    "bytes": 4821,
    "sha256": "<hex>",
    "achieved_level": 3,
    "level5_ready": false
  },
  "summary": {
    "blocking_findings": 0,
    "warnings": 0,
    "infos": 0
  },
  "findings": [],
  "compact_report": "Verifier: guidecheck-hosted 0.1.0\nGuide: https://example.com/.well-known/assistant-guide.txt\nLevel: 3\nSHA-256: <hex>\nBlocking findings: 0\nWarnings: 0\nHash pinned: no\nProceed? yes"
}
```

The hosted response should include an explicit limitation field or finding until Level 4 exists, for example:

```text
{
  "hosted_limitations": [
    "This verifier evaluates Levels 1 through 3 only.",
    "Level 4 provenance and independent anchors are not implemented.",
    "Level 5 runtime conformance is not evaluated."
  ]
}
```

## Frontend Requirements

The `/verify/` page should provide:

- URL input for a public `assistant-guide.txt`
- submit button
- loading state
- compact report display
- full findings table
- raw JSON output panel or download
- clear statement that conformance is not safety
- clear statement that this hosted verifier is currently Level 1-3 only
- privacy note explaining URL logging and retention
- error state for blocked URLs, fetch failure, timeout, and invalid response

The page should not imply that GuideCheck is the only authoritative verifier. Wording should say users may use this verifier or another conformant verifier.

## Vercel Project Shape

The repo currently does not require a framework. Keep the migration minimal unless a later UI requires more.

Recommended options:

1. Static output plus serverless function
   - keep `docs/` as the static output
   - add a Vercel route for `/api/verify`
   - add a static `/verify/` page under `docs/verify/index.html`

2. Lightweight Next.js app
   - move static pages into a Next.js app
   - implement `/verify/` as a page
   - implement `/api/verify` as a route handler

Prefer option 1 for the first migration if Vercel can serve the existing static output cleanly. Prefer option 2 only if the UI needs a richer app structure.

## Files Likely To Add Or Change

Likely new files:

- `vercel.json`
- `api/verify.py` or `api/verify.ts`
- `docs/verify/index.html`
- `docs/verify/verify.js`
- `docs/verify/verify.css`

Possible changed files:

- `README.md`
- `roadmap.md`
- `schemas/verifier-output.schema.json`
- `scripts/guidecheck_verify.py`
- `scripts/check_reference_verifier.py`

Do not commit `.vercel/` unless the team intentionally wants project linkage stored. Do not commit Vercel tokens or environment files.

## Build And Deployment Plan

1. Create a Vercel project for `guidecheck.org`.
2. Decide whether the project root serves `docs/` directly or uses a small build step that copies static assets.
3. Add `vercel.json` routes for static site and API.
4. Add `/verify/` static UI.
5. Add `/api/verify`.
6. Port the local verifier checks into API-safe code.
7. Add public-web fetch safety tests.
8. Run `make verify-fixtures`.
9. Run `make eval`.
10. Deploy preview.
11. Verify:
    - `https://guidecheck.org/`
    - `https://guidecheck.org/verify/`
    - `https://guidecheck.org/.well-known/assistant-guide.txt`
    - `https://guidecheck.org/schemas/verifier-output.schema.json`
12. Promote preview to production only after the canonical URLs and well-known paths work.

## Verification Checklist

Before production cutover:

- local verifier fixtures pass
- generated evals pass
- hosted API blocks `http://` inputs
- hosted API blocks localhost
- hosted API blocks private IPs
- hosted API blocks cloud metadata IPs
- hosted API enforces max response size
- hosted API enforces timeout
- hosted API reports redirect chain
- hosted API does not return internal network details
- `/verify/` labels Level 1-3 limitation
- `/verify/` says conformance is not safety
- canonical `assistant-guide.txt` remains reachable
- schemas remain reachable
- OpenGraph image remains reachable at `/imgs/og.png`
- old GitHub Pages deployment is either disabled or redirects consistently after DNS cutover

## DNS And Cutover Notes

Current canonical domain is `https://guidecheck.org/`.

Cutover should preserve:

- `https://guidecheck.org/`
- `https://guidecheck.org/verify`
- `https://guidecheck.org/verify/`
- `https://guidecheck.org/.well-known/assistant-guide.txt`
- `https://guidecheck.org/schemas/manifest.schema.json`
- `https://guidecheck.org/schemas/verifier-output.schema.json`
- `https://guidecheck.org/schemas/fixture-expected.schema.json`

Avoid introducing `www` as canonical. If Vercel provisions `www`, redirect it to the bare domain.

## Open Decisions

- Whether to use static `docs/` plus serverless API or migrate to a lightweight app framework.
- Whether the API implementation should be Python to reuse current verifier code or TypeScript to match common Vercel examples.
- Whether rate limiting should use Vercel Firewall, Edge Middleware, an external provider, or in-function controls.
- What URL logging and retention policy to publish.
- Whether `/verify/` should return only Level 1-3 or also show "Level 4 not evaluated" as an informational finding.
- Whether to keep GitHub Pages live as a fallback during DNS propagation.

## Handoff Summary

The safest migration is incremental:

1. Move static site hosting to Vercel without changing canonical content.
2. Add `/verify/` UI and `/api/verify` for Level 1-3 only.
3. Harden public-web fetch handling before any public launch claim.
4. Add Level 4 only after anchor formats and fixtures are finished.

Do not market the hosted checker as fully conformant until the verifier profile fixture suite is complete and the hosted implementation passes it.
