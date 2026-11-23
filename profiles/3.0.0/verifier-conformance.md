Status: draft profile 3.0.0, unreleased. No released verifier implements this
profile. Profiles 1.0.0 and 2.0.0 remain the released contracts and are not
changed by this document. Sections 27 and 29 still describe the 2.0.0 output
and fixture contracts; the 3.0.0 schemas and fixture suite do not exist yet.

# GuideCheck Verifier Conformance Profile

## 1. Purpose
This specification defines the GuideCheck Verifier Conformance Profile for tools that evaluate `assistant-guide.txt` artifacts against the Human-Verifiable Assistant Guide profile.
A conformant verifier answers four questions:
- What bytes were evaluated?
- What conformance level did those bytes achieve?
- What evidence supports that result?
- What findings must the human or assistant address before acting?
This profile defines verifier behavior. It does not define a registry of approved verifier implementations.

## 2. Relationship to the Guide Profile
The guide profile defines `assistant-guide.txt`, its conformance levels, action blocks, provenance model, and Level 5 runtime requirements.
This verifier profile defines how a verifier checks those requirements and reports evidence.
A conformant verifier is an implementation that satisfies this profile for a declared guide-profile version and passes the corresponding fixture suite.
The verifier profile is intentionally implementation-neutral. A verifier may be a hosted web service, CLI, library, GitHub Action, CI job, browser extension, or assistant-runtime component.

## 3. Terminology
Guide profile
: The Human-Verifiable Assistant Guide profile.
Verifier profile
: This document.
Verifier
: A tool that evaluates guide bytes and emits conformance evidence.
Conformant verifier
: A verifier that satisfies this profile and passes the fixture suite for the applicable profile version.
Finding
: A machine-readable and human-readable report item describing an error, warning, or informational observation.
Blocking finding
: A finding with severity `error`; it blocks the claimed conformance level.
Fixture suite
: The official test corpus of valid and invalid guides, manifests, anchors, fetch scenarios, and expected findings.

Standard primary verifier
: A verifier URL published by the standards project for a specific verifier-profile version as the default hosted conformance checker. It is not the only conformant verifier and is not an oracle, but it is exempt from off-domain recommended-verifier warnings. For verifier-profile version 1.0.x the designated standard primary verifier is `https://guidecheck.org/verify`, published by the PAICE Foundation.

## 4. Scope
This profile defines two evaluation modes.

Public-web mode is the primary mode. The input is an HTTPS URL to an `assistant-guide.txt` resource. The verifier performs all fetches, header checks, cross-channel anchor checks, redirect handling, and TLS validation defined in this profile.

Local-file mode is a normative extension. The input is a path to a local `assistant-guide.txt` file plus an optional path to a sidecar manifest. The verifier performs all byte-level, content, action-block, approval, command, prohibited-pattern, status, and staleness checks. The verifier MUST skip checks that depend on a live HTTP fetch (HTTP headers, redirect chain, TLS validation, content-variation re-fetch, hosted-verifier SSRF checks). Local-file mode MAY skip cross-channel anchor checks when the verifier has no network access; when network access is available the verifier SHOULD still resolve DNS TXT, registry, repository, and signed security.txt anchors named in metadata.

A verifier MUST report the mode it ran in (`evaluation_mode: public-web` or `evaluation_mode: local-file`). A local-file evaluation MUST NOT report an achieved level higher than Level 3 unless the verifier also fetches and verifies the manifest and at least one independent cross-channel anchor; the level rules of section 25 still apply, but the absence of fetch evidence prevents Level 4 from being asserted on local bytes alone.

Private-repository mode, offline-archive mode, and any other input modes remain implementation extensions outside this profile.

## 5. Non-Goals
This profile does not:
- certify that a guide is safe to follow
- certify publisher identity, intent, or trustworthiness
- execute commands or simulate command effects
- audit the underlying software being installed
- replace package manager trust policy, signing, SBOMs, vulnerability scanning, sandboxing, or human review
- define a central registry of verifier implementations
- require use of any specific hosted verifier

## 6. Verifier Threat Model
A verifier MUST treat every guide, manifest, URL, redirect, DNS response, repository file, registry record, and cross-channel anchor as potentially malicious.
In-scope verifier threats include:
- server-side request forgery against hosted verifiers
- DNS rebinding or private-network resolution
- redirects to unintended hosts
- TLS failure or downgrade
- oversized responses and decompression bombs
- content-type confusion
- malicious guide text attempting to instruct the verifier
- crafted metadata values carrying instructions as data
- hash mismatches across same-origin and independent channels
- malformed action blocks that confuse parsers
- stale or revoked guides
- denial-of-service through slow responses, long redirect chains, or many anchors
Out-of-scope verifier threats include:
- compromise of the verifier host or binary
- compromise of every independent control plane used for provenance
- malicious fixture-suite maintainers
- attacks against the human outside the verifier output
- runtime behavior after verification, except where the verifier is also a Level 5 assistant runtime

## 7. Required Safety Invariants
A conformant verifier MUST:
- never execute commands from the guide
- never evaluate guide text as instructions to the verifier
- never render Markdown, HTML, CSS, JavaScript, SVG, images, or rich media from the guide
- preserve and hash the exact fetched bytes before normalization
- enforce response size, timeout, redirect, and network-target limits
- report findings from evidence, not from model interpretation alone
- produce machine-readable output and human-readable output from the same evidence
- make its verifier name, version, guide-profile version, and verifier-profile version available in output

