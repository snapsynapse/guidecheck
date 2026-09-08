# Schemas

JSON Schema (Draft 2020-12) definitions for machine-readable artifacts referenced by `spec.md` and `verifier-conformance.md`.

The current release profile 2.0.0 has versioned schemas in `schemas/2.0.0/`.
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
