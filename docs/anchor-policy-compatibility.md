# Version-aware anchor policy proposal

Status: approved implementation contract for 1.0.0. Publication and deployment authorized by Sam; delivery evidence is recorded separately.
Scope: GuideCheck AIDR-0001, repository-anchor qualification only.
Baseline: 3ceb30a58488f925844c51c5aad0bc0f94633ff7.

## Approval condition

Sam Rogers's response on 2026-09-05, transcribed verbatim:

> Yes I do approve, provided that the existing level 4 conformant repos are not adversely impacted. I believe we handle this well enough through versioning but I want to make sure that we don't break things with this change

This condition limits the dependent proposal in
[AIDR-0001](../decisions/AIDR-0001-same-control-plane-repository-anchors.md).
The proposed stricter policy must not be applied retrospectively to existing
guides. It does not authorize mandatory migration, retroactive loss of Level 4,
or changing existing guide bytes to meet the new policy.

This is the approved implementation contract, revised at Sam's request to include
version-aware dispatch. It replaces the unconditional application and forced
migration described in the original dependent AIDR position; the position is
retained as recorded reasoning. Sam's approval is conditional on compatibility,
not a claim that compatibility has already been demonstrated for new code.

Sam also reports being the only known user, while noting that external users
cannot be ruled out. Known first-party repositories form the initial adopter
test set. This is not evidence of zero external adoption and does not authorize
breaking unknown consumers. Changes to dependent repositories are not a
prerequisite for legacy compatibility and are not included in this proposal.

## Why a version bump alone is insufficient

The pre-dispatch baseline evaluator requires the `profile-version` metadata field but does
not dispatch anchor evaluation by its value. `GUIDECHECK_VERSION`,
`GUIDE_PROFILE_VERSION`, and `VERIFIER_PROFILE_VERSION` are coupled constants.
The hosted endpoint and local CLI call the same evaluator. Replacing its anchor
predicate globally would downgrade old guides regardless of their declared
version. Bumping the tool or specification version does not prevent that.

The compatibility reference is the behavior of baseline 3ceb30a for previously
accepted inputs, not a claim to reproduce every historical verifier release.
Current static fixtures contain older declarations, and existing hosted tests
explicitly accept a same-repository Pages anchor. Preserve those expectations.

## Required behavior

1. Keep the existing anchor semantics for legacy guides. The published versions
   represented by local release tags are 0.1.0, 0.2.0, 0.3.0, 0.3.1, 0.4.0,
   0.5.0, 0.6.0, 0.7.0, and 0.7.1. Future code must explicitly define supported
   versions rather than using a catch-all numerical comparison.
2. Apply strict repository qualification only when the guide deliberately opts
   into the supported new major profile. No default-to-latest behavior in the
   existing CLI or hosted endpoint. A verifier software upgrade alone must not
   switch the policy used for an unchanged legacy guide.
3. Separate verifier software version, declared guide profile, and evaluated
   policy in reporting. An old-profile Level 4 result remains Level 4 under its
   old policy; it is never relabeled as new-profile conformance. Additive report
   metadata must not introduce new required fields into the legacy contract or
   change its established fields, exit codes, severity counts, or proceed result.
4. Treat an explicit new-profile migration assessment as a separate result. It
   must not replace the ordinary legacy conformance result or fail existing CI
   merely because the guide would not meet the new rules.
5. A new-profile guide or request must not fall back to legacy qualification
   after an unsupported version, malformed version, conflicting guide/manifest
   declaration, or failed strict check. Existing malformed-input behavior must
   not be incidentally rewritten as part of this change.
6. Preserve legacy local-file caps and hosted fetched-evidence requirements.
   Preserve mismatch blocking. Compatibility does not mean accepting newly
   invalid bytes, expired/revoked metadata, missing evidence, or network failure.
7. Keep existing guides, manifests, repository anchors, DNS TXT values, release
   artifacts, and version-specific documentation available and unchanged.
   Updating a self-guide during version synchronization would change its hash
   and require anchor rotation, so decouple those checks before a major bump.
