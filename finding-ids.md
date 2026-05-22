# Finding ID Registry

Status: draft for GuideCheck 0.1.0.

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

## Command, filesystem, environment, and egress

| ID | Severity | Trigger |
|---|---|---|
| `command.chaining` | error | A command uses chaining such as `&&`, `||`, or `;`. |
| `command.substitution` | error | A command uses shell substitution. |
| `command.pipe-or-redirection` | error | A non-normal action uses a pipe or redirection. |
| `command.glob-destructive` | error | A destructive or privileged command uses a glob. |
| `filesystem.cwd.missing` | error | A filesystem action lacks `cwd`. |
| `env.missing` | error | A command references environment variables without `env`. |
| `env.unlisted-variable` | error | A command references variables not listed in `env`. |
| `egress.missing` | error | A networked action lacks `egress`. |
| `egress.wildcard-too-broad` | error | An egress wildcard is broader than one subdomain level. |
| `runner.shell.missing-rationale` | warning | A shell runner lacks a narrow rationale in `notes`. |

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
| `manifest.hash-mismatch` | error | Manifest `guide-sha256` does not match guide bytes. |
| `manifest.bytes-mismatch` | error | Manifest `guide-bytes` does not match guide bytes. |
| `manifest.bytes-invalid` | error | Manifest `guide-bytes` is not an integer. |
| `anchor.independent.missing` | error | Level 4 provenance lacks an independent anchor. |

## Public fetch safety

| ID | Severity | Trigger |
|---|---|---|
| `fetch.scheme.http` | error | Public-web verification input uses HTTP. |
| `fetch.tls.invalid` | error | TLS validation fails. |
| `fetch.redirect.cross-domain` | error | A redirect crosses registered domains. |
| `fetch.ssrf.localhost` | error | A hosted verifier target is localhost. |
| `fetch.ssrf.private-ip` | error | A hosted verifier target resolves to private or local IP space. |
| `fetch.ssrf.metadata-ip` | error | A hosted verifier target is a cloud metadata address. |
| `fetch.ssrf.local-domain` | error | A hosted verifier target is a local-only domain. |

## Change control

Finding ids are part of the verifier fixture contract. Renaming or removing a
fixture-required id is a breaking verifier-profile change unless the fixture
suite version also changes and the old id is explicitly deprecated.
