# Examples

Sample artifacts for the Human-Verifiable Assistant Guide profile. All use the reserved `example.com` domain for guide content. The `recommended-verifier` field points at the real standard primary verifier, `https://guidecheck.org/verify`.

- `level-1-assistant-guide.txt` — a minimal Level 1 guide: readable plain text, canonical URL, task scope, compact verification instruction. No action blocks or metadata block.
- `level-3-assistant-guide.txt` — a full Level 3 guide: metadata block, all required sections, structured `[action]` blocks, approval gates, stop-and-ask conditions, acceptance checklist. ASCII byte profile, 5156 bytes.
- `manifest.txt` — a sidecar manifest for the Level 3 guide. Pairing the Level 3 guide with this manifest and at least one independent cross-channel anchor demonstrates the Level 4 provenance model. The `guide-sha256` and `guide-bytes` values match `level-3-assistant-guide.txt` as committed.

To verify the manifest hash locally:
```
shasum -a 256 level-3-assistant-guide.txt
```
The result must equal the `guide-sha256` value in `manifest.txt`.

These examples are illustrative, not normative. The normative definitions are in `spec.md`.
