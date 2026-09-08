# INTENT

Status: Authoritative for the GuideCheck standard.
Scope: Standards-level strategy for this component. Portfolio-level strategy lives in the PAICE Foundation INTENT. Where this document and a higher-scope document disagree, the higher scope wins for portfolio questions and this document wins for standard-level questions.

## What this standard is

GuideCheck defines the Human-Verifiable Assistant Guide profile for `assistant-guide.txt`: a constrained plain-text artifact for assistant-facing install, implementation, remediation, migration, and operational instructions. It is a trust boundary protocol for agent instruction surfaces. It exists to close one specific trust gap. A human may believe they are approving the operational guidance they can see, while an assistant ingests additional instructions hidden or transformed by a presentation layer.

The standard makes the instruction surface visible, bounded, and practical to review before an assistant acts on it. It preserves review integrity by helping ensure the instructions humans approve are the same instructions agents execute. It does not make instructions safe.

## Why it exists

AI-assisted setup guidance is increasingly consumed by tool-using assistants with real blast radius. The surfaces that carry that guidance, including HTML, rendered Markdown, PDFs, and copied terminal output, can hide content from the human while feeding it to the model. No existing convention solves this. `llms.txt` points assistants at documentation but defines no safety profile. `robots.txt` and `security.txt` are single-purpose and carry no assistant-executable instructions. The gap is real and the consequences are operational, not cosmetic: delegated authority can be diverted into credential exposure, destructive commands, malicious dependency installation, disabled safeguards, or unreviewed tool and agent delegation.

## Design invariants

These are the non-negotiable commitments of the standard. Changing any of them is a major-version decision and requires explicit reconsideration of the threat model.

1. Conformance is not safety. The standard verifies form, structure, and selected provenance signals. It never asserts that a guide is safe, that a publisher is benevolent, or that an assistant may skip human review. Every level, every document, every tool surface restates this.
2. Human-verifiable means actually reviewable. The 8 KiB size cap, the ASCII byte profile, and the one-artifact bounded-task scope exist so that a human can read the entire instruction surface in one sitting. Any change that lets a guide exceed what a human will actually read breaks the standard's purpose.
3. ASCII-only at Level 2 and above. Non-ASCII content is interpreted by an assistant that may not respect field boundaries. The defense against homoglyph, bidi, and invisibility attacks is to allow no such bytes anywhere in the file. This position is final, not provisional.
4. No chained guides. A guide never instructs an assistant to fetch and follow another guide. Silent transitive trust is the attack. Integrity fetches that verify the identity of the current artifact are permitted; instruction fetches that import new directives are not.
5. No central registry, no oracle. The standard is evaluable from the artifact plus its cross-channel anchors. It does not depend on a central list, and it does not let any verifier or hosted checker become a root of trust.
6. The human stays in the control loop. The standard constrains what a guide can ask and what a conformant runtime will enforce. It never removes the human's reading, judgment, and approval.

## Scope boundaries

In scope: the artifact format, the byte profile, the action model, the conformance ladder, the provenance model, the verifier conformance profile, and the runtime contract at Level 5.

Out of scope, and documented as such in spec section 27 and the threat register: publisher and supply-chain compromise, assistant runtimes that ignore the standard, human review error, social engineering through conforming prose, and environment-dependent command behavior. The standard is one layer in a defense stack. It is not the stack.

The standard does not replace sandboxing, least privilege, code signing, package manager trust policy, vulnerability scanning, or human approval. It is designed to be combined with them.

## Conformance philosophy

The conformance ladder is additive and honest. Each level states exactly what it has checked and what it has not. Level 4 adds verifiable provenance but not a safety claim. Level 5 is explicitly a guide-plus-runtime claim, not a guide-only claim, because runtime behavior cannot be asserted by a file.

