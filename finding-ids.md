# Finding ID Registry

Status: draft for GuideCheck 0.2.0.

This registry defines stable finding ids used by the current verifier
conformance fixtures and local evals. Verifiers MAY emit additional finding
ids, but fixture assertions only require ids listed in fixture `expected.json`
files.

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
| `byte-profile.no-nul` | error | A guide contains one or more NUL bytes. |
| `byte-profile.no-ansi-escape` | error | A guide contains one or more ANSI escape bytes. |
| `byte-profile.size-limit` | error | A guide exceeds 8192 bytes. |
| `byte-profile.line-length` | error | A guide contains a line longer than 120 bytes. |
| `byte-profile.line-count` | error | A guide contains more than 400 lines. |

## Disallowed constructs

| ID | Severity | Trigger |
|---|---|---|
| `construct.html` | error | A guide contains HTML-like markup. |
| `construct.markdown-image` | error | A guide contains a Markdown image construct. |
| `construct.data-url` | error | A guide contains a data URL. |
| `construct.javascript` | error | A guide contains a JavaScript construct. |

## Verification instruction

| ID | Severity | Trigger |
|---|---|---|
| `verification-instruction.missing` | error | The compact verification instruction is missing or incomplete. |
| `verification-instruction.single-authority` | error | The guide implies one verifier is authoritative. |

## Metadata

| ID | Severity | Trigger |
|---|---|---|
| `metadata.block-count` | error | The guide has zero or multiple metadata blocks where one is required. |
| `metadata.malformed` | error | A metadata block has malformed lines, fences, keys, or duplicate keys. |
| `metadata.missing-required` | error | A required metadata field is absent. |
| `metadata.url.invalid` | error | A URL metadata field is not an ASCII HTTPS URL. |
| `metadata.status.invalid` | error | The `status` field has an unsupported value. |
| `metadata.status.revoked` | error | The guide status is `revoked`. |
| `metadata.superseded-by.missing` | warning | A deprecated or revoked guide lacks `superseded-by`. |
| `metadata.registry-url.not-record` | error | `registry-url` does not identify a specific registry record. |
| `metadata.recommended-verifier.off-domain` | warning | `recommended-verifier` is not on the canonical URL's registered domain and is not the standard primary verifier. |
| `metadata.last-reviewed.invalid` | warning | The `last-reviewed` date is malformed. |
| `metadata.last-reviewed.age` | info | The verifier reports the age of `last-reviewed`. |
| `metadata.last-reviewed.future` | warning | The `last-reviewed` date appears to be in the future. |
| `metadata.valid-until.invalid` | warning | The `valid-until` date is malformed. |
| `metadata.valid-until.expired` | warning | The `valid-until` date is in the past. |
| `metadata.value.long` | warning | A non-URL metadata value is unusually long. |

## Required content

| ID | Severity | Trigger |
|---|---|---|
| `content.required.title` | error | A Level 3 guide lacks a title. |
| `content.required.canonical-url` | error | A Level 3 guide lacks a canonical source URL. |
| `content.required.repository-url` | error | A Level 3 guide lacks a publisher or repository URL. |
| `content.required.metadata` | error | A Level 3 guide lacks guide metadata. |
| `content.required.task-scope` | error | A Level 3 guide lacks task scope. |
| `content.required.invocation` | error | A Level 3 guide lacks an assistant invocation prompt. |
| `content.required.safety-rules` | error | A Level 3 guide lacks safety rules. |
| `content.required.action-classification` | error | A Level 3 guide lacks action classification. |
| `content.required.actions` | error | A Level 3 guide lacks action blocks or action classes. |
| `content.required.stop-and-ask` | error | A Level 3 guide lacks stop-and-ask conditions. |
| `content.required.acceptance` | error | A Level 3 guide lacks an acceptance checklist. |
| `content.required.threat-model` | error | A Level 3 guide lacks a threat model. |
| `content.required.untrusted-content` | error | A Level 3 guide lacks untrusted content handling. |
| `content.required.disclaimer` | error | A Level 3 guide lacks disclaimer and non-goals. |
| `content.required.authority` | error | A Level 3 guide lacks an authority statement. |

## Action blocks

| ID | Severity | Trigger |
|---|---|---|
| `action-block.malformed` | error | An action block has malformed lines or fences. |
| `action-block.missing-required` | error | An action block lacks `id`, `class`, `approval`, or `command`. |
| `action-block.duplicate-id` | error | Two action blocks use the same `id`. |
| `action-block.approval.invalid` | error | `approval` is not `required` or `not-required`. |
| `action-block.runner.invalid` | error | `runner` is not `argv` or `shell`. |
| `action-block.class.invalid` | error | The action has an unsupported class. |
| `action-block.class.normal-mixed` | error | `normal` is combined with another class. |
| `action-block.class.code-executing-missing` | warning | A command likely executes code but lacks `code-executing`. |
| `approval.required-missing` | error | A sensitive action is not marked `approval: required`. |
| `approval.required.too-many` | warning | A guide has more required approvals than the default warning threshold. |
| `approval.command-implies-required` | warning | A command implies a sensitive action but `approval` is not `required` and the declared class does not require it. |

