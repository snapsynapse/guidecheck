# Schemas

JSON Schema (Draft 2020-12) definitions for machine-readable artifacts referenced by `spec.md` and `verifier-conformance.md`.

The current release profile 2.0.0 has versioned schemas in `schemas/2.0.0/`.
`schemas/3.0.0/` holds draft schemas for the unreleased profile 3.0.0. No
verifier emits or consumes them yet. That directory adds
`shape-registry.schema.json`, which validates the registry of exact invocation
shapes defined in the 3.0.0 guide profile, section 12.

The 3.0.0 schemas differ from the earlier sets in two ways. They are closed:
every object rejects unknown fields and every string is bounded, so the
statement below about additional implementation-specific fields does not apply
to them. And they use no `format` keyword and end every pattern with
`$(?!\n)`, so they mean the same under a validator that searches and under
one that uses ECMAScript semantics. Relations between fields, which no schema can state, are listed in
the 3.0.0 verifier profile, section 27, and implemented for tests in
`scripts/profile_3_0_0_invariants.py`.
`schemas/1.0.0/` remains available for the prior released profile schema
set and root schemas preserve the legacy contract.

`cli-result-posix-json-v1.json` is the standalone experimental POSIX JSON CLI
contract schema. It is selected independently of a guide-declared profile and
is not a profile schema.

- `manifest.schema.json` validates the Level 4 sidecar manifest defined in spec section 11.
- `verifier-output.schema.json` validates the verifier output defined in spec section 26 and verifier-conformance section 27.
- `fixture-expected.schema.json` validates normalized fixture expectations used by the conformance suite.

Schemas are normative for the field set they describe and the constraints they encode. They are non-normative for ordering, additional implementation-specific fields (allowed via `additionalProperties: true`), and exact error wording.

The `$id` URLs resolve under the project canonical domain `https://guidecheck.org/schemas/`.
