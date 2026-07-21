---
id: AIDR-0001
title: Same-control-plane repository anchors
status: open
date: 2026-07-21
arbiter: Sam Rogers
tags: [guidecheck, level-4, provenance, anchors, control-plane]
---
# AIDR-0001: Same-control-plane repository anchors

## Context

GuideCheck Level 4 requires at least one independent cross-channel anchor matching the guide manifest. A public repository file is a recognized channel, but the current profile does not explicitly resolve the case where GitHub controls both the source repository and the GitHub Pages deployment serving the guide. The current session handoff identifies this as the next normative independence decision. Counting a same-control-plane repository file may let one compromised account or repository write path forge both the guide and its asserted independent anchor. Rejecting every repository-file anchor merely because the guide uses Pages may be too broad when ownership, deployment, or immutable-release controls differ.

## Question

Should a repository-file anchor hosted on the same administrative control plane as a GitHub Pages guide count as an independent Level 4 provenance anchor?

## Positions

### Position: codex-gpt-5

- agent: codex-gpt-5
- model: gpt-5
- provider: openai
- stance: recommend
- summary: Do not count a same-administration repository-file anchor as independent unless another distinct control-plane anchor also validates the hash.

Independence should follow compromise boundaries, not URL shape. When one GitHub repository or organization credential can modify both the Pages guide and the repository-file anchor, the anchor raises no meaningful forge cost and should remain visible evidence without satisfying Level 4 by itself. The verifier should emit a specific finding, exclude that anchor from the independent-channel count, and allow Level 4 when another qualifying channel such as DNS TXT, recognized package-registry metadata, a signed security.txt, or a transparency log agrees. The rule should be narrow: a repository-file anchor may still qualify when the guide host is controlled through a genuinely distinct administrative plane and the verifier has a testable basis for that distinction.

This position was written without reading any other participant's position.

## Objections

## Arbitration

## Evidence

- [Current session handoff](../SESSION_HANDOFF.md#next-candidates) identifies same-control-plane repository anchors as the next normative independence decision.
- [Verifier conformance section 23](../verifier-conformance.md#23-cross-channel-anchor-checks) defines recognized independent channels and the Level 4 anchor requirement.
- [Threat register](../threat-register.md#provenance-anchor-risks) explains that Level 4 is intended to raise the cost of forging the guide and provenance evidence together.