## 8. Input Model
A conformant verifier MUST accept an HTTPS URL as its primary public-web input.
The verifier MAY accept optional expected values:
- expected canonical URL
- expected guide SHA-256
- expected guide-profile version
- expected maximum conformance level to evaluate
- expected verifier-profile version
- standard primary verifier URL for the profile version, when configured
- required minimum conformance level, used for the verdict (section 25)
The verifier MUST NOT require credentials, cookies, browser session state, or user-specific headers to fetch a public guide.
If authentication is needed, the input is outside public-web conformance for this profile.

## 9. Fetch Requirements
For public-web verification, the verifier MUST:
- fetch without executing scripts
- use HTTPS
- validate TLS
- reject plaintext HTTP for all levels above Level 0
- reject TLS certificate errors
- send no cookies or ambient browser credentials
- send no authorization headers unless operating in an explicitly non-public extension mode
- limit redirects to a small finite count, default 5
- report every redirect hop
- treat cross-origin redirects as findings
- treat cross-registered-domain redirects as blocking for Level 2 and above
- preserve final URL and original requested URL
- record HTTP status code and response headers
- reject compressed or transferred responses that expand beyond the verifier's configured maximum
- stop reading once enough bytes have been read to prove the guide exceeds the maximum file size
- use a simple, reproducible request profile that avoids content negotiation where practical
Hosted or other public request-proxy verifiers SHOULD enforce a per-request
outbound fetch budget across guide, variation, manifest, and anchor fetches,
and SHOULD deduplicate exact same-URL same-profile fetches within one
verification request.
The verifier SHOULD use conservative timeouts:
- DNS lookup timeout: default 5 seconds
- connection timeout: default 10 seconds
- total fetch timeout: default 30 seconds
- response body read limit: at least 8193 bytes for Level 2+ evaluation, so oversize can be detected
Timeouts and read limits MUST be reported.

The verifier SHOULD perform a content-variation check by re-fetching once with a different harmless user agent or accept profile. If the guide bytes differ, the verifier SHOULD emit a warning and SHOULD fail Level 4 unless the manifest and independent anchors identify exactly one byte sequence as canonical.

## 10. Hosted Verifier Network Safety
A hosted verifier that fetches user-supplied URLs MUST implement SSRF defenses.
It MUST reject or block requests to:
- localhost names, including `localhost`
- loopback ranges, including `127.0.0.0/8` and `::1`
- private IPv4 ranges, including `10.0.0.0/8`, `172.16.0.0/12`, and `192.168.0.0/16`
- link-local ranges, including `169.254.0.0/16` and `fe80::/10`
- unique local IPv6 addresses, including `fc00::/7`
- multicast and unspecified addresses
- cloud metadata services, including `169.254.169.254`
- `.local` and other local-only names when resolvable only inside a private network
It MUST re-check resolved IP addresses after redirects.
It SHOULD pin the resolved address for each outbound connection to reduce DNS rebinding exposure.
It SHOULD perform the final private-network check after DNS resolution and before connection.
It MUST NOT expose raw fetch errors containing internal network details to untrusted users.

## 11. Byte Handling
The verifier MUST compute SHA-256 over the exact fetched bytes.
The verifier MUST compare the byte count with the 8192-byte limit before any other examination of the guide. When the guide exceeds the limit the verifier MUST emit `byte-profile.size-limit`, MUST NOT run any other check, including profile-specific parsing, and MUST report achieved level 0, because no other property of the guide was established. A caller that selects a profile from guide bytes MAY read the declaration in one linear pass first; no check with a cost above linear may run on a guide over the limit.
The verifier MUST split the guide into lines at `0x0A` and at no other byte. A final empty piece after a trailing `0x0A` is not a line. Every rule in sections 13 through 21 is applied to these lines.
For Level 2 and above, the verifier MUST check:
- allowed bytes are only `0x0A` and `0x20` through `0x7E`
- file size is at most 8192 bytes
- each line is at most 120 bytes
- line count is at most 400
- line endings are LF only
- no tabs
- no carriage returns
- no NUL bytes
- no ANSI escape bytes
- no Unicode bidi controls
- no zero-width characters
- no control characters other than LF
A byte outside `0x0A` and `0x20` through `0x7E` is a blocking finding. The verifier MAY report one finding for the first line that contains such a byte instead of one per byte.
The verifier MUST report byte offsets or line and column numbers for byte-profile failures when practical.
The verifier MUST NOT normalize line endings, decode HTML entities, strip comments, render Markdown, or otherwise transform guide bytes before checking byte-profile conformance.
Every check in this profile MUST complete in time linear in the size of the guide. A check that compares each match against all preceding text does not meet this requirement.

## 12. Content-Type and HTTP Header Checks
For served guides, the verifier MUST report:
- `Content-Type`
- `X-Content-Type-Options`
- `Strict-Transport-Security`
- `Content-Length`, when present
- final URL
- redirect chain
- TLS status
For Level 2 and above:
- `Content-Type: text/plain; charset=utf-8` is expected
- missing or incompatible `Content-Type` is a warning unless the profile version being evaluated makes it blocking
- `X-Content-Type-Options: nosniff` is expected when hosting supports it
- HSTS is expected when hosting supports it
The verifier MUST NOT infer safety from headers alone.

## 13. Plain-Text Parsing Rules
The verifier MUST parse guides as raw plain text.
The verifier MUST NOT render Markdown.
The verifier MUST detect disallowed constructs from the guide profile, including:
- HTML
- CSS
- JavaScript
- Markdown images
- remote embeds
- data URLs
- rich-document constructs
- terminal escape sequences
The verifier SHOULD warn on encoded or obfuscated command blobs intended for execution and on instructions to decode and execute hidden content. These are prose scans (section 21) and do not decide a level.
For Level 3, the verifier MUST emit a blocking finding for any line that contains three consecutive backticks or three consecutive tildes (proposed id `construct.code-fence`). The finding does not affect Level 1 or Level 2.
Detection MAY include heuristic warnings for prose patterns. Heuristic warnings MUST be labeled as warnings unless the underlying rule is exact and blocking.