## Command, filesystem, environment, and egress

| ID | Severity | Trigger |
|---|---|---|
| `command.chaining` | error | A command uses chaining such as `&&`, `||`, or `;`. |
| `command.substitution` | error | A command uses shell substitution. |
| `command.pipe-or-redirection` | error | A non-normal action uses a pipe or redirection. |
| `command.glob-destructive` | error | A destructive or privileged command uses a glob. |
| `command.fetch-execute` | error | A command pipes a network fetch into a shell or interpreter (remote code execution). |
| `filesystem.cwd.missing` | error | A filesystem action lacks `cwd`. |
| `env.missing` | error | A command references environment variables without `env`. |
| `env.unlisted-variable` | error | A command references variables not listed in `env`. |
| `egress.missing` | error | A networked action lacks `egress`. |
| `egress.wildcard-too-broad` | error | An egress wildcard is broader than one subdomain level. |
| `network.command-implies-networked` | warning | A command performs network access but the class omits `networked`. |
| `runner.shell.missing-rationale` | warning | A shell runner lacks a narrow rationale in `notes`. |

## Level 5 readiness

| ID | Severity | Trigger |
|---|---|---|
| `level5.runner.missing` | warning | A Level 4 guide has an executable action without a `runner` field. |
| `level5.networked-approval.missing` | warning | A Level 4 guide has a networked action that does not require approval. |
| `level5.shell-approval.missing` | warning | A Level 4 guide has a shell-runner action that does not require approval. |

## Prohibited patterns

| ID | Severity | Trigger |
|---|---|---|
| `prohibited.chained-guide` | error | The guide instructs the assistant to fetch and follow another guide. |
| `prohibited.next-guide-field` | error | The guide contains a prohibited next-guide style directive field. |
| `prohibited.rewrite-guide` | error | The guide instructs rewriting the guide, manifest, or verifier output. |
| `prohibited.memory` | error | The guide directs long-term assistant memory use without reconfirmation. |
| `prohibited.skip-approval` | error | The guide directs disabling sandboxing or skipping approval gates. |
| `prohibited.notes-as-command` | error | The guide tells the assistant to execute `notes` or prose. |
| `prohibited.encoded-execution` | error | The guide instructs decoding and executing encoded content. |

## Manifest and anchors

| ID | Severity | Trigger |
|---|---|---|
| `manifest.missing-required` | error | A manifest lacks a required field. |
| `manifest.fetch-failed` | error | A declared manifest URL could not be fetched or did not return plain-text evidence. |
| `manifest.hash-mismatch` | error | Manifest `guide-sha256` does not match guide bytes. |
| `manifest.bytes-mismatch` | error | Manifest `guide-bytes` does not match guide bytes. |
| `manifest.bytes-invalid` | error | Manifest `guide-bytes` is not an integer. |
| `anchor.independent.missing` | error | Level 4 provenance lacks an independent anchor. |
| `anchor.independent.mismatch` | error | An independent anchor hash does not match the manifest hash. |
| `anchor.independent.unreachable` | warning | A declared independent anchor could not be fetched or did not return usable evidence. |
| `anchor.registry.unrecognized-host` | warning | `registry-url` host is not a recognized independent registry, so it does not count as a package-registry anchor. |
| `anchor.registry.url-mismatch` | warning | Package-registry assistant-guide metadata names a URL that does not match `canonical-url`. |
| `level4.requires-fetch` | info | Level 4 evidence is internally consistent but was not fetched; local-file mode caps the achieved level at 3. |

## Public fetch safety

| ID | Severity | Trigger |
|---|---|---|
| `fetch.scheme.http` | error | Public-web verification input uses HTTP. |
| `fetch.tls.invalid` | error | TLS validation fails. |
| `fetch.redirect.cross-domain` | error | A redirect crosses registered domains. |
| `fetch.content-variation` | warning | Re-fetching with a harmless alternate request profile returned different guide bytes. |
| `fetch.content-variation.unchecked` | warning | The content-variation re-fetch could not be completed. |
| `fetch.ssrf.localhost` | error | A hosted verifier target is localhost. |
| `fetch.ssrf.private-ip` | error | A hosted verifier target resolves to private or local IP space. |
| `fetch.ssrf.metadata-ip` | error | A hosted verifier target is a cloud metadata address. |
| `fetch.ssrf.local-domain` | error | A hosted verifier target is a local-only domain. |
| `header.content-type.missing` | warning | The served guide response has no `Content-Type`. |
| `header.content-type.incompatible` | warning | The served guide response is not `text/plain; charset=utf-8`. |
| `header.x-content-type-options.missing` | warning | The served guide response lacks `X-Content-Type-Options: nosniff`. |
| `header.hsts.missing` | warning | The served guide response lacks `Strict-Transport-Security`. |

## Change control

Finding ids are part of the verifier fixture contract. Renaming or removing a
fixture-required id is a breaking verifier-profile change unless the fixture
suite version also changes and the old id is explicitly deprecated.
