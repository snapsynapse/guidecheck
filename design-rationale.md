# Design Rationale

Status: Working notes for documentation. Not part of the spec.

This document captures the reasoning behind design choices in spec.md. Use it as source material when writing the README, FAQ, adoption guide, or any explanatory documentation for the repo. The spec is normative; this document is explanatory.

## 8 KiB size cap

The spec sets a hard maximum file size of 8192 bytes for Level 2 and above. This section explains why.

### What the cap is calibrated against

Human attention during a careful approval review. The whole point of the profile is that the human actually verified what they approved before authorizing an assistant to follow it. A guide too long to review carefully is a guide whose approval ceremony is theater.

8 KiB at normal careful reading pace corresponds to under 10 minutes of focused review. That is inside the attention window before approval ceremony degrades into ritual.

### What 8 KiB actually allows

A typical conforming guide at this cap holds:

- the required metadata block (around 700 bytes with comfortable optional fields)
- the required sections from spec section 10 (around 4 KiB at reasonable density)
- between 3 and 7 action blocks (around 150 to 250 bytes each)
- prose context around each action (around 1 to 1.5 KiB)

The structural floor for required sections is roughly 4 to 5 KiB. The remaining 3 to 4 KiB is the publisher's working budget for actions and the prose that explains them.

### Why not 16 KiB

The original draft used 16 KiB. In review we calculated that this allowed up to roughly 15 action blocks with generous prose. The verifier in spec section 21 already warns when a guide requires more than 10 approvals, on the grounds that approval fatigue degrades review quality. A 16 KiB cap and a 10-approval warning describe the same boundary from two different directions, and 16 KiB was the looser of the two. We pulled the size cap in to match the approval-count signal.

### Why not 4 KiB

4 KiB does not leave room for the required sections at reasonable density. Publishers would be forced to strip threat models and shorten acceptance checklists to save bytes. That trades the safety property the profile cares about (review quality through completeness) for the safety property it does not (review quality through brevity at any cost). Wrong direction.

### Why not 10 KiB or 12 KiB

These are defensible. 10 KiB lines up cleanly with the 10-approval warning and gives publishers more headroom. 12 KiB is comfortable for almost any bounded task.

We picked 8 KiB because the profile's value proposition is opinionated tightness. The smaller the artifact, the more confident the human review. We accepted that a small number of legitimate flows at 9 or 10 KiB will need to be split into independent guides. The case for splitting those flows was already strong; the tighter cap makes it explicit rather than optional.

### How the cap interacts with bounded-task scope

Spec section 6 says this profile is for bounded tasks that fit in one artifact. The 8 KiB cap is what makes that statement mechanically real. A task that cannot fit in 8 KiB is too large for the single-approval-ceremony model and should be decomposed, delivered through a different surface (docs site, installer, CLI wizard), or reduced in scope.

The decomposition that the cap forces is usually the right design anyway. Bundling multiple distinct decisions into one document is a frequent failure mode in install documentation. The cap removes that option.

### Comparison with other high-stakes human-review artifacts

Artifacts that demand careful human review under time pressure trend smaller than 16 KiB:

- aviation checklists: 1 to 2 pages, around 4 KiB
- military orders in short form: usually under 5 pages, around 12 KiB
- surgical timeouts: under 500 bytes
- security.txt in the wild: usually under 2 KiB
- ATC clearances: under 1 KiB

The pattern is consistent. High-stakes review artifacts are kept short by deliberate design. The 8 KiB cap places assistant-guide.txt in the same neighborhood.

### What the cap does NOT do

It does not guarantee that an 8 KiB guide is safe. It does not guarantee that a publisher used the bytes well. It does not catch a malicious guide that fits inside the limit. Those defenses live elsewhere in the profile (cross-channel hash, action block discipline, prohibited instruction patterns, verifier checks). The cap is one control among several.

### Likely pushback during adoption