## 14. Metadata Parsing
The verifier MUST parse the metadata block by exact fence match:
```text
[assistant-guide-metadata]
...
[/assistant-guide-metadata]
```
A line opens or closes the metadata block only when it equals the fence exactly. A guide with a missing, repeated, nested or near-form metadata fence, or with the text `assistant-guide-metadata` on any other line, does not declare this profile and is refused at selection (section 32). The block a verifier parses under this profile therefore always has exactly one exact pair of fences.
The verifier MUST reject metadata blocks with:
- any duplicate key
- a key named `next-guide`, `then-fetch`, `chain-to`, `follow-next` or `continue-with` (`prohibited.next-guide-field`)
- a line that carries a reserved action field label (section 17)
- malformed `key: value` lines
- keys outside lowercase ASCII letters, digits, and hyphens
- values outside the guide byte profile
The verifier MUST check Level 3 required fields:
- `identifier`
- `profile`
- `profile-version`
- `guide-version`
- `applies-to`
- `canonical-url`
- `repository-url`
- `last-reviewed`
The verifier SHOULD check optional fields when present:
- `source-path`
- `reviewed-by`
- `status`
- `superseded-by`
- `preferred-languages`
- `valid-until`
- `recommended-verifier`
- `verifier-conformance`
- `registry-url`
- `manifest-url`
The verifier MUST validate every URL field against the URL grammar of guide-profile section 11 by exact match and MUST emit `metadata.url.invalid` otherwise. The grammar admits `https://`, a host of two or more labels, and path segments of ASCII letters, digits, `-`, `_`, `.`, `+` and `@`. User information, a port, a query, a fragment, a backslash, a space and percent-encoding are all outside it. The verifier MUST NOT pass a URL field to a general URL parser before this check. Internationalized domain names MUST be expressed in punycode A-label form.
When the verifier compares the hosts of two URL fields it MUST compare exact hosts, or registered domains computed with a public suffix list that includes private suffixes.
The verifier MUST warn when a non-URL metadata value exceeds 80 bytes. URL-valued fields are exempt because a legitimate canonical or repository URL can be long; all other field values are short by design, and an unusually long one is a side-channel risk per guide-profile section 27.
The verifier SHOULD warn when `canonical-url`, `repository-url`, `registry-url`, `manifest-url`, or `recommended-verifier` use unrelated registered domains without explanation.
The verifier SHOULD warn when `recommended-verifier` is not on the same registered domain as `canonical-url`, unless the guide explicitly identifies it as third-party or the URL matches the standard primary verifier for the applicable verifier-profile version.
The reference verifier emits `metadata.recommended-verifier.off-domain` for an off-domain `recommended-verifier` unless it is the configured standard primary verifier for the applicable profile version.
The verifier MUST NOT warn solely because `recommended-verifier` differs from `canonical-url` when `recommended-verifier` matches the standard primary verifier configured for the applicable profile version.
When package-registry metadata is used as an independent Level 4 anchor, the verifier MUST require `registry-url` and MUST validate that it identifies a specific registry record rather than a registry homepage or search result.
When `registry-url` is absent and no other Level 4 independent anchor is available, the verifier SHOULD emit an informational finding for Level 3 and a blocking finding for Level 4.

## 15. Verification Instruction Checks
For Level 1 and above, the verifier MUST check that the canonical verification instruction of guide-profile section 10.2 is present: three consecutive whole lines equal, byte for byte, to the three lines given there, with the first of them before the first exact `[action]` line.
The check is an exact comparison of lines. The verifier MUST NOT accept a paraphrase, a rewrapped copy, a copy inside a longer line, or a set of matching phrases found anywhere in the guide. A guide without the exact lines receives `verification-instruction.missing`.
The verifier SHOULD warn when a guide names a recommended verifier but omits `verifier-conformance` metadata.
The verifier SHOULD warn when a guide states or implies that only one verifier is authoritative (`verification-instruction.single-authority`). This is a prose scan and does not block (section 21).
The verifier SHOULD check whether DNS TXT or signed `security.txt` fields identify a recommended verifier. When those anchors disagree with `recommended-verifier`, the verifier SHOULD emit a warning unless one value is the configured standard primary verifier and the other is explicitly marked as a publisher-local verifier.

## 16. Required Section Checks
For Level 3 and above, the verifier MUST check each of the ten named sections of guide-profile section 10.1 by its heading line. A heading line is a whole line equal to the section name, or to the section name preceded by `# `, `## ` or `### `. Each section MUST have exactly one heading line. A missing heading and a repeated heading are both blocking, under the `content.required.*` id for that section.
The verifier MUST NOT identify a section by a phrase inside a line, by letter case folding, or by any other approximate match.
The verifier MUST check that the first line of the guide begins with `Assistant Guide: ` (`content.required.title`), that `canonical-url` and `repository-url` are present in the metadata block (`metadata.missing-required`), and that at least one exact action block is present (`content.required.actions`).
The Level 3 checks of sections 16 through 21 MUST run for every guide that declares this profile. They do not depend on whether an action block parsed or on any phrase being present.

