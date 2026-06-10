# GuideCheck Human-Verifiable Assistant Guide Profile

## How to read this document

This is the normative specification. It defines exactly what a conforming `assistant-guide.txt` artifact must be. It is a precise reference, not an introduction.

- Deciding whether to adopt GuideCheck, or publishing your first guide: start with `ADOPTION.md`. It explains the conformance ladder, gives a level-by-level path, and carries the guide-author checklist. Return here for the exact requirements.
- Writing a guide: sections 6 through 17 define the artifact, its structure, and its constraints.
- Building a verifier: sections 21 and 26 here, then the normative `verifier-conformance.md`.
- Assessing risk and coverage: sections 14 and 27 here, then `threat-register.md`. Operator practice during a real install is in `operator-guide.md`.
- Understanding why the design is shaped this way: `design-rationale.md`.

## Contents

1. [Purpose](#1-purpose)
2. [Terminology](#2-terminology)
3. [Problem Statement](#3-problem-statement)
4. [Design Goals](#4-design-goals)
5. [Non-Goals](#5-non-goals)
6. [Core Artifact](#6-core-artifact)
7. [Authority Model](#7-authority-model)
8. [Byte-Level Profile](#8-byte-level-profile)
9. [Disallowed Constructs](#9-disallowed-constructs)
10. [Required Sections](#10-required-sections)
11. [Guide Metadata](#11-guide-metadata)
12. [Action Classification](#12-action-classification)
13. [Stop-and-Ask Conditions](#13-stop-and-ask-conditions)
14. [Threat Model](#14-threat-model)
15. [Untrusted Content Handling](#15-untrusted-content-handling)
16. [Public Information Safety](#16-public-information-safety)
17. [Risky Pattern Guidance](#17-risky-pattern-guidance)
18. [Conformance Levels](#18-conformance-levels)
19. [Discovery](#19-discovery)
20. [HTTP Serving Requirements](#20-http-serving-requirements)
21. [Verifier Requirements](#21-verifier-requirements)
22. [Acceptance Checklist](#22-acceptance-checklist)
23. [Lifecycle and Change Management](#23-lifecycle-and-change-management)
24. [Relationship to Existing Work](#24-relationship-to-existing-work)
25. [Locale](#25-locale)
26. [Verifier Output Schema](#26-verifier-output-schema)
27. [Residual Threats](#27-residual-threats)
28. [Operator Responsibilities and Defense in Depth](#28-operator-responsibilities-and-defense-in-depth)

## 1. Purpose

GuideCheck is the standards project for the Human-Verifiable Assistant Guide profile. This specification defines the profile for `assistant-guide.txt`, a constrained plain-text artifact for assistant-facing install, implementation, remediation, migration, and operational instructions.

GuideCheck is the standard, verifier ecosystem, and public site. `assistant-guide.txt` is the artifact. A conforming artifact claims conformance through profile metadata and verifier evidence, not through a branded filename.

The profile exists to reduce a specific trust gap: a human may believe they are approving visible operational guidance while an assistant ingests additional instructions hidden or transformed by a presentation layer.

The profile does not make instructions inherently safe. It makes the instruction surface visible, bounded, and practical to review before an assistant acts on it.

### Important: conformance is not safety

Conformance to this profile, at any level including Level 5, does NOT mean a guide is safe to follow, that the publisher is trustworthy, or that the assistant may proceed without the security practices a competent operator would already apply. A verifier that returns Level 4 has confirmed structure, byte profile, approval-gate presence, and manifest integrity. A Level 5 deployment has added runtime enforcement. Neither has confirmed publisher intent, publisher identity, command effect, or environment fit.

If you are tempted to skip reading the guide because it passed verification, stop. The verifier checks form. You check meaning.

The following practices remain mandatory regardless of conformance level:

- read the full guide yourself before authorizing the assistant
- run the assistant with least-privilege tool permissions and sandboxing
- verify publisher identity out-of-band when the action is high-consequence
- prefer signed releases and reproducible builds for the underlying software
- back up state before any destructive or persistence-changing action
- exercise the guide in a non-production environment first
- keep operating-system and network egress controls in place; do not let an assistant suppress permission prompts
- treat any "safe" or "trusted" claim inside a guide as the publisher's marketing, not as evidence

The companion `operator-guide.md`, pointed to from section 28, expands these into a defense-in-depth checklist. Section 27 enumerates residual threats this profile does not address. Adopters are expected to read both.

## 2. Terminology

`assistant-guide.txt`
: The artifact name for a conforming guide.

Human-Verifiable Assistant Guide profile
: The standard profile defined by this document.

Guide
: A plain-text `assistant-guide.txt` file intended to be reviewed by a human and then used by an assistant for a bounded task.

Assistant
: Any AI system, coding agent, automation agent, or tool-using model that may read the guide and propose or execute actions.

Assistant runtime
: The execution environment that parses the guide, requests approvals, invokes tools, runs commands, applies sandboxing, and records action results.

Verifier
: A scanner or review tool that checks whether a guide satisfies this profile and emits structured evidence.

Publisher
: The project, repository, package, service, or organization publishing the guide.

## 3. Problem Statement

AI-assisted setup and operational guides reach assistants through HTML, rendered Markdown, PDFs, docs sites, copied issue comments, terminal output, and screenshots. Those surfaces can carry content a model ingests but a human never sees: hidden comments, offscreen or invisible text, control characters, terminal escape sequences, and buried instruction blocks. The human reviews the rendered output; the model ingests the raw source; nothing guarantees they are the same document.

For high-consequence tasks, projects need a constrained instruction surface that a human can review in full before authorizing an assistant to follow it. `ADOPTION.md` and `design-rationale.md` expand on the problem and the reasoning; this profile defines the artifact that closes the gap.

## 4. Design Goals

A conforming guide is intended to be:

- visible to humans
- easy for assistants to parse
- constrained enough to remove presentation-layer deception
- explicit about scope, authority, source, actions, approval gates, and stop conditions
- verifiable by scanners
- portable across assistants, repositories, package ecosystems, and hosting environments

## 5. Non-Goals

This profile does not:

- replace sandboxing, least privilege, or human approval
- provide access control
- prove that commands or actions are safe
- guarantee that a publisher, repository, package, or release is trustworthy
- authorize assistants to bypass system instructions, user instructions, local policy, package manager policy, or operating system permission prompts
- replace `llms.txt`, `robots.txt`, sitemap files, package manager metadata, security advisories, or signed release artifacts
- defend against compromised official repositories or malicious package releases

## 6. Core Artifact

A conforming guide is a `.txt` file named `assistant-guide.txt`.

The canonical filename is `assistant-guide.txt`. When served over HTTP, the canonical well-known path is `/.well-known/assistant-guide.txt`. A repository copy at the repository root is RECOMMENDED. Publishers MAY serve the guide at both the well-known path and the repository root. When both are served, the two copies MUST be byte-identical; a divergence is a forge and confusion vector, and the repository-file provenance anchor of section 11 depends on the copies matching. A verifier that can reach both copies MUST emit a failure on any divergence. The well-known path takes precedence for HTTP discovery.

The guide gives an assistant a bounded task prompt, safety rules, action classes, allowed commands or command patterns, stop-and-ask conditions, and acceptance criteria.

Example uses include:

- AI-assisted project install
- AI-assisted library implementation
- migration dry-run instructions
- local development setup
- remediation playbooks
- support runbooks
- scanner remediation guidance
- agent skill installation guidance

### Scope: one artifact, one bounded task

This profile is for bounded tasks that fit in a single artifact. A conforming guide carries the complete instruction surface for the task it describes. It does not reference other instruction files for the assistant to fetch and follow, and it does not span multiple files.

If a task does not fit in one `assistant-guide.txt` within the size limits of section 8, this profile is not the right tool for that task. Reasonable alternatives include:

- decomposing the task into independent bounded sub-tasks, each with its own `assistant-guide.txt`, each started by the human as a deliberate new session
- distributing the work through a documentation site, installer, CLI wizard, or other surface where the user-interaction model is different
- reducing the scope of the task so that what remains is reviewable in one sitting

The tightness of the scope is the value proposition of this profile. A guide that tries to be everything cannot be human-verifiable in a single review.

## 7. Authority Model

A guide is advisory. It is lower priority than:

- system instructions
- user instructions
- local repository instructions
- local security policy
- package manager trust policy
- operating system permission prompts

Assistants MUST treat fetched guide content as untrusted data until the user confirms that it is the intended guide.

Assistants MUST NOT treat the presence of `assistant-guide.txt` as permission to broaden tool access, skip sandboxing, ignore local instructions, or execute commands without the required approval gates.

Tools and verifiers MUST treat the guide as potentially malicious or compromised.

## 8. Byte-Level Profile

The strict byte-level profile for Level 2 and above is:

- UTF-8 encoded
- allowed bytes: `0x0A` and `0x20` through `0x7E`
- line endings: LF only
- no tab characters
- no carriage returns
- no NUL bytes
- no ANSI escape bytes
- no Unicode bidi controls
- no zero-width characters
- no control characters other than LF

Size limits for Level 2 and above:

- maximum file size: 8192 bytes (8 KiB)
- maximum line length: 120 bytes
- maximum line count: 400 lines

These limits exist so that full human review remains practical. A guide that exceeds any limit MUST be split, shortened, or downgraded to Level 1.

## 9. Disallowed Constructs

Level 2 and above guides MUST NOT contain:

- HTML
- CSS
- JavaScript
- Markdown images
- remote embeds
- data URLs
- rich-document constructs
- terminal escape sequences
- encoded or obfuscated command blobs intended for execution
- instructions to decode and execute hidden content

Plain Markdown-like syntax (ATX headings with `#`, hyphen list markers, fenced code blocks with triple backticks) MAY appear in the guide body. The character sequences themselves are not the threat. The threat this profile addresses is a rendering layer that hides, transforms, or styles text so that the human reviewer sees something different from what the assistant ingests.

Because conforming guides are served and stored as `.txt`, browsers, editors, and verifiers display the raw bytes rather than a rendered document. A verifier MUST treat the file as plain text and MUST NOT attempt to render Markdown. Hyperlinks, images, HTML, and any construct that depends on a renderer to reveal its meaning remain disallowed by the list above regardless of whether their source characters would be valid Markdown.

## 10. Required Sections

This section enumerates content a conforming guide must carry. Section names MAY vary across guides, but the information MUST be present and easy to identify.

### 10.1 Required content at Level 3 and above

A Level 3 or higher guide MUST include:

- title
- canonical source URL
- publisher or repository URL
- guide metadata block (section 11)
- task scope
- assistant invocation prompt (section 10.3)
- safety rules
- action classification (section 12)
- normal commands or action classes
- stop-and-ask conditions (section 13)
- acceptance checklist (section 22)
- threat model (section 14), restated by the publisher for this guide's scope
- untrusted content handling (section 15), restated by the publisher
- a disclaimer and non-goals statement, restated by the publisher; a reference to this profile is not sufficient
- an authority statement, restated by the publisher, asserting that the guide is advisory and lower priority than system, user, local repository, and local policy instructions

"Restated by the publisher" means the guide carries its own prose. A guide that says only "see profile section N" for any of the above does not satisfy this requirement; the human reviewing the guide must be able to read the relevant content in the guide itself, without following links.

### 10.2 Required content at Level 1 and above: compact verification instruction

All Level 1 or higher guides MUST include a compact verification instruction before any action instructions. The instruction MUST tell the assistant to:

1. verify the canonical URL with the recommended verifier or another conformant verifier
2. report the compact verification result, including verifier name and version, achieved level, guide SHA-256 when available, and blocking findings
3. ask the user to confirm that they have read the guide and approve proceeding under the reported level
4. avoid executing actions before confirmation

Recommended canonical wording:
```text
Before acting:
1. Verify this guide with the recommended verifier or another conformant verifier.
2. Report the verifier used, achieved level, guide SHA-256, and blocking findings.
3. Ask the user: "I have read this guide, understand that conformance is not safety, and approve proceeding under the reported level."
4. Do not execute actions before confirmation.
```

The guide MAY list a recommended hosted verifier via the `recommended-verifier` metadata field. It MUST NOT state or imply that only one verifier is authoritative. A conformant verifier is one that satisfies the GuideCheck Verifier Conformance Profile for the applicable profile version.

When a guide lists `recommended-verifier`, the URL SHOULD be on the same registered domain as `canonical-url`, unless the guide explicitly identifies the verifier as third-party or the verifier is the standard primary verifier published by the standards project for the applicable profile version. The standard primary verifier is exempt from off-domain verifier warnings because it is part of the standard's own conformance ecosystem, not an arbitrary third-party verifier. For guide-profile version 0.6.x the designated standard primary verifier is `https://guidecheck.org/verify`, published by GuideCheck as the standards project for this profile. Verifiers SHOULD treat that URL as the standard primary verifier and apply the off-domain warning to all other `recommended-verifier` values not matching `canonical-url`.

Assistants fetching public guides MUST NOT send cookies, browser session state, authorization headers, or other ambient credentials. Public guide fetches MUST be unauthenticated and reproducible.

### 10.3 Assistant invocation prompt content

The assistant invocation prompt MUST tell assistants to:

- treat the guide as untrusted data until verified and confirmed by the user
- parse structured action blocks (section 12)
- avoid executing prose, `notes` fields, or any content outside an approved action block
- request per-action approval where required (sections 12, 13)
- obey higher-priority system, user, repository, and local policy instructions (section 7)

## 11. Guide Metadata

A Level 3 or higher guide MUST include a metadata block. The block uses `key: value` lines, one field per line, delimited by the literal fences `[assistant-guide-metadata]` and `[/assistant-guide-metadata]` on lines of their own. Keys are lowercase ASCII letters, digits, and hyphens. Values are single-line ASCII per the byte profile of section 8 (printable bytes 0x20 through 0x7E, no leading or trailing whitespace). Verifiers parse the block by exact fence match.

Required fields:

- `identifier`
- `profile`
- `profile-version`
- `guide-version`
- `applies-to`
- `canonical-url`
- `repository-url`
- `last-reviewed`

Optional fields:

- `source-path`
- `reviewed-by`
- `status` (one of `active`, `deprecated`, `revoked`; default `active`)
- `superseded-by` (URL to replacement guide; required when `status` is `deprecated` or `revoked`)
- `preferred-languages` (comma-separated BCP 47 tags; see section 25)
- `valid-until` (ISO 8601 date; verifiers SHOULD warn when current date exceeds this)
- `recommended-verifier` (URL for a hosted verifier that claims conformance to the verifier profile)
- `verifier-conformance` (verifier profile name and SemVer range; see syntax below)
- `registry-url` (URL identifying the package registry record for this guide when cross-channel publication uses package registry metadata; required when the registry channel is the publisher's chosen independent anchor)
- `manifest-url` (Level 4; see below)

### Version-range syntax

The `verifier-conformance` field uses a SemVer range expressed in npm-compatible operator form: `<name> <op><version>[, <op><version>]`. Allowed operators are `=`, `>=`, `>`, `<=`, `<`, `~`, and `^`. Multiple constraints are comma-separated and combined with logical AND. Example: `human-verifiable-assistant-guide-verifier >=0.6.0, <0.7.0`. Whitespace between operator and version is optional. Verifiers that do not implement the full operator set MUST report unsupported operators as warnings and fall back to exact-version matching.

Example:
```text
[assistant-guide-metadata]
identifier: assistant-guide
profile: human-verifiable-assistant-guide
profile-version: 0.6.0
guide-version: 1.0.0
applies-to: example-project >=2.3.0, <3.0.0
canonical-url: https://example.com/.well-known/assistant-guide.txt
repository-url: https://example.com/org/example-project
source-path: /.well-known/assistant-guide.txt
last-reviewed: 2026-05-22
reviewed-by: security@example.com
status: active
recommended-verifier: https://example.com/check
verifier-conformance: human-verifiable-assistant-guide-verifier >=0.6.0
[/assistant-guide-metadata]
```

All URL values MUST resolve to ASCII hostnames. Internationalized domain names MUST be expressed in punycode (A-label) form. Verifiers MUST reject metadata containing non-ASCII bytes in URL fields; this is already implied by the byte profile but is restated here because URL fields are operationally load-bearing.

URL paths are case-sensitive and SHOULD use the canonical lowercase form.

`canonical-url` is the URL at which the guide itself is served. `repository-url` is the root of the publisher's source repository, where the guide's source and revision history live (for example `https://github.com/example/example-project`). It is a single field; it is not a project landing page, a documentation site, or a marketing page. The repository-file provenance anchor in the cross-channel section below resolves `source-path` against `repository-url`; a `repository-url` that does not point at a source repository disables that anchor.

### Profile and guide versioning

Both `profile-version` and `guide-version` are semantic versions. Profile-version MAJOR is incremented when a change removes a field, tightens a constraint, or invalidates previously conforming guides. MINOR is incremented for additive optional fields or relaxed constraints. PATCH is for editorial fixes. Guide-version is owned by the publisher and follows their release semantics.

### Provenance (Level 4)

The guide file itself does not contain its own hash. Provenance for Level 4 follows a sidecar manifest model analogous to skill-provenance: integrity metadata lives outside the file so the file's bytes can be hashed without an in-file chicken-and-egg field.

A Level 4 guide MUST publish a manifest at a stable URL referenced by `manifest-url`. The manifest is a plain-text or YAML document containing at minimum:

```text
guide-path: /.well-known/assistant-guide.txt
guide-version: 1.0.0
guide-sha256: <hex-encoded sha256 of the assistant-guide.txt bytes>
guide-bytes: <integer byte count>
immutable-release-url: https://example.com/org/example-project/releases/v2.3.1
signature: optional-reference-to-signed-artifact
transparency-log-url: optional-url-to-a-public-append-only-log-entry
```

The hash identifies which version of the file a verifier has examined. The hash does not assert that the file is safe. A verifier that fetches both `assistant-guide.txt` and its manifest MUST recompute the SHA-256 over the fetched bytes and report any mismatch as a Level 4 conformance failure while still permitting Level 3 evaluation of the file contents on their own merits.

A future version of this specification may define a more structured manifest schema. The minimum fields above are stable.

When the publisher has any code-signing infrastructure available (release signing, container signing, package registry signing, PGP, Sigstore, or equivalent), the manifest SHOULD include a `signature` reference. A Level 4 manifest with a signature is a stronger provenance posture than one without; verifiers SHOULD report which form was found. A future revision of this specification may define a higher provenance tier that requires signature and transparency-log evidence; the current spec keeps both as RECOMMENDED so that Level 4 remains achievable for publishers who have not yet adopted code signing.

### Cross-channel publication of the hash

A manifest served from the same origin as the guide is forge-equivalent to the guide itself: an attacker who controls the web host controls both. To raise the forge cost, publishers SHOULD publish the same `guide-sha256` on at least one independent control plane. "Independent" means controlled by different credentials, typically a different vendor, from the web host.

Required posture:

- Level 3: at least one independent channel SHOULD carry the hash
- Level 4: at least one independent channel MUST carry the hash

Recognized independent channels are defined below. A publisher MAY use more than one. The verifier MUST cross-check every channel it can find and MUST emit a failure when channels disagree on the hash.

#### DNS TXT record

Location: `_assistant-guide.<registered-domain>`

Value format, single line:

```text
v=1; sha256=<64-hex>; url=<canonical-url>
```

When a publisher serves more than one guide from the same domain, the TXT value MAY name a manifest instead, and the manifest carries the per-guide hashes:

```text
v=1; manifest=<url>
```

Publishers SHOULD set TTL no greater than 3600 seconds so that hash rotations propagate within an hour. DNSSEC is RECOMMENDED.

#### Package registry metadata

When the project ships as a package, the registry record SHOULD carry the hash. Ecosystem conventions:

- npm `package.json`:
  ```text
  "assistantGuide": {
    "url": "https://example.com/.well-known/assistant-guide.txt",
    "sha256": "<64-hex>"
  }
  ```
- PyPI `pyproject.toml`:
  ```text
  [project.urls]
  Assistant-Guide = "https://example.com/.well-known/assistant-guide.txt"
  ```
  with `sha256` carried in a sidecar `assistant-guide-manifest.txt` referenced by that URL or by `manifest-url` in the guide metadata
- Cargo `Cargo.toml`:
  ```text
  [package.metadata.assistant-guide]
  url = "https://example.com/.well-known/assistant-guide.txt"
  sha256 = "<64-hex>"
  ```
- Other registries: use any project-URLs or arbitrary-metadata facility the registry exposes; the field name SHOULD be recognizably `assistant-guide` or `assistantGuide`.

Package registries are an independent control plane because publish credentials are typically distinct from web-host credentials and from DNS credentials.

Verifiers discover the registry record through the metadata field `registry-url`. The value MUST be a URL to a specific registry record (for example `https://registry.npmjs.org/example-pkg/2.3.1` or `https://pypi.org/pypi/example-pkg/2.3.1/json`), not a registry homepage or search result. When `registry-url` is absent and the publisher relies on the package-registry channel for cross-channel hash publication, the verifier cannot find the anchor and the channel does not count toward the Level 4 cross-channel requirement.
When registry metadata is JSON, verifiers MUST bind the hash to assistant-guide-specific metadata, such as an `assistantGuide` or `assistant-guide` object with a `sha256` field. A generic `sha256` field elsewhere in the registry record is not a GuideCheck anchor.

#### Public repository file

When the source repository is public, the file at `source-path` in the repository serves as an independent anchor. The verifier MUST compare the served bytes against the file at the commit named by `repository-url` and SHOULD record the commit sha in its output.

#### Signed security.txt

A publisher who maintains a PGP-signed `security.txt` per RFC 9116 MAY add the following extension fields:

```text
Assistant-Guide: https://example.com/.well-known/assistant-guide.txt
Assistant-Guide-SHA256: <64-hex>
```

An unsigned security.txt does NOT count as an independent channel because it lives on the same origin as the guide. A signed security.txt counts because the trust anchor is the signing key, not the file.

#### Public append-only transparency log

A publisher MAY anchor `guide-sha256` in a public append-only transparency log, for example a Sigstore Rekor entry, a certificate-transparency-style log, or a git-backed append-only log hosted under independent credentials. The log entry MUST record `guide-sha256` and `canonical-url`, and MUST be retrievable from a stable, publicly readable URL. Verifiers discover the entry through the optional manifest field `transparency-log-url`.

A transparency log counts as an independent control plane when it is operated under credentials distinct from the web host and its entries cannot be silently rewritten or deleted. Append-only semantics raise the forge cost beyond a plain mirror: an attacker cannot retroactively replace the anchored hash without leaving the original entry visible. A verifier that retrieves a log entry MUST compare its hash against the manifest hash and MUST emit a failure on divergence, the same as for any other independent channel.

#### Discovery aids that are NOT evidence

The following surfaces are permitted for human and tool discovery but MUST NOT be treated by verifiers as forge-resistant evidence of the hash, because they share the same origin as the guide:

- HTML head: `<link rel="assistant-guide" href="https://example.com/.well-known/assistant-guide.txt">`
- HTTP response header on the guide itself
- unsigned security.txt with the extension fields above

Verifiers MAY surface these for UX but MUST NOT count them when checking the "at least one independent channel" requirement.
## 12. Action Classification

A Level 3 or higher guide MUST classify actions into these categories at minimum:

- normal: non-privileged and non-destructive local actions
- networked: actions that make external network calls
- destructive: actions that delete, overwrite, reset, revoke, rotate, or irreversibly mutate state
- privileged: actions requiring elevated permissions such as root, admin, production, cloud, or cluster access
- persistence-changing: installs, service changes, startup changes, system path writes, configuration changes, or scheduled tasks
- data-accessing: reads from databases, logs, secrets managers, private repositories, customer data, or other sensitive stores
- code-executing: actions that execute project code, dependency code, package scripts, build hooks, generated code, test suites, or local scripts

The `normal` class is mutually exclusive with the other classes. Any action that is networked, destructive, privileged, persistence-changing, data-accessing, or code-executing is not normal.

Privileged, destructive, persistence-changing, data-accessing, and code-executing actions MUST require explicit human approval before execution at Level 3 and above. Running project, dependency, or build code executes arbitrary logic under the operator's authority, so it is gated at the same level as the other high-consequence classes.

Networked actions SHOULD require approval unless the user has already approved the source and purpose.

### Action block shape

So that verifiers can mechanically detect missing approval gates, a Level 3 or higher guide MUST express each substantive action using the following block shape:

```text
[action]
id: install-deps
class: persistence-changing, networked, code-executing
approval: required
command: npm ci
runner: argv
[/action]
```

Fields:

- `id`: short ASCII identifier unique within the guide
- `class`: one or more of the categories enumerated above, comma-separated
- `approval`: `required` or `not-required`
- `command`: the literal command, or a narrow command pattern
- `runner` (optional): `argv` or `shell`
- `notes` (optional): single-line rationale

Actions whose class list includes `privileged`, `destructive`, `persistence-changing`, `data-accessing`, or `code-executing` MUST set `approval: required`. A verifier MUST emit a failure when this constraint is violated. Prose discussion around action blocks remains permitted.

### Command field restrictions

The `command` field is parsed and displayed as a literal. To keep what the human approves identical to what the assistant runs:

- one command per action block; no chaining via `&&`, `||`, `;`, or newline
- no shell substitution: the characters `$(`, backticks, and `${` MUST NOT appear in the command
- no redirection (`>`, `<`, `>>`, `<<`) and no pipes (`|`) unless the action is only classed as `normal` and the redirection target is a path inside the declared `cwd`
- no glob expansion in `destructive` or `privileged` commands
- environment-variable references via `$NAME` are permitted only when the variable is listed in an `env:` field on the same action

For any action that reads or writes the filesystem, the block MUST include:

```text
cwd: <path relative to repository root, or absolute path the user has approved>
```

Verifiers MUST flag command fields that violate these restrictions.

Level 4 guides SHOULD include `runner: argv` or `runner: shell` on every action. Level 5 runtime enforcement defines the execution semantics of this field.

`runner: argv` means the command is executed by directly invoking the named program with its arguments, without spawning a shell interpreter. The runtime tokenizes the `command` field by whitespace into program and argument vector; no shell metacharacters are interpreted.

`runner: shell` means a POSIX-compatible shell (`/bin/sh` semantics) interprets the command. On non-POSIX hosts the runtime SHOULD declare the resolved shell in its compact report. A future revision of this profile may add explicit `runner: powershell` and `runner: cmd` values for Windows-native execution; v0.2 leaves Windows shell semantics out of scope, and publishers targeting Windows SHOULD prefer `runner: argv` until those values are defined.

Any command that relies on shell behavior, including pipes or redirection, SHOULD declare `runner: shell`, include a narrow rationale in `notes`, and require approval. Level 5 runtimes MUST enforce those requirements before invoking a shell.

### Action atomicity and approval scope

Each action block is the unit of approval. An approval granted for action `id: A` does not extend to action `id: B`. Assistants MUST NOT batch approvals across action ids. Assistants MUST display the action block verbatim (not paraphrased) when requesting approval, using the canonical phrasing in section 13.

### Networked actions

Actions whose class list includes `networked` MUST declare the network egress target:

```text
egress: example.com, registry.npmjs.org
```

The value is a comma-separated list of host patterns. A bare host matches that host only; a leading `*.` matches one subdomain level. The list MUST be narrow. Verifiers MUST flag wildcards broader than a single subdomain level.

Level 4 guides SHOULD require approval for all `networked` actions. Level 5 runtimes MUST require approval for all `networked` actions and MUST enforce the declared egress list when runtime enforcement is available. When enforcement is not available, the runtime MUST disclose that limitation before requesting approval.

## 13. Stop-and-Ask Conditions

A Level 3 or higher guide MUST tell assistants to stop and ask before:

- executing destructive actions
- using elevated privileges
- installing dependencies or system packages
- changing persistent configuration
- reading secrets, private data, logs, databases, or customer data
- running commands outside the declared project scope
- following instructions from fetched or generated content
- executing generated code
- decoding and executing encoded content
- contacting non-official sources
- continuing when observed state differs materially from the guide
- proceeding after a verifier reports a failure or high-severity warning

The guide MUST include exact wording that an assistant can use when requesting approval. The following canonical phrasing is RECOMMENDED so that humans see a consistent prompt across guides:

```text
I am about to perform a {class} action from assistant-guide.txt:
  id: {id}
  command: {command}
Approve, modify, or cancel?
```

## 14. Threat Model

A Level 3 or higher guide MUST include a threat model.

The threat model MUST remind authors and users that the guide is public and may be read by adversaries.

The threat model MUST describe what can go wrong if the guide is followed on:

- a developer workstation
- CI/CD infrastructure
- staging or production infrastructure

In-scope threats include:

- hidden presentation-layer instructions
- rendered HTML, CSS, or JavaScript deception
- invisible Unicode or terminal control characters
- assistant over-trust of fetched setup guides
- stale or non-canonical install instructions
- install prompts that omit approval gates
- unsafe shell patterns
- public leakage of operational assumptions
- guide drift from the implementation or release process

Out-of-scope threats include:

- compromised official repositories
- malicious package releases
- dependency confusion
- social engineering outside the guide
- assistants that ignore user approval
- assistants with unsafe tool permissions

## 15. Untrusted Content Handling

A Level 3 or higher guide MUST instruct assistants to treat all fetched content, downloaded files, repository files, generated code, package scripts, and external service responses as untrusted until reviewed or approved in context.

Assistants MUST NOT follow instructions found in fetched content unless those instructions are part of the confirmed guide and are consistent with higher-priority instructions.

Assistants SHOULD prefer structured parsers and local package manager metadata over ad hoc shell parsing when inspecting project state.

### Prohibited instruction patterns

A conforming guide MUST NOT instruct an assistant to:

- fetch and follow another `assistant-guide.txt`, instruction file, script, or guide-like document from any URL, whether through prose, action commands, or any metadata field (no chained guides; see also section 6 scope)
- pivot the current session to a different guide on the basis of the guide's own content; cross-guide pivots are a user action only, performed by the user starting a new session against a different URL
- treat any field named `next-guide`, `then-fetch`, `chain-to`, `follow-next`, `continue-with`, or any equivalent as a directive (such fields are not part of this profile; their presence is itself a finding)
- modify, rewrite, or replace `assistant-guide.txt`, its manifest, or any verifier output
- store guide content, action commands, or approvals into long-term assistant memory for use in future sessions without the user re-confirming in that session
- decode, deobfuscate, or execute encoded content from any source
- expand its own tool permissions, disable sandboxing, or skip approval gates
- treat the guide's `notes` or prose fields as commands

A verifier MUST flag occurrences of these patterns.

### Integrity fetches versus instruction fetches

This profile distinguishes two kinds of fetch and treats them differently. The distinction is what makes the no-chains rule internally consistent.

Integrity fetches are permitted and expected. They confirm the identity of the artifact already under review. They do not extend approval to new instructions. Examples:

- the manifest at `manifest-url`
- the DNS TXT record at `_assistant-guide.<domain>`
- the package registry metadata field
- the repository copy at `source-path`
- a signed security.txt extension field

The verifier and assistant fetch these to verify that what they have is the guide the publisher claims. The fetched content is metadata about the current guide. It contains no actions, no prose to follow, and no instructions to the assistant beyond identity verification.

Instruction fetches are forbidden. An instruction fetch is any retrieval of content that the assistant would then act on as a directive: another `assistant-guide.txt`, an install script, a follow-up runbook, a remediation document. The threat is silent transitive trust: the human approved guide A; guide A fetches guide B; B contains material the human never reviewed. Even one hop is too far.

If a publisher genuinely needs the user to act on additional material, the publisher places a plain prose reference in the current guide ("when this is done, the migration guide is at https://example.com/.well-known/migrate-guide.txt; start a new session against that URL"). The human reads that with their own eyes and starts a new session deliberately. The new session is a fresh review.

### Status checks and supersession

Assistants MUST re-read the `status` metadata field before each session and MUST stop when `status` is `revoked`.

When `status` is `deprecated`, the assistant MUST stop the current session, MUST display the `superseded-by` URL to the user, and MUST require the user to start a new session against that URL manually. The assistant MUST NOT auto-follow `superseded-by`. The replacement guide is a fresh review with a fresh approval ledger.

### Time-of-check / time-of-use

For Level 4 guides, assistants SHOULD pin the manifest `guide-sha256` at the start of a session and treat any mid-session mismatch as a stop condition. The guide that was reviewed is the guide that runs; a publisher rotation, mirror swap, or attacker-controlled re-host during a session MUST NOT silently change the instruction surface.

## 16. Public Information Safety

A guide MUST NOT include:

- secrets, tokens, passwords, API keys, or private credentials
- non-public internal hostnames, IP addresses, or endpoints
- private admin paths not otherwise public
- sensitive topology details
- remediation details that materially expand external knowledge of private infrastructure

Authors SHOULD write the guide under the assumption that adversaries can read it.

## 17. Risky Pattern Guidance

Guides MUST NOT contain:

- unqualified `sudo` invocations (a `sudo` command without an explicit narrow target binary and arguments)
- absolute safety claims such as "always safe", "guaranteed secure", or "no risk"

Guides SHOULD avoid:

- `curl | sh` and equivalent pipe-to-shell patterns
- qualified `sudo` use, except when unavoidable, narrowly scoped, and approval-gated
- broad deletion paths such as `/`, `/*`, `~`, or repository parents
- broad `chmod`, `chown`, or permission weakening
- environment-variable enumeration without a narrow purpose
- credential scraping or broad secrets access
- unscoped `kubectl`, `terraform`, cloud, database, or production operations
- generated-code execution without review
- encoded command blobs

When a risky pattern is unavoidable, the guide MUST explain why it is needed, narrow its scope, and require explicit approval.

## 18. Conformance Levels

### Level 0: Not conformant

Instructions are available only through HTML, PDF, rich Markdown rendering, screenshots, videos, terminal output, or another surface that may hide or transform text.

### Level 1: Plain text available

A `.txt` guide exists and is reachable from a canonical project surface.

Requirements:

- text is directly readable without script execution
- canonical project or repository URL is present
- task scope is stated
- compact verification instruction is present before action instructions

### Level 2: Human-verifiable byte profile

Level 1 plus:

- strict byte-level profile is satisfied
- guide is short enough for full human review
- no disallowed constructs
- when served over HTTP, `Content-Type` SHOULD be `text/plain; charset=utf-8`
- when hosting supports it, `X-Content-Type-Options: nosniff` SHOULD be present

### Level 3: Assistant safety contract

Level 2 plus:

- all required sections are present
- approval gates are explicit
- action classes are present
- stop-and-ask conditions are present
- official sources are listed
- untrusted content handling is stated
- public information safety is addressed
- acceptance checklist is included
- the guide avoids overclaiming safety
- the `guide-sha256` SHOULD be cross-published on at least one independent control plane as defined in section 11

### Level 4: Verifiable provenance

Level 3 plus verifiable provenance evidence.

Required at Level 4:

- sidecar manifest at `manifest-url` with `guide-sha256`, `guide-bytes`, and `immutable-release-url`
- the `guide-sha256` MUST be cross-published on at least one independent control plane as defined in section 11 (DNS TXT, package registry metadata, public repository file, signed security.txt, or public append-only transparency log)
- the verifier MUST report which channels were checked and MUST emit a failure on any cross-channel hash divergence

Recommended at Level 4:

- changelog entry covering guide changes
- signed release artifact reference

Level 4 guides SHOULD prepare for Level 5 runtime enforcement by:

- using `runner: argv` or `runner: shell` on every action
- marking every `networked` action as `approval: required`
- keeping action commands executable without a shell where practical
- declaring narrow `cwd`, `env`, and `egress` fields wherever applicable
- avoiding package lifecycle scripts, generated-code execution, and local-script execution unless the action is explicitly classified as `code-executing`

Verifier output MAY report `level5_ready` for guide-side preparation. The
canonical predicate for that boolean lives in the GuideCheck Verifier
Conformance Profile. It is not an achieved Level 5 claim.

### Level 5: Runtime-enforced execution

Level 5 is not a guide-only claim. It is a guide plus assistant-runtime claim.

Level 5 requires Level 4 plus a conformant assistant runtime that mechanically enforces the guide's execution contract. The runtime MUST:

- parse the guide as data before treating any part of it as actionable
- run a conformant verifier before proposing or executing actions
- display the compact verification report and receive user confirmation before proposing or executing actions
- compare the guide bytes it will use against the verifier-reported SHA-256 before proposing or executing actions
- stop if the agent-fetched guide bytes differ from the verifier-reported SHA-256
- make only structured `[action]` blocks executable
- treat prose, `notes`, metadata, fetched content, manifests, verifier output, and repository files as non-executable unless represented by an approved action block
- reject or stop on guide content that violates Level 4 conformance
- require every executable action block to declare `runner`
- reject executable action blocks that omit required fields or applicable `cwd`, `env`, and `egress` fields
- pin the guide bytes and manifest `guide-sha256` for the session
- preserve the verifier output in the session approval ledger
- maintain a session-local approval ledger keyed by guide URL, guide hash, verifier name, verifier version, achieved level, and action id
- display each action block verbatim before approval
- prohibit batched approvals across action ids
- require approval for all `networked`, `privileged`, `destructive`, `persistence-changing`, `data-accessing`, and `code-executing` actions
- execute commands without invoking a shell when `runner: argv` is declared
- require `approval: required` and an explicit `runner: shell` declaration before invoking a shell
- disclose the runner, cwd, relevant environment variable names, and network enforcement status before approval
- enforce declared `egress` lists when the runtime has network-control capability
- disclose when declared `egress` lists are advisory rather than enforced
- refuse chained-guide following, self-modification, tool-permission expansion, and encoded-content execution
- prevent guide content, action commands, approvals, and verifier output from being stored into long-term assistant memory unless the user explicitly reconfirms that storage in the current session
- log approved actions, rejected actions, executed commands, cwd, runner, exit status, and timestamps

If any of these runtime guarantees are absent, the deployment MUST NOT claim Level 5 even when the guide itself satisfies Level 4.

A future version of this specification may add a higher provenance tier with a transparency-log requirement or raise `signature` from RECOMMENDED to REQUIRED at that tier.

## 19. Discovery

Projects SHOULD make `assistant-guide.txt` discoverable from at least one canonical surface:

- `/.well-known/assistant-guide.txt` (canonical HTTP location)
- repository root
- README
- `llms.txt` (or the variant `llm.txt`; see note below)
- project documentation
- package metadata (see section 11 cross-channel publication)
- security or support documentation, including `security.txt` extension fields
- HTML `<link rel="assistant-guide">` on the project homepage
- DNS TXT record at `_assistant-guide.<domain>`
- DNS TXT or signed `security.txt` fields identifying the recommended verifier

Discovery mechanisms MUST NOT require script execution.

Some of the surfaces above are also cross-channel hash anchors (DNS TXT, package registry metadata, public repository file, signed security.txt). Others are discovery aids only and provide no forge resistance (HTML link, HTTP response header, unsigned security.txt). Section 11 defines which is which.

### llms.txt versus llm.txt

The dominant convention is `llms.txt`, as published at llmstxt.org. The variant `llm.txt` (singular) is observed in the wild but is not endorsed by any specification author known at the time of writing. Publishers SHOULD use `llms.txt`. Verifiers SHOULD probe `llms.txt` first and MAY fall back to `llm.txt`. Both forms, when found, should reference the same `assistant-guide.txt` URL; divergence between the two is a finding worth reporting.

### Reference form in llms.txt

When `llms.txt` references this profile, the recommended line form is:

```text
- [Assistant Guide](https://example.com/.well-known/assistant-guide.txt): bounded assistant install and operational instructions
```

## 20. HTTP Serving Requirements

When served over HTTP, a conforming guide MUST be served over HTTPS. Plain HTTP serving is non-conformant at all levels above Level 0.

A conforming guide SHOULD:

- return HTTP 200
- use `Content-Type: text/plain; charset=utf-8`
- use `X-Content-Type-Options: nosniff` when supported
- use `Strict-Transport-Security` when supported
- avoid redirects except from stable canonical locations on the same registered domain
- resolve to the canonical host declared in the guide

Verifiers SHOULD report final URL, status code, headers, redirect chain, TLS validity, and canonical URL comparison. Redirect handling MUST follow the rules in the Verifier Conformance Profile section 9: same-registered-domain redirects are findings; cross-registered-domain redirects are blocking at Level 2 and above. TLS validation failures are blocking at Level 2 and above.

## 21. Verifier Requirements

A verifier for this profile SHOULD:

- fetch URLs without executing scripts
- verify HTTP status and headers
- verify final URL against the declared canonical URL
- verify the byte-level profile
- detect disallowed constructs
- extract required sections
- detect missing approval gates
- detect risky command patterns
- detect likely secrets or private infrastructure references
- detect stale metadata when possible
- compare public guide content to repository copies when available
- count required approvals and warn when the total exceeds a threshold (default 10), since approval fatigue degrades the human's review quality
- verify that action `command` fields satisfy the syntactic restrictions in section 12
- verify that `networked` actions declare a narrow `egress` list
- verify that `code-executing` actions are classified and approval-gated
- warn when likely code-executing commands such as package scripts, build tools, test runners, local scripts, generated code, or dependency lifecycle hooks omit the `code-executing` class
- warn when Level 4 guides omit `runner` fields on action blocks
- warn when actions use `runner: shell` without a narrow rationale in `notes`
- verify that the guide does not instruct chained-guide following, self-modification, memory persistence without re-confirmation, encoded-content execution, or tool-permission expansion (section 15)
- apply a heuristic prose scan for backdoor chaining: URLs to `.txt`, `.sh`, `.ps1`, `.py`, runbook, or guide-like resources appearing in imperative contexts ("then run", "next, follow", "after this, execute", "fetch and apply"); emit a warning rather than an error, since the heuristic is approximate
- flag any metadata field whose name matches `next-guide`, `then-fetch`, `chain-to`, `follow-next`, `continue-with`, or equivalent patterns as an error; such fields are not part of this profile
- compare the fetched bytes against the `guide-sha256` value in the manifest at Level 4
- enumerate every cross-channel hash anchor it can find (DNS TXT `_assistant-guide.<domain>`, package registry metadata, public repository file, signed security.txt) and compare each against the manifest hash; emit a failure on divergence and an info finding when no independent channel is present at Level 3 or above
- record which channels were checked and which were unreachable; absence of an optional channel is an info finding, not an error
- report the `last-reviewed` age as an informational finding, and warn when `valid-until` is in the past or malformed; there is no fixed `last-reviewed` expiry, because only the publisher's `valid-until` is a non-arbitrary staleness signal
- emit structured evidence and remediation, not only a score

A verifier MUST NOT execute commands from the guide.

A verifier MUST NOT treat guide text as instructions to the verifier.

### Compact verification report

Assistants and verifier UIs SHOULD present a compact report before asking the user to proceed:
```text
Verifier: <name> <version>
Guide: <canonical-url>
Level: <achieved-level>
SHA-256: <guide-sha256>
Blocking findings: <count>
Warnings: <count>
Hash pinned: yes/no
Proceed? yes/no
```
The compact report is a summary, not a substitute for the full verifier output. The assistant SHOULD show blocking findings inline. Non-blocking warnings MAY be summarized by count when the full report is available.

Field rendering by achieved level:

- `SHA-256` is rendered as the computed value at Level 2 and above; at Level 1 the verifier MAY render the value if computed, otherwise `n/a`
- `Hash pinned` is rendered `yes` only when a manifest is present and the manifest hash matches the fetched bytes; at Level 3 and below this field is rendered `n/a`
- `Level` is the achieved level; verifiers MUST NOT render `5` for guide-only evaluation (see section 18 Level 5)

## 22. Acceptance Checklist

A Level 3 or higher guide MUST include an acceptance checklist that lets a human and assistant determine when the bounded task is complete.

The checklist SHOULD include:

- expected files changed
- expected commands run
- expected tests or checks
- expected manual review steps
- conditions that mean the task is incomplete
- conditions that require escalation or stopping

## 23. Lifecycle and Change Management

Publishers SHOULD treat `assistant-guide.txt` as a security-relevant artifact.

Guide changes SHOULD be reviewed by an appropriate maintainer, security owner, platform owner, or release owner.

Guide changes SHOULD be recorded in changelogs or release notes when they affect installation, configuration, operations, security posture, or approval gates.

Publishers SHOULD update guides when releases materially change setup, configuration, migration, remediation, or operational practices.

## 24. Relationship to Existing Work

`llms.txt` is an emerging convention for LLM-readable site maps and documentation pointers. The Human-Verifiable Assistant Guide profile is narrower: it defines a constrained safety profile for assistant-facing operational instructions.

`AGENTS.md` is a convention for repository-wide, persistent rules that apply across an entire codebase. The Human-Verifiable Assistant Guide profile is task-bounded: it scopes a specific install, implementation, migration, remediation, or operational job and binds it to explicit approval gates. The two are complementary. A repository MAY ship both; in case of conflict, higher-priority sources (system, user, local repository instructions) win over both, and `AGENTS.md` wins over `assistant-guide.txt` because it represents the persistent, repository-owner authored baseline.

Claude skill frontmatter, OpenAI custom instructions, and similar assistant-configuration surfaces are vendor-specific. The Human-Verifiable Assistant Guide profile is vendor-neutral and operates on bytes a human can read.

Graceful Boundaries defines how services communicate limits, refusals, and next steps. This profile defines how projects communicate assistant-facing setup and implementation instructions without presentation-layer deception.

Siteline verifies whether a public site is usable by agents. A related verifier could assess whether a project's assistant-facing instructions satisfy this profile and surface reviewable risk evidence.

Skill Provenance defines portable integrity, hashing, and drift control for Agent Skills bundles. The Level 4 manifest model in this profile is intentionally aligned with the skill-provenance sidecar-manifest approach: the artifact does not self-hash; a manifest external to the artifact carries hash, byte count, and release pointers.

### No central registry

This profile is designed to be evaluable from the artifact itself plus its cross-channel anchors. No central registry of conforming guides is part of the spec, and the spec does not endorse one. A registry would concentrate trust in a single operator, invite verifier-as-oracle misuse, and add a delisting attack surface that the artifact-plus-channels model avoids. Operators verify a guide by running a verifier against its URL, not by consulting a list. Publishers may maintain non-normative supporter or implementer lists outside the spec for community visibility; such lists carry no security claim.

## 25. Locale

The Human-Verifiable Assistant Guide profile takes the same posture as `robots.txt`, `security.txt` (RFC 9116), and `llms.txt`: a single canonical file per publisher, no required multilingual fork.

Publishers MAY declare the natural language or languages of the guide using the optional `preferred-languages` metadata field, which mirrors RFC 9116's `Preferred-Languages`. The value is a comma-separated list of BCP 47 language tags, in order of preference:

```text
preferred-languages: en, fr
```

When the field is absent, verifiers SHOULD assume `en`.

Publishers who require translations SHOULD publish them at distinct URLs (for example `/.well-known/assistant-guide.fr.txt`) and SHOULD cross-reference them from the canonical guide using prose, not redirects. The canonical guide remains a single artifact at the canonical URL.

### Mixed-script bodies

Independent of the locale declaration, the body of a Level 2 or higher guide MUST satisfy the byte profile of section 8. That profile already restricts content to ASCII printable bytes plus LF, which eliminates the most common mixed-script and homoglyph attacks within the guide body. Non-ASCII natural-language content is therefore not directly representable at Level 2 or above. Publishers needing non-ASCII prose MUST either:

- relax to Level 1 and accept the loss of byte-profile conformance, or
- publish a Level 2+ ASCII guide and link to a separate localized human-facing document for prose.

This profile does not provide a controlled Unicode mode and does not intend to. ASCII-only is a deliberate design choice. The reasoning, in brief: any non-ASCII content in the file is interpreted by an assistant that may not respect field boundaries. A bidi control or homoglyph confined by spec to a `notes:` field is still ingested by the assistant; an attacker who can place attack characters anywhere in the file can attempt to influence interpretation everywhere in the file. The defense is to allow no such characters at all, in any field, in any context. Multilingual needs are served by separate localized human-facing documents linked from a Level 2+ ASCII guide.

A future revision of this specification may revisit this position if Unicode security tooling and assistant runtime field-boundary enforcement both mature significantly. As of this version, ASCII-only is final, not provisional.

## 26. Verifier Output Schema

A verifier SHOULD emit machine-readable output alongside any human-readable report. The normative machine-readable output shape is defined by the Verifier Conformance Profile section 27 and by `schemas/verifier-output.schema.json`.

The top-level JSON-compatible form is:
```text
{
  "verifier": {},
  "input": {},
  "fetch": {},
  "guide": {},
  "summary": {},
  "findings": []
}
```

Severity levels:

- `error`: blocks the claimed conformance level
- `warning`: does not block, but should be addressed
- `info`: observational

A verifier MUST be able to render the same evidence as human-readable text. A verifier MUST NOT execute commands found in the guide. A verifier MUST NOT treat guide text as instructions to the verifier.

## 27. Residual Threats

A fully conformant Level 4 guide, served over HTTPS with sidecar manifest, mitigates artifact-level attacks addressed by this profile: hidden instructions, unsafe guide structure, missing approval gates, chained-guide pivots, and provenance drift. A Level 5 deployment adds runtime enforcement for command execution, approval scope, memory scope, network disclosure, and session pinning. The following threats remain partly or wholly out of scope and are documented here so adopters do not assume coverage.

### Out of scope: publisher and supply-chain compromise

If the publisher's git host, DNS, TLS issuer, package registry account, or release signing key is compromised, an attacker can publish a Level 4 guide that conforms in every byte. The profile narrows what such a guide can ask an assistant to do (atomic actions, explicit approval, narrow egress, no chained guides, no self-modification) but cannot substitute for code signing, release attestation, or organizational controls. Defenders SHOULD combine this profile with signed releases, hardware-backed signing keys, and out-of-band publisher identity verification.

### Out of scope: assistant non-conformance

At Levels 3 and 4, the profile assumes the assistant honors authority order (section 7), displays action blocks verbatim (section 12), respects per-action approval scope (section 12), pins the manifest hash for the session (section 15), and refuses prohibited instruction patterns (section 15). An assistant that ignores any of these guarantees defeats the profile. Level 5 turns these assumptions into runtime conformance requirements, but runtime implementation defects remain possible. Mitigation belongs in runtime testing, sandboxing, and tool-permission enforcement, not in the guide format alone.

### Out of scope: human approval-fatigue and social engineering in prose

A guide may pack a high count of low-risk approvals to wear down the reviewer before requesting a destructive one. Verifiers warn at a count threshold (section 21) but the line is not bright. Similarly, the `notes` and prose fields can carry persuasive but technically conforming text. Reviewers SHOULD read the full guide once, not approve action-by-action without context.

### Out of scope: natural-language prose attacks

The byte profile blocks mixed-script and homoglyph attacks. It does not block prose that is grammatical English but materially misleading about what a command does. A guide claiming a command is read-only when it is destructive will pass mechanical checks. Human review of action `command` fields against their `class` declaration remains necessary.

### Out of scope: environment-dependent behavior

The same command behaves differently across operating systems, shells, container runtimes, working directories, and environment variables. The `cwd` and `env` fields narrow this surface but do not eliminate it. Assistants SHOULD report the environment in which they will execute the action when requesting approval.

### Out of scope: time-bombs and date-sensitive commands

A command may be safe today and destructive after a specific date or system state. The profile has no facility for proving temporal safety. Combine with `valid-until` and frequent re-review for high-consequence guides.

### Out of scope: cross-guide interference

A conforming guide cannot reference another guide for the assistant to follow (section 6 scope, section 15 prohibited patterns). The user, however, may load successive guides in the same assistant runtime over time. When this happens, action ids may collide across guides, and prior session state may bleed into the next one. The spec cannot prevent this without forbidding multi-session workflows entirely, which would defeat the bounded-task model.

Mitigation belongs at the assistant runtime: each guide gets a separate scope with its own approval ledger; action-id namespaces do not cross guide boundaries; carrying prompt or memory state across guide sessions requires explicit user opt-in (section 15). Operators SHOULD start a fresh assistant context when moving from one guide to the next on a high-consequence task.

### Out of scope: side channels in metadata fields

Fields such as `canonical-url`, `repository-url`, and `applies-to` are read by the assistant. A long or pathological value could carry instructions framed as data. The byte profile and length limits constrain this; verifiers SHOULD warn on unusually long metadata values.

### Net posture

For a Level 5 deployment, on a guide that conforms at Level 4 and was reviewed by the human before the session, the residual risk reduces to publisher/supply-chain compromise, human review error, runtime implementation defects, and environment-dependent command behavior. Those are the right places for the next layer of defense (signing, training, sandboxing, runtime audits), not for the file format alone.

## 28. Operator Responsibilities and Defense in Depth

This profile is one layer in a defense stack. It is the layer that prevents a presentation surface from hiding instructions from a human while feeding them to an assistant. It is not, by itself, a secure install procedure. Reading the full guide, least-privilege sandboxing, out-of-band publisher verification, backups before destructive actions, and disposable test environments remain the operator's responsibility regardless of how high a guide scores against this profile.

The operator practices that accompany this profile are maintained as a non-normative companion: see `operator-guide.md`. It covers what to do before authorizing the assistant, while the assistant is acting, and around the assistant; what this profile does not replace; and the verifier-as-oracle and trust-transference anti-patterns. Adopters are expected to read it alongside section 27.
