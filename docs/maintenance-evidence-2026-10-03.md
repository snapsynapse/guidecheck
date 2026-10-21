# Maintenance and integration evidence

> Status note (2026-10-21): Point-in-time receipt. The tranche changes described as local were committed in 34331b9 and are on main. Handoff files it mentions no longer exist. Later main state, including c08b82e, is not covered.

Date: 2026-10-03 America/Denver. Scope: GuideCheck component maintenance.
Status: local documentation and diagnostic tranche; no commit, push, release or deployment performed by this tranche.

## Baseline and public state

The checkout started clean on `main` at `48848bf1b5b48b5ca369a48e1162e7d9b0c1daec`, equal to fetched `origin/main` and its upstream. There were no open repository PRs or issues at assessment time.

| Claim | Observed evidence | Limit |
|---|---|---|
| Current-head CI passes | [Test run 35950094380](https://github.com/snapsynapse/guidecheck/actions/runs/35950094380) for `48848bf` | CI is not runtime conformance or deployment evidence |
| 2.0.0 is published | [Release](https://github.com/snapsynapse/guidecheck/releases/tag/v2.0.0), created September 7 local time, September 8 UTC; source archives, conformance kit, checksums and signature/certificate assets listed | Asset presence was checked; signatures were not cryptographically reverified in this tranche |
| Current production source matches main | [Deployment manifest](https://guidecheck.org/deploy-manifest.json) names `48848bf`; listed implementation digests and selected public-surface digests match local files | Source identity does not certify all hosted behavior |
| Self-guide anchors match | Live guide is 8,065 bytes, SHA-256 `4b30202c809a3db037290371da8fed6a9681255199e0e19cfe1a0a7fc1d5df9e`; both authoritative nameservers and public DNS match | A dated DNS observation, not permanent assurance |
| Hosted self-guide reaches Level 4 | Fresh report has zero blockers and warnings; `level5_ready` remains guide-side preparation | Self-guide still selects the frozen 0.7.1 policy; this is not a 2.0.0 or Level 5 runtime result |
| Security metadata repair is delivered | Commit `0efe4ee` is on main; served security.txt matches local bytes | The security.txt is unsigned and is not independently qualifying evidence |
| Package metadata repair is present | Commit `fda5a67` declares MIT in `pyproject.toml` | Source metadata, not a new package-index publication |
| Commit signing is in use | GitHub reports `48848bf` verified | Local SSH verification reported no configured allowed-signers file; that local trust check remains separate |

The [machine-readable receipt](evidence/publisher-state-2026-10-03.json) retains UTC timestamps, digest comparisons, the complete hosted response, DNS resolver response and authoritative TXT readbacks. Those timestamps fall on October 4 UTC and October 3 in the session's America/Denver timezone. No DNS, guide, manifest or production mutation was made.

## Component direction and integration

The September 22 owner direction is now carried into [INTENT](../INTENT.md#inspectable-installation-and-standards-integration), [design rationale](../design-rationale.md#why-inspectable-installation-is-the-target) and [operator guidance](../operator-guide.md#what-the-result-establishes). It concerns inspectable installation and eventual integration into a suitable larger standard. Attack elimination remains an objective, not a present guarantee.

The initial public wording and crosswalk shipped in `29fc38a` and `48848bf`. This local tranche completes the companion positioning, replaces generic ACS hooks with pinned method names, checks AgBOM component alternatives and distinguishes the upstream repository version from its wire/schema version. No runtime adapter, external submission, endorsement or acceptance is established.

ACS sources are pinned at `27799c2c27414a483a4a043b957bfd2997d53231`. The [integration note](acs-integration.md) links the exact schema paths. The component schema SHA-256 is `b3d4ef0edf57f6488f7894dd1e52aa40df033b8ea333725a3a81b4992bad16e5`; skill-load schema SHA-256 is `a992c21016de8c446cb0086178afe2ce0dae7d683e13e867e2b13432e948407b`. The review establishes schema shape and interpretation, not validated adapter payloads or wire interoperability.

The LLM Top 10 2026 mapping remains blocked on source access. Its [official resource page](https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/) links a download that returned an HTML `No Access` page during direct retrieval; the web reader also could not retrieve the document. The [initiative page](https://genai.owasp.org/initiatives/top-10-for-llm-and-genai/) lists workstreams without a versioned item table. This does not justify assigning 2026 ids. The [roadmap](../roadmap.md#current-work-queue-reconciled-2026-10-03) owns the remaining source-access task.

## Parser finding

The [DNS characterization](dns-anchor-parsing-2026-10-03.md) and its deterministic 110-case result capture malformed input acceptance across all 11 supported declarations. Runtime implementation, supported profiles, fixtures, schemas and frozen reports are unchanged. A future version-selected correction is recommended but not decided or implemented.

## Handoff disposition

- September 7 DNS/security queue: resolved observations and repair provenance migrated here; the old mismatch is not pending work. Removed after evidence readback.
- September 22 integration queue, including September 24 progress: accepted component direction and integration analysis migrated into the linked documents. LLM source access and any future implementation or owner-selected outreach are explicit roadmap items. Removed after destination readback.
- September 1 signing/OpenSSF/citation queue: retained as unprocessed separate work. Current signing evidence narrows the prerequisite question; it does not complete Scorecard, badge, citation, DOI, attestation or future-tag verification work.

Prior outreach remains owner-reported history with incomplete records. No external contribution or formal acceptance is established by the inspected sources. The fuller account remains in LocalBrain's GuideCheck outreach context; it is not reduced to the two contacts in the older July note. No outreach occurred in this tranche.

## Local validation and closeout

The session crossed midnight; final closeout is October 4 America/Denver. The October 3 filenames retain the date of the assessment and source observations.

- `make test test-verify-ui` passed: legacy and strict complete-report replays, profile dispatch, bounded execution, corrected content, 138 eval cases, 74 reference-verifier cases, 84 contract fixtures, fetch/anchor/API checks, CLI/scanner checks and UI rendering/copy/download behavior.
- Two fresh diagnostic runs were byte-identical to the retained 110-case result.
- Local Markdown link targets resolved, and `git diff --check` passed.
- Released evaluators, profiles, schemas, fixtures, published self-guide/manifest bytes and frozen reports were unchanged. No public-contract rebuild or package release was needed for this documentation/standalone-diagnostic tranche.
- The two processed repo handoffs were removed after destination readback. Their source SHA-256 values were `eb5eaea5a66bab64e9ae43bbbea270aa8756d8501bb250bcd16b2dc9a7e7798f` (DNS/security) and `e0146627269bbb383ad4f6282efea7e2ecd9e612fe92ccdbd3d19a4f4a0b6c44` (integration).
- The signing/OpenSSF/citation handoff remains with an October 4 checkpoint. All tranche changes are local and uncommitted; the source-access-dependent LLM 2026 mapping remains explicitly open.