## 17. Action Block Parsing
The verifier MUST parse action blocks by exact fence match:
```text
[action]
...
[/action]
```
A line opens a block only when it equals `[action]` and closes one only when it equals `[/action]`. The verifier MUST emit `action-block.malformed` for:
- `[action]` inside an open action block or inside the metadata block
- `[/action]` where no action block is open
- an action block still open at the end of the guide
- reserved marker text: any other line that, after lowercasing and removing spaces and tabs, contains `[action`, `[/action`, `<action`, `</action`, `{action` or `{/action`
The verifier MUST emit `action-block.field-outside-block` for every line outside an exact action block that has a reserved label. Split the line at every colon and set aside the last piece; the line has a reserved label when any remaining piece, reduced to its ASCII letters and lowercased, equals `id`, `class`, `approval` or `command`. The check applies inside the metadata block. A line that carries reserved marker text is reported for that and not also for a label.
Inside a block, the verifier MUST check each line in this order and report the first failure only:
- no colon followed by one space: `action-block.malformed`
- a key outside the fixed list: `action-block.unknown-key`
- an empty value, a value that begins or ends with a space, or a value with a byte outside `0x20` through `0x7E`: `action-block.malformed`
The verifier MUST also emit `action-block.malformed` when a key appears more than once in a block. Every `command` line in a block is checked under section 19, including a repeated one.
The fixed key list is `id`, `class`, `approval`, `command`, `runner`, `cwd`, `egress`, `notes`, `env`, `params`, `exec-sha256`, `exec-opaque`. The first seven are required; a block that lacks one receives `action-block.missing-required`.
The verifier MUST check `id` against its grammar, 1 to 32 ASCII letters, digits or hyphens (`action-block.id.invalid`), and MUST compare ids by exact bytes (`action-block.duplicate-id`).
The verifier MUST parse `class` as a list separated by a comma and one space. An unknown or repeated class is `action-block.class.invalid`. The `normal` class is mutually exclusive with all other classes (`action-block.class.normal-mixed`).
Allowed classes are:
- `normal`
- `networked`
- `destructive`
- `privileged`
- `persistence-changing`
- `data-accessing`
- `code-executing`
The verifier MUST emit `action-block.approval.invalid` unless `approval` is `required` or `not-required`, and `action-block.runner.invalid` unless `runner` is `argv`.
A finding MUST locate its line by number. The verifier MUST NOT copy an action id, a key, a value, or any other guide-authored text into a finding message or evidence field.

## 18. Action Approval Checks
The verifier MUST emit an error when an action whose class list includes any of the following has `approval: not-required`:
- `privileged`
- `destructive`
- `persistence-changing`
- `data-accessing`
- `code-executing`
For Level 4, the verifier SHOULD warn when actions whose class list includes `networked` do not use `approval: required`.
For Level 5 readiness, the verifier SHOULD warn unless all `networked`, `privileged`, `destructive`, `persistence-changing`, `data-accessing`, and `code-executing` actions use `approval: required`.
The verifier SHOULD count required approvals and warn when the total exceeds a default threshold of 10.

## 19. Command Field Checks
The verifier MUST tokenize a `command` value by splitting it at every `0x20` byte. This is the only tokenizer. The verifier MUST NOT apply shell lexing, quote handling, or pattern search to a command.
A `command` value rejected by the value rule of section 17 is reported there and is not checked under this section.
The verifier MUST emit `command.grammar` unless all of the following hold:
- every token is non-empty
- every byte of every token is an ASCII letter, a digit, or one of `-`, `_`, `.`, `+`, `/`, `:`, `=`, `@`, `,`
- the first token consists only of ASCII letters, digits, `-`, `_`, `.` and `+`, or is `./` followed by one or more non-empty segments of those characters joined by `/`
A command that fails this check has no argument vector, and the checks below do not apply to it.
For a command in the grammar the verifier MUST:
- emit `command.path.escape` when any token, split at every `/`, `:`, `=`, `@` and `,`, has a piece that ends with exactly two dots
- emit `command.path.absolute` when a token begins with `/`, or the text after its first `=` begins with `/`, and the action does not set `approval: required`
The verifier MUST NOT interpret any token as a prefix. `sudo` is a program name like any other.

### Tier assignment
The verifier MUST load the shape registry of the declared profile version and MUST assign each action to exactly one tier.
An action is shape-listed when its argument vector matches a registry entry: equal length, and at every position either the exact string or a slot of the stated type (`local-ref`, `https-url`, `word`, `number`, as defined in guide-profile section 12). No entry matches a prefix of an argument vector. A registry in which two entries can match the same argument vector is invalid, and the verifier MUST refuse to use it. An action that declares `params` is never shape-listed.
For a shape-listed action the verifier MUST emit:
- `action-block.class.under-declared` when the declared classes do not include every class in the entry's floor
- `action-block.malformed` when the action declares `exec-opaque`
Every other action is opaque. For an opaque action the verifier MUST emit:
- `action.program-opaque` (warning), once per action
- `action-block.class.under-declared` when the declared classes do not include `code-executing`
- `approval.required-missing` when `approval` is not `required`
- a blocking finding (proposed id `action.program-opaque.unacknowledged`) when `exec-opaque: acknowledged` or `notes` is absent
The verifier MUST report the number of shape-listed and opaque actions.

### Local references and pins
A local reference is a token, or the text after the first `=` of a token, that begins with `./`. A reference requires a pin when it is the program token, or when the action's class list includes `code-executing`. An entry with `execution: bound` requires a pin on the file its `pin` field names.
The verifier MUST emit:
- `command.local-ref.unpinned` when an action has a reference or bound entry that requires a pin and no `exec-sha256`, or has more than one reference that requires a pin
- `action-block.malformed` when `exec-sha256` is not 64 lowercase hexadecimal characters
- `action.exec-target-unresolved` when `exec-sha256` is declared and nothing in the action requires a pin
- `exec-sha256.unverified` (info) when the verifier did not read the pinned file
- `exec-sha256.mismatch` when it read the file and the hash differs
- `exec-sha256.transitive-unpinned` when a readable pinned file invokes a further repository file that is not pinned
A static verifier does not resolve bare filenames. A verifier that reads the repository MUST resolve each argument of a `code-executing` action against `cwd` and MUST emit `command.local-ref.unpinned` when one names an existing file that is not written as a pinned local reference.

