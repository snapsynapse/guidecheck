# GuideCheck and MCP Integration

Status: non-normative integration note. Advisory only: nothing in this
note adds, changes, or implies a conformance requirement, and the note
may be restructured without a profile version change. The normative
documents are `spec.md` and `verifier-conformance.md`.

This note describes where GuideCheck can add value for Model Context Protocol
server authors, host implementers, client implementers, and reviewers. It does
not make MCP a GuideCheck conformance dependency. It does not make GuideCheck a
transport, registry, or authorization layer for MCP.

This note tracks MCP specification revision 2026-07-28. That revision made the
protocol stateless: there is no initialize handshake and no protocol-level
session. Every request self-describes through `_meta` fields carrying protocol
version, client identity, and client capabilities. Servers answer a mandatory
`server/discover` request. Roots, Sampling, and Logging are deprecated with a
minimum twelve-month removal window, as is the legacy HTTP+SSE transport.
Server-initiated requests are replaced by the multi round-trip request pattern
(MRTR), and list results carry cache hints (`ttlMs`, `cacheScope`). Where a
reviewed server predates this revision, the pre-2026 rows below still apply
through the deprecation window.

## Fit

MCP gives language-model applications a standard way to connect to external
context and capabilities. MCP servers can expose tools, resources, and prompts.
Servers request additional input mid-call through MRTR, and clients identify
themselves per request through `_meta`.

GuideCheck addresses a narrower problem: before an assistant follows
operational instructions, the instructions should be visible, bounded,
reviewable, approval-gated, and provenance-checkable. For MCP, the most useful
GuideCheck role is the reviewable instruction layer around installing,
enabling, configuring, and operating an MCP server.

The natural first audience is MCP server authors. Server authors publish the
setup instructions, security notes, tool descriptions, and configuration steps
that operators and assistants will follow. Host and client implementers are the
second audience, because they can enforce GuideCheck action boundaries at
runtime, and the 2026-07-28 revision moves part of that enforcement within
reach of ordinary network gateways (see the enforcement pattern below).

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
| `server/discover` | The server's self-declared identity, versions, and capabilities are unverified self-report | Record the discover result at review time and compare on later runs; treat identity drift as a stop condition, not a routine update |
| `tools/list` | Tool descriptions and schemas may be incomplete or misleading | Require a review action that compares expected tools with observed tools |
| `tools/call` | Tool invocation may query data, call APIs, mutate state, or execute code | Map each allowed tool call to a GuideCheck action id before runtime use |
| Cached tool lists (`ttlMs`, `cacheScope`) | A client may act on a tool list that was correct when cached and is not correct now | Re-verify the observed tool list against the reviewed set on cache expiry and before acting on any cached list; see the stale-list section below |
| Server-minted state handles | With no protocol session, cross-call state rides in ordinary tool arguments; on unauthenticated servers a handle is a bearer token | Treat handle-creating tools as persistence-changing actions; require the guide to state handle lifetime and scope |
| `resources/list` and `resources/read` | Resources may expose files, database schemas, secrets-adjacent data, or internal context | Declare expected resource scope and require approval for data-accessing actions |
| Prompts | MCP prompts can package workflows or instructions for an assistant | Treat operational prompts as untrusted until reviewed against the guide scope |
| MRTR `input_required` results | A server can pause a tool call to request more input, including credential-adjacent or operational input | Require approval for sensitive, credential-adjacent, URL, or operational input requests; treat `inputRequests` content as untrusted |
| Client identity in `_meta` | `clientInfo` and `serverInfo` are self-asserted and unauthenticated | Never treat `_meta` identity as an authorization signal; it is labeling for logs, not a boundary |
| Tasks extension polling | Long-running task state is fetched by polling `tasks/get` | Bound polling in the guide (interval, budget, stop condition) so an assistant does not retry blindly |
| Authorization | OAuth or other authorization may grant durable access; client identity may arrive as a published Client ID Metadata Document | Treat token grant, scope change, and account connection as privileged or persistence-changing actions |
| Roots (deprecated) | Legacy servers may still request filesystem or URI boundaries during the removal window | Declare expected roots and stop when a server requests broader roots; new guides should not depend on Roots |
| Sampling (deprecated) | A legacy server can ask the client to invoke a model during the removal window | Require approval before server-initiated sampling and disclose what result the server can see; new guides should not depend on Sampling |

