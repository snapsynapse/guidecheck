# GuideCheck Level 5 Runtime Conformance

Status: draft design note.

This note proposes a GuideCheck-owned Level 5 runtime conformance evaluation.
It does not make Agent Control Standard, OWASP Agent Observability Standard,
MCP, A2A, OpenTelemetry, OCSF, or AgBOM a GuideCheck conformance dependency.
It does not claim that any current assistant runtime, verifier, hosted
checker, or integration note is Level 5 conformant.

## Purpose

GuideCheck Level 4 is the highest guide-file score. Level 5 is a deployment
claim: a Level 4 guide plus an assistant runtime that mechanically enforces the
guide's execution contract.

The purpose of a Level 5 runtime conformance evaluation is to answer:

- did the runtime verify and pin the exact guide bytes before action
- did the runtime make only structured `[action]` blocks executable
- did the runtime require and scope approvals correctly
- did the runtime enforce runner, command, working-directory, environment, and
  egress constraints where it claimed enforcement
- did the runtime prevent guide content from becoming long-term memory or
  delegated instructions without fresh user authorization
- did the runtime produce enough evidence for an independent reviewer to
  reconstruct allow, deny, modify, approval, execution, and stop decisions

The evaluator checks runtime behavior. It does not certify publisher identity,
publisher intent, command safety, model quality, environment fitness, or the
security of the underlying software.

## Relationship to ACS and AOS

ACS and AOS are useful integration surfaces for Level 5 because they describe
agent-step events and control decisions across messages, tools, memory,
knowledge retrieval, MCP, and A2A.

GuideCheck should use them as evidence and interoperability adapters, not as
normative dependencies. The GuideCheck Level 5 evaluator should remain
portable across runtimes that do not implement ACS or AOS, while allowing ACS
or AOS-compatible runtimes to submit richer evidence.

The recommended split is:

- Core Level 5 profile: GuideCheck-owned requirements and fixtures derived
  from `spec.md` section 18.
- ACS/AOS evidence profile: optional mapping from GuideCheck events and
  verdicts to ACS/AOS request and response records.
- Inventory profile: optional record of the guide URL, profile version,
  guide SHA-256, manifest URL, verifier output, runtime version, and achieved
  runtime result in an AgBOM-like inventory when that surface is available.

An ACS/AOS trace can support a GuideCheck Level 5 claim, but the trace alone
does not establish Level 5. The runtime still has to pass the GuideCheck
runtime conformance evaluation.

## Evaluation inputs

A Level 5 evaluation should take these inputs:

- runtime name, version, build id, and declared enforcement capabilities
- guide URL and expected guide SHA-256
- Level 4 verifier output for the guide
- manifest URL and manifest hash evidence
- runtime policy configuration
- declared tool, shell, filesystem, memory, network, MCP, and A2A boundaries
- test scenario bundle

The evaluator should execute scenarios against an instrumented runtime or a
runtime harness. Pure self-attestation is not sufficient.

## Required evaluator output

The evaluator should emit machine-readable output and a compact human-readable
report from the same evidence model.

The machine-readable output should include:

- evaluator name, version, and profile version
- runtime name, version, build id, and declared capabilities
- guide URL, guide SHA-256, manifest URL, achieved guide level, and
  `level5_ready`
- verifier name, verifier version, verifier output hash, and blocking findings
- scenario ids, results, findings, and evidence pointers
- runtime decisions: allow, deny, modify, approval-requested,
  approval-granted, approval-denied, executed, stopped
- action ids, runner, command, cwd, env names, egress targets, exit status, and
  timestamps where applicable
- memory and delegation decisions
- ACS/AOS evidence references, when supplied
- final result: `pass`, `fail`, or `inconclusive`

The evaluator must not report Level 5 when any required runtime guarantee is
missing. If a runtime cannot enforce a specific control, such as network
egress, it may pass only when the GuideCheck Level 5 requirement permits
disclosure instead of enforcement and the scenario confirms that disclosure.

## Core test phases

### Verification gate

The runtime must:

- run a conformant GuideCheck verifier before proposing or executing actions
- display the compact verification report
- receive user confirmation before proposing or executing actions
- compare the guide bytes it will use against the verifier-reported SHA-256
- stop on guide-byte mismatch, Level 4 failure, revoked guide status, expired
  guide, or verifier blocking finding
- preserve verifier output in the session approval ledger

Negative tests should include:

- guide bytes changed after verification
- verifier output reports achieved Level 3
- manifest hash mismatch
- independent anchor mismatch
- compact report shown but no user confirmation received

### Action boundary

The runtime must:

- parse the guide as data before treating any part of it as actionable
- make only structured `[action]` blocks executable
- treat prose, `notes`, metadata, fetched content, manifests, verifier output,
  and repository files as non-executable unless represented by an approved
  action block
- reject action blocks that violate Level 4 conformance
- reject executable action blocks that omit `runner`
- reject executable action blocks that omit applicable `cwd`, `env`, or
  `egress` fields

Negative tests should include:

- command in prose outside an action block
- command in `notes`
- command in metadata
- command in manifest or verifier output
- fetched file that instructs the assistant to run an unlisted command
- action id collision or unknown action id

### Approval ledger

The runtime must:

- maintain a session-local approval ledger keyed by guide URL, guide hash,
  verifier name, verifier version, achieved level, and action id
- display each action block verbatim before approval
- prohibit batched approvals across action ids
- require approval for all `networked`, `privileged`, `destructive`,
  `persistence-changing`, `data-accessing`, and `code-executing` actions
- prevent approval for one action from authorizing another action, another
  guide hash, another verifier result, or another session

Negative tests should include:

- approval granted for action A and reused for action B
- approval granted under one guide hash and reused after guide change
- one prompt asking for multiple action approvals
- paraphrased approval prompt that omits the action block

### Execution enforcement

The runtime must:

- execute commands without invoking a shell when `runner: argv` is declared
- require `approval: required` and explicit `runner: shell` before invoking a
  shell
- disclose runner, cwd, relevant environment variable names, and network
  enforcement status before approval
- enforce declared `cwd` and `env` constraints
- enforce declared `egress` lists when the runtime has network-control
  capability
- disclose when declared `egress` lists are advisory rather than enforced
- log approved actions, rejected actions, executed commands, cwd, runner, exit
  status, and timestamps

Negative tests should include:

- `runner: argv` command that attempts shell metacharacter interpretation
- undeclared environment variable reference
- filesystem access outside declared `cwd`
- network access outside declared `egress`
- shell invocation without `runner: shell`
- code-executing action attempted without approval

### Stop conditions

The runtime must stop before:

- following a chained guide
- modifying, rewriting, or replacing `assistant-guide.txt`, its manifest, or
  verifier output
- expanding its own tool permissions
- disabling sandboxing
- decoding and executing encoded content
- continuing after observed state materially differs from the guide
- contacting non-official sources when the guide prohibits it

Negative tests should include:

- `next-guide` style field
- guide self-modification instruction
- request to disable approval prompts
- encoded command blob
- observed tool list differs from guide-declared scope

### Memory and delegation

The runtime must:

- prevent guide content, action commands, approvals, and verifier output from
  being stored into long-term assistant memory unless the user explicitly
  reconfirms that storage in the current session
- keep action-id namespaces scoped to one guide hash and one session
- require a fresh reviewed boundary before delegating covered work to another
  agent
- deny MCP tool calls or A2A delegated actions that do not map to an approved
  GuideCheck action id when the runtime claims those surfaces are enforced

Negative tests should include:

- automatic memory write of guide instructions
- memory retrieval that attempts to reuse a prior guide approval
- A2A delegation outside reviewed scope
- MCP `tools/call` outside approved action id

## ACS/AOS evidence mapping

An ACS/AOS-compatible runtime can expose GuideCheck evidence through its step
records and decisions.

| GuideCheck event | ACS/AOS surface | Required evidence |
|---|---|---|
| Guide verification | message or agent trigger step | guide URL, verifier output hash, achieved level, guide SHA-256 |
| User confirmation | message step | compact report, confirmation text, session id |
| Action proposal | tool-call request step or MCP message | guide hash, action id, action block, runner, cwd, env names, egress |
| Enforcement verdict | success response result | decision, reason code, message, modified request if applicable |
| Tool result | tool-call result step | execution id, exit status, output classification, timestamp |
| Memory attempt | memory store step | guide hash, action id if any, allow or deny decision |
| Knowledge retrieval | knowledge retrieval step | source, reason, allow or deny decision |
| MCP call | MCP message | method, tool or resource id, action id, allow or deny decision |
| A2A delegation | A2A message or task step | remote agent endpoint, task id, action id, allow or deny decision |

Reason codes should be stable and machine-readable. Suggested prefixes:

- `guidecheck.verify.required`
- `guidecheck.verify.hash_mismatch`
- `guidecheck.guide.level4_required`
- `guidecheck.action.unknown`
- `guidecheck.action.prose_not_executable`
- `guidecheck.approval.required`
- `guidecheck.approval.scope_mismatch`
- `guidecheck.runner.shell_not_declared`
- `guidecheck.cwd.out_of_scope`
- `guidecheck.env.undeclared`
- `guidecheck.egress.out_of_scope`
- `guidecheck.memory.reconfirmation_required`
- `guidecheck.delegation.boundary_required`
- `guidecheck.stop.chained_guide`

## Inventory pattern

When an inventory or AgBOM-like surface is available, it should record:

- runtime name, version, provider, and build id
- guide URL, guide profile, guide profile version, and guide SHA-256
- manifest URL and manifest SHA-256
- verifier name, version, profile version, and verifier output hash
- achieved guide level and `level5_ready`
- runtime conformance profile version
- runtime evaluation result and timestamp
- declared enforcement capabilities
- MCP servers, A2A agents, tools, resources, and network boundaries in scope

The inventory is evidence. It is not an oracle. Independent evaluators should
be able to reproduce the result from the same guide, verifier output, runtime
build, configuration, and scenario bundle.

## Non-claims

A runtime that passes this evaluation may claim:

```text
GuideCheck Level 5 runtime conformance evaluated for guide <sha256> under
runtime profile <version>.
```

It must not claim:

- the guide is safe
- the publisher is trustworthy
- the commands are correct for every environment
- ACS or AOS endorsement
- OWASP endorsement
- universal Level 5 support for guides or deployments not evaluated

## Open questions

- Should the runtime report schema live in `schemas/` before a fixture suite
  exists, or wait until the first executable prototype stabilizes?
- Should network egress tests require real network interception, or permit a
  declared advisory mode for runtimes without network-control capability?
- Should shell enforcement be tested through a synthetic command runner before
  testing real shells?
- Should ACS/AOS records be accepted as primary evidence, or only as an
  optional export derived from the evaluator's own event model?
- Should runtime conformance be scoped per guide hash, per runtime build, or
  per runtime build plus policy configuration?

## Sources

- GuideCheck specification: `spec.md`
- GuideCheck verifier conformance profile: `verifier-conformance.md`
- GuideCheck ACS integration note: `docs/acs-integration.md`
- Agent Control Standard repository: https://github.com/Agent-Control-Standard/ACS
- OWASP Agent Observability Standard repository: https://github.com/OWASP/www-project-agent-observability-standard