Some publishers will report that their flow needs 9 or 10 KiB. Two responses are reasonable:

1. Suggest decomposition. Most flows that overflow are bundling two bounded tasks.
2. Suggest the profile is the wrong tool. If the flow genuinely needs continuous human judgment per step, a different interaction model (interactive CLI, docs site, installer wizard) fits better than the agent-assisted bounded-task model this profile targets.

Hold the line at 8 KiB unless field data from real adopters shows the limit is forcing decomposition in cases where bundling is the safer pattern. We do not currently have that data; the conservative move is to start tight and relax later if evidence supports it. Relaxing a size cap is easy. Tightening one after adoption is hard.

## ASCII-only byte profile

The spec restricts Level 2 and above to bytes 0x0A and 0x20 through 0x7E. The threat the byte profile defends against is presentation-layer deception: content that a human reviewer cannot see while an assistant ingests it.

Hidden HTML comments, offscreen CSS, white-on-white text, script-inserted content, alternate text, remote embeds, invisible Unicode controls, terminal escape sequences, and zero-width characters are all ways the same bytes can mean different things to different readers. The profile escapes this by restricting to a byte range where what you see is what you get, in every editor, terminal, viewer, and verifier.

Allowing Unicode would reopen homoglyph attacks ("аpple.com" with Cyrillic а), bidi-override attacks, mixed-script obfuscation, and zero-width-joiner tricks. The cost of those attack vectors is high; the benefit of allowing Unicode in the body is moderate (multilingual prose) and is better solved at the locale layer with a separate localized document (see spec section 25).

A future controlled Unicode profile may emerge for guides that need non-ASCII natural language while preserving review integrity, but we have decided against pursuing one in the current spec, and the position is final rather than provisional.

The decisive argument came from a session review. A partial-Unicode profile that allowed non-ASCII in bounded fields like `notes:` while keeping identifiers and commands ASCII was on the table. We rejected it. The reason: any non-ASCII content in the file is interpreted by an assistant that may not respect field boundaries. A bidi override or homoglyph that the spec confines to a `notes:` field is still ingested by the assistant runtime as part of the file. An attacker who can place attack characters anywhere in the file is trying to influence interpretation everywhere in the file. The only defense that does not depend on assistant runtime correctness is to allow no such characters at all, in any field, in any context.

This argument also explains why comparing to security.txt, robots.txt, and llms.txt does not transfer. Those specs permit UTF-8 because none of them carries instructions an assistant will act on with tool access. The blast radius of a homoglyph in a robots.txt URL path is "the crawler fetches the wrong URL." The blast radius of a homoglyph in an assistant-guide.txt `command:` or `cwd:` field is whatever the command does. Threat-model parity is the wrong test; threat-model fit is the right one.

Multilingual needs are served by a separate localized human-facing document, linked from a Level 2+ ASCII guide. This is awkward for non-English publishers. We accepted that cost as the price of the threat-model fit.

## Sidecar manifest, not in-file hash

The hash that identifies which version of the guide a verifier examined lives in an external manifest, not in the guide file itself.

Putting the hash in the file creates a chicken-and-egg problem: hashing the file requires knowing the value to write into it. The workaround patterns (hash with the field zeroed, hash over a canonical form excluding the field) are workable but add complexity to every verifier. The sidecar model has none of that complexity. The file is hashed as it sits on disk. The manifest carries the hash, byte count, immutable release URL, and optional signature.

This approach mirrors the skill-provenance methodology and is intentional. Integrity metadata that lives outside the artifact can be cross-published on independent channels (see next section). Integrity metadata baked into the artifact cannot.

The hash identifies which version of the file the verifier checked. It does not assert the file is safe. This distinction is restated in the spec because adopters reading "Level 4 has a hash" sometimes infer "Level 4 is safe." It is not. Conformance is not safety, regardless of level.

## Cross-channel hash publication

