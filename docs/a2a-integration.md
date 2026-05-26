# GuideCheck and A2A Integration

Status: non-normative integration note.

This note describes where GuideCheck can add value for Agent2Agent protocol
implementations and deployments. It does not make A2A a GuideCheck conformance
dependency. It does not claim that GuideCheck authenticates, endorses, or
controls remote agents.

## Fit

A2A gives agents a protocol for discovery, communication, task delegation, and
artifact exchange. GuideCheck addresses a different layer: whether operational
instructions that an assistant may follow are bounded, reviewable,
approval-gated, and provenance-checkable before action.

The strongest GuideCheck role in A2A is boundary control. A local assistant may
delegate work to a remote agent, receive returned artifacts, or pass along
instructions that cause another assistant to act. GuideCheck can help separate
reviewed operational instructions from untrusted cross-agent content.

## Agent Card companion pattern

An A2A Agent Card advertises information about an agent and its capabilities.
When an agent expects assistants to install, configure, authorize, delegate to,
or operate it, the publisher can provide a companion `assistant-guide.txt`.

The companion guide can state:

- which agent endpoint and publisher are in scope
- which task categories the guide covers
- which delegated actions require approval
- what data may be shared with the remote agent
- what credentials or account grants are out of scope
- how returned artifacts should be reviewed
- where verifier output and provenance evidence can be checked
- when the local assistant must stop and ask

This is a documentation pattern, not an A2A extension requirement.

## Delegated task pattern

Before sending a high-consequence task to a remote agent, a client or host can
use a GuideCheck guide as a policy input:

- verify the remote agent's companion guide
- confirm the requested task fits the guide scope
- confirm the guide is current and has not expired
- record the guide hash and achieved level
- require approval before sharing sensitive data, credentials, customer data,
  repository contents, database records, or internal documents
- require approval before authorizing persistence, account connection, billing,
  production mutation, or networked side effects
- stop if the remote agent asks for a broader task than the reviewed guide
  covers

Approval granted to a local assistant should not automatically authorize a
remote agent, a downstream agent, or a downstream tool. Delegation is its own
boundary.

## Returned artifact pattern

A2A artifacts can contain text, files, structured data, or other outputs. If a
returned artifact instructs the receiving assistant to take operational action,
the artifact should be treated as untrusted content.

The receiving assistant should not follow those instructions merely because
they arrived through A2A. For high-consequence actions, the instructions should
be converted into, or referenced by, a verified `assistant-guide.txt` before
execution.

This pattern is especially important for:

- remediation instructions
- install or migration steps
- shell commands
- code patches that include operational follow-up steps
- credential or token handling instructions
- production support runbooks
- instructions to call MCP tools or other remote agents

## A2A to MCP chain pattern

A common deployment can combine both protocols:

1. A local assistant receives a user request.
2. The local assistant delegates part of the task to a remote A2A agent.
3. The remote agent uses MCP tools to query data, call APIs, or operate a
   service.
4. The remote agent returns artifacts or instructions to the local assistant.

GuideCheck can provide a common review and audit layer across that chain:

- the A2A companion guide identifies the delegation scope
- the MCP integration guide identifies allowed tool and resource scope
- each high-consequence operation maps to an action id
- approval is recorded at the boundary where authority is granted
- returned artifacts are not treated as executable instructions by default

## Runtime event pattern

A host, client, gateway, or observability system can record GuideCheck evidence
alongside A2A task events:

- guide URL
- guide hash
- verifier id
- achieved level
- task id
- remote agent id or endpoint
- delegated action id
- approval result
- artifact id
- stop condition, if triggered

These records should not turn the hosted verifier into a central oracle.
Independent verifiers should be able to produce equivalent evidence from the
same guide and anchors.

## Sources

- A2A protocol specification: https://a2a-protocol.org/v0.3.0/specification/