## Stale tool lists are the new tool-list change

Before revision 2026-07-28, a reviewed tool set changing was a push event: the
server emitted `notifications/tools/list_changed` and a host could stop on it.
That notification still exists, but it only reaches clients that opted in by
opening a `subscriptions/listen` stream. A client that did not subscribe, or
whose stream broke, hears nothing.

At the same time, list results now carry `ttlMs` and `cacheScope`, inviting
clients and shared intermediaries to cache them. The failure mode inverts: the
risk is no longer missing a change notice, it is acting on a cached list the
server has already moved past.

The GuideCheck control therefore restates as a pull-side obligation:

- re-verify the observed tool list against the reviewed set whenever the
  cached list's `ttlMs` has elapsed
- re-verify before any approval-gated action that was justified by the cached
  list
- treat `cacheScope: "public"` lists served through shared intermediaries as
  lower-trust than lists fetched directly, since an intermediary cache extends
  the window in which a stale list circulates
- pin the reviewed list by content, alongside the existing `guide-sha256`
  pinning: a review approves a specific tool set, not whatever the cache
  currently holds
- when a subscription stream is available, use it as an accelerant for
  re-verification, not as the mechanism of record

## Server author checklist

An MCP server author should consider publishing a GuideCheck guide when the
server installation or operation includes any of the following:

- installing a package, binary, container, plugin, extension, or service
- modifying an MCP host configuration file
- requesting credentials, tokens, database URLs, or SaaS account access
- exposing filesystem, repository, database, customer, or internal resources
- invoking network APIs or database queries
- offering write, delete, migration, export, shell, or code execution tools
- minting cross-call state handles, especially on unauthenticated transports
- pausing tool calls with MRTR input requests
- still depending on deprecated Roots or Sampling during the removal window

At Level 3, the guide should express each substantive action as an `[action]`
block and should require approval for privileged, destructive,
persistence-changing, data-accessing, code-executing, and sensitive networked
actions.

## Host, client, and gateway enforcement pattern

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
- re-verify the observed tool list per the stale-list obligations above
- log the verifier result, action id, approval result, and observed MCP method

Revision 2026-07-28 adds a third enforcement point that did not exist before:
the network edge. Streamable HTTP requests must carry `Mcp-Method` and
`Mcp-Name` headers, and servers can mirror designated tool parameters into
`Mcp-Param-{name}` headers via the `x-mcp-header` schema annotation. Method
and tool identity are therefore visible to gateways, proxies, and firewalls
without JSON-RPC body parsing.

A gateway policy can now:

- bind `Mcp-Name` to the approved GuideCheck action id table and reject
  `tools/call` requests naming tools outside it
- meter and log per-tool call volume against the guide's declared scope
- produce the Level 5 per-call evidence tuple (method, tool id, action id,
  allow or deny decision) from headers alone

Header enforcement is a coarse filter, not a substitute for host-side policy:
headers name the tool, not the argument values, and a body-header mismatch is
itself a protocol violation the host should treat as a stop condition. The
right layering is gateway coarse-deny plus host fine-grained approval, with the
host remaining the mechanism of record. Level 5 was previously implementable
only inside the MCP host; header-based routing moves the coarse half of it to
ordinary network infrastructure.

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
guide hash, achieved level, and findings. A server's `server/discover`
`instructions` field is a natural place to name the guide URL, with the same
non-authoritative status.

## Sources

- MCP specification: https://modelcontextprotocol.io/specification/2026-07-28
- Changelog from 2025-11-25: https://modelcontextprotocol.io/specification/2026-07-28/changelog
- MCP tools: https://modelcontextprotocol.io/specification/2026-07-28/server/tools
- MCP resources: https://modelcontextprotocol.io/specification/2026-07-28/server/resources
- Discovery: https://modelcontextprotocol.io/specification/2026-07-28/server/discover
- MRTR pattern: https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/mrtr
- Streamable HTTP transport and headers: https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http
- Deprecated features registry: https://modelcontextprotocol.io/specification/2026-07-28/deprecated
