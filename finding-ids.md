# Finding ID Registry

Status: draft for GuideCheck 0.1.0.

This registry defines stable finding ids used by the current verifier conformance fixtures. Verifiers MAY emit additional finding ids, but fixture assertions only require ids listed in fixture `expected.json` files.

## Conventions

- Finding ids use lowercase ASCII.
- Components are separated by dots.
- Use the narrowest stable rule name available.
- Do not encode severity in the id. Severity is reported separately.

## Byte profile

| ID | Severity | Trigger |
|---|---|---|
| `byte-profile.no-tabs` | error | A guide contains one or more tab bytes. |
| `byte-profile.no-carriage-returns` | error | A guide contains one or more carriage return bytes. |
| `byte-profile.non-ascii-byte` | error | A guide contains a byte outside LF and printable ASCII. |

## Change control

Finding ids are part of the verifier fixture contract. Renaming or removing a fixture-required id is a breaking verifier-profile change unless the fixture suite version also changes and the old id is explicitly deprecated.
