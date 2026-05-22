# Security Policy

GuideCheck is a security-relevant standards project. Reports about weaknesses in the Human-Verifiable Assistant Guide profile, the verifier conformance profile, the schemas, or a published guide are welcome.

## Reporting

Email security@paice.work.

Do not open a public issue for a security report. Public disclosure before a fix or a documented mitigation can put adopters at risk.

Include where practical:

- which document, section, schema, or guide is affected
- the profile version
- the threat: what an attacker can achieve
- a concrete reproduction or worked example
- any suggested mitigation

## Scope

In scope:

- a profile rule that can be satisfied while still permitting the attack it was meant to prevent
- a conformance level that can be claimed without the protection it implies
- a verifier requirement that is unsound or that a conformant verifier could pass while missing a real attack
- a schema that permits a dangerous or malformed artifact
- an example or fixture that is itself unsafe or misleading

Out of scope, by design, and documented in `spec.md` section 27 and `threat-register.md`:

- compromise of a publisher, web host, DNS provider, package registry, or signing key
- an assistant runtime that ignores the profile
- human review error or social engineering through conforming prose
- environment-dependent command behavior

A report that the profile does not defend an out-of-scope threat is not a vulnerability, but a report that an out-of-scope threat should be moved in scope is welcome as a design discussion.

## Response

Reports are acknowledged and triaged. A confirmed weakness in a normative document is addressed in a profile revision with a `CHANGELOG.md` entry. Where a fix changes conformance, the change follows the versioning rules in `CONTRIBUTING.md`.

## Disclaimer

This profile reduces a specific trust gap. It does not make instructions safe. Conformance is not safety. See `spec.md` section 1.