## 20. Filesystem, Environment, Egress, and Parameter Checks
The verifier MUST check `cwd` against its grammar: `.`, or segments of ASCII letters, digits, `-`, `_`, `.` and `+` joined by `/`, with no `..` segment, optionally preceded by `/`. A value outside the grammar, and an absolute value on an action without `approval: required`, are blocking (proposed id `filesystem.cwd.invalid`).
The verifier MUST check `egress`: the literal `none`, or host patterns separated by a comma and one space, each two or more DNS labels joined by `.`, optionally preceded by `*.` and then at least two labels. A value outside the grammar is `egress.pattern`.
The verifier MUST emit `egress.missing` when an action whose class list includes `networked` declares `egress: none`, and a blocking finding (proposed id `egress.class-mismatch`) when an action that does not include `networked` declares a host pattern.
The verifier MUST check `env` as names separated by a comma and one space, each an ASCII letter or underscore followed by letters, digits or underscores (proposed id `env.invalid`). A command cannot reference a variable, so there is no reference check.
The verifier MUST check `params`: names of 2 to 32 uppercase ASCII letters, digits or underscores, separated by a comma and one space, none repeated, each occurring in the command as a whole token or as the whole text after the first `=` of a token, and none as the program token (proposed id `params.invalid`).

## 21. Prohibited Pattern Checks
The exact field names `next-guide`, `then-fetch`, `chain-to`, `follow-next` and `continue-with` are blocking as metadata keys (section 14) and are blocking in an action block as unknown keys (section 17).
The verifier SHOULD scan prose for instructions that direct an assistant to:
- fetch and follow another guide, script, instruction file, or runbook
- pivot the current session to another guide
- modify, rewrite, or replace `assistant-guide.txt`, its manifest, or verifier output
- store guide content, action commands, or approvals into long-term assistant memory without current-session reconfirmation
- decode, deobfuscate, or execute encoded content
- expand tool permissions, disable sandboxing, or skip approval gates
- treat `notes` or prose fields as commands
A match is a warning under the corresponding `prohibited.*` id. Under this profile a prose scan MUST NOT emit an error and MUST NOT lower or raise the achieved level. The same holds for scans of negation, overclaimed safety, and backdoor-chaining hints.
A prose scan MUST process the guide line by line, after the size limit has been enforced, in time linear in the size of the guide. It MUST NOT re-read earlier text for each match.
A verifier MAY run a classifier over the prose after these checks. Its result is advisory, is reported with the classifier's identity, and never determines a level.

## 22. Provenance and Manifest Checks
For Level 4, the verifier MUST fetch the manifest URL declared by `manifest-url`.
The manifest fetch MUST obey the same fetch safety requirements as guide fetches.
The verifier MUST parse at least these manifest fields:
- `guide-path`
- `guide-version`
- `guide-sha256`
- `guide-bytes`
- `immutable-release-url`
The verifier MUST recompute SHA-256 over the fetched guide bytes and compare it with `guide-sha256`.
The verifier MUST compare `guide-bytes` with the fetched byte count.
The verifier MUST report a Level 4 conformance failure when manifest hash or byte count does not match.
The verifier MUST validate manifest values before comparing them. `guide-sha256` MUST be 64 lowercase hexadecimal characters (proposed id `manifest.hash-invalid`). `guide-bytes` MUST be ASCII digits with no sign, separator or leading zero (`manifest.bytes-invalid`). A key that appears twice is blocking (proposed id `manifest.malformed`). An empty value is not a match and is not an absence: a manifest that is supplied and is not valid MUST produce a blocking finding.
The verifier MAY continue Level 3 content evaluation after Level 4 failure.
When `signature` is present, the verifier SHOULD report it. Signature verification is not required by this profile unless a future profile version makes it required.
When `transparency-log-url` is present, the verifier SHOULD retrieve the referenced log entry and check it as a cross-channel anchor under section 23.

## 23. Cross-Channel Anchor Checks
For Level 4, the verifier MUST enumerate every cross-channel hash anchor it can find and compare each anchor hash with the manifest hash.
Recognized independent channels are:
- DNS TXT at `_assistant-guide.<registered-domain>`
- package registry metadata
- signed `security.txt` extension fields
- public append-only transparency log referenced by the manifest `transparency-log-url` field
Repository files at `source-path` are checked for consistency only and MUST NOT qualify as independent provenance in this profile.
A fetching verifier MUST NOT count a `registry-url` toward the Level 4 cross-channel requirement unless its host is a recognized package registry whose publish credentials are distinct from the guide's web host. A `registry-url` on any other host can be served by the guide publisher and provides no independence; the verifier SHOULD emit `anchor.registry.unrecognized-host` (warning) and MUST NOT fetch it as anchor evidence. If the package-registry channel is the only declared anchor, Level 4 then fails via `anchor.independent.missing`.
A verifier that parses JSON package-registry metadata MUST extract the anchor hash only from assistant-guide-specific metadata, such as an `assistantGuide` or `assistant-guide` object with a `sha256` field. It MUST NOT count an unrelated `sha256` field elsewhere in the registry record as the assistant-guide anchor.
When package-registry assistant-guide metadata includes a guide URL, the verifier SHOULD compare it with `canonical-url` and warn with `anchor.registry.url-mismatch` on disagreement. This warning does not by itself block Level 4 when the anchor hash matches.
The verifier MUST emit a failure when independent channels disagree on the hash. A repository-file mismatch also MUST block Level 4, even though a repository match never qualifies.
The verifier MUST report which channels were checked, which were found, which were unreachable, and which were unavailable.
Unreachable optional channels are findings but do not by themselves block Level 4 if at least one independent channel is present and agrees.
Same-origin discovery aids MUST NOT count as independent anchors:
- HTML link tags
- HTTP response headers
- unsigned `security.txt`
- same-origin pages that link to the guide

