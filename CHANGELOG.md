# Changelog

All notable changes to the Human-Verifiable Assistant Guide profile and its companion documents are recorded here. The format follows Keep a Changelog conventions. Profile versions follow Semantic Versioning as defined in `spec.md` section 11.

## 0.1.0 - 2026-05-21

Initial draft for review.

### Specification

- Human-Verifiable Assistant Guide profile for `assistant-guide.txt`
- core artifact, one-artifact bounded-task scope, canonical well-known path
- strict ASCII byte profile, 8 KiB size cap, 120-byte line and 400-line limits
- disallowed constructs and Markdown-as-text clarification
- required sections at Level 3, compact verification instruction at Level 1, assistant invocation prompt content
- guide metadata block with normative fences, version-range syntax, and field set
- sidecar manifest provenance model and cross-channel hash publication (DNS TXT, package registry, public repository file, signed security.txt)
- action classification with seven classes including `code-executing`, structured `[action]` blocks, command field restrictions, `runner` semantics
- stop-and-ask conditions and canonical approval phrasing
- threat model, untrusted content handling, integrity-versus-instruction fetch distinction, hard ban on chained guides
- public information safety and risky pattern guidance
- five-level conformance ladder including Level 5 runtime-enforced execution
- discovery surfaces, HTTPS serving requirements, verifier requirements, verifier output schema
- residual threats and operator defense-in-depth checklist
- locale handling and final ASCII-only position

### Companion documents

- Verifier Conformance Profile defining public-web and local-file evaluation modes, fetch safety, SSRF defenses, level calculation, output schema, and fixture suite conformance
- design rationale capturing the reasoning behind the 8 KiB cap, ASCII-only profile, sidecar manifest, cross-channel publication, hard chained-guide ban, and other decisions
- threat register enumerating network, hosting, provenance, verifier, runtime, user, and availability risk classes
- JSON Schema for the manifest and verifier output

### Project

- designated standard primary verifier at `https://guidecheck.org/verify`
- canonical site at `https://guidecheck.org/`
