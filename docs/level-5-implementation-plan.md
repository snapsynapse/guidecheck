# Level 5 Runtime Conformance Implementation Plan

Status: committed implementation plan; the profile it produces stays a design
draft until its fixture suite and evaluator exist.

Per the 2026-06-09 decision recorded in `INTENT.md` under Level 5 ownership,
GuideCheck owns this work: the runtime fixture suite and the scenario-driven
evaluator are deliverables of the standard. Execution is gated by
`docs/pre-level-5-readiness.md`, and no runtime conformance claim is made
before the gate clears.

This plan sequences work needed to turn the Level 5 runtime conformance design
into a testable GuideCheck profile. It keeps Level 5 separate from the Level 1
through Level 4 guide verifier.

## Goals

- Define a GuideCheck-owned runtime conformance profile for Level 5.
- Build a scenario-driven evaluator that tests runtime behavior.
- Produce reproducible evidence from the same event model for human reports,
  machine-readable reports, and optional ACS/AOS exports.
- Keep ACS/AOS, MCP, A2A, OpenTelemetry, OCSF, and AgBOM as optional
  interoperability surfaces.
- Keep MCP and A2A enforcement out of core Level 5 unless a future spec change
  explicitly promotes them.

## Non-goals

- Do not extend the guide-only verifier to report achieved Level 5.
- Do not make ACS or AOS a required dependency.
- Do not certify command safety, publisher trust, model quality, or
  environment suitability.
- Do not require production credentials, real destructive operations, or
  uncontrolled network calls in the conformance suite.

## Phase 0: Profile framing

Deliverables:

- Move `docs/level-5-runtime-conformance.md` from design note to candidate
  profile once open questions are resolved.
- Add stable terminology for runtime, harness, scenario, event, verdict,
  ledger, and evidence.
- Define `declared_enforced_surfaces` for optional tool, MCP, A2A, memory, or
  knowledge-retrieval enforcement.
- Scope runtime conformance to the runtime build, policy configuration, and
  guide SHA-256.
- Define the session boundary as starting after user confirmation of a verified
  guide hash and ending on explicit close, runtime restart, guide hash change,
  verifier result change, or a declared idle timeout.
- Define claim language and non-claim language.

Exit criteria:

- `spec.md` still states Level 5 requirements.
- The Level 5 runtime profile explains how those requirements are evaluated.
- No document implies a guide-only Level 5 score.

## Phase 1: Evidence model and schema draft

Deliverables:

- Draft `schemas/runtime-evaluation-output.schema.json`.
- Draft `schemas/runtime-event.schema.json` or an equivalent event fragment
  used inside the evaluation output.
- Define stable scenario result values: `pass`, `fail`, `skip`,
  `inconclusive`.
- Define stable verdict values: `allow`, `deny`, `modify`,
  `approval-requested`, `approval-granted`, `approval-denied`, `executed`,
  `stopped`.
- Define finding severities aligned with verifier output: `error`, `warning`,
  `info`.
- Reference draft runtime reason codes from `docs/runtime-reason-codes.md`.

Exit criteria:

- The schema can represent every event required by the core test phases.
- The schema can reference, but does not require, ACS/AOS records.
- The schema records declared enforced surfaces without requiring MCP or A2A.
- The compact report can be generated from the same evidence object.

## Phase 2: Scenario corpus

Deliverables:

- Add `runtime-fixtures/` or `fixtures/runtime/`.
- Create positive and negative scenarios for:
  - verification gate
  - guide hash mismatch
  - action boundary
  - approval ledger scope
  - runner enforcement
  - cwd enforcement
  - env enforcement
  - egress enforcement or disclosure
  - stop conditions
  - memory storage
- Create optional enforced-surface scenarios for MCP tool-call mapping and A2A
  delegation boundary only after the core scenario corpus is stable.
- Add expected result files for each scenario.

Exit criteria:

- Scenarios are deterministic and require no production credentials.
- Destructive and networked behavior uses fake tools, local harness servers, or
  synthetic command runners.
- Fixture expectations can be checked without invoking an LLM.

## Phase 3: Runtime harness interface

Deliverables:

- Define a portable harness protocol for driving runtimes through scenarios.
- Support at least one local adapter that simulates runtime decisions without
  needing a real assistant product.
