# Threat Register

Status: Working notes. Companion to spec.md and design-rationale.md.

This document enumerates known risk classes in the verifier-guide-agent setup defined by GuideCheck's Human-Verifiable Assistant Guide profile. Some risks are mitigated by the current design, some are reduced, and some remain outside the scope of the profile. The list exists to guide documentation, fixture design, hosted-checker hardening, and future spec work.

Risks here are not redundant with section 27 of the spec (Residual Threats). Section 27 names the high-level out-of-scope categories that adopters must understand. This document records the operational risk classes underneath those categories that fixture authors, verifier implementers, and runtime designers must address in their own work.

## Network path risks

- Man-in-the-middle between the verifier and `assistant-guide.txt`: mitigated by HTTPS, TLS validation, no plaintext HTTP above Level 0, hash verification, and cross-channel anchors. Residual risk remains if TLS trust is compromised or the attacker also controls enough provenance channels.
- Man-in-the-middle between the agent and `assistant-guide.txt`: mitigated only if the agent verifies the same canonical URL and pins the same guide hash before acting. Residual risk remains when the agent fetches the guide separately and does not compare bytes against verifier output.
- Man-in-the-middle between the verifier and manifest: reduced by HTTPS and manifest hash checks, but a same-origin manifest is forge-equivalent to the guide. This is why Level 4 requires an independent cross-channel hash.
- Man-in-the-middle between the verifier and independent anchors: reduced by the independent control-plane model, but not eliminated. DNS, package registry, repository, and signed security.txt channels each have their own transport and account risks.
- Enterprise TLS interception: a corporate proxy may present a locally trusted certificate and rewrite guide or verifier traffic. This may be intentional local policy or an attack. The verifier can report certificate details, but cannot determine organizational intent.
- DNS poisoning or resolver compromise: a verifier or agent may be directed to the wrong host before TLS validation. TLS blocks many cases, but DNS compromise plus certificate issuance or host compromise remains dangerous.
- BGP or routing attacks: traffic may be routed through an attacker. HTTPS and independent hashes reduce content substitution risk but do not remove availability or traffic-analysis risk.
- TLS certificate authority compromise or mis-issuance: an attacker with a valid certificate for the target domain can substitute content unless independent hash anchors or signatures catch the change.
- HSTS absence or downgrade pressure: the spec rejects plaintext HTTP above Level 0, but users or nonconformant agents may still follow downgraded links outside the profile.

## Origin and hosting risks

- Web host compromise: an attacker controlling the guide host can publish a conforming malicious guide. Level 4 raises the forge cost through independent anchors, but cannot prove publisher intent.
- CDN or edge cache poisoning: a verifier and an agent may receive different bytes from different edge locations or cache states. Hash pinning and byte comparison reduce this, but availability and inconsistency remain.
- Stale cache serving old guides: an old guide may remain reachable after revocation or supersession. `status`, `valid-until`, and hash rotation help only if the verifier and agent fetch fresh enough bytes and honor status.
- Split-horizon DNS or regional content variation: verifiers in different locations may fetch different guide bytes. The profile can detect hash differences when anchors are stable, but cannot force global hosting consistency.
- Content negotiation differences: hosts may return different bytes based on user agent, Accept headers, locale, compression, or IP. Verifiers should use simple fetches and report headers, but the publisher must avoid variant responses for the guide.
- Redirect manipulation: redirects can move verification to a different host or path. The spec treats same-registered-domain redirects as findings and cross-registered-domain redirects as blocking at Level 2 and above.
- Domain expiration or takeover: a previously valid canonical URL can later resolve to a new operator. Cross-channel anchors, signatures, and last-reviewed dates reduce but do not eliminate this risk.
- Subdomain takeover: an abandoned host used for guides, manifests, or anchors may be claimed by an attacker. Verifiers can detect hash divergence, not ownership history.

## Provenance anchor risks

- Same-origin manifest forgery: if the guide and manifest live on the same compromised host, both can be changed together. This is explicitly why same-origin manifest alone is not enough for Level 4.
- Independent channel compromise: DNS, package registry, repository, or signing-key compromise can allow a malicious guide to pass Level 4. The design raises the attack cost; it does not make compromise impossible.
- Multiple-anchor disagreement: anchors may disagree because of attack, rotation, cache delay, or publisher error. The verifier can fail Level 4 and report evidence, but humans still need to decide whether to wait, investigate, or stop.
- Repository branch mutation: a repository URL that points to a branch rather than an immutable commit can change after verification. Immutable source URLs or commit identifiers reduce this risk.
- Package registry metadata drift: registry metadata may lag the public guide or reference a guide for a different package version. Verifiers can compare `applies-to`, but cannot infer publisher intent in every ecosystem.
- DNS TXT stale records: low TTLs help, but resolvers may cache old TXT records. Hash rotations can produce temporary false failures or, in worse cases, stale trust signals.
- Signed security.txt key compromise: a signed security.txt anchor is only as strong as the signing key and key-management process.
- Signature without transparency: a valid signature proves key control, not that a change was reviewed or publicly visible. This motivates possible future transparency-log requirements.

