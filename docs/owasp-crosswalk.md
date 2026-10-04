# GuideCheck and OWASP GenAI Crosswalk

Status: non-normative crosswalk, checked 2026-10-03. Advisory only: nothing
in this note adds, changes, or implies a conformance requirement. The
normative documents are the released profiles under `profiles/` and the
legacy `spec.md` and `verifier-conformance.md`. This note does not claim
OWASP review, endorsement, or acceptance of GuideCheck.

This note maps the threats GuideCheck addresses to two OWASP GenAI Security
Project resources:

- the OWASP Top 10 for Agentic Applications for 2026 (ASI identifiers), used
  here as the threat vocabulary
- the Agent Control Standard (ACS) v0.1.0, donated to the OWASP GenAI
  Security Project and announced on 2026-09-01, used here as the runtime
  enforcement target

OWASP announced the LLM Top 10 2026 on 2026-09-01. Its resource page is dated
August 3. The exact identifiers remain unverified: on October 3 the linked
download returned an HTML page titled `No Access`, not the advertised document.
The initiative page lists LLM workstream names but does not establish their
edition. Do not relabel 2025 identifiers as 2026. This bounded source-access
gap is tracked in the [roadmap](../roadmap.md#current-work-queue-reconciled-2026-10-03).

## Control status

Each row states what GuideCheck delivers today and what it does not.

- Delivered: a verifier checks the guide bytes today and emits the listed
  finding ids. Static fixtures pin the expected result.
- Runtime-dependent: GuideCheck supplies a declared contract, but only a
  conformant runtime can enforce it. No Level 5 runtime conformance claim
  exists yet.
- Out of scope: the profile does not address this threat.

Conformance is not safety. A verifier confirms form; the human confirms
meaning.

## Threat, control, evidence, and gap map

| Threat channel | OWASP Agentic | GuideCheck control | Evidence | Status and gap |
|---|---|---|---|---|
| Hidden text in rendered surfaces: HTML comments, CSS-hidden text, script, images, data URLs | ASI01 Agent Goal Hijack | Level 2 construct profile; `guidecheck scan` for existing files | `construct.html`, `construct.javascript`, `construct.markdown-image`, `construct.data-url`, `surface.hidden-html-comment`, `surface.css-hidden-text`; fixtures `html-construct`, `javascript-construct`, `markdown-image`, `data-url` | Delivered for adopting guides and scanned files. Instructions that reach an agent through other channels are not covered. |
| Invisible bytes: bidi controls, zero-width and tag characters, ANSI escapes, control bytes | ASI01 | Level 2 strict ASCII byte profile; scanner surface checks | `byte-profile.non-ascii-byte`, `surface.invisible-unicode.bidi-control`, `surface.invisible-unicode.zero-width`, `surface.invisible-unicode.tag-characters`, `surface.ansi-escape`; fixtures `non-ascii-byte`, `byte-ansi`, `byte-control`, `byte-nul` | Delivered. |
| Instructions buried in long content | ASI01, ASI09 Human-Agent Trust Exploitation | 8 KiB cap, line limits, explicit `[action]` blocks | fixtures `oversize`, `overlong-line`, `byte-too-many-lines`, `action-section-missing`, `action-malformed-line` | Form delivered. Whether an agent executes only action blocks is runtime-dependent. |
| Dangerous command shapes: fetch-and-execute, encoded execution, substitution, chaining, destructive globs | ASI02 Tool Misuse, ASI05 Unexpected Code Execution | Level 3 command restrictions and approval gates | `command.fetch-execute`, `prohibited.encoded-execution`, `command.substitution`, `command.chaining`, `command.glob-destructive`; fixtures `command-fetch-execute-as-normal`, `encoded-execution`, `prohibited-encoded-execution-negation-evasion`, `command-substitution`, `command-chaining`, `destructive-glob` | Detection delivered. Blocking execution is runtime-dependent. Shell, PATH, and environment semantics remain a residual risk. |
| Executed surface outside the reviewed guide: invoked scripts, package lifecycle hooks | ASI04 Agentic Supply Chain Vulnerabilities, ASI05 | Level 3 bounded execution: invoked targets must be inlined or hash-pinned | `action.exec-unbounded`, `action.exec-opaque`, `action.exec-target-unresolved`; fixtures `exec-unbounded-script`, `exec-opaque-bound`, `command-local-script-under-declared`, `code-executing-class-missing` | Delivered in local verification. Hosted pinned-artifact verification is pending. The dependency graph is not proven safe. |
| Approval bypass and self-extending guides: skip-approval text, guide rewriting, chained or next guides | ASI01, ASI09 | Level 3 prohibited patterns and approval requirements | `prohibited.skip-approval`, `prohibited.rewrite-guide`, `prohibited.next-guide-field`, `prohibited.chained-guide`, `approval.required-missing`; fixtures `prohibited-skip-approval`, `prohibited-rewrite-guide`, `prohibited-next-guide`, `chained-guide`, `approval-required-missing` | Detection delivered. Enforcing approval is runtime-dependent. |
| Privilege and egress overreach: undeclared environment variables, broad egress | ASI03 Identity and Privilege Abuse, ASI02 | Declared `env`, `egress`, `cwd`, and `runner` fields per action | `env.unlisted-variable`, `env.missing`, `egress.wildcard-too-broad`, `egress.missing`, `filesystem.cwd.missing`; fixtures `env-unlisted`, `env-missing`, `egress-broad-wildcard`, `networked-egress-missing`, `cwd-missing` | Declared contract delivered. Enforcing the declared egress and environment is runtime-dependent. |
| Memory contamination: guide content or approvals reused outside the session | ASI06 Memory and Context Poisoning | Profile prohibits storing guide-derived instructions without reconfirmation | `prohibited.memory` | Runtime-dependent. |
| Guide substitution and provenance: swapped bytes, divergent copies | ASI04 | Level 4 sidecar manifest and independent anchor; hosted fetch safety | `manifest.hash-mismatch`, `manifest.bytes-mismatch`, `anchor.independent.mismatch`, `anchor.independent.missing`, `fetch.ssrf.*`; fixtures `cross-channel-hash-divergence`, `manifest-hash-mismatch`, `single-authority-verifier`, `public-fetch/*` | Delivered on the hosted verifier for DNS TXT, package-registry, transparency-log, and legacy repository-file anchors. Signed `security.txt` anchors are not fetched. An agent that refetches without comparing hashes, or acts after the guide changes, is a runtime gap. |
| Verifier overtrust: a green report treated as permission | ASI09 | Required disclaimer; compact report states limits | `content.required.disclaimer`; `level5_ready` never reported as an achieved Level 5 | Partially addressed. User behavior cannot be enforced by the artifact. |
| Delegation across agents | ASI07 Insecure Inter-Agent Communication, ASI08 Cascading Failures | No chained guides; A2A integration patterns | `prohibited.chained-guide`; `docs/a2a-integration.md` | Integration pattern only. |
| Compromised endpoint, malicious but conforming prose, rogue agents | ASI10 Rogue Agents | None | `threat-register.md` residual trust boundaries | Out of scope. |

## ACS v0.1.0 hook crosswalk

The [pinned ACS hook catalog](https://github.com/GenAI-Security-Project/agent-control-standard/blob/27799c2c27414a483a4a043b957bfd2997d53231/docs/spec/instrument/hooks.md)
defines 19 `steps/*` hooks, the wrapped `protocols/MCP/*`
namespace, and the `agbom/*` inventory methods. A Guardian Agent receives
decision-eligible hooks and returns the dispositions allowed by each method;
some lifecycle hooks are audit-only. The table shows the GuideCheck
evidence a Guardian policy could use at each point. None of this is
implemented as an ACS policy today.

The source revision is `27799c2c27414a483a4a043b957bfd2997d53231`, checked
2026-10-03. Repository version 0.1.2 and the v0.1.0 schema/wire contract are
distinct. These policy inputs are not a claim that every GuideCheck value is
a native field in an ACS hook payload.

| ACS method | GuideCheck evidence | Guardian decision it enables |
|---|---|---|
| `steps/sessionStart` | guide URL, SHA-256, profile version, achieved level, blocking findings | bind the session to one verified guide hash; deny when findings are blocking |
| `steps/userMessage`, `steps/knowledgeRetrieval` | guide bytes and hash | flag or deny instruction artifacts that do not match the verified guide hash |
| `steps/skillRegister`, `steps/skillLoad` | verifier result and Level 4 provenance for guide-like instruction packages | vet the instruction artifact before load, closing the consent gap ACS documents for skills |
| `steps/toolCallRequest` | action id, class, command, runner, cwd, env, egress, approval state | allow only commands that match a declared action block; require approval for gated classes |
| `steps/toolCallResult` | acceptance checklist and stop-and-ask conditions | stop when observed state diverges from the guide |
| `steps/memoryStore` | the `prohibited.memory` rule | deny storing guide-derived instructions without reconfirmation |
| `steps/subagentStart` | the no-chained-guides rule | deny passing guide authority to a sub-agent without a fresh reviewed boundary |
| `agbom/snapshot` | guide URL, profile version, SHA-256, manifest URL, achieved level | inventory the instruction artifact as a component of the agent system |
| `protocols/MCP/*` | MCP install and configuration guides | apply the same checks to MCP server setup; see `docs/mcp-integration.md` |

The ACS reference implementation at the pinned revision evaluates `steps/toolCallRequest`
and `steps/toolCallResult` live. The other rows depend on hosts and
Guardians that emit and enforce those hooks.

## Gaps

- Runtime enforcement. The runtime-dependent rows above are the Level 5
  surface. An ACS Guardian enforcing the hook policy above is a candidate
  Level 5 runtime. A Level 5 claim still requires the GuideCheck runtime
  fixture suite and evaluator, which do not exist yet.
- AgBOM representation is now schema-reviewed in the [integration note](acs-integration.md#agbom-representation): `skill` when registered as loadable content, or `knowledge_source` when retrieved as reference material. Neither classification proves approval or runtime enforcement. A complete-artifact digest cannot be replaced with a guide-only digest when other files are bundled.
- LLM Top 10 2026 identifiers remain source-access-blocked as described above. Resume only from the official edition or a supplied copy with provenance.
- An implemented adapter and its report/approval binding remain future work. The ACS note now uses the pinned method names; A2A wrapping remains reserved by that source.
- Hosted verification of pinned execution targets and signed `security.txt`
  anchors remain open; see `roadmap.md`.

## Sources

- OWASP Top 10 for Agentic Applications for 2026:
  https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/
- OWASP GenAI LLM Top 10 2026:
  https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/
- ACS announcement, 2026-09-01:
  https://genai.owasp.org/2026/09/01/owasp-genai-security-project-unveils-2026-top-10-for-llm-applications-new-agent-control-standard-and-sponsors-as-community-tops-30000-members/
- Agent Control Standard: https://genai.owasp.org/resource/agent-control-standard-acs/
- ACS repository, hook catalog `docs/spec/instrument/hooks.md`:
  https://github.com/GenAI-Security-Project/agent-control-standard
- GuideCheck finding ids: `finding-ids.md`; fixtures: `fixtures/`; residual
  risks: `threat-register.md`
