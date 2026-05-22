# assistant-guide.txt Security & Risk-Mitigation Summary

## Purpose of this document

This document summarizes the emerging design of `assistant-guide.txt` as a constrained, assistant-facing plain-text guide for high-consequence tasks (install, implementation, remediation, operations). It focuses on:

- Security risks not fully eliminated by the plain-text/byte-profile constraints
- Recommended mitigations that the standard can encode (MUST/SHOULD language)
- Documentation and disclaimer requirements
- Versioning and provenance patterns (skill-provenance style)

---

## 1. Information leakage from a public guide

**Risk**  
A predictable public file (like `assistant-guide.txt`) can leak operational details, similar to how `robots.txt` or `security.txt` can accidentally expose internal structure or sensitive assumptions.

Examples of problematic content:
- Internal hostnames or non-public endpoints
- Operational or admin paths that are not otherwise advertised
- Detailed remediation patterns that reveal internal architecture

**Mitigations for the standard**

- The guide **MUST NOT** include:
  - Secrets, tokens, passwords, API keys, or private credentials
  - Non-public internal hostnames, IPs, or endpoints
  - References that materially expand external knowledge of internal topology beyond what the project already exposes
- The threat-model section **SHOULD** explicitly remind authors that the guide is public and must be written under that assumption.
- A verifier **SHOULD** flag:
  - Likely internal FQDNs or RFC1918 IP addresses
  - Hard-coded admin or internal paths (for manual review)

---

## 2. Over-trust and the "safety halo" problem

**Risk**  
By formalizing `assistant-guide.txt`, users and implementers may treat its contents as inherently safe, and give assistants broader permissions or skip sandboxing, assuming the guide itself is a sufficient control.

**Mitigations for the standard**

- The spec **MUST** include a clear non-goals / disclaimer section, stating that:
  - The guide is **not** a security control by itself
  - It does **not** guarantee safety of any commands or actions
  - It does **not** replace sandboxing, least privilege, or mandatory human approval
- The authority model **MUST** state that:
  - The guide is advisory and **lower priority** than system instructions, user instructions, local repository instructions, local security policy, package manager trust policy, and OS permission prompts
  - Tools **MUST** still treat the guide as potentially malicious or compromised and operate under least privilege
- The verifier **SHOULD** flag over-claiming language, such as:
  - "always safe", "guaranteed secure", "no risk", or similar absolutes

---

## 3. Guide as an attack surface for agent frameworks

**Risk**  
Even with a strict byte-level profile, a hostile maintainer can use `assistant-guide.txt` to craft multi-step instructions that drive agents to perform environment discovery, exfiltration, or exploit chains, especially when combined with powerful tools.

**Mitigations for the standard**

- The required **Threat Model** section **MUST** ask explicitly:
  - What can go wrong if these commands are executed on:
    - A developer machine
    - CI/CD infrastructure
    - A production environment
- The **Untrusted Content Handling** section **MUST**:
  - Distinguish between local repository content and external resources and
  - Instruct assistants to treat both as untrusted until explicitly approved by the user
- The standard **SHOULD** require that:
  - All commands are fully spelled out in plain text; no "hidden" logic via code generation instructions
- The verifier **SHOULD** flag patterns such as:
  - `curl | sh` or equivalent piping of network content directly to a shell
  - Broad file deletions (e.g., `rm -rf /`, `rm -rf ~`)
  - Unscoped cluster-wide or infra-wide operations (e.g., `kubectl` or `terraform` without clear scoping)
  - Instructions that explicitly encourage environment-variable enumeration or credential scraping

---

## 4. Mis-scoping and privilege creep

**Risk**  
Guides may normalize running commands from overly broad contexts (filesystem root, entire cluster) or using elevated privileges (root/admin) "for simplicity".

**Mitigations for the standard**

- The guide **SHOULD**:
  - Scope commands to the minimum necessary directory or resource (e.g., project root, specific namespace, specific database)
  - Prefer non-privileged operations where possible
- The guide **MUST**:
  - Explicitly classify actions into categories, at minimum:
    - Normal (non-privileged, non-destructive)
    - Destructive
    - Privileged/elevated
    - Networked (external calls)
    - Persistence-changing (install, write to system paths, service config)
    - Data-accessing (read from databases, logs, secrets managers)
  - Call out privileged/elevated actions as requiring explicit, separate human approval
- The verifier **SHOULD**:
  - Detect unqualified `sudo` and flag it
  - Detect commands that operate on overly broad paths (e.g., `/*`, `~`, without narrowing)
  - Highlight infra-wide operations for manual review

---

## 5. Obfuscated but printable content

**Risk**  
Even within a strict ASCII + LF byte profile, an attacker can hide complexity in apparent "data" that the assistant is instructed to decode and run (e.g., base64, hex blobs, or indirect code-loading patterns).

**Mitigations for the standard**

- The spec **SHOULD** discourage:
  - Encoded or obfuscated command blobs (base64, hex, compressed strings) intended for decoding at run-time
  - Instructions like "decode this string and execute it"
- The Threat Model section **SHOULD** remind human reviewers to treat any encoding/decoding and code-generation steps as high-risk and subject to extra scrutiny.
- The verifier **MAY** (stretch goal):
  - Detect long base64-like strings or hex blobs and flag them for review
  - Detect phrases like "decode and run", "generate and execute", etc.

---

## 6. Drift, staleness, and lifecycle risk