## 24. Status and Staleness Checks
The verifier MUST parse `status` when present.
If `status: revoked`, the verifier MUST emit an error and achieved level MUST be no higher than Level 1.
If `status: deprecated`, the verifier MUST emit an error (proposed id `metadata.status.deprecated`), the achieved level MUST be no higher than Level 2, and the verifier MUST report the `superseded-by` URL when it is present and satisfies the URL grammar.
When `status` is `deprecated` or `revoked`, missing `superseded-by` is a finding.
The verifier MUST parse `last-reviewed` when present.
The verifier SHOULD parse `valid-until` when present.
The verifier MUST report the `last-reviewed` age as an informational finding. There is no fixed `last-reviewed` expiry threshold; only the publisher's `valid-until` is a non-arbitrary staleness signal, so a stale `last-reviewed` date is surfaced for the human to judge rather than warned on against an arbitrary cutoff.
The verifier SHOULD warn when:
- `valid-until` is in the past
- `valid-until` is malformed
- dates are in the future in a way that appears erroneous
The verifier MUST report the date and time used for staleness evaluation.

## 25. Level Calculation
The verifier MUST calculate `achieved_level` from evidence.
A guide achieves Level 0 when no conforming plain-text guide is available or the resource is only available through a non-plain-text surface.
A guide achieves Level 1 when:
- the public-web guide was fetched over HTTPS with valid TLS
- a `.txt` guide is directly readable without script execution
- `canonical-url` and `repository-url` are present in the metadata block and satisfy the URL grammar
- the `Task scope` heading line is present exactly once
- the canonical verification instruction is present before the first action block
A guide achieves Level 2 when Level 1 is satisfied and:
- the byte profile passes
- size, line length, and line count limits pass
- no disallowed constructs are present
A guide achieves Level 3 when Level 2 is satisfied and:
- every required section has exactly one heading line
- metadata is valid and `status` is `active`
- at least one action block is present
- no finding of sections 13 through 20 with severity `error` is present
- no fenced code block is present
Every `error` finding of sections 13 through 20 blocks Level 3. Warnings, including every prose-scan result, do not.
A guide achieves Level 4 when Level 3 is satisfied and:
- manifest is present and valid
- guide hash and byte count match the manifest
- at least one independent cross-channel anchor is present
- every found independent anchor agrees with the manifest hash
A verifier MUST NOT report achieved Level 5 for a guide alone. Level 5 is a deployment claim that combines Level 4 guide conformance with runtime enforcement. A verifier MAY report `level5_ready: true` when the guide satisfies Level 4 and all Level 5 preparation recommendations pass.

For this verifier-profile version, `level5_ready: true` means:
- achieved level is Level 4
- every action classed as `networked`, `privileged`, `destructive`, `persistence-changing`, `data-accessing`, or `code-executing` uses `approval: required`

The `level5_ready` signal is guide-side preparation only. It is not an achieved Level 5 claim, and it does not assert that any runtime enforced the guide.

### Verdict
The compact report's last line is the verdict. The verifier MUST render `Proceed? yes` only when all of the following hold:
- the number of `error` findings is zero
- the achieved level is at least 3
- the achieved level is at least the level the caller required, when the caller required one
Otherwise the verifier MUST render `Proceed? no` followed by a `Reason:` line carrying the first applicable phrase of `blocking findings`, `below Level 3`, `below the required level`.
The exit status or response status of a verifier MUST agree with the verdict: a result that is not `Proceed? yes` MUST NOT be reported as success.

## 26. Finding Severity
The verifier MUST use these severities:
- `error`: blocks the claimed or target conformance level
- `warning`: does not block the achieved level but should be reviewed
- `info`: observational evidence
The verifier MAY include implementation-specific severities in an extension field, but MUST map them to `error`, `warning`, or `info`.
A finding MUST NOT contain guide-authored text. Messages are fixed strings, location is a line number, and an evidence field carries only values the verifier computed. Outside findings, a report may render a guide value only when it is a URL field that satisfies the URL grammar.
Every finding MUST include:
- stable finding id
- severity
- message
- evidence location when available
- affected profile section when available
- remediation text when available

