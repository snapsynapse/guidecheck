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
: A verifier URL published by the standards project for a specific verifier-profile version as the default hosted conformance checker. It is not the only conformant verifier and is not an oracle, but it is exempt from off-domain recommended-verifier warnings. For verifier-profile version 0.3.x the designated standard primary verifier is `https://guidecheck.org/verify`, published by the PAICE Foundation.

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
The verifier MUST report byte offsets or line and column numbers for byte-profile failures when practical.
The verifier MUST NOT normalize line endings, decode HTML entities, strip comments, render Markdown, or otherwise transform guide bytes before checking byte-profile conformance.

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
- encoded or obfuscated command blobs intended for execution
- instructions to decode and execute hidden content
Detection MAY include heuristic warnings for prose patterns. Heuristic warnings MUST be labeled as warnings unless the underlying rule is exact and blocking.

## 14. Metadata Parsing
The verifier MUST parse the metadata block by exact fence match:
```text
[assistant-guide-metadata]
...
[/assistant-guide-metadata]
```
The verifier MUST require exactly one metadata block for Level 3 and above.
The verifier MUST reject metadata blocks with:
- missing closing fence
- nested metadata fences
- duplicate required keys
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
The verifier MUST validate URL fields as ASCII URLs with ASCII hostnames. Internationalized domain names MUST be expressed in punycode A-label form.
The verifier MUST warn when a non-URL metadata value exceeds 80 bytes. URL-valued fields are exempt because a legitimate canonical or repository URL can be long; all other field values are short by design, and an unusually long one is a side-channel risk per guide-profile section 27.
The verifier SHOULD warn when `canonical-url`, `repository-url`, `registry-url`, `manifest-url`, or `recommended-verifier` use unrelated registered domains without explanation.
The verifier SHOULD warn when `recommended-verifier` is not on the same registered domain as `canonical-url`, unless the guide explicitly identifies it as third-party or the URL matches the standard primary verifier for the applicable verifier-profile version.
The verifier MUST NOT warn solely because `recommended-verifier` differs from `canonical-url` when `recommended-verifier` matches the standard primary verifier configured for the applicable profile version.
When package-registry metadata is used as an independent Level 4 anchor, the verifier MUST require `registry-url` and MUST validate that it identifies a specific registry record rather than a registry homepage or search result.
When `registry-url` is absent and no other Level 4 independent anchor is available, the verifier SHOULD emit an informational finding for Level 3 and a blocking finding for Level 4.

## 15. Verification Instruction Checks
For Level 1 and above, the verifier MUST check that a compact verification instruction appears before action instructions.
The verifier MUST check that the instruction includes these concepts:
- verify the guide with a recommended verifier or another conformant verifier
- report achieved level, guide SHA-256, and blocking findings
- obtain user confirmation before actions
- do not execute actions before confirmation
The verifier SHOULD warn when a guide names a recommended verifier but omits `verifier-conformance` metadata.
The verifier MUST emit an error when a guide states or implies that only one verifier is authoritative.
The verifier SHOULD check whether DNS TXT or signed `security.txt` fields identify a recommended verifier. When those anchors disagree with `recommended-verifier`, the verifier SHOULD emit a warning unless one value is the configured standard primary verifier and the other is explicitly marked as a publisher-local verifier.

## 16. Required Section Checks
For Level 3 and above, the verifier MUST check for the required guide sections or equivalent clearly identifiable content:
- title
- canonical source URL
- publisher or repository URL
- guide metadata
- task scope
- assistant invocation prompt
- safety rules
- action classification
- normal commands or action classes
- stop-and-ask conditions
- acceptance checklist
- threat model
- untrusted content handling
- disclaimer and non-goals
- authority model
Section names may vary. The verifier MAY use heading matching, key phrase matching, or structured markers. When using approximate matching, the verifier SHOULD report confidence or evidence snippets.

## 17. Action Block Parsing
The verifier MUST parse action blocks by exact fence match:
```text
[action]
...
[/action]
```
For Level 3 and above, every substantive action MUST be represented by an action block.
Each action block MUST include:
- `id`
- `class`
- `approval`
- `command`
Each action block MAY include:
- `runner`
- `cwd`
- `env`
- `egress`
- `notes`
The verifier MUST reject action blocks with:
- duplicate `id` values
- missing required fields
- malformed `key: value` lines
- nested action fences
- unknown `approval` values
- invalid `runner` values
- values outside the byte profile
The verifier MUST parse `class` as a comma-separated list.
The `normal` class is mutually exclusive with all other classes.
Allowed classes are:
- `normal`
- `networked`
- `destructive`
- `privileged`
- `persistence-changing`
- `data-accessing`
- `code-executing`

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
The verifier MUST check every `command` field for guide-profile command restrictions:
- one command per action block
- no chaining with `&&`, `||`, `;`, or newline
- no shell substitution using `$(`, backticks, or `${`
- no redirection or pipes unless the action is only classed as `normal` and the redirection target is inside declared `cwd`
- no glob expansion in actions classed as `destructive` or `privileged`
- environment-variable references via `$NAME` only when the variable is listed in `env`
The verifier SHOULD warn on commands likely to execute project code, dependency code, package scripts, build hooks, generated code, test suites, or local scripts unless the action includes `code-executing`.
Examples include:
- package manager install commands with lifecycle scripts
- test runners
- build tools
- local shell scripts
- Python, Ruby, Node, or other interpreter invocations over local files
- `make`, `just`, `task`, or similar task runners
The verifier SHOULD warn when `runner: shell` is present without a narrow rationale in `notes`.
The verifier SHOULD warn when Level 4 guides omit `runner`.