A conformant verifier is a testable implementation claim. The fixture suite is the conformance target. GuideCheck publishes a primary verifier at https://guidecheck.org/verify for usability but never presents it as the only authoritative verifier. Anyone may build a conformant verifier; the fixture suite is how independent implementations stay in agreement.

## Level 5 ownership

Decided 2026-06-09: GuideCheck owns the Level 5 runtime conformance profile, including the runtime fixture suite and the scenario-driven evaluator. They are deliverables of this standard, not design notes handed to runtime vendors. The work is gated by `docs/pre-level-5-readiness.md`: the Level 5 documents stay design drafts and no runtime conformance claim is made until the runtime fixture suite and evaluator profile exist and pass the same contract discipline as the guide-file suite. `docs/level-5-implementation-plan.md` is the sequencing plan for that work. Owning the evaluator does not create an oracle; like the guide-file verifier, the runtime evaluator is a reference implementation against a published fixture suite that anyone may reimplement.

## Admission criteria for changes

A proposed change is admitted only if it satisfies all of the following.

1. It does not weaken a design invariant without an explicit, documented threat-model justification reviewed by a maintainer with security ownership.
2. It keeps `spec.md` and `verifier-conformance.md` in agreement. The two documents are versioned together and must not drift.
3. It updates the affected schemas, examples, and fixtures in the same change.
4. It records a `CHANGELOG.md` entry and, for normative changes, follows the SemVer rules in `CONTRIBUTING.md`.
5. It does not introduce a central registry, an oracle, a single point of trust, or a dependency on one hosted service.
6. It does not expand the artifact past what a human will review in one sitting.

A change that adds an optional field or a compatible verifier check is a minor version. A change that removes a field, tightens a constraint, or invalidates previously conforming guides or verifiers is a major version.

## Recalibration gates

The following decisions are settled for v0.2 but are explicitly open to revision when a stated condition is met. Until the condition is met, the decision stands and is not relitigated.

- 8 KiB size cap. Revisit only if field data from real adopters shows the cap is forcing decomposition in cases where bundling is the safer pattern. Relaxing a cap is easy; tightening one after adoption is hard, so the default is to hold.
- ASCII-only byte profile. Revisit only if Unicode security tooling and assistant-runtime field-boundary enforcement both mature significantly. The bar is high and deliberate.
- Signature and transparency-log as RECOMMENDED, not REQUIRED, at Level 4. Revisit when code-signing infrastructure is common enough across adopters that a higher provenance tier requiring it would not exclude the long tail.
- No controlled Unicode mode. Tied to the ASCII-only gate above.
- No central registry. Revisit only as a federated, advisory, non-endorsing index, and only if adoption demand is demonstrated. Never as a centralized authority.

## Open questions

Tracked in `roadmap.md` under Future profile directions. The live items are a possible higher provenance tier requiring signature and transparency-log evidence, Level 5 runtime attestation, and a canonical approval receipt. None of these block v0.2. The 2026-05-21 review resolved the prior open-question lists; see `roadmap.md` under Resolved in the 0.1.0 review.

The canonical approval receipt (opened 2026-07-31, detail in `roadmap.md`) is the one with a live design fork rather than a deferred yes/no. Level 5 already mandates the binding and the log, but the session approval ledger is a required field set with no canonical serialization, so an approval cannot be recomputed, signed, or carried across a trust boundary. Level 4 gives guide provenance; the receipt would give execution provenance. The fork to resolve first is whether requesting identity is a field inside the record or the signer over it, because the encoding depends on the answer, and the two choices are different trust models: a field is publisher-asserted metadata a verifier cannot check, a signature makes identity the thing that authenticates the record. Sequenced after Level 5 fixture-suite design under the `docs/pre-level-5-readiness.md` gate, so the format ships with conformance tests rather than as a bare schema.

## Relationship to the PAICE portfolio

