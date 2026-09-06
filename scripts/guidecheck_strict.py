"""Profile 1.0.0 provenance qualification; legacy semantics remain isolated."""
from dataclasses import dataclass
from datetime import datetime, timezone
import guidecheck_legacy as legacy
from guidecheck_profiles import PROFILE_NAME, ProfileError, policy_key


@dataclass
class AnchorEvidence(legacy.AnchorEvidence):
    qualifies_for_level4: bool = False
    qualification_reason: str = "absent"

    def as_dict(self):
        result = super().as_dict()
        result.update(qualifies_for_level4=self.qualifies_for_level4,
                      qualification_reason=self.qualification_reason)
        if self.channel == "repository-file":
            result["independence"] = "unestablished"
        return result


def manifest_profile_matches(text):
    fields = {"profile": [], "profile-version": []}
    for line in text.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            if key.strip().lower() in fields:
                fields[key.strip().lower()].append(value.strip())
    if fields["profile"] != [PROFILE_NAME] or len(fields["profile-version"]) != 1:
        return False
    try:
        return policy_key(fields["profile-version"][0]) == "1.0.0"
    except ProfileError:
        return False


def evaluate_guide(data, manifest_text=None, anchor_texts=None, anchor_paths=None,
                   now=None, evidence_fetched=False):
    # Reuse frozen content validation with no anchors. It cannot award Level 4
    # or emit Level 5 readiness findings before strict qualification completes.
    now = now or datetime.now(timezone.utc)
    findings, achieved, _, manifest, _ = legacy.evaluate_guide(
        data, manifest_text, now=now, evidence_fetched=evidence_fetched,
    )
    findings = [f for f in findings if f.id != "anchor.independent.missing"]
    metadata = legacy.parse_metadata(legacy.decode_text(data), [], now.date())
    claimed = bool(metadata.get("manifest-url"))
    if manifest is not None and not manifest_profile_matches(manifest_text):
        manifest.valid = False
        legacy.add_finding(findings, "manifest.profile-version.mismatch", "error",
                           "manifest must declare exactly one matching profile name and version")
    anchors = []
    for channel, text in sorted((anchor_texts or {}).items()):
        if channel not in legacy.ANCHOR_CHANNELS:
            legacy.add_finding(findings, "anchor.channel.unsupported", "warning",
                               "unsupported anchor channel cannot qualify", evidence=channel)
            continue
        observed = legacy.extract_anchor_sha256(channel, text)
        expected = manifest.guide_sha256 if manifest is not None else None
        status = "absent" if observed is None else (
            "present-matches" if observed == expected else "present-mismatch")
        if status == "absent":
            reason = "absent"
        elif status == "present-mismatch":
            reason = "hash-mismatch"
        elif not evidence_fetched:
            reason = "local-evidence-not-fetched"
        elif channel == "repository-file":
            reason = "repository-independence-unestablished"
        else:
            reason = "qualifying-channel"
        anchors.append(AnchorEvidence(
            channel=channel, status=status, observed_sha256=observed,
            evidence_path=str(anchor_paths[channel]) if anchor_paths and channel in anchor_paths else None,
            qualifies_for_level4=reason == "qualifying-channel",
            qualification_reason=reason,
        ))
        if channel == "repository-file" and observed is not None:
            legacy.add_finding(findings, "anchor.repository-file.independence-unestablished", "warning",
                               "repository hash evidence does not establish independent provenance and cannot qualify for Level 4")
        if status == "present-mismatch":
            fid = "anchor.repository-file.mismatch" if channel == "repository-file" else "anchor.independent.mismatch"
            legacy.add_finding(findings, fid, "error", "anchor hash does not match manifest guide-sha256", evidence=channel)
        anchor_url = legacy.extract_anchor_url(channel, text)
        if metadata.get("canonical-url") and anchor_url and anchor_url != metadata["canonical-url"]:
            legacy.add_finding(findings, "anchor.registry.url-mismatch", "warning",
                               "package-registry assistant-guide URL does not match canonical-url", evidence=anchor_url)
    qualifying = any(a.qualifies_for_level4 for a in anchors)
    mismatches = any(a.status == "present-mismatch" for a in anchors)
    if claimed and not qualifying and not mismatches:
        legacy.add_finding(findings, "anchor.independent.missing", "error",
                           "no fetched qualifying independent anchor is available for Level 4")
    if not evidence_fetched and any(a.status == "present-matches" for a in anchors):
        legacy.add_finding(findings, "level4.requires-fetch", "info",
                           "local evidence was checked for consistency only; Level 4 requires fetched qualifying evidence")
    blockers = any(f.severity == "error" and f.id.startswith(("anchor.", "manifest.")) for f in findings)
    if achieved >= 3 and claimed and manifest is not None and manifest.valid and qualifying and not blockers:
        achieved = 4
    else:
        achieved = min(achieved, 3)
    actions = legacy.parse_actions(legacy.decode_text(data), [])
    ready = legacy.check_level5_readiness(actions, findings) if achieved >= 4 else False
    return findings, achieved, ready, manifest, anchors


def decorate_report(result, selection):
    """Mutate a newly built strict report only; never touch a legacy result."""
    result["verifier"].update(version="1.0.0", verifier_profile_version="1.0.0", guide_profile_version="1.0.0")
    result["profile_selection"] = {
        "declared_version": selection.declared_version,
        "evaluated_policy": "1.0.0",
    }
    anchors = result.get("cross_channel_anchors", [])
    count = sum(a["qualifies_for_level4"] for a in anchors)
    result["qualifying_anchor_count"] = count
    lines = [f"Profile: 1.0.0 (declared {selection.declared_version})", f"Qualifying anchors: {count}"]
    for anchor in anchors:
        if anchor["channel"] == "repository-file":
            lines.append(f"Repository hash: {anchor['status']}; independent provenance: unestablished; counts toward Level 4: no")
    # Render from the final level, not the pre-decoration legacy text.
    guide, summary, verifier = result["guide"], result["summary"], result["verifier"]
    source = result["input"].get("url", result["input"].get("path"))
    result["compact_report"] = "\n".join([
        f"Verifier: {verifier['name']} {verifier['version']}", f"Guide: {source}",
        *lines, f"Level: {guide['achieved_level']}", f"SHA-256: {guide['sha256']}",
        f"Blocking findings: {summary['blocking_findings']}", f"Warnings: {summary['warnings']}",
        f"Hash pinned: {'yes' if guide['achieved_level'] >= 4 else 'no'}",
        f"Proceed? {'yes' if summary['blocking_findings'] == 0 else 'no'}",
    ])
    if "hosted_limitations" in result:
        result["hosted_limitations"] = [
            "Profile 1.0.0 excludes repository-file hashes from Level 4 qualification; matching repository bytes remain corroboration.",
            *result["hosted_limitations"],
        ]
    return result