## 27. Required Output Schema
A conformant verifier MUST emit machine-readable output.
The following complete example conforms to the versioned output schema:
```json
{
  "verifier": {
    "name": "guidecheck-hosted",
    "version": "1.0.0",
    "verifier_profile": "human-verifiable-assistant-guide-verifier",
    "verifier_profile_version": "2.0.0",
    "guide_profile": "human-verifiable-assistant-guide",
    "guide_profile_version": "2.0.0"
  },
  "input": {
    "evaluation_mode": "public-web",
    "url": "https://snapsynapse.github.io/compat/.well-known/assistant-guide.txt",
    "submitted_url": "https://snapsynapse.github.io/compat/.well-known/assistant-guide.txt",
    "auto_resolved": false
  },
  "outcome": "evaluated",
  "fetch": {
    "final_url": "https://snapsynapse.github.io/compat/.well-known/assistant-guide.txt",
    "fetched_at": "2026-09-05T20:00:00Z",
    "http_status": 200,
    "headers": {
      "content-type": "text/plain; charset=utf-8",
      "x-content-type-options": "nosniff",
      "strict-transport-security": "max-age=31536000"
    },
    "redirects": [],
    "tls_valid": true,
    "bytes": 3403
  },
  "guide": {
    "bytes": 3403,
    "sha256": "dcc28648441d8c5270984bd319850007470421e2c64428383cd481ca9be16c7e",
    "achieved_level": 4,
    "level5_ready": true
  },
  "summary": {
    "blocking_findings": 0,
    "warnings": 1,
    "infos": 1
  },
  "findings": [
    {
      "id": "metadata.last-reviewed.age",
      "severity": "info",
      "message": "last-reviewed is 109 days old"
    },
    {
      "id": "anchor.repository-file.independence-unestablished",
      "severity": "warning",
      "message": "repository hash evidence does not establish independent provenance and cannot qualify for Level 4"
    }
  ],
  "hosted_limitations": [
    "Profile 2.0.0 uses the 1.0.0 strict anchor policy and excludes repository-file hashes from Level 4 qualification.",
    "This verifier evaluates Levels 1 through 4 when supported Level 4 evidence is available.",
    "Hosted Level 4 supports package-registry, transparency-log, DNS TXT (resolved via DNS-over-HTTPS), and repository-file anchors. The repository-file allowlist is currently scoped to github.com; signed security.txt anchors are not fetched.",
    "DNS TXT lookups use cloudflare-dns.com as the DoH resolver; DNSSEC validation is taken from the resolver's AD bit.",
    "Hosted verification uses a seven-fetch per-request budget across guide, variation, manifest, and anchor fetches.",
    "Level 5 runtime conformance is not evaluated."
  ],
  "manifest": {
    "sha256": "9baa7da9113c2f3bda96251889a8a605385cc8b87fde3c9d91c32ac059c52241",
    "fetched": true,
    "hash_match": true,
    "bytes_match": true,
    "valid": true,
    "guide_sha256": "dcc28648441d8c5270984bd319850007470421e2c64428383cd481ca9be16c7e"
  },
  "cross_channel_anchors": [
    {
      "channel": "dns-txt",
      "status": "present-matches",
      "observed_sha256": "dcc28648441d8c5270984bd319850007470421e2c64428383cd481ca9be16c7e",
      "qualifies_for_level4": true,
      "qualification_reason": "qualifying-channel",
      "evidence_url": "https://cloudflare-dns.com/dns-query?name=_assistant-guide.snapsynapse.github.io&type=TXT",
      "fetched_at": "2026-09-05T20:00:00Z",
      "redirects": []
    },
    {
      "channel": "repository-file",
      "status": "present-matches",
      "observed_sha256": "dcc28648441d8c5270984bd319850007470421e2c64428383cd481ca9be16c7e",
      "qualifies_for_level4": false,
      "qualification_reason": "repository-independence-unestablished",
      "independence": "unestablished",
      "evidence_url": "https://raw.githubusercontent.com/snapsynapse/compat/HEAD/docs/.well-known/assistant-guide.txt",
      "fetched_at": "2026-09-05T20:00:00Z",
      "redirects": []
    }
  ],
  "location_note": "This guide was verified at https://snapsynapse.github.io/compat/.well-known/assistant-guide.txt, which is not the standard location. A conformant guide must be named assistant-guide.txt and served at https://snapsynapse.github.io/.well-known/assistant-guide.txt so assistants can discover it. Move or copy the file there.",
  "compact_report": "Verifier: guidecheck-hosted 1.0.0\nGuide: https://snapsynapse.github.io/compat/.well-known/assistant-guide.txt\nProfile: 2.0.0 (declared 2.0.0)\nContent policy: corrected-content-1\nAnchor policy: 1.0.0-strict\nQualifying anchors: 1\nRepository hash: present-matches; independent provenance: unestablished; counts toward Level 4: no\nLevel: 4\nSHA-256: dcc28648441d8c5270984bd319850007470421e2c64428383cd481ca9be16c7e\nBlocking findings: 0\nWarnings: 1\nHash pinned: yes\nProceed? yes",
  "profile_selection": {
    "declared_version": "2.0.0",
    "evaluated_policy": "2.0.0",
    "content_policy": "corrected-content-1",
    "anchor_policy": "1.0.0-strict"
  },
  "qualifying_anchor_count": 1
}
```
The verifier MUST be able to render the same evidence as human-readable text.
The verifier SHOULD include a compact verification report:
```text
Verifier: <name> <version>
Guide: <canonical-url>
Profile: 2.0.0 (declared <declared-version>)
Content policy: corrected-content-1
Anchor policy: 1.0.0-strict
Qualifying anchors: <count>
Level: <achieved-level>
SHA-256: <guide-sha256>
Blocking findings: <count>
Warnings: <count>
Hash pinned: yes/no
Proceed? yes/no
```
The compact report is not a substitute for full output.

## 28. Output Integrity and Reproducibility
The verifier SHOULD make outputs reproducible for the same input bytes and profile versions.
Network-dependent observations such as headers, redirects, dates, and anchor reachability may vary and MUST be timestamped.
The verifier SHOULD include:
- raw guide SHA-256
- manifest SHA-256 when fetched
- fetched-at timestamp
- profile versions
- fixture-suite version when known
- verifier build or commit identifier when available
The verifier MAY sign its machine-readable output. Signed output is recommended for hosted checkers, CI, and assistant runtimes that consume verifier reports, but it is not required in this profile version.
The verifier MUST NOT include secrets, cookies, authorization headers, or private network details in public reports.