GuideCheck is a PAICE Foundation standard. It sits alongside the other open-spec components in the portfolio and follows the same posture: vendor-neutral, portable, security and interoperability as baseline. The verifier at https://guidecheck.org/verify is the standard's own conformance checker, not a commercial gate. Portfolio-level decisions about positioning and sequencing are owned by the PAICE Foundation INTENT, not this document.

## Versioning and authority

The current profile is declared in `profiles/1.0.0/spec.md` and tracked in `CHANGELOG.md`. The current version is 1.0.0, released. Root normative documents preserve the legacy contract; the self-guide remains pinned to 0.7.1. The version is asserted by `scripts/check_version_sync.py` against `scripts/guidecheck_constants.py` against independently pinned release, engine, and self-guide identities, so the status here and the released tag cannot silently disagree. `spec.md` and `verifier-conformance.md` are normative. `design-rationale.md` and `threat-register.md` are explanatory and must stay consistent with the normative documents. `archive/` is historical and is not edited.

## Corrected content checks

Decided by Sam on 2026-09-07: preserve frozen legacy reports and add an explicitly selected corrected evaluation path. The September 7 detector review reproduced negation false positives, affirmative-instruction false negatives, and unpinned script-dispatch gaps. These are maintenance of existing content-check obligations, not authority to silently alter a published evaluation contract.

Existing supported profile behavior, findings, levels, report identity, and exit semantics remain frozen. The corrected path must have an explicit selection and distinguishable policy identity; its precise selector, version, normative changes, and migration design remain to be proposed under the admission criteria above. This decision does not automatically revise the released strict 1.0.0 policy, which reuses legacy content checks. Implementation, release, and hosted acceptance are not completed by this decision.

Sam also decided on 2026-09-07 that an unresolved execution target blocks Level 3 acceptance on the corrected path. The guide must establish the effective target and satisfy the applicable pinning contract. A declared hash alone cannot resolve an unidentified target. This requirement does not change any released legacy or 1.0.0 evaluation.

## Maintenance and demand gate

The June 9 disposition parked new product investment while maintaining existing
adoption commitments. Its revisit triggers were ten external AI Posture
declarations or Obligation First bindings, a validity-badge decision, or a paying
counterparty requesting conformance checking. This does not change GuideCheck's
standard scope or authorize a cross-standard certification product. The September
5 session implements existing bounded-execution obligations as maintenance.

## Changelog

- 2026-09-07: Sam selected blocking unresolved execution targets for Level 3 on the opt-in corrected path; released evaluations remain frozen.
- 2026-09-07: Sam selected preservation of frozen legacy reports with opt-in corrected content checks. Recorded the decision and remaining selector/version design scope; evaluator and published profiles remain unchanged.
- 2026-09-05: Sam approved the version-aware anchor proposal with legacy compatibility required. The local 1.0.0 candidate excludes repository-file evidence from independent qualification, while the dispatcher preserves supported legacy evaluations and published self-guide bytes. Release and deployment remain separate. See `docs/anchor-policy-compatibility.md` and `docs/anchor-dispatch-validation.md`.

- 2026-07-31: Opened the canonical approval receipt as a live open question, prompted by an external question about binding approval to the exact executing action. Detail in `roadmap.md`; the identity fork (field in the record versus signer over it) is the first thing to resolve, gated behind Level 5 fixture-suite design.
- 2026-07-21: Released profile 0.7.1 with verifier false-positive fixes for wrapped verification instructions and CLI `eval` result prose, expanded parser regressions, refreshed hosted-verifier copy, and adoption guidance derived from the Harnessie field report.
- 2026-06-09: Recorded the Level 5 ownership decision (GuideCheck owns the runtime fixture suite and evaluator, gated by pre-level-5 readiness). Updated version status to 0.6.0 released and noted the version-sync check. Backfilled missing entries: the version line had been bumped through 0.2.0 to 0.6.0 without changelog entries.
- 2026-05-21: Initial INTENT for the GuideCheck standard, drafted alongside the v0.1.0 bootstrap.
