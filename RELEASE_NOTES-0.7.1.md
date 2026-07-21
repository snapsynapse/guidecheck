# GuideCheck 0.7.1

GuideCheck 0.7.1 is a backward-compatible verifier hardening and documentation
release. It resolves two false blockers found during the Harnessie adoption
without changing the normative profile requirements or finding-id contract.

## Fixed

- compact verification instructions may wrap concept pairs across lines
  without producing a false `verification-instruction.missing` blocker
- CLI result prose such as `tool eval (expect ...)` no longer triggers the
  JavaScript detector; JavaScript `eval` call syntax remains blocking across
  spaces, newlines, and case variants
- repeated per-action command classification is cached, and the Level 5
  readiness scan is simpler without changing its output contract

## Documentation

- added GitHub Pages `.nojekyll`, response-header, Level 4 rotation, and
  volatile-fact maintenance guidance
- clarified that an immutable release URL may identify the release being
  authored but must resolve when the guide is published
- refreshed hosted-verifier copy to describe the current seven-fetch budget
  and supported Level 4 anchors
- corrected project context to reflect Sigstore signing shipped in 0.6.0

## Verification

- full `make test` suite passes, including 134 eval cases, 70 verifier fixtures,
  80 contract validations, parser regressions, hosted API and anchor tests,
  fetch replay, CLI checks, and 58 scanner tests
- GuideCheck's own guide and the Harnessie adopter guide pass the local
  reference verifier
- adversarial parser coverage confirms that actual JavaScript `eval` calls are
  still blocked and maximum-size inputs do not cause pathological regex runtime

## Residual risks and follow-up

- repository-file anchors served from the same control plane as a Pages
  deployment are not yet distinguished from independent anchors; adopters
  should retain a genuinely independent channel such as DNS TXT
- bounded-execution requirements defined in 0.7.0 are not yet emitted as local
  verifier findings; enforcement remains planned for a subsequent 0.7.x release
- signed `security.txt` is not fetched by the hosted verifier
- GuideCheck's independent DNS TXT anchor must be rotated after publishing so
  it carries the 0.7.1 guide digest
