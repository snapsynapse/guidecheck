# Experimental CLI contract
`guidecheck verify` preserves its existing output and exit behavior unless the caller explicitly passes `--contract posix-json-v1`. The selector is experimental. It does not select or reinterpret a GuideCheck profile. `guidecheck scan` does not implement this contract.
## Process boundary
The selected contract writes exactly one terminal JSON object to stdout. Help text may be written to stderr. The terminal object follows `schemas/cli-result-posix-json-v1.json` and separates operational completion from the requested verification gate.
If a selected invocation ends without that terminal object, the run is incomplete. Diagnostics do not substitute for a terminal record.
`operational.status: complete` means the local verifier evaluated the guide and produced the nested `report`. It does not mean the guide passed. The `report` value is the established GuideCheck verifier report without renamed or removed fields. `legacy_exit_code` records the exit status the ordinary verifier invocation would have returned for the same evaluated report and gate flags.
Contract help completes without requesting verification, so its terminal record has `gate.status: not_requested` and no report.
GuideCheck's schema shares the A11y pilot's contract identity, operational result, gate status, terminal marker, and exit-status conventions. Its schema is tool-specific. The A11y adapter models a multi-stage pipeline and accessibility gate modes; GuideCheck models one local verification operation, uses `gate.mode: verify`, and nests the established verifier report. Consumers must validate against the GuideCheck schema.
The local verifier evaluates Levels 1 through 3. It can check local Level 4 sidecar and anchor consistency, but it cannot establish fetched provenance or award Level 4. When `--level 4` is the only unmet gate, the contract reports `inconclusive` rather than treating the local capability limit as proof of nonconformance. Blocking findings and a requested warning failure take rejection precedence.
`--format text` and `--pretty` cannot be combined with the selected contract because the contract owns stdout. `--json` is accepted as a redundant JSON assertion. Without `--contract posix-json-v1`, all three retain their established behavior.
The selected parser rejects abbreviated options, unknown selectors, duplicate singular options, and repeated `--anchor` channels. `--anchor` may be repeated only for distinct channels. Text after a literal `--` remains a path argument and does not select the contract.
Contract options use separate values only: write `--contract posix-json-v1`, not `--contract=posix-json-v1`.
| Error id | Remediation |
|---|---|
| `invalid-invocation`, `unsupported-option-syntax`, `missing-contract-value`, `unsupported-contract`, `duplicate-option`, `conflicting-output-option`, `duplicate-anchor-channel` | Correct the contract arguments and run the command again. |
| `invalid-profile-data`, `invalid-input-text` | Correct the guide, sidecar, or profile assertion before repeating. |
| `guide-input-missing`, `manifest-input-missing`, `anchor-input-missing` | Provide the missing local input path. |
| `input-permission-denied` | Grant read access to the named input. |
| `input-io-failure` | Resolve the identified local I/O condition. |
| `operational-failure` | Inspect stderr and reconcile the local verifier state before repeating. |
## Exit status
| Status | Meaning |
|---|---|
| 0 | Verification completed and the requested gate accepted, or contract help completed. |
| 2 | Verification completed with a confirmed gate rejection. |
| 3 | Verification completed, but local evaluation cannot establish the requested Level 4 result. |
| 64 | The contract invocation is malformed or uses an unsupported option, selector, or output flag. |
| 65 | The requested profile or guide profile data is invalid or unsupported. |
| 66 | A required guide, manifest, or anchor input is missing. |
| 74 | The verifier has specific file I/O failure evidence. |
| 77 | The verifier has specific permission-denied evidence. |
| 1 | Verification failed without evidence for a narrower category. |
`retryable` and `safe_to_repeat` are conservative. Operational failures set both to false. The contract does not infer a category from diagnostic prose.
## Invocation
Replace: GUIDE_PATH -> reviewed local assistant-guide.txt path
Customize
```bash
guidecheck verify GUIDE_PATH --contract posix-json-v1
```