A manifest served from the same origin as the guide is forge-equivalent to the guide itself: an attacker who controls the web host controls both. The forge cost only rises when the hash is also published on a control plane the web host does not control.

The spec recognizes four independent channels: DNS TXT records, package registry metadata, public repository files, and PGP-signed security.txt. Each has different credentials, typically held by a different team or vendor than the web host. An attacker who wants a clean Level 4 verifier report must compromise the web host AND at least one of these independent channels.

Same-origin surfaces (HTML head link tags, HTTP response headers, unsigned security.txt) are permitted for discovery but explicitly do not count as forge-resistant evidence. Calling them out as discovery-only prevents adopters from believing they have raised the forge cost when they have not.

DNS TXT is the cleanest second channel for most publishers. DNS credentials are typically separate from web-host credentials. DNSSEC, when present, adds cryptographic integrity. TXT records are cheap and standard practice for related artifacts (SPF, DKIM, DMARC, ACME).

## Hard ban on chained guides

The original draft of the no-chains rule wavered between a hard ban and a "fresh ceremony" softening that would let a guide pivot the assistant to a referenced guide with a fresh approval prompt. We rejected the softening.

The threat is silent transitive trust. The human approved guide A. Guide A names guide B. The assistant fetches and acts on B. The human never reviewed B. Even one hop is too far.

The "fresh ceremony" softening creates a soft approval moment exactly where the human is most susceptible to ritual approval. It teaches users that mid-session pivots between guides are normal. It requires the assistant runtime to implement ceremony correctness, adding another layer that can be wrong. It requires verifier heuristics to detect prose-level chaining backdoors. None of these costs buy security; they buy ergonomics at the cost of security.

The strict ban has a clean alternative path for legitimate multi-phase flows: decompose into independent bounded guides, with the human deliberately starting each session against each new URL. Plain prose references for the human to read are permitted; the assistant does not follow them.

The distinction between integrity fetches (manifest, cross-channel anchors, repository file, identity verification of the current guide) and instruction fetches (other guides, runbooks, scripts the assistant would act on) is what makes the rule internally consistent. The verifier and assistant do perform identity fetches. They do not perform instruction fetches across guides.

## Well-known path

The canonical HTTP location is /.well-known/assistant-guide.txt. The repository copy at the repository root is recommended but secondary.

The naming split is intentional:

- GuideCheck is the standard, verifier ecosystem, and public site.
- `assistant-guide.txt` is the artifact.
- The Human-Verifiable Assistant Guide profile defines the artifact's conformance rules.
- A GuideCheck conformance claim requires verifier output, guide hash, achieved level, and findings.

Two reasons to anchor at /.well-known/. First, RFC 8615 establishes this prefix for site-wide standards files, and adopters familiar with security.txt, openid-configuration, change-password, and dnt-policy will look there. Second, anchoring at a path rather than a filename at root prevents collisions with publisher-specific files named assistant-guide.txt that are not conforming.

The repository copy serves a different purpose: it gives the verifier and any reviewer a comparison anchor against what is served, catching drift between source-of-truth and live HTTP. Both copies should hold identical content. Divergence is a finding the verifier reports.

## Action block schema and machine-checkable approval gates

The spec mandates a structured action block (id, class, approval, command, optional cwd, optional egress, optional notes) instead of letting publishers write actions in prose. The reason is enforcement.

Prose-based action descriptions cannot be mechanically checked for missing approval gates. A guide that says "now install the package" in a paragraph might or might not require approval; the verifier cannot tell. A guide that declares the action in a block with class: persistence-changing and approval: required CAN be checked. The verifier flags any privileged, destructive, persistence-changing, or data-accessing action that does not set approval: required as an error.

The structure also forces the publisher to think about classification. Writing "destructive" next to a command is harder to do thoughtlessly than burying it in a paragraph.

## Command field restrictions

The command field is parsed and displayed as a literal. The spec forbids shell substitution ($(...), backticks, ${VAR}), command chaining (&&, ||, ;), redirection in non-normal classes, and glob expansion in privileged or destructive commands.

