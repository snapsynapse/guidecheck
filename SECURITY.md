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

## Release artifact signing

From 0.6.0 onward, every GitHub release of GuideCheck is signed with
[Sigstore](https://sigstore.dev) cosign keyless from the tag-triggered
workflow at `.github/workflows/release.yml`. The signed artifacts are the
release tarball, the release zip, the conformance kit tarball, and the
combined `SHA256SUMS` file. Each ships with a `.sig` and `.crt` bundle
attached to the same GitHub release.

The verification identity for every signature is:

```
certificate-identity:    https://github.com/snapsynapse/guidecheck/.github/workflows/release.yml@refs/tags/v<version>
certificate-oidc-issuer: https://token.actions.githubusercontent.com
```

To verify a downloaded artifact, install
[cosign](https://docs.sigstore.dev/cosign/installation/) and run:

```
cosign verify-blob \
  --certificate guidecheck-0.6.0.tar.gz.crt \
  --signature   guidecheck-0.6.0.tar.gz.sig \
  --certificate-identity 'https://github.com/snapsynapse/guidecheck/.github/workflows/release.yml@refs/tags/v0.6.0' \
  --certificate-oidc-issuer 'https://token.actions.githubusercontent.com' \
  guidecheck-0.6.0.tar.gz
```

A successful verification confirms three properties: the artifact bytes have not changed since signing; the signature was issued by the release workflow at the named repository under the named tag; the signing event is recorded in the public Rekor transparency log and can be inspected at https://search.sigstore.dev.

Earlier releases (0.5.0 and prior) are unsigned. The `SHA256SUMS` file published with each release remains the integrity reference for those tags.

Reports of misuse of the signing identity (a release that does not come from the workflow above) are in scope and welcome.

## Disclaimer

This profile reduces a specific trust gap. It does not make instructions safe. Conformance is not safety. See `spec.md` section 1.
