# Contributing

The Human-Verifiable Assistant Guide profile is a security-relevant standard. Changes are reviewed with that in mind.

## What lives where

- `spec.md` and `verifier-conformance.md` are normative. Changes to either are profile changes.
- `design-rationale.md` and `threat-register.md` are explanatory. They must stay consistent with the normative documents.
- `schemas/` is normative for the field sets it describes.
- `examples/` and `fixtures/` must remain consistent with the current profile version.
- `archive/` is historical and is not edited.

## Profile versioning

Profile versions follow Semantic Versioning as defined in `spec.md` section 11.

- MAJOR: a change that removes a field, tightens a constraint, or invalidates previously conforming guides or verifiers
- MINOR: an additive optional field, a relaxed constraint, or a new compatible check or fixture
- PATCH: an editorial fix with no conformance effect

Every normative change updates `CHANGELOG.md` in the same commit.

## Proposing a change

1. Open an issue describing the problem, not just the proposed wording. Security standards fail most often from unstated assumptions.
2. State the threat model impact. If the change weakens a defense, say so and justify it.
3. For normative changes, identify every section, schema, example, and fixture affected. Spec and verifier-conformance must not drift apart.
4. If the change affects the conformance ladder, the verifier output schema, or the action block shape, expect a longer review.

## Review

Normative changes are reviewed by a maintainer with security ownership. A change that adds, removes, or reclassifies an attack mitigation is reviewed against `threat-register.md` and `spec.md` section 27.

## Fixtures

A change to verifier behavior is incomplete without fixture coverage. The fixture suite under `fixtures/` is the conformance target for verifier implementations. Add or update fixtures in the same change that alters a verifier requirement.

## Style

Documentation follows the repository markdown conventions: plain headings, no emphasis inside headings, triple-backtick code fences, no em dashes, bare `https` domains. Guide examples and fixtures must satisfy the byte profile they claim to demonstrate.

## Security issues

Do not open a public issue for a vulnerability in the profile, a verifier, or a published guide. See `SECURITY.md`.

## License

Contributions to specification text and documentation are accepted under CC-BY-4.0. Contributions to code and schemas are accepted under MIT. By contributing you agree your contribution is licensed under the applicable license.