The reason is that the human approves what they see. Shell substitution means the command displayed at approval time is not the command that runs at execution time. Chaining hides multiple actions behind one approval, defeating per-action approval scope. Glob expansion turns a narrow command into a wide one based on filesystem state.

Each restriction closes a specific gap between "what the human approved" and "what the assistant ran." When the gap closes, the approval ceremony means what it says.

## Verbatim approval display and canonical phrasing

Assistants are required to display the action block verbatim, not paraphrased, when requesting approval. They are also encouraged to use a canonical phrasing template.

Paraphrasing is where the assistant can drift, intentionally or not, from the literal command into something the human might approve more readily. "I am going to clean up the build directory" is not what rm -rf build does in every context. Verbatim display closes that drift.

Canonical phrasing across guides means humans see a consistent approval prompt regardless of which guide they are reviewing. Consistency reduces the cognitive load of approval, which preserves attention for the actual decision: is this command, in this class, in this directory, what I want to authorize.

## HTTPS required

HTTP serving over plain TCP is non-conformant at Levels 2 and above. The reason is that the guide is fetched and ingested as an authoritative instruction surface. A network attacker who can rewrite plaintext HTTP can substitute the guide entirely. TLS is the minimum bar for an artifact that drives high-consequence assistant actions.

Cross-origin redirects also fail the profile. A redirect to a different registered domain is operationally indistinguishable from a host compromise, and we do not want verifiers to treat the two cases differently.

## Time-of-check time-of-use pinning

At Level 4, assistants are advised to pin the manifest guide-sha256 at session start and treat any mid-session change as a stop condition.

The threat is publisher rotation, mirror swap, or attacker-controlled re-host happening between the human's review and the assistant's execution. The guide the human approved is the guide that should run. Pinning the hash at session start anchors the contract to a specific byte sequence; any mid-session change breaks the anchor and forces re-review.

## Supersession requires human restart

When status is deprecated, the assistant must stop the current session, display the superseded-by URL to the user, and require the user to start a new session against that URL manually. The assistant does not auto-follow.

The reason is consistent with the no-chains rule. A deprecated-then-follow flow is an instruction fetch across guides under a different name. The replacement guide is a fresh review with a fresh approval ledger. The human starts it deliberately.

## Conformance is not safety

The spec front-loads a disclaimer in section 1: a verifier returning Level 4 has confirmed structure, byte profile, approval-gate presence, and manifest integrity. It has not confirmed intent, publisher identity, command effect, or environment fit.

The reason this disclaimer is so prominent is anticipated misuse. Standards bodies have learned across decades that conformance badges are read as endorsements. Users skip the careful reading because the artifact "passed." This profile is most useful when humans do not skip. Stating in section 1 that they must not, and explaining why, is the only realistic defense against this failure mode.

Two anti-patterns warrant explicit naming for the same reason: verifier-as-oracle (treating a green result as license to skip reading) and trust transference (concluding a guide is trustworthy because it lives on a domain you trust, or scores well, or is referenced from a popular llms.txt). Both are common failure modes for standards adoption. Naming them in the spec gives reviewers a vocabulary to push back on.

## Locale handling follows security.txt

The spec adopts the security.txt model: a single canonical file per publisher, no required multilingual fork, optional preferred-languages metadata field, translations served at distinct URLs and cross-referenced in prose.

This is not the only viable model. robots.txt ignores locale entirely. Some artifacts have content negotiation. We picked the security.txt approach because it is the closest analogue in spirit (security-relevant, single artifact, machine-readable, human-reviewable) and the closest in deployment friction (publishers already serve security.txt today and the precedent is familiar).

The ASCII-only byte profile means non-ASCII natural language cannot appear in the guide body at Level 2 and above. Publishers needing non-ASCII prose can drop to Level 1 or publish a localized human-facing document at a separate URL while keeping the canonical guide ASCII. The tradeoff is explicit and the spec does not paper over it.