8. Do not introduce a legacy support sunset or compulsory migration in this
   tranche. Such a policy needs a separate maintainer decision.

This intentionally leaves the old policy's known independence limitation in
legacy results. Preserving those claims and imposing the strict rule on the
same results are incompatible objectives. Reports must state which policy was
evaluated without converting that distinction into a legacy failure.

## Dispatch design

### Policy selection

Use one shared, side-effect-free selector for the CLI and hosted entry point.
Select from the guide's original metadata bytes before anchor qualification.
Keep the input bytes and guide hash unchanged. Do not rewrite metadata to run
an old guide through the new engine, and do not infer policy from the installed
package version, hostname, requested conformance level, or current date.

The selector returns an immutable selection containing the declared version,
the selected engine, and its policy identifier, or a dispatch error. Pass that
selection through fetching, evaluation, and reporting. No downstream caller may
select a policy again from mutable defaults or from the observed hash result.

| Guide declaration or request | Selection | Contract |
|---|---|---|
| Exact 0.1.0, 0.2.0, 0.3.0, 0.3.1, 0.4.0, 0.5.0, 0.6.0, 0.7.0, or 0.7.1 | Legacy engine, baseline 3ceb30a | Preserve existing anchor eligibility, levels, findings, reports, and CLI exit behavior |
| Exact 1.0.0, after that profile is implemented and supported | Strict engine | Repository matches remain visible but do not qualify; another qualifying channel is required for Level 4 |
| 1.0.0 before support is enabled | Unsupported | No legacy fallback and no 1.0.0 conformance result |
| Supported release plus syntactically valid SemVer build metadata | Same policy key as that release | Preserve the raw declaration; build metadata never selects stronger or weaker rules |
| Any unlisted release, range, prerelease, or malformed version token | Unsupported or invalid selector | Never silently map to the nearest version; no prerelease-to-final fallback |
| A lower-level guide with no metadata block/version declaration | Existing legacy diagnostic path | Preserve valid Level 1/2 use and existing missing-metadata diagnostics; do not invent a profile declaration |
| Duplicate, conflicting, or malformed metadata boundaries | Invalid selector or existing legacy failure | Never choose one conflicting version by first-value or last-value wins; never produce a new positive conformance result |
| Caller explicitly requires 1.0.0 but guide declares a legacy version | Requirement mismatch | Reject; a caller's required profile is an assertion, not an instruction to reinterpret old bytes |

For malformed legacy inputs already rejected by the baseline, preserve existing
diagnostics where there is an unambiguous legacy selection. If there is no unique
selection, return a dispatch error instead of guessing. A required-profile
assertion always takes precedence over that compatibility diagnostic path.

The supported legacy list is explicit. Do not implement `major < 1` or `version
<= current` as a shortcut. The existing verifier may accept undeclared or
unpublished versions because it does not validate them; these are an inventory
gap, not evidence of support. If a must-preserve adopter uses one, stop rollout
and resolve it explicitly before changing hosted behavior. Do not silently add
an exception or require the adopter to change bytes to make a test pass.

