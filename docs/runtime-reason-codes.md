# Runtime Reason Codes

Status: draft registry for future Level 5 runtime evaluation.

This draft registry is for runtime enforcement decisions. It is separate from
`finding-ids.md`, which records guide verifier finding ids. Codes here are not
normative until a runtime conformance profile and fixture suite exist.

Runtime reason codes should remain separate from verifier finding ids unless a
future profile revision deliberately merges the registries. The two registries
represent different evidence: verifier findings describe guide artifacts;
runtime reason codes describe runtime decisions.

## Format

Runtime reason codes use lowercase dotted identifiers:

```text
guidecheck.<area>.<reason>
```

Runtime evaluators and adapters should preserve these codes in machine-readable
output so allow, deny, modify, approval, execution, and stop decisions can be
compared across runtimes.

## Draft codes

| Code | Decision class | Meaning |
|---|---|---|
| `guidecheck.verify.required` | stopped | No conformant verifier result was available before action. |
| `guidecheck.verify.hash_mismatch` | stopped | Runtime guide bytes differed from verifier-reported SHA-256. |
| `guidecheck.guide.level4_required` | stopped | The guide did not achieve Level 4 for a Level 5 evaluation. |
| `guidecheck.action.unknown` | denied | Requested action id is not present in the pinned guide. |
| `guidecheck.action.prose_not_executable` | denied | Requested operation came from prose, notes, metadata, or other non-action content. |
| `guidecheck.approval.required` | approval-requested | Action requires explicit user approval before execution. |
| `guidecheck.approval.scope_mismatch` | denied | Approval was bound to a different action, guide hash, verifier result, or session. |
| `guidecheck.runner.shell_not_declared` | denied | Operation would invoke a shell without `runner: shell`. |
| `guidecheck.runner.shell_rationale_missing` | denied | Shell runner action lacks the required narrow `notes` rationale for the evaluator scenario. |
| `guidecheck.cwd.out_of_scope` | denied | Operation attempts filesystem access outside declared `cwd`. |
| `guidecheck.env.undeclared` | denied | Operation references an environment variable not declared by the action. |
| `guidecheck.egress.out_of_scope` | denied | Operation attempts network egress outside declared `egress`. |
| `guidecheck.memory.reconfirmation_required` | denied | Long-term memory storage needs explicit current-session reconfirmation. |
| `guidecheck.delegation.boundary_required` | denied | Delegation requires a fresh reviewed boundary. |
| `guidecheck.surface.not_declared` | denied | Runtime was asked to enforce or use a surface not declared in evaluation inputs. |
| `guidecheck.stop.chained_guide` | stopped | Runtime encountered a chained-guide instruction. |

## Open questions

- Which draft codes should become fixture-required once the runtime fixture
  suite exists?
- Should reason-code versioning follow the runtime profile version or a
  separate registry version?
- Should adapters translate these codes to ACS/AOS reason codes, or preserve
  them as GuideCheck-native values inside adapter metadata?
