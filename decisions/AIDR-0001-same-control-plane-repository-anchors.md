---
id: AIDR-0001
title: Same-control-plane repository anchors
status: open
date: 2026-07-21
arbiter: Sam Rogers
tags: [guidecheck, level-4, provenance, anchors, control-plane]
---
# AIDR-0001: Same-control-plane repository anchors

## Context

GuideCheck Level 4 requires at least one independent cross-channel anchor matching the guide manifest. A public repository file is a recognized channel, but the current profile does not explicitly resolve the case where GitHub controls both the source repository and the GitHub Pages deployment serving the guide. The current session handoff identifies this as the next normative independence decision. Counting a same-control-plane repository file may let one compromised account or repository write path forge both the guide and its asserted independent anchor. Rejecting every repository-file anchor merely because the guide uses Pages may be too broad when ownership, deployment, or immutable-release controls differ.

## Question

Should a repository-file anchor hosted on the same administrative control plane as a GitHub Pages guide count as an independent Level 4 provenance anchor?

## Positions

### Position: codex-gpt-5

- agent: codex-gpt-5
- model: gpt-5
- provider: openai
- stance: recommend
- summary: Do not count a same-administration repository-file anchor as independent unless another distinct control-plane anchor also validates the hash.

Independence should follow compromise boundaries, not URL shape. When one GitHub repository or organization credential can modify both the Pages guide and the repository-file anchor, the anchor raises no meaningful forge cost and should remain visible evidence without satisfying Level 4 by itself. The verifier should emit a specific finding, exclude that anchor from the independent-channel count, and allow Level 4 when another qualifying channel such as DNS TXT, recognized package-registry metadata, a signed security.txt, or a transparency log agrees. The rule should be narrow: a repository-file anchor may still qualify when the guide host is controlled through a genuinely distinct administrative plane and the verifier has a testable basis for that distinction.

This position was written without reading any other participant's position.

### Position: codex-gpt-6

- agent: codex-gpt-6
- model: gpt-6
- provider: openai
- stance: alternative
- summary: Exclude repository-file evidence from Level 4 qualification when separate administration is unestablished; the first implementation must treat all supported repository fetches as corroboration because no positive independence evidence protocol exists.

Prepared 2026-09-05 after reading Position codex-gpt-5. This is a dependent
analysis, not an independent review. This proposal is non-normative and awaits
Sam Rogers's arbitration. The existing position and Arbitration section are
preserved.

#### Rule proposed for arbitration

A repository hash match establishes byte agreement. It does not establish
separate credentials or a separate compromise boundary. Known shared
administration MUST NOT qualify, and unknown administration MUST NOT qualify.
Another qualifying matching channel may satisfy Level 4; it never changes the
excluded repository's own qualification.

For the first implementation, repository-file evidence is corroboration only.
The current hosted fetch contract has no authenticated evidence of administrative
separation. Therefore even an actually separate deployment remains unestablished
to this verifier. This affects all repository-only Level 4 results, not just
GitHub Pages. Do not hide that migration cost behind a Pages-specific warning.

A future positive exception requires a separately specified, reviewed, testable
evidence protocol. Do not introduce an operator checkbox, publisher assertion,
hostname heuristic, or test-only `independent=true` input as that protocol.
This proposal does not implement that exception or claim it already exists.

#### Threat model and observable evidence

The relevant attack is one authority changing both the served guide and the
candidate anchor, including changing the source that an automatic deployment
consumes. Different vendor names or runtime hosting accounts do not establish
independence if one repository write triggers both publications. Conversely,
sharing a vendor does not by itself establish shared customer credentials.
The claim is bounded resistance to joint forgery, never publisher trust or safety.

| Evidence | What it establishes | What it does not establish |
|---|---|---|
| Fetched repository bytes and manifest hash | Agreement at the observed fetch | Separate administration |
| Repository commit identifier | Identity of that repository object | Who selected it or whether one actor can publish a new guide naming a different object |
| Different domain, vendor, owner label, or custom domain | A routing or naming distinction | Disjoint write, deployment, recovery, SSO, or automation authority |
| A repository CNAME file, workflow YAML, or server header | A publisher-controlled deployment claim or hint | Current enforced permissions or exhaustive deployment topology |
| Authenticated hosting configuration identifying the same source and publication authority | Evidence of a shared path under the stated configuration | Absence of every other shared authority |
| Independently authenticated, complete authority evidence | Potential basis for a future separation rule | A capability of the current public hosted fetcher |