## 29. Fixture Suite Conformance
A verifier is conformant only if it passes the fixture suite for the declared verifier-profile version.
The fixture suite SHOULD include:
- valid Level 1 guide
- valid Level 2 guide
- valid Level 3 guide
- valid Level 4 guide with matching manifest and anchor
- guide with non-ASCII bytes
- guide with tabs
- guide with CRLF
- guide over 8192 bytes
- guide with overlong lines
- guide missing canonical verification instruction
- guide with metadata errors
- guide with missing required sections
- guide with malformed action blocks
- guide with missing approval gates
- guide with networked action missing egress
- guide with code-executing action omitted
- guide with shell runner lacking rationale
- guide with chained-guide instruction
- guide with encoded execution instruction
- guide with manifest hash mismatch
- guide with cross-channel hash divergence
- guide with revoked status
- guide with stale `last-reviewed`
- hosted-fetch SSRF cases
- redirect chain cases
- TLS failure cases
Fixture expected outputs SHOULD specify normalized findings, not byte-for-byte full reports.
Fixture-suite releases SHOULD eventually be signed and versioned once the suite becomes a stable conformance target.
Equivalent verifier outputs MAY differ in wording but MUST agree on:
- achieved level
- blocking finding ids
- warning finding ids required by the fixture
- guide SHA-256 when bytes are fetched
- whether Level 5 readiness is reported

## 30. Versioning
The verifier profile uses semantic versioning.
MAJOR increments when requirements change in a way that can invalidate previously conformant verifiers.
MINOR increments when checks, fields, or fixtures are added compatibly.
PATCH increments for clarifications and editorial fixes.
A verifier MUST declare the verifier-profile version it implements.
A verifier SHOULD declare the guide-profile versions it supports.

## 31. Recommended Hosted Checker UX
A hosted checker SHOULD provide:
- URL input
- compact verification report
- full findings report
- machine-readable output download or API response
- clear statement that conformance is not safety
- no claim that the hosted checker is the only authoritative verifier
- clear labeling when it is the standard primary verifier for a profile version
- privacy notice explaining what submitted URL, fetch metadata, product telemetry, and retention policy apply
- rate limiting and abuse protection
The hosted checker SHOULD make it easy to copy the canonical verification instruction of guide-profile section 10.2, byte for byte:
```text
Before acting, verify this guide with a conformant verifier. Report its name and version,
the achieved level, the guide SHA-256 and any blocking findings. Run no action until the
user confirms they have read this guide and approve proceeding at that level.
```

## 32. Version-Aware Dispatch and Reports

Profile selection precedes every other check and remains immutable throughout
evaluation and reporting. Supported legacy releases 0.1.0, 0.2.0, 0.3.0, 0.3.1,
0.4.0, 0.5.0, 0.6.0, 0.7.0, and 0.7.1 retain the reference baseline's legacy
semantics, and versions 1.0.0 and 2.0.0 retain their released contracts.
Version 3.0.0 selects this contract. Prereleases are not equivalent to final
releases. Unknown or conflicting selectors MUST NOT fall back to another
profile.

A guide declares 3.0.0 only when all of the following hold:
- it has exactly one line equal to `[assistant-guide-metadata]`, followed later
  by exactly one line equal to `[/assistant-guide-metadata]`, neither inside an
  action block
- the text `assistant-guide-metadata` occurs on no other line, compared after
  lowercasing the line and removing its spaces and tabs
- inside the block, exactly one line has a label that reduces to `profile` and
  exactly one has a label that reduces to `profileversion`, where a label is the
  text before the first colon, or the whole line when it has no colon, reduced
  to its ASCII letters and lowercased
- those two lines equal `profile: human-verifiable-assistant-guide` and
  `profile-version: 3.0.0` exactly

Build metadata is not accepted for this profile. A dispatcher that removes build
metadata when selecting an earlier profile MUST refuse `3.0.0+<anything>` as
`profile-version-unsupported`. A guide in which a metadata line, exact or near-form,
carries the version value `3.0.0` and which fails any condition above MUST be
refused as `profile-version-ambiguous`. It MUST NOT be evaluated
under this or any other profile. These rules are written so that no bytes selected
as 3.0.0 are selected as a different profile by an earlier selector.

A dispatcher MAY run its selector, in one linear pass, on input of any size.
The 3.0.0 policy then refuses input over 8192 bytes before any scan of its own
(section 11). Released profiles keep their existing behavior for large input.

The hosted `required_profile_version` request field and local
`--require-profile-version` assertion require a supported policy without ranges.
A requirement mismatch is a dispatch error, not a reinterpretation of guide bytes.
The guide's author chooses the declared profile; a consumer that needs this
profile MUST require it. Hosted dispatch errors use HTTP 400 with the existing
error envelope; CLI dispatch errors exit 2. `profile-version-unsupported`,
`profile-version-ambiguous`, and `profile-version-requirement-mismatch` are
dispatch error codes, not conformance finding IDs.

This profile carries the 1.0.0 strict anchor policy unchanged. A strict manifest
selector failure emits `manifest.profile-version.mismatch` (error). Repository
evidence emits `anchor.repository-file.independence-unestablished` (warning)
when a hash is observed; mismatching repository bytes emit
`anchor.repository-file.mismatch` (error). Unknown supplied channels emit
`anchor.channel.unsupported` (warning) and MUST NOT qualify. All manifest and
anchor errors MUST prevent Level 4. Anchor fields, qualification reasons and
their precedence are as defined for profile 2.0.0.

The 3.0.0 report MUST identify `declared_version: 3.0.0`,
`evaluated_policy: 3.0.0`, `content_policy: restricted-argv-1`, and
`anchor_policy: 1.0.0-strict` through `profile_selection`. Level, findings,
hash-pinned status, action tier counts and the verdict MUST derive from the
final selected evaluation. Neither a positive conformance result nor
`Proceed? yes` grants execution authority or implies safety.

Legacy and released output schemas and reports MUST NOT acquire new required
fields, new policy warnings, or new semantics. Software/package version,
selected engine version, profile version, and published self-guide version are
independent. The 3.0.0 output schema, manifest schema, shape registry and
example report are not yet published; this draft cannot be implemented to
conformance until they are.