- Define required harness operations:
  - load guide bytes
  - provide verifier output
  - provide runtime policy configuration
  - present compact report
  - simulate user confirmation
  - propose action
  - approve, deny, or cancel action
  - attempt tool call
  - attempt memory store
  - attempt declared-surface operation
  - collect event log

Exit criteria:

- The evaluator can run against a reference fake runtime.
- Runtime adapters can be added without changing scenario semantics.
- The harness can prove both positive and negative behavior.

## Phase 4: Evaluator prototype

Deliverables:

- Add `scripts/eval_runtime_level5.py` or equivalent.
- Load scenario bundles.
- Drive the harness adapter.
- Validate emitted events against the runtime event schema.
- Compare scenario results to expected files.
- Emit JSON and compact text reports.

Exit criteria:

- The fake runtime passes positive scenarios and fails intentional negative
  variants.
- CI can run the runtime fixture suite in deterministic local mode.
- The existing Level 1 through Level 4 verifier tests remain unchanged.

## Phase 5: ACS/AOS adapter

Deliverables:

- Add an optional adapter that exports GuideCheck runtime events to ACS/AOS
  request and response records.
- Add example records for:
  - guide verification
  - action proposal
  - enforcement verdict
  - tool result
  - memory store denial
  - MCP tool call denial
  - A2A delegation denial
- Validate example records against the current ACS/AOS JSON schema when the
  schema is locally available.
- Add a non-dependency test showing the core evaluator passes when ACS/AOS
  export is disabled and no ACS/AOS records are present.

Exit criteria:

- ACS/AOS export is generated from the GuideCheck event model.
- Missing ACS/AOS tooling does not block core Level 5 evaluation.
- Docs clearly state that ACS/AOS evidence supports but does not establish
  GuideCheck Level 5 by itself.

## Phase 6: Documentation integration

Deliverables:

- Link the Level 5 runtime conformance doc from `README.md`, `ADOPTION.md`,
  and `roadmap.md` once it is stable enough for public navigation.
- Add a short operator explanation that Level 5 is evaluated deployment
  behavior, not a guide score.
- Add examples of passing, failing, and inconclusive runtime reports.
- Add a migration note for runtime implementers that already emit ACS/AOS
  records.
- Keep detailed runtime sequencing in this plan and keep `roadmap.md` at the
  level of milestones.

Exit criteria:

- Public docs consistently say `Guide score: Level 4 of 4` and
  `Runtime: Level 5 evaluated` where applicable.
- No docs suggest `Level 4 of 5` or `almost Level 5`.
- Runtime implementers can find the scenario corpus and output schema.

## Phase 7: Conformance claim hardening

Deliverables:

- Decide whether runtime evaluation reports should be signed.
- Decide whether fixture suite releases should be signed before accepting
  third-party runtime claims.
- Define report retention and reproducibility expectations.
- Define versioning rules for the runtime profile and fixture suite.

Exit criteria:

- A third party can reproduce a runtime conformance result from the same
  runtime build, policy configuration, guide hash, verifier output, and
  scenario bundle.
- Claims include enough version data to be falsifiable.

## Initial file map

- `docs/level-5-runtime-conformance.md`: design note and candidate profile.
- `docs/level-5-implementation-plan.md`: phased implementation plan.
- `schemas/runtime-evaluation-output.schema.json`: future output schema.
- `schemas/runtime-event.schema.json`: future event schema, if separated.
- `fixtures/runtime/`: future runtime scenario corpus.
- `scripts/eval_runtime_level5.py`: future local evaluator.
- `examples/runtime-reports/`: future human and JSON examples.
- `docs/runtime-reason-codes.md`: draft runtime decision-code registry.

## Suggested first implementation slice

Start with the smallest executable path:

1. Define the runtime evaluation output schema.
2. Create five scenarios: verify gate pass, hash mismatch fail, prose command
   fail, action approval pass, approval scope mismatch fail.
3. Implement a fake runtime adapter.
4. Implement the evaluator against the fake runtime.
5. Add compact report rendering.
6. Add CI coverage for the runtime fixture suite.

That slice proves the evaluation architecture before tackling network,
memory, MCP, A2A, and ACS/AOS exports.