GitHub documents branch and Actions publication, including custom domains. A
custom domain cannot serve as a test for independence. Actions publication does
not require a repository CNAME file, so its absence cannot establish separation.
These are deployment facts; the conclusion about independence is this position's
threat-model inference.

No extra authenticated-account access or topology crawling is proposed. The
first hosted implementation reports repository independence as `unestablished`
for every repository fetch, including obvious Pages cases. That is deliberately
less specific than asserting shared administration from URL shape. Known-shared
scenarios still have a deterministic outcome: no repository qualification.

The other recognized channels retain their current rules in this bounded
proposal. DNS, registry, and log results are not newly certified as having
disjoint credentials. The existing limitations of those adapters remain; this
decision cannot justify a broader claim that all administrative separation has
been verified. Signed security.txt remains unavailable to the hosted fetcher.

#### Actual evaluation path and required implementation boundaries

At baseline `3ceb30a58488f925844c51c5aad0bc0f94633ff7`:

1. `derive_repository_file_url` allows GitHub repository URLs and derives a raw
   file URL. Its allowlist controls fetch support, not independence.
2. `_hosted_level4_evidence` inserts fetched repository text in `anchor_texts`
   without administration evidence. `_fetch_text_evidence` returns text, so the
   downstream anchor object does not retain the fetch URL and redirect details.
3. `check_anchors` produces `present-matches` from hash equality and uses that
   same status to suppress `anchor.independent.missing`.
4. `evaluate_guide` separately counts any `present-matches` as enough for Level 4.
   Its computed `level4_blockers` set is not itself an eligibility condition.
5. The hosted caller appends fetch findings after level calculation. Adding a
   warning or even a blocking finding there cannot reliably lower the level.
6. Local mode caps otherwise consistent fetched-style evidence at Level 3.
   Human reports currently derive `Hash pinned` from achieved level alone.

The fix must preserve observed evidence while using one shared qualification
predicate in both the missing-anchor check and the final level calculation.
All Level 4 blockers must prevent Level 4; they must not reduce an otherwise
valid Level 3 result. Eligibility must be resolved before building either report.
No later reconstruction from hash status may restore an excluded anchor.

Proposed predicate: a qualifying match is a supported, fetched, usable matching
anchor that satisfies its channel's qualification rule. Repository-file never
satisfies that rule in this first implementation. Local supplied files never
satisfy the fetched condition. The same core predicate serves both callers;
`evidence_fetched=True` alone cannot promote a repository match.

#### Findings and human/machine contract

Retain `status` as the hash/availability result. Add required output fields to
each emitted anchor: `qualifies_for_level4` (boolean) and `qualification_reason`
(a closed enum: `qualifying-channel`, `repository-independence-unestablished`,
`local-evidence-not-fetched`, `hash-mismatch`, `unreachable`, `absent`). Reason
precedence is availability, mismatch, local mode, then channel policy. Add
`independence: unestablished` to repository evidence, separately from the reason.
Other channels do not gain an `independence: established` assertion.

Preserve available source URL, fetch time, and redirect evidence through the
hosted evidence adapter; never fabricate a commit SHA from a branch or tag.
Unsupported repository hosts retain their existing info finding and are not
fetched. Missing and unreachable sources must be distinguishable in evidence
or findings. Unsupported caller-supplied channel names must never qualify.

Proposed new finding: `anchor.repository-file.independence-unestablished`,
warning, for a usable repository hash whose independence cannot qualify.
Keep its hash and observed status visible. Emit `anchor.independent.missing`
as an error for a Level 4 claim with no qualifying matching anchor, unless an
existing mismatch error already explains the failure.

Preserve conservative conflict blocking: a found repository hash mismatch still
blocks Level 4 even though a repository match cannot supply positive provenance.
Use a new `anchor.repository-file.mismatch` error so the message does not call
excluded evidence independent. Other channel mismatches retain
`anchor.independent.mismatch`. A matching DNS anchor does not erase a conflicting
repository hash. This avoids silently weakening the existing divergence check.

