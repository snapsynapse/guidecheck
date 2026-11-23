#!/usr/bin/env python3
"""Draft profile 3.0.0 is reachable from the local reference CLI, and from nowhere else.

The dispatcher selects 3.0.0 only for a caller that passes `allow_draft`. The
local CLI does. The hosted verifier, the experimental CLI contract and every
other caller of the dispatcher keep refusing it exactly as before.
"""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import guidecheck_profiles as profiles
import guidecheck_restricted as restricted
import guidecheck_restricted_registry as embedded
import guidecheck_verify as gv
import profile_3_0_0_invariants as invariants
import test_hosted_api as hosted
from validate_contracts import registered_finding_ids, validate_json_schema_instance

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures" / "profiles" / "3.0.0"
VALID = FIXTURES / "valid-level-3" / "guide.txt"
SCHEMA = json.loads((ROOT / "schemas/3.0.0/verifier-output.schema.json").read_text(encoding="ascii"))
CLI = [sys.executable, str(ROOT / "scripts/guidecheck_cli.py"), "verify"]


def run(*arguments):
    return subprocess.run([*CLI, *map(str, arguments)], text=True, capture_output=True)


class LocalCliTests(unittest.TestCase):
    def report(self, completed):
        report = json.loads(completed.stdout)
        errors = []
        validate_json_schema_instance(errors, ROOT / "schemas", report, SCHEMA, strict=True)
        self.assertEqual(errors, [])
        self.assertEqual(invariants.check_report(report, registered_finding_ids()), [])
        return report

    def test_a_conforming_guide_passes_and_says_the_profile_is_a_draft(self):
        completed = run(VALID)
        report = self.report(completed)
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(report["verdict"], {"proceed": True})
        self.assertEqual(report["profile_selection"]["content_policy"], "restricted-argv-1")
        self.assertEqual(report["input"], {"evaluation_mode": "local-file", "repository_read": False,
                                           "path": restricted._path_token(VALID)})
        self.assertIn("draft profile 3.0.0", completed.stderr)
        self.assertIn("unreleased", completed.stderr)

    def test_text_output_is_the_compact_report(self):
        completed = run(VALID, "--format", "text")
        self.assertEqual(completed.returncode, 0)
        self.assertTrue(completed.stdout.rstrip("\n").endswith("Proceed? yes"))
        self.assertIn("Profile: 3.0.0\n", completed.stdout)

    def test_the_exit_status_follows_the_verdict(self):
        cases = {
            "blocking finding": (FIXTURES / "command-pipe" / "guide.txt", [], "blocking findings"),
            "below Level 3 with nothing else wrong": (FIXTURES / "no-action-block" / "guide.txt", [], "blocking findings"),
            "below the required level": (VALID, ["--level", "4"], "below the required level"),
            "refused for size": (FIXTURES / "oversize" / "guide.txt", [], "blocking findings"),
        }
        for label, (path, options, reason) in cases.items():
            with self.subTest(case=label):
                completed = run(path, *options)
                self.assertEqual(completed.returncode, 1)
                self.assertEqual(self.report(completed)["verdict"], {"proceed": False, "reason": reason})
                text = run(path, *options, "--format", "text").stdout
                self.assertTrue(text.rstrip("\n").endswith(f"Proceed? no\nReason: {reason}"))
        self.assertEqual(run(VALID, "--level", "3").returncode, 0)

    def test_a_level_below_three_is_never_a_success(self):
        """The released profiles exit 0 below Level 3 when no level is required. The draft does not."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "guide.txt"
            path.write_bytes(VALID.read_bytes().replace(b"Threat model\n", b"Threats\n"))
            completed = run(path)
            self.assertEqual(completed.returncode, 1)
            self.assertEqual(self.report(completed)["guide"]["achieved_level"], 2)

    def test_fail_on_warning_still_applies(self):
        completed = run(VALID, "--fail-on-warning")
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(self.report(completed)["verdict"], {"proceed": True})
        self.assertIn("--fail-on-warning", completed.stderr)

    def test_profile_requirements(self):
        self.assertEqual(run(VALID, "--require-profile-version", "3.0.0").returncode, 0)
        for required in ("2.0.0", "1.0.0", "0.7.1"):
            with self.subTest(required=required):
                completed = run(VALID, "--require-profile-version", required)
                self.assertEqual(completed.returncode, 2)
                self.assertIn("profile-version-requirement-mismatch", completed.stderr)
        completed = run(VALID, "--require-profile-version", "3.0.0+build.1")
        self.assertEqual(completed.returncode, 2)
        self.assertIn("profile-version-unsupported", completed.stderr)
        released = ROOT / "fixtures/profiles/2.0.0/local-consistency/guide.txt"
        completed = run(released, "--require-profile-version", "3.0.0")
        self.assertEqual(completed.returncode, 2)
        self.assertIn("profile-version-requirement-mismatch", completed.stderr)

    def test_a_declaration_that_is_not_exact_is_refused_not_reinterpreted(self):
        data = VALID.read_bytes()
        cases = {
            "build metadata": (data.replace(b"profile-version: 3.0.0", b"profile-version: 3.0.0+build.1"), "profile-version-unsupported"),
            "indented selector": (data.replace(b"profile-version: 3.0.0", b" profile-version: 3.0.0"), "profile-version-ambiguous"),
            "padded fence": (data.replace(b"[/assistant-guide-metadata]", b"[/assistant-guide-metadata] "), "profile-version-ambiguous"),
            "second selector": (data.replace(b"profile-version: 3.0.0", b"profile-version: 3.0.0\nprofile-version: 2.0.0"), "profile-version-ambiguous"),
            "second selector in other words": (data.replace(b"profile-version: 3.0.0", b"profile-version: 3.0.0\n- profile-version: 2.0.0"), "profile-version-ambiguous"),
            "no profile name": (data.replace(b"profile: human-verifiable-assistant-guide\n", b""), "profile-version-ambiguous"),
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "guide.txt"
            for label, (changed, code) in cases.items():
                with self.subTest(case=label):
                    self.assertNotEqual(changed, data)
                    path.write_bytes(changed)
                    completed = run(path)
                    self.assertEqual((completed.returncode, completed.stdout), (2, ""))
                    self.assertIn(code, completed.stderr)

    def test_released_profiles_behave_as_before(self):
        for version, fixture in (("2.0.0", "fixtures/profiles/2.0.0/local-consistency/guide.txt"),
                                 ("0.7.1", "fixtures/valid/level-3/guide.txt")):
            with self.subTest(version=version):
                completed = run(ROOT / fixture, "--format", "text")
                self.assertNotIn("draft profile", completed.stderr)
                self.assertNotIn("Content policy: restricted-argv-1", completed.stdout)
                self.assertNotIn("Reason:", completed.stdout)


class EveryOtherCallerStillRefusesTests(unittest.TestCase):
    def test_the_dispatcher_default(self):
        data = VALID.read_bytes()
        for call in (lambda: profiles.select_profile(data), lambda: profiles.select_profile(data, "3.0.0"),
                     lambda: profiles.policy_key("3.0.0"), lambda: gv.evaluate_guide(data),
                     lambda: gv.evaluate_local_file(VALID)):
            with self.assertRaises(profiles.ProfileError) as raised:
                call()
            self.assertEqual(raised.exception.code, "profile-version-unsupported")
        self.assertNotIn("3.0.0", profiles.SUPPORTED_VERSIONS)
        selection = profiles.select_profile(data, allow_draft=True)
        self.assertTrue(selection.restricted and selection.modern and not selection.strict and not selection.corrected)

    def test_the_hosted_verifier(self):
        data = VALID.read_bytes()
        url = "https://example.com/.well-known/assistant-guide.txt"
        calls = []

        def fetch(requested, request_profile="default", accept_override=None):
            calls.append(requested)
            return hosted.fetched(requested, 200, data)

        for body in ({"url": url}, {"url": url, "required_profile_version": "3.0.0"}):
            with self.subTest(body=sorted(body)):
                calls.clear()
                with redirect_stdout(io.StringIO()):
                    request = hosted.run_post(body, fetch)
                self.assertEqual(request.status, 400)
                self.assertEqual(request.body["error"]["code"], "profile-version-unsupported")
                self.assertEqual(calls, [url])
        source = (ROOT / "api/verify.py").read_text(encoding="utf-8")
        self.assertNotIn("allow_draft", source)
        self.assertNotIn("guidecheck_restricted", source)

    def test_the_experimental_cli_contract(self):
        completed = run(VALID, "--contract", "posix-json-v1")
        result = json.loads(completed.stdout)
        self.assertEqual(result["operational"]["status"], "failed")
        self.assertIn("profile-version-unsupported", result["operational"]["error"]["message"])
        self.assertNotEqual(completed.returncode, 0)

    def test_nothing_imports_the_draft_evaluator_at_load(self):
        """A caller that never selects 3.0.0 never loads its code."""
        for module in ("guidecheck_verify", "guidecheck_profiles", "guidecheck_cli", "guidecheck_cli_contract"):
            script = f"import sys, {module}; print('guidecheck_restricted' in sys.modules, 'profile_3_0_0_invariants' in sys.modules)"
            completed = subprocess.run([sys.executable, "-c", script], cwd=ROOT / "scripts", text=True, capture_output=True)
            with self.subTest(module=module):
                self.assertEqual(completed.stdout.split(), ["False", "False"], completed.stderr)


class PackagingTests(unittest.TestCase):
    def test_the_embedded_registry_is_the_profile_file(self):
        self.assertEqual(embedded.REGISTRY_BYTES, restricted.REGISTRY_PATH.read_bytes())
        self.assertEqual(restricted.load_registry().sha256, restricted.load_registry(restricted.REGISTRY_PATH).sha256)

    def test_the_package_lists_every_module_the_cli_can_load(self):
        project = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        for module in ("guidecheck_restricted", "guidecheck_restricted_registry", "profile_3_0_0_invariants"):
            self.assertIn(f'"{module}"', project)

    def test_the_evaluator_runs_without_the_repository_around_it(self):
        """Only the listed modules, copied elsewhere: what an installed package has."""
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            for path in (ROOT / "scripts").glob("*.py"):
                if not path.name.startswith(("test_", "check_", "validate_", "eval_", "build_", "diagnose_")):
                    (target / path.name).write_bytes(path.read_bytes())
            guide = target / "guide.txt"
            guide.write_bytes(VALID.read_bytes())
            completed = subprocess.run([sys.executable, "-E", "-s", str(target / "guidecheck_cli.py"), "verify", str(guide), "--format", "text"],
                                       cwd=target, text=True, capture_output=True)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("Actions: 6 (5 shape-listed, 1 opaque)", completed.stdout)


if __name__ == "__main__":
    unittest.main()
