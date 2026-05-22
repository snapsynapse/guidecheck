# INTENT

Status: Authoritative for the GuideCheck standard.
Scope: Standards-level strategy for this component. Portfolio-level strategy lives in the PAICE Foundation INTENT. Where this document and a higher-scope document disagree, the higher scope wins for portfolio questions and this document wins for standard-level questions.

## What this standard is

GuideCheck defines the Human-Verifiable Assistant Guide profile for `assistant-guide.txt`: a constrained plain-text artifact for assistant-facing install, implementation, remediation, migration, and operational instructions. It exists to close one specific trust gap. A human may believe they are approving the operational guidance they can see, while an assistant ingests additional instructions hidden or transformed by a presentation layer.

The standard makes the instruction surface visible, bounded, and practical to review before an assistant acts on it. It does not make instructions safe.

## Why it exists

AI-assisted setup guidance is increasingly consumed by tool-using assistants with real blast radius. The surfaces that carry that guidance, including HTML, rendered Markdown, PDFs, and copied terminal output, can hide content from the human while feeding it to the model. No existing convention solves this. `llms.txt` points assistants at documentation but defines no safety profile. `robots.txt` and `security.txt` are single-purpose and carry no assistant-executable instructions. The gap is real and the consequences are operational, not cosmetic.

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

The following decisions are settled for v0.1 but are explicitly open to revision when a stated condition is met. Until the condition is met, the decision stands and is not relitigated.

- 8 KiB size cap. Revisit only if field data from real adopters shows the cap is forcing decomposition in cases where bundling is the safer pattern. Relaxing a cap is easy; tightening one after adoption is hard, so the default is to hold.
- ASCII-only byte profile. Revisit only if Unicode security tooling and assistant-runtime field-boundary enforcement both mature significantly. The bar is high and deliberate.
- Signature and transparency-log as RECOMMENDED, not REQUIRED, at Level 4. Revisit when code-signing infrastructure is common enough across adopters that a higher provenance tier requiring it would not exclude the long tail.
- No controlled Unicode mode. Tied to the ASCII-only gate above.
- No central registry. Revisit only as a federated, advisory, non-endorsing index, and only if adoption demand is demonstrated. Never as a centralized authority.

## Open questions

Tracked in `spec.md` section 29 and `verifier-conformance.md` section 32. The live items are a possible higher provenance tier requiring signature and transparency-log evidence, a canonical finding-id registry, fixture-suite signing, and Level 5 runtime attestation. None of these block v0.1.

## Relationship to the PAICE portfolio

GuideCheck is a PAICE Foundation standard. It sits alongside the other open-spec components in the portfolio and follows the same posture: vendor-neutral, portable, security and interoperability as baseline. The verifier at https://guidecheck.org/verify is the standard's own conformance checker, not a commercial gate. Portfolio-level decisions about positioning and sequencing are owned by the PAICE Foundation INTENT, not this document.

## Versioning and authority

The profile version is declared in `spec.md` and tracked in `CHANGELOG.md`. The current version is 0.1.0, draft for review. `spec.md` and `verifier-conformance.md` are normative. `design-rationale.md` and `threat-register.md` are explanatory and must stay consistent with the normative documents. `archive/` is historical and is not edited.

## Changelog

- 2026-05-21: Initial INTENT for the GuideCheck standard, drafted alongside the v0.1.0 bootstrap.