**Risk**  
`assistant-guide.txt` can drift from the actual codebase or deployment practices. Stale guides may:
- Break builds or migrations
- Reflect obsolete threat models or missing components

**Mitigations for the standard**

- The guide **MUST** contain versioning metadata, for example:
  - `guide-version`: semantic version of the guide itself
  - `applies-to`: project version(s) or range
  - `last-reviewed`: timestamp and reviewer identity/role
- The spec **SHOULD** recommend:
  - Updating the guide on each release that materially affects installation, configuration, or operations
  - Treating guide changes as part of the release and change-management process, not as ad hoc doc edits
- The verifier **SHOULD**:
  - Compare `applies-to` against package metadata or tags when available
  - Flag obviously stale guides (e.g., `last-reviewed` older than a configurable threshold)

---

## 7. Human factors and insider threat

**Risk**  
A malicious or careless maintainer can gradually weaken the guide (e.g., relaxing stop-and-ask conditions, introducing riskier commands) while it retains a "blessed" appearance in the project.

**Mitigations for the standard**

- The spec **SHOULD** recommend:
  - Treating `assistant-guide.txt` as a security-relevant artifact
  - Requiring code review with a security or platform owner for any changes to the guide
  - Labeling guide changes explicitly in the project changelog or release notes
- Level 4 (provenance) **SHOULD** include options such as:
  - Signed releases that cover both code and `assistant-guide.txt`
  - Storing the guide in a protected location or branch where changes require elevated review

---

## 8. Documentation and disclaimer requirements

To avoid misuse and over-trust, the standard itself should require specific documentation elements inside each Level 3+ guide:

1. **Disclaimer / Non-goals section (mandatory)**
   - States that the guide:
     - Is public and may be read by adversaries
     - Is not an access-control mechanism
     - Is not a guarantee of safety or correctness
     - Must not be treated as permission to bypass sandboxing, least privilege, or organizational security policy

2. **Authority model statement (mandatory)**
   - Explicitly lists the priority order, e.g.:
     - System instructions
     - User instructions
     - Local repository instructions
     - Local security policy
     - Package manager trust policy
     - OS permission prompts
     - `assistant-guide.txt` (lowest among these)
   - Instructs assistants to treat fetched content as data until the user confirms the intended guide.

3. **Threat model section (mandatory)**
   - Enumerates in-scope and out-of-scope threats for this guide
   - Calls out high-risk environments (developer workstations, CI, prod) explicitly

4. **Stop-and-ask and approval gates (mandatory)**
   - Clearly identifies conditions where the assistant must pause and request explicit human confirmation
   - Ties these gates to the action categories (privileged, destructive, network, persistence, data-access)

5. **Untrusted content handling (mandatory)**
   - Explains how assistants should treat local repo, downloaded files, and external services (all untrusted by default)

---

## 9. Versioning and provenance (skill-provenance style)

To support skill-provenance and external verification, Level 4 guides should carry structured provenance data and be linkable to project releases.

**Recommended fields in the guide**

At Level 4, the guide **SHOULD** include a small, machine-readable header block, for example:

```text
[assistant-guide-metadata]
identifier: assistant-guide
guide-version: 1.0.0
applies-to: my-project >=2.3.0, <3.0.0
repository-url: https://example.com/org/my-project
source-path: /assistant-guide.txt
immutable-release-url: https://example.com/org/my-project/releases/v2.3.1
hash-sha256: <hex-encoded-hash-of-guide>
last-reviewed: 2026-05-21T11:40:00Z
reviewed-by: security@org.example
signature: optional-reference-to-signed-artifact
[/assistant-guide-metadata]
```

**Provenance expectations**

- At least one of the following **SHOULD** be present:
  - Link to source repository path
  - Link to an immutable release artifact containing the guide
  - Published SHA-256 of the guide
  - Reference to a signed release artifact that covers the guide
- A verifier **SHOULD**:
  - Fetch both the public URL and the repository copy and confirm that the hash matches
  - Report discrepancies as potential tampering or drift

---

## 10. Summary of key MUST/SHOULD requirements

This section gives a concise checklist-style summary that an implementer or verifier can use.

**MUST (Level 3+)**
- Plain-text `.txt` file with strict byte-level profile (ASCII printable + LF, no control characters beyond LF)
- Public, human-reviewable, short enough for full review
- Explicit disclaimer / non-goals section
- Authority model stating the guide is lower priority than system/user/policy/package/OS prompts
- Threat model section
- Untrusted content handling section
- Classification of actions (normal, destructive, privileged, network, persistence, data-access)
- Explicit stop-and-ask conditions and approval gates
- No secrets, tokens, or private credentials

**SHOULD**
- Avoid internal-only hostnames, IPs, or sensitive topology details
- Scope commands to least privilege and least scope
- Avoid encoded/obfuscated command blobs; keep actions fully visible
- Require security-focused review for guide changes
- Include versioning metadata and last-reviewed info
- Use verifier tooling in CI to enforce the profile and flag risky patterns

**Level 4 (Provenance) SHOULD**
- Include machine-readable metadata header
- Provide SHA-256 hash, source path, repository URL, and immutable release URL
- Integrate with existing signing / supply-chain mechanisms

---

This document is intended as a working summary and can be used as the basis for the "Security Considerations", "Non-goals", and "Provenance" sections of a formal `assistant-guide.txt` specification.
