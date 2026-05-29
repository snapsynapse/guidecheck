# GuideCheck Adoption Guide

This is the practical on-ramp to GuideCheck. It explains what an
`assistant-guide.txt` artifact is, what the conformance ladder means in
operational terms, and how to publish a conforming guide one level at a time.
For the exact normative requirements, `spec.md` is authoritative; this guide
points into it.

GuideCheck is a trust boundary protocol for agent instruction surfaces. It
helps ensure the instructions humans approve are the same instructions agents
execute.

## Who this is for

Adopt GuideCheck if you publish instructions an AI assistant will act on:

- AI-assisted install, setup, or local-development guides
- migration and upgrade runbooks
- remediation and incident playbooks
- support and operations runbooks
- agent skill installation guidance
- MCP server installation, configuration, tool review, and resource review
  guidance
- A2A companion guidance for delegated tasks, returned artifacts, and
  remote-agent operating boundaries

It is relevant to maintainers who ship those guides, to security and platform
engineers who review them, to MCP and A2A implementers working across agent
trust boundaries, and to verifier authors building tooling.

## Why this exists

An AI-assisted guide reaches an assistant through HTML, rendered Markdown,
PDFs, docs sites, copied terminal output, and screenshots. Each of those
surfaces can carry text a model ingests but a human never sees. A tool-using
assistant then runs those instructions with the operator's authority: it
executes commands, edits files, installs packages, and calls APIs.

That is a review-integrity problem. The human may approve one instruction
surface while the assistant executes another. In operational terms, the
failure can look like credential exposure, a destructive command, a malicious
dependency install, disabled safeguards, broader MCP tool access, or a remote
agent returning instructions that were never reviewed as executable guidance.

GuideCheck removes the presentation layer. It defines one artifact, a
plain-text file named `assistant-guide.txt`, small enough and strict enough
that the text a human reviews is the text the assistant runs. See `spec.md`
section 3, and `design-rationale.md` for the reasoning.

## The conformance ladder

The ladder is additive and honest. Each level states what it has checked and
what it has not. A higher level adds structure and provenance; it never adds a
safety claim.

| Level | What it establishes | What you publish |
|---|---|---|
| 0 | Instructions are only available through surfaces that can hide or transform text | nothing yet |
| 1 | A plain-text guide exists, is reachable, and carries the compact verification instruction | a `.txt` guide |
| 2 | Strict ASCII byte profile, size limits, no disallowed constructs | the same guide, within the byte profile |
| 3 | A full assistant safety contract: required sections, action blocks, explicit approval gates | a structured guide |
| 4 | Verifiable provenance: a sidecar manifest plus a cross-channel hash on an independent control plane | guide, manifest, one anchor |
| 5 | A conformant assistant runtime mechanically enforces the execution contract | guide plus runtime |

## Choosing a target level

- Level 1 to 2 is the right first commitment for most publishers. It is
  plain-text work and removes the presentation-layer attack surface
  immediately.
- Level 3 is the recommended target for any guide that drives real
  operational actions. It is the first level with mechanical approval gates.
- Level 4 suits high-consequence guides where the publisher can host a
  manifest and publish a hash on an independent channel.
- Level 5 is a joint guide-plus-runtime claim. A guide author reaches Level 4;
  Level 5 is asserted by a conformant runtime, not by a file.

A guide is not obliged to reach Level 3 in one step. Publishing at Level 1 or
2 first is a valid and useful state.

For teams seeking the highest guide-file score, the target is Level 4 of 4.
If verifier output also says `level5_ready: true`, the guide is prepared for a
Level 5 runtime check. The checker should not present this as `Level 4 of 5`
or as a missing point.

## How to reach each level

### Level 1: plain text available

1. Write the task instructions as a plain `.txt` file named
   `assistant-guide.txt`.
2. State the task scope and the canonical project or repository URL.
3. Add the compact verification instruction before any action instructions.
   Canonical wording is in `spec.md` section 10.2.
4. Make it reachable from a canonical surface: serve it at
   `/.well-known/assistant-guide.txt`, place it at the repository root, or
   both. When both are served, keep them byte-identical (`spec.md` section 6).

### Level 2: human-verifiable byte profile

1. Restrict the file to the byte profile: ASCII printable bytes plus LF, no
   tabs, no carriage returns, no control or invisible characters (`spec.md`
   section 8).
2. Stay within the limits: 8192 bytes, 120 bytes per line, 400 lines.
3. Remove disallowed constructs: HTML, CSS, JavaScript, images, remote
   embeds, data URLs, escape sequences, encoded command blobs (`spec.md`
   section 9).
4. Serve it with `Content-Type: text/plain; charset=utf-8` and
   `X-Content-Type-Options: nosniff` (`spec.md` section 20).

### Level 3: assistant safety contract