## Verifier implementation risks

- Malicious verifier: a verifier can lie about conformance, hide findings, or report a fake hash. Fixture-suite conformance reduces accidental divergence, not malicious behavior.
- Compromised hosted checker: a hosted checker can return false reports or leak URLs being checked. Users and agents should know which verifier was used and should not treat the hosted checker as an oracle.
- Buggy verifier parser: malformed metadata, action blocks, or edge-case bytes may be parsed incorrectly. The fixture suite should include parser-confusion cases.
- Verifier version skew: a verifier may implement an older profile version and miss newer requirements. Reports must include guide-profile and verifier-profile versions.
- Fixture-suite compromise: if official fixtures or expected findings are compromised, implementations can be trained to the wrong behavior. Fixture releases should eventually be signed.
- Heuristic false negatives: prose-level attacks, backdoor chaining, and risky command semantics cannot be perfectly detected. Heuristics should warn, but human review remains required.
- Heuristic false positives: a verifier may over-warn and train users to ignore findings. Severity calibration and fixture discipline matter.
- Verifier output tampering: the report shown to the user or agent may be altered after generation. Signed verifier output may be worth considering later, especially for hosted checkers and CI.
- UI rendering bugs in verifier reports: even if the guide is ASCII, the report UI may render findings, URLs, or snippets in confusing ways. Reports should escape guide content and avoid active links where they could mislead.
- Hosted-checker SSRF: a public checker that fetches user-supplied URLs can be abused to reach private networks or metadata services. The verifier conformance profile adds network safety requirements, but implementation defects remain possible.
- Hosted-checker privacy leakage: submitting a guide URL to a hosted checker reveals interest in a project, version, or internal initiative. Public-web scope accepts this for the hosted flow, but the checker should disclose any retained URL, host, path, fetch, agent-category, expected-level, achieved-level, or outcome telemetry and should avoid raw URLs, query strings, prompts, model responses, IP addresses, and stable visitor identifiers unless explicitly justified.
- Denial of service against verifier: slow responses, large responses, redirect loops, many anchors, and decompression bombs can exhaust verifier resources. Timeouts and read limits reduce but do not eliminate abuse.

## Agent and runtime risks

- Agent fetches different bytes than verifier: if the agent re-fetches the guide and does not compare hash or pinned bytes, it may act on content the verifier did not evaluate.
- Time-of-check time-of-use gap: a guide can change between verification, user review, and action execution. Level 4 hash pinning and Level 5 session pinning reduce this gap.
- Nonconformant agent behavior: an agent may execute prose, ignore action blocks, batch approvals, skip verification, or follow chained guides. Level 5 defines runtime enforcement, but the file format cannot force an arbitrary agent to comply.
- Raw prompt ingestion: if the guide is pasted into an agent as instructions rather than parsed as data, prose can influence behavior outside action blocks. The invocation prompt and Level 5 parser-mediated execution reduce this risk.
- Long-term memory contamination: an agent may store guide content, commands, or approvals and reuse them later outside the original context. The spec prohibits this without reconfirmation, but enforcement belongs to the runtime.
- Approval ledger confusion: action ids may collide across sessions or guides. Level 5 scopes approvals by guide hash and action id, but lower levels rely on assistant behavior.
- Tool-permission expansion: a guide can ask for broader permissions in plain text even if prohibited. A verifier can flag the request, but the runtime and user must refuse it.
- Shell and environment ambiguity: a displayed command can behave differently depending on shell, PATH, aliases, working directory, operating system, or environment variables. `runner`, `cwd`, and `env` reduce this, but command semantics remain environment-dependent.
- Package lifecycle execution: package managers and build tools may run scripts that are not visible in the guide. The `code-executing` class and verifier warnings surface this risk, but cannot prove the dependency graph is safe.
- Network egress mismatch: a guide may declare narrow egress while the runtime cannot enforce it. Level 5 requires disclosure when egress is advisory, but network enforcement must come from the runtime or host.
- Local malware or compromised workstation: malware can alter guide bytes, verifier output, assistant behavior, clipboard content, terminal output, or executed commands. This profile does not defend against a compromised endpoint.

## User and workflow risks