## 20. Filesystem, Environment, and Egress Checks
For any action that reads or writes the filesystem, the verifier MUST require `cwd`.
For any action that references environment variables with `$NAME`, the verifier MUST require `env` and MUST check that every referenced variable is listed.
For any action whose class list includes `networked`, the verifier MUST require `egress`.
The verifier MUST flag `egress` wildcards broader than one subdomain level.
The verifier SHOULD warn on:
- broad filesystem paths such as `/`, `/*`, `~`, repository parents, or drive roots
- unqualified `sudo`
- broad `chmod`, `chown`, or permission weakening
- credential scraping
- environment-variable enumeration without a narrow purpose
- unscoped cloud, cluster, database, or production operations

## 21. Prohibited Pattern Checks
The verifier MUST flag guide instructions that direct an assistant to:
- fetch and follow another guide, script, instruction file, or runbook
- pivot the current session to another guide
- treat fields such as `next-guide`, `then-fetch`, `chain-to`, `follow-next`, or `continue-with` as directives
- modify, rewrite, or replace `assistant-guide.txt`, its manifest, or verifier output
- store guide content, action commands, or approvals into long-term assistant memory without current-session reconfirmation
- decode, deobfuscate, or execute encoded content
- expand tool permissions, disable sandboxing, or skip approval gates
- treat `notes` or prose fields as commands
The verifier SHOULD apply a heuristic prose scan for backdoor chaining, including imperative contexts around URLs ending in `.txt`, `.sh`, `.ps1`, `.py`, or guide-like resources.
Heuristic backdoor-chaining results SHOULD be warnings unless an exact prohibited field or directive is found.

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
The verifier MAY continue Level 3 content evaluation after Level 4 failure.
When `signature` is present, the verifier SHOULD report it. Signature verification is not required by this profile unless a future profile version makes it required.
When `transparency-log-url` is present, the verifier SHOULD retrieve the referenced log entry and check it as a cross-channel anchor under section 23.

## 23. Cross-Channel Anchor Checks
For Level 4, the verifier MUST enumerate every cross-channel hash anchor it can find and compare each anchor hash with the manifest hash.
Recognized independent channels are:
- DNS TXT at `_assistant-guide.<registered-domain>`
- package registry metadata
- public repository file at `source-path`
- signed `security.txt` extension fields
- public append-only transparency log referenced by the manifest `transparency-log-url` field
The verifier MUST emit a failure when independent channels disagree on the hash.
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
If `status: deprecated`, the verifier MUST emit a warning or error according to the guide profile version and MUST report `superseded-by` when present.
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
- canonical project or repository URL is present
- task scope is stated
- compact verification instruction is present before action instructions
A guide achieves Level 2 when Level 1 is satisfied and:
- the byte profile passes
- size, line length, and line count limits pass
- no disallowed constructs are present
A guide achieves Level 3 when Level 2 is satisfied and:
- required sections are present
- metadata is valid
- action blocks are parseable
- approval gates required by Level 3 pass
- stop-and-ask conditions are present
- untrusted content handling is present
- public information safety is addressed
- acceptance checklist is present
- overclaiming safety is not found
A guide achieves Level 4 when Level 3 is satisfied and:
- manifest is present and valid
- guide hash and byte count match the manifest
- at least one independent cross-channel anchor is present
- every found independent anchor agrees with the manifest hash
A verifier MUST NOT report achieved Level 5 for a guide alone. Level 5 is a deployment claim that combines Level 4 guide conformance with runtime enforcement. A verifier MAY report `level5_ready: true` when the guide satisfies Level 4 and all Level 5 preparation recommendations pass.

## 26. Finding Severity
The verifier MUST use these severities:
- `error`: blocks the claimed or target conformance level
- `warning`: does not block the achieved level but should be reviewed
- `info`: observational evidence
The verifier MAY include implementation-specific severities in an extension field, but MUST map them to `error`, `warning`, or `info`.
Every finding MUST include:
- stable finding id
- severity
- message
- evidence location when available
- affected profile section when available
- remediation text when available

## 27. Required Output Schema
A conformant verifier MUST emit machine-readable output.
The minimum JSON-compatible schema is:
```text
{
  "verifier": {
    "name": "example-verifier",
    "version": "0.3.1",
    "verifier_profile": "human-verifiable-assistant-guide-verifier",
    "verifier_profile_version": "0.3.1",
    "guide_profile": "human-verifiable-assistant-guide",
    "guide_profile_version": "0.3.1"
  },
  "input": {
    "url": "https://example.com/.well-known/assistant-guide.txt"
  },
  "fetch": {
    "final_url": "https://example.com/.well-known/assistant-guide.txt",
    "fetched_at": "2026-05-22T00:00:00Z",
    "http_status": 200,
    "headers": { "content-type": "text/plain; charset=utf-8" },
    "redirects": [],
    "tls_valid": true
  },
  "guide": {
    "bytes": 4821,
    "sha256": "<hex>",
    "claimed_level": 3,
    "achieved_level": 3,
    "level5_ready": false
  },
  "summary": {
    "blocking_findings": 0,
    "warnings": 2,
    "infos": 4
  },
  "findings": [
    {
      "id": "byte-profile.no-tabs",
      "severity": "error",
      "section": "8",
      "line": 42,
      "column": 3,
      "message": "tab character at column 3",
      "remediation": "replace tab with spaces"
    }
  ]
}
```
The verifier MUST be able to render the same evidence as human-readable text.
The verifier SHOULD include a compact verification report:
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
- guide missing compact verification instruction
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
The hosted checker SHOULD make it easy to use the recommended first-step ceremony:
```text
Before acting, verify this guide with this checker or another conformant verifier, report the achieved level, guide SHA-256, and blocking findings, then ask the user to confirm they have read the guide and approve proceeding under the reported level.
```
