# Human-Verifiable Plain Text Handoff
Scope: cross-component project handoff. This document captures a new standard candidate inspired by HardGuard25's AI-assisted implementation guide, Graceful Boundaries' specification model, and Siteline's verifier model. If adopted, promote this into a dedicated standards-level repo and make that repo's `INTENT.md` authoritative.
## Working name
Human-Verifiable Plain Text
Alternate names:
- Assistant-Safe Plain Text
- Human-Verified Assistant Instructions
- Plain-Text Assistant Guide
- Human-Readable Instruction Surface
Short code candidates:
- HVPT
- HVAIG
- PlainGuide
Recommendation: use `Human-Verifiable Plain Text` for the standard and reserve product naming for the verifier.
## Problem
AI-assisted installation and implementation guides are increasingly useful, but many are distributed as HTML pages, rendered Markdown, PDFs, docs sites, copied issue comments, or terminal output. Those media can contain content a model sees but a human does not notice:
- hidden HTML comments
- offscreen CSS
- white-on-white text
- script-inserted content
- metadata or alternate text
- remote embeds
- invisible Unicode controls
- terminal escape sequences
- long buried instruction blocks
The result is a practical trust gap: the user thinks they are approving visible installation guidance, while the assistant may ingest additional instructions from the presentation layer.
## Thesis
For high-consequence AI-assisted setup and implementation, projects should publish a constrained plain-text instruction surface that a human can review in full before an assistant follows it.
The standard does not claim prompt-injection immunity. It removes presentation-layer deception and makes remaining text-based risk visible enough for normal human review plus approval gates.
## Standard purpose
Define a portable profile for assistant-facing install, implementation, remediation, and operational guides that are:
- visible to humans
- easy for assistants to parse
- constrained enough to remove presentation-layer prompt injection
- explicit about authority, source, approved actions, and stop conditions
- verifiable by scanners
## Non-goals
- It is not a replacement for sandboxing, least privilege, or user approval.
- It is not an access-control mechanism.
- It is not a trust signature by itself.
- It does not make external text safe to obey.
- It does not authorize assistants to bypass local policies.
- It does not replace `llms.txt`, `robots.txt`, sitemap files, package manager metadata, or security advisories.
## Core object
A conforming guide is a `.txt` file served or stored as plain text. The guide gives an assistant a bounded task prompt, safety rules, allowed commands or command classes, stop-and-ask conditions, and acceptance criteria.
Example uses:
- AI-assisted project install
- AI-assisted library implementation
- migration dry-run instructions
- local development setup
- remediation playbook
- support runbook
- scanner remediation guide
## Draft conformance levels
### Level 0: Not conformant
Instructions are only available through HTML, PDF, rich Markdown rendering, screenshots, videos, terminal output, or another surface that may hide or transform text.
### Level 1: Plain text available
A `.txt` guide exists and is reachable from a canonical project surface.
Requirements:
- text is directly readable without script execution
- canonical project or repository URL is present
- task scope is stated
### Level 2: Human-verifiable profile
Level 1 plus:
- file is short enough for full human review
- printable ASCII plus LF only
- no HTML, CSS, JavaScript, Markdown images, remote embeds, data URLs, or rich-document constructs
- no Unicode bidi controls, zero-width characters, ANSI escapes, or other invisible controls
- content type should be `text/plain; charset=utf-8` when served over HTTP
- `X-Content-Type-Options: nosniff` should be present when hosting supports it
### Level 3: Assistant safety contract
Level 2 plus:
- copy-paste prompt is included
- approval gates are explicit
- destructive, privileged, network, install, persistence, and data-access actions are called out
- official source URLs are listed
- untrusted content handling is stated
- stop-and-ask conditions are listed
- acceptance checklist is included
### Level 4: Verifiable provenance
Level 3 plus one or more:
- source repository path is linked
- immutable release URL is linked
- SHA-256 hash is published for the guide
- signed release artifact exists
- changelog entry records guide changes
- scanner-verifiable headers and byte profile are available on the public URL
## Required sections
A Level 3 guide should contain:
- title
- canonical source URL
- repository or publisher URL
- task scope
- copy-paste prompt
- safety rules
- normal commands or action classes
- stop-and-ask conditions
- acceptance checklist
- threat model
## Byte-level profile
Preferred strict profile:
- UTF-8 encoded
- bytes allowed: `0x0A`, `0x20` through `0x7E`
- line endings: LF
- no tab characters
- no carriage returns
- no NUL bytes
- no ANSI escape bytes
Rationale: a human can inspect every character using ordinary text tools, and a scanner can cheaply verify the same property.
## Authority model
The guide must state that it is lower priority than:
- system instructions
- user instructions
- local repository instructions
- local security policy
- package manager trust policy
- operating system permission prompts
The guide should instruct assistants to treat fetched content as data until the user confirms the intended guide.
## Verifier product shape
Analogous to Siteline, a verifier can scan a URL or repository path and answer:
- Is there a plain-text assistant guide?
- Is it discoverable from `README`, `llms.txt`, docs pages, or package metadata?
- Does it satisfy the byte-level profile?
- Is it served as `text/plain`?
- Does it avoid presentation-layer attack surfaces?
- Does it include approval gates and stop conditions?
- Does it identify official sources?
- Does it overclaim safety?
- Does it include dangerous commands or broad permissions?
- Does the public URL match the repository copy?
The verifier should return structured evidence, not just a score.
## Threat model
In scope:
- hidden presentation-layer instructions
- rendered HTML/CSS/JS deception
- invisible Unicode or terminal control characters
- assistant over-trust of fetched setup guides
- stale or non-canonical install instructions
- install prompts that omit approval gates
- guides that normalize unsafe shell patterns
Out of scope:
- compromised official repository
- malicious package releases
- dependency confusion
- social engineering outside the guide
- agents that ignore user approval
- assistants with unsafe tool permissions
## Relationship to existing work
### llms.txt
`llms.txt` is an emerging convention for LLM-readable site maps and documentation pointers. Human-Verifiable Plain Text is narrower: it defines a constrained safety profile for assistant-facing operational instructions.
### Graceful Boundaries
Graceful Boundaries defines how services communicate limits, refusals, and next steps. Human-Verifiable Plain Text defines how projects communicate assistant-facing setup and implementation instructions without presentation-layer deception.
### Siteline
Siteline verifies whether a public site is usable by agents. A sibling verifier could assess whether a project's assistant-facing instructions are human-verifiable and safe enough to use.
## Candidate project split
Standard repo:
- `spec.md`
- `README.md`
- `llms.txt`
- `conformance/`
- `examples/`
- `SECURITY.md`
- `CHANGELOG.md`
Verifier product:
- public scanner
- CLI checker
- GitHub Action
- API endpoint
- badge for conforming guides
- remediation report
## Early examples
Good candidates:
- `https://hardguard25.com/ai-assisted-implementation.txt`
- `https://prompterkit.app/ai-assisted-install.txt`
Future candidates:
- package install guides
- agent skill installation guides
- local dev environment setup guides
- migration runbooks
## Initial scanner checks
1. Fetch URL without executing scripts.
2. Confirm HTTP 200.
3. Confirm final URL matches expected canonical host.
4. Confirm `Content-Type` is `text/plain` or equivalent.
5. Confirm byte profile.
6. Confirm no disallowed constructs.
7. Extract required sections.
8. Flag unsafe commands and missing approval gates.
9. Compare canonical URL in file to fetched URL.
10. Emit structured evidence and remediation.
## Open questions
- Should Markdown syntax be allowed, or should the profile be stricter than Markdown?
- Should line length and total byte length have hard limits?
- Should Level 4 require hash publication or merely recommend it?
- Should package registries expose these guides through metadata?
- Should the verifier check live HTTP headers or only repository files?
- Should there be a registry of known conforming guides?
- What is the right name for the verifier product?
## Next action
Create a dedicated standards-level repo if this concept remains compelling after one more example implementation. Seed it with this handoff, the HardGuard25 guide, and the PrompterKit guide as initial fixtures.