- Verifier-as-oracle misuse: users may treat a green report as permission to skip reading. The spec repeatedly says conformance is not safety, but behavior cannot be forced by the artifact.
- Confirmation fatigue: even a compact ceremony can become ritual. The 8 KiB cap, action blocks, and approval threshold reduce fatigue but do not eliminate it.
- Warning fatigue: too many warnings may cause users to ignore all warnings. Verifier design must keep blocking findings distinct from non-blocking warnings.
- Phishing through recommended verifier URL: a malicious guide may name a verifier that looks official but is not. The spec allows recommended verifiers but requires that no verifier be presented as uniquely authoritative.
- Typosquatted verifier or project domains: humans may not notice lookalike ASCII domains. ASCII-only removes Unicode homoglyphs inside the guide, but not all domain-confusion attacks.
- Misleading but conforming prose: a guide can accurately conform while describing dangerous commands in reassuring language. Mechanical checks cannot determine intent.
- User approves despite blocking findings: the assistant should stop when findings are blocking, but a human may override in nonconformant tooling. This is outside the profile's enforcement ability.
- Clipboard substitution: copying commands, URLs, or approval text through the clipboard can be altered by local software. Verbatim display helps only if the runtime executes the displayed bytes.

## Availability and failure-mode risks

- Verifier unavailable: if the recommended verifier is down, users may skip verification or use an unknown checker. The spec permits alternate conformant verifiers to avoid single-service dependency.
- Anchor unavailable: DNS, repository, registry, or security.txt anchors may be temporarily unreachable. The verifier can report this, but availability failures can block Level 4.
- Revocation not reachable: a revoked guide may remain cached or mirrored while its supersession signal is unavailable. Short validity windows and cross-channel anchors reduce the window.
- Clock skew: stale or future dates depend on the verifier's clock. Verifiers must report evaluation time, but clock trust is external.
- Rate limiting and abuse controls: hosted checkers may block legitimate checks under load or attack. This affects usability more than artifact integrity, but users may respond by skipping verification.

## Residual trust boundaries

- The profile verifies form, structure, and selected provenance signals. It does not verify publisher benevolence.
- Level 4 makes silent guide substitution harder. It does not make malicious official content safe.
- Level 5 makes runtime behavior more constrained. It does not make command effects safe across every environment.
- A conformant verifier is a testable implementation claim, not a trust claim.
- A recommended hosted checker improves usability, but it is not a root of trust.
- The human remains part of the control loop: reading the guide, understanding the reported level, judging the command intent, and deciding whether the surrounding operational controls are adequate.

## Mitigations adopted in v0.1

The current draft adopts several mitigations that reduce the verifier-guide-agent gap without turning the standard into a registry or a hosted-service dependency.

- Agent byte agreement: Level 5 runtimes compare the guide bytes they will use against the verifier-reported SHA-256 and stop on mismatch. This directly addresses the case where the verifier and agent fetch different bytes.
- Compact report hash display: compact verification reports include the guide SHA-256, making byte identity visible and auditable.
- Approval-ledger binding: Level 5 approval ledgers bind approvals to guide URL, guide hash, verifier name, verifier version, achieved level, and action id. This reduces cross-guide and cross-session approval confusion.
- No ambient credentials for public guide fetches: agents, like verifiers, fetch public guides without cookies, browser session state, authorization headers, or other ambient credentials. This reduces credential leakage and user-specific guide variants.
- Recommended-verifier domain discipline: guides SHOULD recommend a verifier on the same registered domain as the guide, explicitly mark third-party verifiers, or use the standard primary verifier. This reduces verifier phishing while preserving a default hosted checker for usability.
- Standard primary verifier exception: the standard primary verifier published by the standards project is exempt from off-domain warnings. The exception is narrow: it avoids false warnings for the standard's default checker without making that checker the only authoritative verifier.
- Domain mismatch warnings: verifiers warn when canonical URL, repository URL, manifest URL, or recommended verifier live on unrelated registered domains without explanation.
- Content-variation checks: verifiers may re-fetch with a different harmless request profile and warn if bytes differ. This catches user-agent targeting, content negotiation surprises, and some CDN inconsistencies.
- Safer verifier discovery: DNS TXT and signed security.txt may identify recommended verifier URLs, giving publishers a way to anchor the verifier recommendation outside the guide itself.

## Future hardening

The remaining items are intentionally left as future hardening because they add operational burden or require ecosystem maturity:

- Signed verifier reports would reduce report tampering and help CI or assistant runtimes consume hosted-checker output.
- Transparency logs for guide manifests would reduce silent malicious rotation and post-compromise history rewriting.
- Signed fixture-suite releases would protect the verifier-conformance test corpus once implementations depend on it.
- Level 5 runtime attestation would make runtime conformance claims more testable and less self-asserted.