1. Add the metadata block with all required fields (`spec.md` section 11).
2. Add the required sections, each restated in the guide's own prose: title,
   scope, invocation prompt, safety rules, threat model, untrusted content
   handling, authority statement, and disclaimer (`spec.md` section 10.1).
3. Express every substantive action as a structured `[action]` block with
   `id`, `class`, `approval`, and `command` (`spec.md` section 12).
4. Set `approval: required` on every `privileged`, `destructive`,
   `persistence-changing`, `data-accessing`, or `code-executing` action.
5. Add stop-and-ask conditions and an acceptance checklist (`spec.md`
   sections 13 and 22).

### Level 4: verifiable provenance

1. Publish a sidecar manifest at a stable URL with `guide-sha256`,
   `guide-bytes`, and `immutable-release-url`; name it in the `manifest-url`
   metadata field (`spec.md` section 11).
2. Cross-publish the same `guide-sha256` on at least one independent control
   plane: a DNS TXT record, package registry metadata, a public repository
   file, a signed `security.txt`, or a public append-only transparency log.
3. Confirm a verifier reports both the manifest match and one agreeing
   independent anchor.

Package registry examples:

- npm `package.json`:
```text
"assistantGuide": {
  "url": "https://example.com/.well-known/assistant-guide.txt",
  "sha256": "<64-hex>"
}
```
- PyPI `pyproject.toml`:
```text
[project.urls]
Assistant-Guide = "https://example.com/.well-known/assistant-guide.txt"
```
  Carry the hash in the sidecar manifest referenced by the guide metadata.
- Cargo `Cargo.toml`:
```text
[package.metadata.assistant-guide]
url = "https://example.com/.well-known/assistant-guide.txt"
sha256 = "<64-hex>"
```
- Generic registry metadata:
```text
assistantGuide.url = "https://example.com/.well-known/assistant-guide.txt"
assistantGuide.sha256 = "<64-hex>"
```

When package registry metadata is the chosen independent anchor, include a
`registry-url` in the guide metadata that points to a specific package record,
not a registry homepage or search result.
For JSON registry records, put the hash inside assistant-guide-specific
metadata, such as `assistantGuide.sha256`; unrelated `sha256` fields elsewhere
in the package record do not count as GuideCheck anchors.

### Level 5: runtime-enforced execution

Level 5 is not a guide-only claim. A guide author prepares for it by reaching
Level 4 and following the Level 5 preparation list in `spec.md` section 18.
The Level 5 claim itself belongs to a conformant assistant runtime that
mechanically enforces the execution contract defined in `spec.md` section 18.

## Guide-author checklist

Use this before publishing. It tracks the normative requirements; `spec.md`
is authoritative on each.

Level 1
- [ ] file is plain `.txt`, named `assistant-guide.txt`
- [ ] task scope stated
- [ ] canonical project or repository URL present
- [ ] compact verification instruction appears before any action instructions
- [ ] reachable from a canonical surface; both copies byte-identical if both are served

Level 2
- [ ] byte profile satisfied: ASCII printable plus LF, no tabs, carriage returns, control, or invisible characters
- [ ] within 8192 bytes, 120 bytes per line, 400 lines
- [ ] no disallowed constructs
- [ ] served as `text/plain; charset=utf-8` with `nosniff`

Level 3
- [ ] metadata block present with all required fields
- [ ] all required sections present and restated in the guide's own prose
- [ ] every substantive action is an `[action]` block
- [ ] `approval: required` on every privileged, destructive, persistence-changing, data-accessing, and code-executing action
- [ ] `command` fields satisfy the section 12 restrictions
- [ ] `networked` actions declare a narrow `egress`
- [ ] stop-and-ask conditions and acceptance checklist present
- [ ] no safety overclaiming

Level 4
- [ ] sidecar manifest published and named in `manifest-url`
- [ ] `guide-sha256` cross-published on at least one independent channel
- [ ] a verifier confirms the manifest match and one agreeing anchor

Level 5 readiness
- [ ] every action declares `runner`
- [ ] every networked action uses `approval: required`
- [ ] shell actions use `runner: shell`, require approval, and include a narrow `notes` rationale
- [ ] applicable `cwd`, `env`, and `egress` fields are narrow and explicit
- [ ] verifier output reports `level5_ready: true`

## Conformance is not safety

Conformance to this profile, at any level, does not mean a guide is safe to
follow, that the publisher is trustworthy, or that an assistant may skip the
security practices a competent operator already applies. A verifier confirms
form. The human confirms meaning. Read the full guide before authorizing an
assistant, and read `operator-guide.md` for the defense-in-depth practices
that go with adoption.

## Next steps

- `spec.md`: the normative Human-Verifiable Assistant Guide profile
- `verifier-conformance.md`: the normative profile for verifier tools
- `operator-guide.md`: non-normative operator practices
- `examples/`: sample conforming guides
- Verify a guide at https://guidecheck.org/verify
