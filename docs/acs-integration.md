# GuideCheck and ACS Integration

Status: non-normative integration note. Advisory only: nothing in this
note adds, changes, or implies a conformance requirement, and the note
may be restructured without a profile version change. The normative
documents are `spec.md` and `verifier-conformance.md`.

This note describes where GuideCheck can add value for the Agent Control
Standard. It does not make ACS a GuideCheck conformance dependency. It does
not claim that GuideCheck implements ACS hooks, replaces ACS policy
enforcement, or verifies that an ACS runtime behaves correctly.

## Fit

ACS defines a runtime control plane for AI agents. It standardizes middleware
hooks at agent decision points and lets enforcement tooling allow, deny, or
modify actions before they reach production systems.

GuideCheck addresses the instruction artifact that can drive those actions.
It defines a bounded `assistant-guide.txt` surface with explicit action
blocks, approval gates, command restrictions, provenance evidence, and a
runtime-enforcement preparation path.

The intersection is direct: GuideCheck can provide a verified instruction and
action contract that ACS middleware can enforce at runtime.

Source check: 2026-10-03, pinned ACS revision
[`27799c2c27414a483a4a043b957bfd2997d53231`](https://github.com/GenAI-Security-Project/agent-control-standard/tree/27799c2c27414a483a4a043b957bfd2997d53231).
That tree declares repository version 0.1.2 and retains the v0.1.0 wire/schema
directory. The method names below target those pinned schemas, not an assumed
equivalence between repository and protocol versions.

## Control-plane mapping

| ACS method | GuideCheck evidence available to a Guardian policy | Proposed runtime use |
|---|---|---|
| `steps/sessionStart` | guide URL, selected profile, hash and report | establish the session's reviewed artifact and policy context |
| `steps/userMessage`, `steps/knowledgeRetrieval` | guide bytes, provenance and hash | distinguish retrieved content from approved instructions |
| `steps/skillRegister`, `steps/skillLoad` | artifact identity and verification report | vet a guide packaged as a skill and correlate each load with the approved registration and digest |
| `steps/toolCallRequest` | action id, command, runner, cwd, env, egress and approval | deny execution outside the reviewed action or without its approval |
| `steps/toolCallResult` | acceptance checklist and stop conditions | stop on divergence; treat remediation text as untrusted input |
| `steps/memoryStore`, `steps/memoryContextRetrieval` | session-bound guide authority | prevent storage or reuse from silently extending approval |
| `steps/agentResponse` | disclaimer and report limits | avoid presenting guide conformance as a safety guarantee |
| `steps/subagentStart` | delegation boundary and no-chaining rule | require a fresh reviewed boundary for delegation |
| `agbom/snapshot`, `agbom/changed` | component identity and relevant artifact digest | inventory the artifact and expose changes |

These are policy inputs, not claims that ACS defines native fields for every
GuideCheck value in the table. An adapter must specify how it obtains and binds
the report, approval and action record. The pinned reference implementation
evaluates only `steps/toolCallRequest` and `steps/toolCallResult` live. Other
hooks require a host and Guardian that emit and enforce them. See the
[hook catalog](https://github.com/GenAI-Security-Project/agent-control-standard/blob/27799c2c27414a483a4a043b957bfd2997d53231/docs/spec/instrument/hooks.md)
and [implementation limits](https://github.com/GenAI-Security-Project/agent-control-standard/blob/27799c2c27414a483a4a043b957bfd2997d53231/README.md).

## AgBOM representation

The pinned [component schema](https://github.com/GenAI-Security-Project/agent-control-standard/blob/27799c2c27414a483a4a043b957bfd2997d53231/specification/v0.1.0/agbom/component.json)
has no `assistant-guide` component type. The appropriate existing type depends
on how the host uses the artifact:

| Host use | Existing schema representation | Limit |
|---|---|---|
| The guide is registered as a loadable skill | `type: skill`, with `id`, `name`, `skill_fields.description` and `skill_fields.definition.ref`/`digest` | The digest must cover the complete loadable artifact. A guide digest alone does not cover bundled scripts or model files. |
| The guide is retrieved as reference material | `type: knowledge_source`, with `id`, `name` and `knowledge_source_fields.source_type: other`; `endpoint` can name its URL | This branch supplies no dedicated guide-digest or verifier-report binding. Inventory membership does not approve execution. |

Mapping the guide to `skill` is a conditional integration recommendation, not
an OWASP classification of every guide. The
[`steps/skillLoad` schema](https://github.com/GenAI-Security-Project/agent-control-standard/blob/27799c2c27414a483a4a043b957bfd2997d53231/specification/v0.1.0/hooks/skill-load.json)
binds activation to a prior approved registration using the skill id and actual
artifact digest. A boolean assertion that a digest was verified is insufficient.
The base [knowledge-retrieval schema](https://github.com/GenAI-Security-Project/agent-control-standard/blob/27799c2c27414a483a4a043b957bfd2997d53231/specification/v0.1.0/hooks/knowledge-retrieval.json)
does not itself make retrieved guide content approved instructions.

No new ACS component type is needed to document either existing route. A future
adapter must still define report/approval binding and demonstrate enforcement;
this schema review does not implement that adapter or validate a runtime.

## Policy pattern

An ACS-compatible runtime can treat GuideCheck verifier output as one policy
input:

- require Level 3 or higher before executing an assistant-facing operational
  guide
- require Level 4 for production-impacting guides where provenance matters
- require `level5_ready: true` before enabling strict runtime enforcement
- pin the guide bytes by SHA-256 before planning or tool execution
- deny tool calls that do not map to a verified GuideCheck action id
- require approval where the action block declares `approval: required`
- deny commands, paths, environment variables, or network egress outside the
  reviewed action block
- stop when the observed tool list, resource set, agent endpoint, or runtime
  state differs materially from the guide

This pattern keeps the two projects separate. ACS supplies the runtime hooks
and enforcement verdicts. GuideCheck supplies the reviewed instruction
contract and verifier evidence.

## Event and inventory pattern

ACS trace and inventory systems can record GuideCheck evidence without making
the hosted GuideCheck verifier an oracle:

- guide URL
- guide profile version
- guide SHA-256
- verifier name and version
- achieved level
- manifest URL
- independent anchor status
- action id
- approval result
- enforcement verdict
- stop condition, if triggered

Independent verifiers should be able to produce equivalent evidence from the
same guide and anchors.

## MCP and A2A chain pattern

The pinned ACS catalog defines `protocols/MCP/*`; `protocols/A2A/*` is reserved
for v0.2 and has no normative v0.1 wrapping semantics. A future integration can
follow this pattern, with any A2A transport binding left explicit and separate:

1. GuideCheck verifies the assistant-facing operational guidance.
2. ACS hooks enforce the selected GuideCheck action at runtime.
3. MCP tools or A2A delegation execute only when covered by the verified
   action and approval state.
4. ACS trace and AgBOM records capture the guide hash, action id, tool or
   agent endpoint, and enforcement verdict.

This gives operators a chain from human review to runtime enforcement to
audit evidence.

## Sources

- ACS homepage: https://agentcontrolstandard.ai/
- ACS at OWASP GenAI: https://genai.owasp.org/resource/agent-control-standard-acs/
- ACS repository: https://github.com/GenAI-Security-Project/agent-control-standard
- ACS instrument specification: https://aos.owasp.org/spec/instrument/specification/