Parse SemVer syntax strictly before lookup. For this proposal, the policy key is
the supported release version with valid build metadata omitted. Preserve the
raw version in the selection record. For example, `0.7.1+build.7` selects legacy
0.7.1 and `1.0.0+build.7` selects strict 1.0.0; `1.0.0-rc.1` does not select the
final release. This is an explicit GuideCheck dispatch rule informed by
[SemVer sections 9-11](https://semver.org/#spec-item-9), which distinguish
prereleases from build metadata. Test empty suffixes, illegal characters,
leading zeroes, and valid build identifiers. Audit the broader published schema
against this parser before release; previously accepted but nonconforming input
is not a reason to silently map to an unsupported policy.

### Manifest and caller consistency

The guide is the primary selector. A manifest never upgrades or downgrades the
selected policy. A legacy manifest may omit its currently optional profile
fields without losing eligibility. Preserve existing handling of old-only
manifest metadata within the legacy engine.

For 1.0.0, require the manifest's profile name and version to agree with the
guide, in addition to its hash and byte-count checks. Reject missing, duplicate,
or conflicting profile selectors in new-profile manifests. A legacy guide
accompanied by an explicit 1.0.0 manifest must not be accepted as a new-profile
result. Contradictory cross-major evidence is a dispatch/evidence error, never
a reason to switch engines.

Add an optional `required_profile_version` hosted request field and
`--require-profile-version` CLI assertion. Both require a supported version
without ranges and compare its policy key with the selected guide's policy key.
Valid build metadata is retained but ignored for that policy comparison. They do not alter
guide bytes or choose a weaker evaluator. Existing requests and commands omit
them and retain declared-version dispatch. `requested_level` and `--level`
retain their existing behavior; level and profile are different constraints.

An unsupported selector or unsatisfied caller profile assertion returns an
explicit error with no conformance claim: the existing hosted error-envelope
shape with HTTP 400, or a CLI dispatch/usage error with exit 2. Proposed error
codes are `profile-version-unsupported`, `profile-version-ambiguous`, and
`profile-version-requirement-mismatch`. Strict manifest disagreement is instead
a blocking `manifest.profile-version.mismatch` finding under the already
selected strict engine; it prevents Level 4 without invoking legacy evaluation.

Selecting a supported legacy profile intentionally remains possible. Otherwise
backward compatibility would be illusory. A consumer requiring the stronger
policy must pin that requirement using the new assertion. This is the explicit
defense against a publisher changing a guide's declaration back to 0.7.1; a
default legacy-compatible verifier cannot promise that defense on the caller's
behalf. No legacy Level 4 result is presented as satisfying a 1.0.0 requirement.

### Engine and output isolation

Preserve the baseline evaluator and its constants, anchor adapter behavior,
report builders, and schema as a versioned legacy implementation. Move or wrap
them without semantic changes and establish equivalence before introducing
strict behavior. Avoid scattering conditional version checks through the
existing evaluator. Both engines may share transport code only when fixed-input
replay proves that doing so preserves legacy fetch order, budgets, and results.
New topology lookups are not part of the strict policy or legacy request path.

Keep the existing CLI command and `/api/verify` entry point. They dispatch to
the selected engine. Legacy results retain the existing JSON body structure,
anchor objects, finding order and severity counts, compact report, and exit
codes. Do not append migration warnings to legacy reports. Their `verifier`
object identifies the legacy engine and its 0.7.1 verification contract, not the
new dispatcher package. That identity is honest only while the preserved engine
is equivalent to baseline 3ceb30a; record the baseline commit in implementation
provenance. Do not mislabel modified strict logic as the legacy engine.

The dispatcher/package has its own software version, reported by package/CLI
version output and hosted response metadata outside the legacy JSON body.
The legacy guide-profile version in the established report remains 0.7.1,
meaning the current legacy checking contract, even when the guide declares an
older supported version. This is not a new claim of exact historical semantics.
The new-profile report explicitly identifies declaration 1.0.0, evaluated
profile 1.0.0, strict engine version, and the qualification fields proposed in
the AIDR. New required fields belong to a separate versioned output schema;
they are not retrofitted into the legacy schema.

The UI routes rendering by the report's evaluated profile. Its legacy rendering
path remains unchanged; the strict path shows qualifying evidence and the
profile used. Downloads and copied compact reports use the same selected
result. A migration comparison feature is deferred from this tranche; it must
never replace a normal legacy result if introduced later.

### Version and artifact separation

Replace the single-version synchronization assumption with explicit assertions
for dispatcher/package version, each engine's verifier contract, supported guide
profiles, latest released profile, and the repository's own published guide.
Retain checks for byte-identical root and well-known copies. Pin the existing
self-guide, manifest, and anchor hashes before editing version-bearing files.

In particular, a package or new-profile version bump must not rewrite the
self-guide's `profile-version`, `guide-version`, `applies-to`, or
`verifier-conformance` range. The compatibility verifier can still evaluate
that guide through its legacy engine. Old verifier-conformance ranges refer
to the selected legacy engine's contract, not the dispatcher version. Do not
introduce new range-enforcement behavior into legacy evaluation in this change;
the current core does not enforce that field as a version selector.

Preserve immutable legacy spec/schema references and published release assets.
Prepare new-profile documents and fixtures under explicit new-version identity.
Do not present 1.0.0 as released merely to satisfy the version checker. The
new profile and dispatcher release remain a major release, with release status
separate from development version. Exact package/entry-point commands used by
adopters must be exercised, including consumers that pin older tool versions.

## Paired compatibility acceptance matrix

Every row defines an acceptance test; implementation evidence is linked below.
Legacy/new fixture pairs differ in their intentional profile declarations and
recomputed manifest bindings only; tests must not leave stale hashes after
changing metadata. All otherwise valid content and fetch evidence are replayed
at a fixed time against both baseline and candidate.

| Case | Legacy expected | New-profile expected |
|---|---|---|
| Matching repository only, Pages or custom domain | Level 4, unchanged report | Level 3; no qualifying anchor |
| Matching repository plus qualifying matching DNS | Level 4, unchanged report | Level 4; repository still excluded |
| Repository mismatch plus matching DNS | Existing Level 4 failure preserved | Level 4 failure with strict mismatch identity |
| Local supplied matching evidence | Existing Level 3 cap and report | Level 3 cap; no fetched provenance claim |
| Known missing/unreachable or conflicting evidence | Existing failure/availability behavior preserved | Strict matrix outcomes; no fallback |
| Guide has old verifier-conformance range | Same legacy behavior under upgraded package | New guide names a compatible strict engine; dispatcher version is not substituted |
| Caller requires 1.0.0 | Requirement mismatch, no new-profile claim | Strict result, or strict failure; never legacy fallback |
| Unsupported, ambiguous, or cross-major selectors | No guessed support; inventory exceptions block rollout | Explicit failure before qualification |
| Requests alternating legacy/new versions in one process | Stable legacy engine and response every time | Stable strict engine and response every time |
| Concurrent requests and evidence-cache reuse | No strict state leaks into legacy evaluation | Cached bytes cannot import legacy qualification |
| Version update and artifact checks | Self-guide/manifest/anchor bytes unchanged | New-version artifacts explicitly identified |
| CLI/API/compact report/UI/download | Existing result and consumer parsing preserved | One coherent profile and qualification result |

Extend differential testing beyond the 54 initial cases: compare every existing
static fixture and hosted scenario with baseline outputs, including exact finding
sets, counts, levels, readiness, anchor evidence, and CLI exit status. Normalize
only documented volatile fields such as timestamps and absolute fixture paths.
Do not normalize away policy versions, finding order, new warnings, anchor status,
or report changes. Preserve the old expectations; add new-profile cases instead
of changing legacy expected results to fit the candidate.

## Readiness and remaining decisions

Implementation update: Sam approved this proposal with "Proposal approved.
Please continue" on 2026-09-05. The local dispatcher, isolated legacy engine,
strict engine, versioned schemas/specifications, and regression gates are now
implemented. See [validation evidence](anchor-dispatch-validation.md) for the
current results. The sequence below remains the acceptance and delivery checklist.

Local implementation is complete. Legacy compatibility, caller opt-in, engine
isolation, and versioned qualification are covered by the local regression gates.
Sam's existing approval remains conditional on preserving that compatibility.

Publication and deployment are authorized by Sam. The candidate has been compared
with freshly fetched public adopter artifacts, but exact committed CI, release
artifacts, and staged deployment checks remain. Do not make a zero-breakage
guarantee for unknown external consumers from the observed compatibility results.

| Checkpoint | Evidence required to move on | Current state |
|---|---|---|
| Legacy isolation and dispatch | Exact baseline differential suite, selector grammar coverage, legacy output and package-entry-point compatibility | Implemented; baseline replay and installed-wheel checks pass |
| New profile implementation | Paired old/new fixtures, caller assertions, schema/report parity, mixed-request isolation, full suite | Implemented and locally validated |
| Adopter compatibility | Read-only first-party inventory; recorded versions, hashes, verifier ranges, CI commands, and baseline/candidate results | 25 local paths and 16 public fetch/replay reports match baseline |
| Release readiness | All preceding gates pass, immutable legacy references available, self-guide/anchors unchanged, release/version checks pass | Local gates pass; exact committed CI, release assets, and staged deployment verification remain |
| Deployment | Separately authorized publication/deployment, staged verification, known prior deployment and reviewed rollback steps | Authorized by Sam in the subsequent release request; verification remains required |

No new information is required from Sam to revise this proposal or begin local
implementation. Known external consumers would be useful additions if they
surface, but their absence does not block local work. If inventory finds an
adopter that cannot be preserved by the proposed dispatcher, bring back that
specific repository, command, before/after result, and proposed resolution.
Do not reopen the whole policy decision or ask for blanket permission to migrate
everything. Sam subsequently authorized staging, commit, push, release, and deployment.
Dependent-repository and anchor changes remain outside this release.

## Implementation sequence and release gate

1. Establish the unchanged baseline and a permanent legacy compatibility test
   covering each listed version through the actual hosted request handler and
   shared evaluator, including repository-only Pages and custom-domain guides.
2. Implement explicit version selection and report identity before changing any
   qualification predicate. Legacy output must still satisfy its existing schema.
3. Implement the strict predicate exclusively in the new-profile path. Extend
   the AIDR fixture matrix with paired old/new cases from the same guide content,
   including supported new versions, unsupported future versions, and mismatched
   declarations. Old repository-only guides pass under the old policy; opted-in
   new guides require another qualifying channel.
4. Preserve published profile documentation while preparing the new major
   normative documents and schema. Decouple software, profile, self-guide, and
   release-status checks; do not mutate published anchor bytes as a side effect.
5. Run the complete suite with old expectations intact and new expectations in
   separate cases. Check JSON, compact report, CLI exit, hosted endpoint, and UI
   parity. Compare representative adopter artifacts against the unchanged
   baseline at a fixed evaluation time and with replayed fetch responses.
6. Before any separately authorized deployment, compare current and candidate
   hosted results for known first-party Level 4 adopters without modifying their
   repositories or anchors. Record which published guide bytes were evaluated.
   A regression blocks release. Keep the previous deployment available for
   rollback; deployment and rollback actions require their own authorization.

Passing baseline tests alone establishes a reference. The candidate's regression
tests and adopter comparisons provide the implementation evidence; release and
deployment require their remaining gates. No universal no-regression claim is
earned by the synthetic suite or finite adopter sample.

## Baseline capture before implementation, 2026-09-05

- `scripts/test_legacy_anchor_compatibility.py` is wired into `make test` and
  passes 54 replayed scenarios across the nine pinned legacy declarations:
  18 hosted repository-only results, nine local consistency results, and
  27 mismatch/missing-anchor results. Hosted cases include Pages and a custom
  domain, and preserve anchor output, level, warning count, and compact result.
- Full `make test` passed: 138 evals, 74 reference fixtures, 84 contract
  validations, and all existing regression suites, plus the new compatibility
  gate. AIDR lint and `git diff --check` passed.
- No verifier policy, version constant, published guide, manifest, or anchor
  changed during this compatibility preparation. Version-aware dispatch,
  strict-profile implementation, and candidate-versus-adopter comparison remain
  pending. Nothing was committed, pushed, released, or deployed.
