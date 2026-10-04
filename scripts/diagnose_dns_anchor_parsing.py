#!/usr/bin/env python3
"""Offline characterization, not normative acceptance tests or a parser repair.

Emit a deterministic report for DNS record selection and all supported profile
evaluators. evidence_fetched=True models supplied evidence; no network is used.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

import guidecheck_legacy as legacy
from guidecheck_hosted_anchors import select_dns_txt_record
from guidecheck_profiles import SUPPORTED_VERSIONS
from guidecheck_verify import evaluate_guide

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures/profiles/2.0.0/dns-only"
NOW = datetime(2026, 10, 3, 12, tzinfo=timezone.utc)


def artifacts(version):
    guide = (FIXTURE / "guide.txt").read_text().replace(
        "profile-version: 2.0.0", "profile-version: " + version
    ).encode()
    digest = hashlib.sha256(guide).hexdigest()
    manifest = (FIXTURE / "manifest.txt").read_text()
    for field, value in {
        "profile-version": version,
        "guide-sha256": digest,
        "guide-bytes": str(len(guide)),
    }.items():
        manifest = re.sub(r"^" + field + r": .*?$", field + ": " + value,
                          manifest, flags=re.M)
    url = re.search(r"^canonical-url: (.+)$", manifest, re.M).group(1)
    return guide, manifest, digest, url


def capture():
    rows = []
    for version in sorted(SUPPORTED_VERSIONS, key=lambda v: tuple(map(int, v.split(".")))):
        guide, manifest, digest, url = artifacts(version)
        wrong = "0" * 64

        def record(fields, canonical=url):
            return "v=1; " + fields + "; url=" + canonical

        correct_record = record("sha256=" + digest)
        wrong_record = record("sha256=" + wrong)
        cases = {
            "valid": [correct_record],
            "wrong-hash": [wrong_record],
            "doubled-prefix": [record("sha256=sha256=" + digest)],
            "duplicate-identical": [record("sha256=" + digest + "; sha256=" + digest)],
            "conflict-correct-first": [record("sha256=" + digest + "; sha256=" + wrong)],
            "conflict-wrong-first": [record("sha256=" + wrong + "; sha256=" + digest)],
            "embedded-field": [record("note=sha256=" + digest)],
            "wrong-url": [record("sha256=" + digest, "https://other.example/guide.txt")],
            "rrset-correct-first": [correct_record, wrong_record],
            "rrset-wrong-first": [wrong_record, correct_record],
        }
        for case, records in cases.items():
            selected = select_dns_txt_record(records, url)
            anchors = {"dns-txt": selected} if selected is not None else {}
            findings, level, _, _, evidence = evaluate_guide(
                guide, manifest, anchors, now=NOW, evidence_fetched=True
            )
            row = {
                "profile": version,
                "case": case,
                "records": records,
                "selected_record": selected,
                "guide_sha256": digest,
                "extracted_sha256": legacy.extract_anchor_sha256("dns-txt", selected) if selected else None,
                "achieved_level": level,
                "blocking_ids": sorted({f.id for f in findings if f.severity == "error"}),
                "anchor_status": evidence[0].status if evidence else None,
            }
            if case == "valid" and (level != 4 or row["blocking_ids"]):
                raise RuntimeError("invalid diagnostic control: " + version)
            rows.append(row)
    sources = [
        "scripts/guidecheck_legacy.py", "scripts/guidecheck_hosted_anchors.py",
        "scripts/guidecheck_profiles.py", "scripts/guidecheck_strict.py",
        "scripts/guidecheck_corrected.py", "scripts/guidecheck_verify.py",
        "fixtures/profiles/2.0.0/dns-only/guide.txt",
        "fixtures/profiles/2.0.0/dns-only/manifest.txt",
    ]
    return {
        "kind": "diagnostic-only",
        "evaluation_time": NOW.isoformat(),
        "mode": "offline supplied-evidence simulation; no public-web verification",
        "source_sha256": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in sources},
        "rows": rows,
    }


if __name__ == "__main__":
    print(json.dumps(capture(), indent=2))
