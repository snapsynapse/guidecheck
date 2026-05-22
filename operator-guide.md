# Operator Guide: Defense in Depth

Status: non-normative companion to `spec.md`.

This guide is for the operator: the person who authorizes an assistant to
follow an `assistant-guide.txt` and supervises it while it acts. It is not
part of the normative profile. It collects the practices that go with
adopting GuideCheck, regardless of how high a guide scores against the
profile. Read it alongside `spec.md` section 27, which enumerates the threats
the profile does not address.

GuideCheck is one layer in a defense stack. It is the layer that prevents a
presentation surface from hiding instructions from a human while feeding them
to an assistant. It is not, by itself, a secure install procedure. The
practices below remain the operator's responsibility regardless of how high a
guide scores against the profile.

## Before authorizing the assistant

- Read the full guide. The size limits in `spec.md` section 8 exist so that
  "read the full guide" is realistic. If the guide is too long to read, treat
  that as a finding.
- Confirm the canonical URL with the publisher through a channel that does not
  depend on the same web property. For high-consequence operations, prefer a
  signed release note, a code-signing key fingerprint, or a person you trust
  who can vouch for the publisher.
- Compare the `applies-to` field against the version of the software you
  actually have. A guide written for `>=2.3.0, <3.0.0` is not a guide for your
  `3.1.0` install.
- Check `status` and `valid-until`. A `deprecated` or expired guide is a stop,
  not a warning.
- Decide your tolerance per action class before you start. Pre-committing to
  "I will not approve any `privileged` action today" prevents in-the-moment
  approval drift.

## While the assistant is acting

- Keep the assistant on least-privilege tool permissions. A guide that fits
  this profile still needs a sandbox underneath it.
- Do not let the assistant raise its own permissions, disable sandboxing, or
  batch approvals across action ids. `spec.md` section 12 forbids the guide
  from asking; the runtime should also forbid the assistant from doing.
- Watch the verbatim action block at each approval prompt. If the displayed
  command does not match what the assistant is about to run, stop and
  investigate.
- Maintain operating-system permission prompts. If the OS asks for elevation,
  that question is for you, not the assistant.
- Log executed actions. Post-hoc review is the only defense against
  approval-fatigue mistakes.

## Around the assistant

- Back up state before any destructive or persistence-changing action. The
  guide may declare a command non-destructive; your backup is what protects
  you when the declaration is wrong.
- Run unfamiliar guides in a disposable environment first: a VM, a container,
  a scratch workstation, a non-production cluster. Promotion to production is
  a separate decision.
- Apply network egress controls at the host or network layer. The `egress`
  field in a guide is a declaration; your firewall is the enforcement.
- Keep secrets out of the assistant's reach. `spec.md` section 16 forbids
  secrets in the guide; you still must not hand the assistant a session that
  has unrestricted access to credential stores.

## What this profile does not replace

- code signing, release attestation, and software bill of materials for the
  underlying project
- package manager trust policy and lockfile review
- vulnerability scanning of the dependencies the guide installs
- security review of the underlying software itself
- incident response, monitoring, and audit
- organizational change-management for production systems

If you are deploying AI-assisted installs at scale, treat conforming guides as
one control among many. A program built on this profile alone is
under-defended.

## Anti-pattern: verifier as oracle

Do not run a guide through a verifier, see a green result, and skip reading
it. The verifier is a filter that catches a specific class of
presentation-layer and structural attacks. It cannot detect a publisher who
has decided to harm you in plain ASCII. Your reading is the control that
catches that case.

## Anti-pattern: trust transference

A guide is not trustworthy because:

- it is on a domain that hosts other things you trust
- it has a high conformance level
- a verifier returned no findings
- it is referenced from a popular `llms.txt`
- an assistant said it looked fine

A guide is provisionally trustworthy when its publisher is known, its content
matches your expectations for the task, its actions are scoped and
approval-gated, and the surrounding operational controls (backups, sandbox,
least privilege, signed releases) are in place. Conformance contributes to
that judgment. It does not constitute it.
