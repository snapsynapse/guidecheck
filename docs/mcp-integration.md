# GuideCheck and MCP Integration

Status: non-normative integration note. Advisory only: nothing in this
note adds, changes, or implies a conformance requirement, and the note
may be restructured without a profile version change. The normative
documents are `spec.md` and `verifier-conformance.md`.

This note describes where GuideCheck can add value for Model Context Protocol
server authors, host implementers, client implementers, and reviewers. It does
not make MCP a GuideCheck conformance dependency. It does not make GuideCheck a
transport, registry, or authorization layer for MCP.

## Fit

MCP gives language-model applications a standard way to connect to external
context and capabilities. MCP servers can expose tools, resources, and prompts.
MCP clients can expose roots, sampling, and elicitation flows to servers.

GuideCheck addresses a narrower problem: before an assistant follows
operational instructions, the instructions should be visible, bounded,
reviewable, approval-gated, and provenance-checkable. For MCP, the most useful
GuideCheck role is the reviewable instruction layer around installing,
enabling, configuring, and operating an MCP server.

The natural first audience is MCP server authors. Server authors publish the
setup instructions, security notes, tool descriptions, and configuration steps
that operators and assistants will follow. Host and client implementers are the
second audience, because they can later enforce GuideCheck action boundaries at
runtime.

## Database MCP server pattern

Database MCP servers are a strong first target because they combine common MCP
use with clear review needs:

- package installation
- host configuration changes
- credential and connection-string handling
- schema and table discovery
- read queries over sensitive data
- possible write, migration, export, or destructive queries
- network egress to a database host or proxy

A database MCP server author can publish an `assistant-guide.txt` for assistant
assisted installation and review. A Level 3 guide should make the following
plain before an assistant acts:

- which MCP server package or repository is in scope
- which host configuration file may be changed
- which database engines or endpoints are expected
- whether the server is read-only or write-capable
- which credentials are needed and how they must not be exposed
- which tools and resources the MCP server is expected to expose
- which actions require explicit human approval
- when the assistant must stop and ask

## MCP surface mapping

| MCP surface | GuideCheck concern | GuideCheck pattern |
|---|---|---|
| Server install instructions | Assistant may install packages, edit host config, or start a local process | Publish a Level 3 `assistant-guide.txt` with explicit action blocks |
| `tools/list` | Tool descriptions and schemas may be incomplete or misleading | Require a review action that compares expected tools with observed tools |
| `tools/call` | Tool invocation may query data, call APIs, mutate state, or execute code | Map each allowed tool call to a GuideCheck action id before runtime use |
| Tool list changes | A server may expose new capabilities after approval | Stop and ask when the observed tool list changes materially |
| `resources/list` and `resources/read` | Resources may expose files, database schemas, secrets-adjacent data, or internal context | Declare expected resource scope and require approval for data-accessing actions |
| Prompts | MCP prompts can package workflows or instructions for an assistant | Treat operational prompts as untrusted until reviewed against the guide scope |
| Roots | Roots define filesystem or URI boundaries for server operation | Declare expected roots and stop when a server requests broader roots |
| Sampling | A server can ask the client to invoke a model | Require approval before server-initiated sampling and disclose what result the server can see |
| Elicitation | A server can ask the user for additional information | Require approval for sensitive, credential-adjacent, URL, or operational elicitation flows |
| Authorization | OAuth or other authorization may grant durable access | Treat token grant, scope change, and account connection as privileged or persistence-changing actions |

## Server author checklist

An MCP server author should consider publishing a GuideCheck guide when the
server installation or operation includes any of the following:

- installing a package, binary, container, plugin, extension, or service
- modifying an MCP host configuration file
- requesting credentials, tokens, database URLs, or SaaS account access
- exposing filesystem, repository, database, customer, or internal resources
- invoking network APIs or database queries
- offering write, delete, migration, export, shell, or code execution tools
- asking the client to perform sampling or elicitation

At Level 3, the guide should express each substantive action as an `[action]`
block and should require approval for privileged, destructive,
persistence-changing, data-accessing, code-executing, and sensitive networked
actions.

## Host and client enforcement pattern

Host and client implementers can use GuideCheck verifier output as input to
runtime policy. This is Level 5 design research until a runtime conformance
fixture suite exists.

A host or client policy can:

- require a verified guide before installing or enabling an MCP server
- pin the guide bytes by `guide-sha256`
- require the selected action id before invoking an MCP tool
- deny `tools/call` when no guide action covers the requested operation
- deny `resources/read` outside the declared resource scope
- deny networked actions outside declared `egress`
- require fresh approval for data-accessing, code-executing, privileged,
  destructive, or persistence-changing tool calls
- stop when `notifications/tools/list_changed` changes the reviewed tool set
- log the verifier result, action id, approval result, and observed MCP method

GuideCheck should remain one policy input. It does not replace MCP
authorization, host sandboxing, least privilege, data-loss prevention, secret
management, package manager trust policy, or human judgment.

## Documentation and discovery pattern

MCP server documentation can point to the guide from install and security
sections:

```text
Assistant guide: https://example.com/.well-known/assistant-guide.txt
Verifier: https://guidecheck.org/verify
```

If a registry, marketplace, or package manager adds MCP server metadata, it can
also carry a non-authoritative pointer to the guide and its hash. The
GuideCheck conformance claim remains valid only when backed by verifier output,
guide hash, achieved level, and findings.

## Sources

- MCP specification: https://modelcontextprotocol.io/specification/2025-06-18
- MCP tools: https://modelcontextprotocol.io/specification/2025-06-18/server/tools
- MCP resources: https://modelcontextprotocol.io/specification/2025-06-18/server/resources