Human output must show, for example, "Repository hash: matches; independent
provenance: unestablished; counts toward Level 4: no" and a qualifying-anchor
count derived from the same booleans. A repository-only Level 4 claim reports
Level 3, `Hash pinned: no`, and `Proceed? no` due to the missing-anchor error.
Repository plus qualifying DNS reports Level 4 with the repository warning
visible. `Proceed?` remains the verifier's finding result, not human execution
approval. Local mode reports hash consistency, a Level 3 cap, and no fetched
provenance. Neither report implies safety or publisher trust.

#### Proposed fixture outcomes

These are acceptance criteria for arbitration, not implemented or passing tests.
Unless specified, every case has valid Level 3 content and a valid manifest and
claims Level 4. "Other qualifying channel" assumes its existing channel contract
is satisfied; merely naming a DNS or registry URL is insufficient.

| Scenario | Repository qualification | Expected result |
|---|---|---|
| Known shared administration; only matching repository | False; unestablished to the public fetcher | Level 3; repository warning and missing-anchor error |
| Known shared administration; matching repository plus qualifying matching DNS | False | Level 4; one qualifying channel; repository warning remains |
| Genuinely separate administration, supported by external audit evidence but no supported verifier evidence protocol | False | Level 3; unestablished, not a claim that the audit is false |
| Separate domain/vendor or a different GitHub owner only | False | Level 3; naming is insufficient |
| Custom-domain Pages, with or without CNAME file | False | Same result as repository-only Pages; no hostname bypass |
| Tagged or commit-pinned matching repository only | False | Level 3; immutability does not prove independence |
| Canonical/final URL or redirect changes with identical repository bytes | False | No promotion from routing changes; retain fetch evidence |
| Repository mismatch plus qualifying matching DNS | False | Level 3; repository mismatch error, no Level 4 |
| Repository match plus mismatching recognized channel | False | Level 3; independent mismatch error |
| Unsupported repository host only | No fetched anchor | Level 3; existing unsupported-host info and missing-anchor error |
| Missing/unreachable repository only | False or no usable anchor | Level 3; missing-anchor error and available fetch diagnostics |
| Missing/unreachable repository plus qualifying matching DNS | False or no usable anchor | Level 4; availability finding does not block |
| Matching local repository and DNS files | False for all local evidence | At most Level 3; consistency visible, missing fetched qualification explicit |
| Hosted caller passes matching repository and `evidence_fetched=True` | False | Level 3; core evaluator cannot bypass channel policy |
| Unknown channel injected into shared evaluator | False | Cannot satisfy missing-anchor check or Level 4 calculation |
| Lower-level guide without a Level 4 claim and repository corroboration | False | No missing-Level-4 error solely from the repository policy |
| Human report, JSON, and hosted UI for each case | Identical qualification | Level, findings, anchor count, and limitations agree |

A positive repository-independence fixture is intentionally unavailable in the
first slice. A genuine separate-control-plane case tests the honest unknown
outcome. Fabricating a positive fixture without an implementable evidence
protocol would not resolve the handoff's evidence requirement.

#### Alternatives and compatibility

| Alternative | Benefit | Consequence |
|---|---|---|
| Keep current channel recognition | No adopter migration | Matching self-publication continues to claim independent provenance |
| Exclude only obvious same-repository Pages URLs; count unknown cases | Narrow change | Custom domains and opaque deployment chains can bypass the rule; false Level 4 claims remain |
| Recommended first slice: repository corroboration only | Deterministic rule; no invented evidence; closes unknown-state bypass | Genuine independent repository-only deployments also lose Level 4 until another qualifying channel is available |
| Build an administration-evidence protocol now | Could admit genuine separation | Requires credential, delegation, freshness, revocation, and trusted-evidence design beyond the bounded slice |

The general independence language already requires different credentials, but
the public-repository subsection explicitly grants anchor status and current
hosted tests award Level 4 for same-repository Pages. The proposed change
invalidates existing accepted results and adds required output semantics.
Under CONTRIBUTING.md and INTENT.md this is a MAJOR profile change, with 1.0.0
the next major number from 0.7.1. Do not ship it as a 0.7.x patch or silently
change 0.7.1 conformance semantics. A legacy result must remain identified by
its old verifier/profile version; it is not upgraded by relabeling.

Adopter impact is known qualitatively, not counted across the portfolio. Existing
repository-only hosted regression cases must change in the new-profile suite.
Before release, inventory affected first-party claims read-only and provide
migration guidance: retain repository corroboration and supply another channel
that meets its existing qualification contract. Local Level 3 remains available.
Any external anchor mutation or cross-repository remediation is separate work.

