#!/usr/bin/env python3
"""Profile selection, strict qualification, and caller/report boundary tests."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stdout
from dataclasses import FrozenInstanceError
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import guidecheck_verify as gv
import guidecheck_profiles as profiles
import guidecheck_strict as strict
import test_hosted_api as hosted
from test_legacy_anchor_compatibility import artifacts, GUIDE_URLS, RAW_URL, NOW
from validate_contracts import validate_json_schema_instance

ROOT = Path(__file__).resolve().parents[1]


class ProfileDispatchTests(unittest.TestCase):
    def evaluate(self, version="1.0.0", dns=False, local=False):
        data, manifest, _ = artifacts(version, GUIDE_URLS[0])
        anchors = {"repository-file": data.decode()}
        if dns:
            anchors["dns-txt"] = "v=1; sha256=" + hashlib.sha256(data).hexdigest()
        return gv.evaluate_guide(data, manifest, anchors, now=NOW, evidence_fetched=not local)

    def test_exact_and_build_metadata_dispatch(self):
        for version in (*profiles.LEGACY_VERSIONS, "1.0.0", "0.7.1+build.001", "1.0.0+build.7"):
            with self.subTest(version=version):
                data, _, _ = artifacts(version, GUIDE_URLS[0])
                selected = profiles.select_profile(data)
                self.assertEqual(selected.declared_version, version)
                self.assertEqual(selected.policy_version, version.split("+")[0])
                self.assertEqual(profiles.select_profile(data, version.split("+")[0]), selected)
                with self.assertRaises(FrozenInstanceError):
                    selected.policy_version = "0.7.1"

    def test_unsupported_and_malformed_versions_never_fall_back(self):
        for version in ("0.8.0", "1.0.1", "2.0.0", "1.0.0-rc.1", "01.0.0", ">=1.0.0", "1.0.0+", "1.0.0+a..b", "1.0.0+a_b", "1.0.0 ", " 1.0.0", ""):
            with self.subTest(version=version):
                data, _, _ = artifacts(version, GUIDE_URLS[0])
                with self.assertRaises(profiles.ProfileError):
                    profiles.select_profile(data)

    def test_conflicting_or_duplicate_new_selectors(self):
        data, _, _ = artifacts("1.0.0", GUIDE_URLS[0])
        for replacement in (b"profile-version: 0.7.1\nprofile-version: 1.0.0", b"profile-version: 1.0.0\nprofile-version: 1.0.0"):
            with self.assertRaises(profiles.ProfileError):
                profiles.select_profile(data.replace(b"profile-version: 1.0.0", replacement))
        legacy_data, _, _ = artifacts("0.7.1", GUIDE_URLS[0])
        with self.assertRaises(profiles.ProfileError):
            profiles.select_profile(legacy_data, "1.0.0")
        with self.assertRaises(profiles.ProfileError):
            gv.evaluate_guide(data, selection=profiles.select_profile(legacy_data))

    def test_static_strict_fixture_matrix_and_schema(self):
        schema = json.loads((ROOT / "schemas/1.0.0/verifier-output.schema.json").read_text())
        fixture_schema = json.loads((ROOT / "schemas/1.0.0/fixture-expected.schema.json").read_text())
        for path in sorted((ROOT / "fixtures/profiles/1.0.0").iterdir()):
            with self.subTest(case=path.name):
                expected = json.loads((path / "expected.json").read_text())
                contract_errors = []
                validate_json_schema_instance(contract_errors, path, expected, fixture_schema)
                self.assertEqual(contract_errors, [])
                data = (path / "guide.txt").read_bytes()
                sources = {p.stem: p.read_text() for p in (path / "anchors").glob("*.txt")}
                findings, level, ready, manifest, anchors = gv.evaluate_guide(
                    data, (path / "manifest.txt").read_text(), sources, now=NOW,
                    evidence_fetched=expected["evidence_fetched"],
                )
                self.assertEqual(level, expected["achieved_level"])
                self.assertEqual(sorted(f.id for f in findings if f.severity == "error"), expected["blocking_finding_ids"])
                self.assertEqual(sum(a.qualifies_for_level4 for a in anchors), expected["qualifying_anchor_count"])
                selection = profiles.select_profile(data)
                result = hosted.hv.build_evaluated(
                    GUIDE_URLS[0], GUIDE_URLS[0], False, hosted.fetched(GUIDE_URLS[0], 200, data),
                    findings, level, ready, NOW, manifest, anchors, selection=selection,
                )
                if not expected["evidence_fetched"]:
                    result = gv.output_for(gv.evaluate_local_file(
                        path / "guide.txt", path / "manifest.txt",
                        {p.stem: p for p in (path / "anchors").glob("*.txt")}, now=NOW,
                    ))
                    self.assertEqual(result["input"]["evaluation_mode"], "local-file")
                self.assertEqual(result["guide"]["achieved_level"], level)
                self.assertIn(f"Level: {level}\n", result["compact_report"])
                self.assertEqual(result["verifier"]["guide_profile_version"], "1.0.0")
                errors = []
                validate_json_schema_instance(errors, path, result, schema)
                self.assertEqual(errors, [])
                for anchor in result.get("cross_channel_anchors", []):
                    if anchor["channel"] == "repository-file":
                        self.assertFalse(anchor["qualifies_for_level4"])
                        self.assertEqual(anchor["independence"], "unestablished")

    def test_other_channel_cannot_restore_repository_qualification(self):
        findings, level, _, _, anchors = self.evaluate(dns=True)
        self.assertEqual(level, 4)
        self.assertEqual([(a.channel, a.qualifies_for_level4) for a in anchors], [("dns-txt", True), ("repository-file", False)])
        self.assertIn("anchor.repository-file.independence-unestablished", [f.id for f in findings])

    def test_unknown_channel_cannot_qualify(self):
        data, manifest, _ = artifacts("1.0.0", GUIDE_URLS[0])
        findings, level, _, _, anchors = gv.evaluate_guide(data, manifest, {"invented": data.decode()}, now=NOW, evidence_fetched=True)
        self.assertEqual(level, 3)
        self.assertEqual(anchors, [])
        self.assertIn("anchor.channel.unsupported", [f.id for f in findings])

    def test_manifest_profile_binding(self):
        data, manifest, _ = artifacts("1.0.0", GUIDE_URLS[0])
        for changed in (manifest.replace("profile-version: 1.0.0", ""), manifest + "profile-version: 1.0.0\n", manifest.replace("profile-version: 1.0.0", "profile-version: 2.0.0"), manifest.replace("profile: human-verifiable-assistant-guide", "profile: wrong")):
            findings, level, _, evidence, _ = gv.evaluate_guide(data, changed, {"dns-txt": "v=1; sha256=" + hashlib.sha256(data).hexdigest()}, now=NOW, evidence_fetched=True)
            self.assertEqual(level, 3)
            self.assertFalse(evidence.valid)
            self.assertIn("manifest.profile-version.mismatch", [f.id for f in findings])
        old_data, _, _ = artifacts("0.7.1", GUIDE_URLS[0])
        with self.assertRaises(profiles.ProfileError):
            gv.evaluate_guide(old_data, manifest)

    def test_mixed_requests_do_not_share_policy_state(self):
        versions = ["0.7.1", "1.0.0"] * 20
        with ThreadPoolExecutor(max_workers=4) as executor:
            levels = list(executor.map(lambda v: self.evaluate(version=v)[1], versions))
        self.assertEqual(levels, [4, 3] * 20)

    def test_hosted_assertions_and_strict_report(self):
        for version in ("0.7.1", "1.0.0", "0.7.1", "1.0.0"):
            data, manifest, manifest_url = artifacts(version, GUIDE_URLS[0])
            calls = []
            def fetch(url, request_profile="default", accept_override=None):
                calls.append(url)
                if url in (GUIDE_URLS[0], RAW_URL):
                    return hosted.fetched(url, 200, data)
                if url == manifest_url:
                    return hosted.fetched(url, 200, manifest.encode())
                if url.startswith("https://cloudflare-dns.com/"):
                    return hosted.fetched(url, 200, b'{"Status":0}', "application/dns-json")
                self.fail(url)
            with redirect_stdout(io.StringIO()):
                request = hosted.run_post({"url": GUIDE_URLS[0]}, fetch)
            self.assertEqual(request.body["guide"]["achieved_level"], 4 if version == "0.7.1" else 3)
            if version == "1.0.0":
                anchor = request.body["cross_channel_anchors"][0]
                self.assertEqual(anchor["evidence_url"], RAW_URL)
                self.assertIn("fetched_at", anchor)
                self.assertFalse(anchor["qualifies_for_level4"])
            calls.clear()
            with redirect_stdout(io.StringIO()):
                request = hosted.run_post({"url": GUIDE_URLS[0], "required_profile_version": "1.0.0"}, fetch)
            if version == "0.7.1":
                self.assertEqual(request.status, 400)
                self.assertEqual(request.body["error"]["code"], "profile-version-requirement-mismatch")
                self.assertEqual(calls, [GUIDE_URLS[0]])
            else:
                self.assertEqual(request.status, 200)

    def test_cli_profile_assertion_and_strict_output(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "guide.txt"
            manifest_path = Path(directory) / "manifest.txt"
            for version in ("0.7.1", "1.0.0"):
                data, manifest, _ = artifacts(version, GUIDE_URLS[0])
                path.write_bytes(data)
                manifest_path.write_text(manifest)
                result = subprocess.run([sys.executable, str(ROOT / "scripts/guidecheck_cli.py"), "verify", str(path), "--manifest", str(manifest_path), "--require-profile-version", "1.0.0"], text=True, capture_output=True)
                self.assertEqual(result.returncode, 2 if version == "0.7.1" else 1)
                if version == "1.0.0":
                    output = json.loads(result.stdout)
                    self.assertEqual(output["profile_selection"]["evaluated_policy"], "1.0.0")

    def test_preserved_artifact_digests(self):
        record = json.loads((ROOT / "fixtures/compatibility/preserved-artifacts.json").read_text())
        for name, digest in record["sha256"].items():
            with self.subTest(path=name):
                self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), digest)


if __name__ == "__main__":
    unittest.main()
