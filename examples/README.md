# Examples

Sample artifacts for GuideCheck's Human-Verifiable Assistant Guide profile. All use the reserved `example.com` domain for guide content. The `recommended-verifier` field points at the real standard primary verifier, `https://guidecheck.org/verify`.

- `level-1-assistant-guide.txt` — a minimal Level 1 guide: readable plain text, canonical URL, task scope, compact verification instruction. No action blocks or metadata block.
- `level-3-assistant-guide.txt` — a full Level 3 guide: metadata block, all required sections, structured `[action]` blocks, approval gates, stop-and-ask conditions, acceptance checklist. ASCII byte profile, 5210 bytes. When paired with the manifest and anchor below, it can be evaluated as a Level 4 candidate.
- `mcp-database-server-assistant-guide.txt` — a Level 3 guide for reviewing, installing, and smoke-testing a database MCP server in a local development host.
- `manifest.txt` — a sidecar manifest for the Level 3 guide. Pairing the Level 3 guide with this manifest and at least one independent cross-channel anchor demonstrates the Level 4 provenance model. The `guide-sha256` and `guide-bytes` values match `level-3-assistant-guide.txt` as committed.
- `anchor.txt` — a DNS TXT-style independent anchor example for the guide hash.

To verify the manifest hash locally:
```
shasum -a 256 level-3-assistant-guide.txt
```
The result must equal the `guide-sha256` value in `manifest.txt`.

To verify Level 4 locally, provide the guide, manifest, and at least one
independent anchor file to the reference CLI:
```
python3 ../scripts/guidecheck_verify.py level-3-assistant-guide.txt --manifest manifest.txt --anchor dns-txt=anchor.txt --level 4 --pretty
```

These examples are illustrative, not normative. The normative definitions are in `spec.md`.