The coherent implementation touches spec section 11 and Level 4 language,
verifier-conformance sections 6/23/25 and report rules, finding-ids, output schema,
both evidence/evaluation callers, hosted UI and examples, static fixtures,
hosted regressions, adoption/operator guidance, threat register, CHANGELOG,
and version-synchronized surfaces. No normative or verifier changes are made
by recording this proposal. After arbitration, full `make test`, new boundary
regressions, schema/report parity checks, and `git diff --check` are required.

## Objections

### Objection: codex-gpt-6 to Position codex-gpt-5

The phrase "unless another distinct control-plane anchor also validates" could
be implemented by restoring qualification to the repository when DNS matches.
The other channel should satisfy the requirement on its own; repository evidence
must remain excluded. Also, "a testable basis" for genuine separation is not yet
an input contract or a supported public evidence source. Counting unknown cases
until that basis exists would retain the bypass for custom domains and opaque
deployment chains. My alternative makes the resulting broader migration cost
explicit rather than claiming a narrow Pages detector solves it.

## Arbitration

## Evidence

- Sam Rogers approved the revised proposal on 2026-09-05 with the verbatim instruction: "Proposal approved. Please continue". This approves local implementation subject to the previously recorded compatibility condition. [Implementation validation](../docs/anchor-dispatch-validation.md) and [adopter receipts](../docs/anchor-dispatch-adopters.json) record the resulting evidence; they do not claim release or deployment. The original positions, objections, and human-owned Arbitration section remain preserved.
- [Revised version-aware dispatch proposal](../docs/anchor-policy-compatibility.md#dispatch-design), requested by Sam on 2026-09-05, specifies legacy/strict routing, caller profile assertions, manifest consistency, isolated engine identities, separate output contracts, unchanged self-guide artifacts, and paired compatibility gates. This current proposal limits strict enforcement to the new profile and replaces the original dependent position's unconditional migration consequence. Original positions and objections remain preserved. It is ready for local implementation under Sam's compatibility condition; release readiness is not yet established.
- [Compatibility contract and Sam's verbatim conditional approval](../docs/anchor-policy-compatibility.md), recorded 2026-09-05, constrain the proposal: existing Level 4 adopters must retain legacy behavior; the stricter policy requires explicit new-profile selection. A version bump alone does not satisfy that condition. The proposal's forced-migration consequence is not approved for legacy guides. No agent-authored arbitration is inserted here.
- [Shared anchor evaluation](../scripts/guidecheck_verify.py) contains `check_anchors`, `evaluate_guide`, `AnchorEvidence`, and the local report; inspected at baseline 3ceb30a.
- [Hosted evidence and report](../api/verify.py) fetches repository text and appends hosted findings after core level calculation.
- [Repository URL derivation](../scripts/guidecheck_hosted_anchors.py) is fetch support with no administration resolver; [fetch safety](../scripts/guidecheck_fetch.py) enforces transport limits, not administrative independence.
- [Hosted regression cases](../scripts/test_hosted_api.py) include `test_evaluated_level4_repository_file_github`, which expects Level 4 from same-repository Pages with no DNS record, and tag/commit URL variants.
- [Output schema](../schemas/verifier-output.schema.json) currently distinguishes anchor hash/availability status but has no qualification or independence fields.
- [Profile section 11](../spec.md#11-guide-metadata) defines different-credential independence but also explicitly recognizes public repository files.
- [Contribution versioning](../CONTRIBUTING.md#profile-versioning) and [INTENT admission criteria](../INTENT.md#admission-criteria-for-changes) require a major version for tightened constraints or invalidated conformance.
- [GitHub Pages publishing sources](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site) and [custom domains](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site), consulted 2026-09-05, support the deployment facts; they do not prove an individual publisher's administration is separate.
- [Current work queue](../roadmap.md#current-work-queue-reconciled-2026-09-05) identifies same-control-plane repository anchors as the next normative independence decision.
- [Verifier conformance section 23](../verifier-conformance.md#23-cross-channel-anchor-checks) defines recognized independent channels and the Level 4 anchor requirement.
- [Threat register](../threat-register.md#provenance-anchor-risks) explains that Level 4 is intended to raise the cost of forging the guide and provenance evidence together.
