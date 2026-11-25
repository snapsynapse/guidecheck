# Examples

Sample artifacts for GuideCheck's Human-Verifiable Assistant Guide profile. All use the reserved `example.com` domain for guide content. The `recommended-verifier` field points at the real standard primary verifier, `https://guidecheck.org/verify`.

- `level-1-assistant-guide.txt` — a minimal Level 1 guide: readable plain text, canonical URL, task scope, compact verification instruction. No action blocks or metadata block.
- `level-3-assistant-guide.txt` — a full Level 3 guide: metadata block, all required sections, structured `[action]` blocks, approval gates, stop-and-ask conditions, acceptance checklist. ASCII byte profile, 5210 bytes. When paired with the manifest and anchor below, it can be evaluated as a Level 4 candidate.
- `2.0.0-corrected-bound-inline/guide.txt`: the repaired copy of the released fixture `fixtures/profiles/2.0.0/corrected-bound-unpinned/guide.txt`, used by the README "Try it" lesson. The repository script dispatch (`npm --prefix subdir run check`) is replaced by a command a reviewer can read in the guide, and `manifest-url` is removed so a local check is not claiming Level 4. Under `--require-profile-version 2.0.0 --level 3` it reaches Level 3 with no blocking findings. `scripts/test_readme_trial.py` holds both halves of the lesson.
- `mcp-database-server-assistant-guide.txt` — a Level 3 guide for reviewing, installing, and smoke-testing a database MCP server in a local development host.
- `manifest.txt` — a sidecar manifest for the Level 3 guide. Pairing the Level 3 guide with this manifest and at least one independent cross-channel anchor demonstrates the Level 4 provenance model. The `guide-sha256` and `guide-bytes` values match `level-3-assistant-guide.txt` as committed.
- `anchor.txt` — a DNS TXT-style independent anchor example for the guide hash.

To verify the manifest hash locally:
```
shasum -a 256 level-3-assistant-guide.txt
```
The result must equal the `guide-sha256` value in `manifest.txt`.

To check Level 4 evidence locally, provide the guide, manifest, and at least one
independent anchor file to the reference CLI. The CLI confirms the evidence is
internally consistent but caps at Level 3 (reporting `level4.requires-fetch`),
because Level 4 requires fetched provenance. The hosted verifier at
https://guidecheck.org/verify reports declared anchors as unverified and also
caps at Level 3, so no GuideCheck verifier currently asserts Level 4:
```
python3 ../scripts/guidecheck_verify.py level-3-assistant-guide.txt --manifest manifest.txt --anchor dns-txt=anchor.txt --pretty
```

These examples are illustrative, not normative. The normative definitions are in `spec.md`.
