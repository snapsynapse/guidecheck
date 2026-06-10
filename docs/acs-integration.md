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

## Control-plane mapping

| ACS surface | GuideCheck evidence | Runtime use |
|---|---|---|
| Input hook | guide URL, verifier result, guide hash, expected level | require a verified guide before accepting high-consequence instructions |
| Planning or lifecycle hook | task scope, required sections, stop-and-ask conditions | stop when the plan leaves the reviewed guide scope |
| Tool-selection hook | action ids, action classes, declared approval gates | restrict available tools to actions covered by the guide |
| Tool-call hook | command, runner, cwd, env, egress, approval state | allow, deny, or modify tool calls before execution |
| Tool-result hook | acceptance checklist, stop conditions | stop when observed state diverges from the guide |
| Memory hook | untrusted content handling and memory contamination risks | deny long-term storage of guide-derived instructions without reconfirmation |
| Output hook | disclaimer, conformance limits, compact report | prevent overclaiming that conformance means safety |
| Sub-agent hook | no chained guides, delegation boundary, A2A notes | require a fresh reviewed boundary for delegated agents |
| AgBOM inventory | guide URL, profile version, SHA-256, manifest URL, achieved level | inventory the instruction artifact as part of the agent system |

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

ACS explicitly targets agent systems that use MCP and A2A. GuideCheck can sit
above both:

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
- ACS instrument specification: https://aos.owasp.org/spec/instrument/specification/
