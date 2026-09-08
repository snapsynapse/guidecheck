# GuideCheck 2.0.0 release notes

Release version: 2.0.0

GuideCheck 2.0.0 adds the opt-in `corrected-content-1` policy for guides that
explicitly declare profile 2.0.0. It retains the `1.0.0-strict` anchor policy:
repository-file evidence remains corroborating and cannot qualify a guide for
Level 4. An unresolved execution target blocks Level 3 under this policy.

The release preserves the isolated 0.7.1 legacy engine, the prior 1.0.0
profile, the 0.7.1 self-guide, and all frozen reports. Existing guides are not
migrated or reinterpreted automatically.

The experimental POSIX JSON CLI contract, selected with
`--contract posix-json-v1`, is independent of the guide-declared profile
selector. See `docs/cli-contract.md`.

The normative corrected-content policy is
`docs/corrected-content-policy-2026-09-07.md`.