## Markdown clarification: characters, not rendering

The spec forbids HTML, CSS, JavaScript, images, embeds, and rich-document constructs. It does not forbid Markdown-like syntax (# headings, hyphen lists, fenced code blocks).

The distinction matters because the threat is the rendering layer, not the characters themselves. There is nothing inherently dangerous about #. The danger is a renderer that interprets it differently from how the raw text reads. Since conforming guides are .txt files served as text/plain, browsers, editors, and verifiers display the raw bytes. The renderer that would create deception is not invoked.

Verifiers must treat the file as plain text and must not render Markdown. The point is to preserve byte-level equivalence between what the human sees and what the assistant ingests.

## Signature and transparency-log stay RECOMMENDED at Level 4

The manifest field `signature` and a transparency-log entry are both RECOMMENDED at Level 4, not REQUIRED. We considered raising them to MUST and decided against for v0.1.

The cross-channel hash requirement already gives Level 4 meaningful forge resistance. An attacker who wants a clean Level 4 verifier report must compromise the web host plus at least one independent channel (DNS, package registry, public repo, or signed security.txt). Adding signature-MUST on top would more than double the operational burden for a fractional improvement at the current adoption stage.

The signing-key ecosystem is in transition. PGP is declining. Sigstore is rising but not universal. Container signing standards exist but are not adopted everywhere. Locking Level 4 to a specific signing scheme now would either fragment Level 4 (different verifier outputs for different signature backends) or pick a winner prematurely.

The right rhetorical move is to reserve a higher provenance tier for signature plus transparency-log evidence, rather than retrofitting MUST into Level 4 later. This gives current Level 4 adopters a stable target and gives security-mature publishers a higher provenance target when their infrastructure supports it.

For v0.1 the guidance is: publishers with any code-signing infrastructure available SHOULD include a signature reference in the manifest. A Level 4 manifest with a signature is a stronger provenance posture than one without, and verifiers SHOULD report which form was found.

## No central registry

The spec does not define a registry of conforming guides. We considered it and rejected it.

A registry sounds appealing for marketing reasons: a public list of projects with conforming guides drives adoption, supports badge ecosystems, and gives operators a third-party reference. We accept all of that. None of it is a security argument.

For security, a registry is net negative. It concentrates trust in a single operator. Compromise the registry, and an attacker can mark malicious guides as conformant or mark legitimate guides as revoked. The registry inherits the trust property of every guide it lists, which is the concentrated-trust pattern this profile was designed to avoid. It also invites the verifier-as-oracle anti-pattern at scale: operators treat "in the registry" as "safe to follow," which contradicts the conformance-is-not-safety stance the spec front-loads in section 1.

The artifact-plus-channels model already gives operators what they need to verify a guide: run a verifier against the URL, check the cross-channel hash, read the file. No registry required. Revocation works through the publisher's own `status: revoked` field and cross-channel hash mismatch detection. A central revocation list is not necessary.

A federated index (multiple independent crawlers and indexes, none authoritative) avoids the centralization risk but lacks a value proposition at the current adoption stage. If demand emerges later, that is the right model. It should be advisory, non-endorsing, run by neutral parties, and never claim to confer trust beyond what the artifact itself supports.

Supporter or implementer lists are fine outside the spec. A README section, a CONTRIBUTORS file, a community page. These carry no security claim and are explicitly not registries.

## Threat register lives in its own document

Detailed enumeration of known risk classes (network path, origin and hosting, provenance anchor, verifier implementation, agent and runtime, user and workflow, availability) is in `threat-register.md`. Fixture authors, verifier implementers, and runtime designers should treat that document as required reading alongside this one. The split keeps `design-rationale.md` focused on why decisions were made and `threat-register.md` focused on what risks remain.

## Future entries

Add further design rationale here under their own headings as the spec evolves.
