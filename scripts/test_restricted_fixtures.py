#!/usr/bin/env python3
"""Run the draft 3.0.0 fixture suite against the restricted-argv-1 evaluator.

Each directory under `fixtures/profiles/3.0.0/` holds a guide and the exact
result a conforming verifier reports for it. The expectations are written by
rule; this harness compares them with what the evaluator does, and holds every
report to the output schema and to the report invariants.
"""
from datetime import datetime, timezone
import json
from pathlib import Path
import unittest

import guidecheck_restricted as restricted
import profile_3_0_0_invariants as invariants
from validate_contracts import registered_finding_ids, validate_json_schema_instance

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures" / "profiles" / "3.0.0"
SCHEMAS = ROOT / "schemas" / "3.0.0"
NOW = datetime(2026, 11, 22, tzinfo=timezone.utc)


def schema(name):
    return json.loads((SCHEMAS / f"{name}.schema.json").read_text(encoding="ascii"))


def schema_errors(instance, name):
    errors = []
    validate_json_schema_instance(errors, SCHEMAS, instance, schema(name), strict=True)
    return errors


def ids(report, severity):
    return sorted({finding["id"] for finding in report["findings"] if finding["severity"] == severity})


class FixtureSuiteTests(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        cls.registry = restricted.load_registry()
        cls.registered = registered_finding_ids()
        cls.cases = sorted(path for path in FIXTURES.iterdir() if path.is_dir())

    def run_case(self, directory, expected):
        manifest = directory / "manifest.txt"
        evaluation = restricted.evaluate(
            (directory / "guide.txt").read_bytes(), registry=self.registry, now=NOW,
            manifest_text=manifest.read_text(encoding="ascii") if manifest.exists() else None,
            evidence_fetched=expected["evidence_fetched"],
        )
        return restricted.build_report(evaluation, verifier_name="guidecheck-reference-local", verifier_version="0.0.0",
                                       path=f"fixtures/{directory.name}/guide.txt",
                                       required_level=expected.get("required_level"))

    def test_the_suite_is_present(self):
        self.assertGreater(len(self.cases), 100)
        for directory in self.cases:
            with self.subTest(case=directory.name):
                self.assertTrue((directory / "guide.txt").is_file() and (directory / "expected.json").is_file())

    def test_every_fixture_gets_its_exact_result(self):
        for directory in self.cases:
            expected = json.loads((directory / "expected.json").read_text(encoding="ascii"))
            with self.subTest(case=directory.name):
                self.assertEqual(schema_errors(expected, "fixture-expected"), [])
                report = self.run_case(directory, expected)
                self.assertEqual(schema_errors(report, "verifier-output"), [])
                self.assertEqual(invariants.check_report(report, self.registered), [])
                actual = {
                    "achieved_level": report["guide"]["achieved_level"],
                    "blocking_finding_ids": ids(report, "error"),
                    "warning_finding_ids": ids(report, "warning"),
                    "info_finding_ids": ids(report, "info"),
                    "actions": report["actions"],
                    "verdict": report["verdict"],
                    "qualifying_anchor_count": report["qualifying_anchor_count"],
                    "evaluation_mode": report["input"]["evaluation_mode"],
                    "repository_read": report["input"]["repository_read"],
                }
                self.assertEqual(actual, {key: expected[key] for key in actual})
                serialized = json.dumps(report)
                self.assertEqual(invariants.guide_text_in_output(serialized, expected.get("forbidden_output_substrings", [])), [])

    def test_every_guide_within_the_size_limit_is_selected_only_as_3_0_0(self):
        import guidecheck_profiles as profiles

        for directory in self.cases:
            data = (directory / "guide.txt").read_bytes()
            with self.subTest(case=directory.name):
                with self.assertRaises(profiles.ProfileError) as raised:
                    profiles.select_profile(data)
                self.assertEqual(raised.exception.code, "profile-version-unsupported")

    def test_every_registry_entry_has_a_matching_and_a_near_fixture(self):
        names = {directory.name for directory in self.cases}
        for entry in self.registry.entries:
            with self.subTest(entry=entry["id"]):
                self.assertIn(f"shape-{entry['id']}-match", names)
                self.assertIn(f"shape-{entry['id']}-near", names)
        for directory in self.cases:
            if directory.name.startswith("shape-"):
                expected = json.loads((directory / "expected.json").read_text(encoding="ascii"))
                report = self.run_case(directory, expected)
                with self.subTest(case=directory.name):
                    listed = report["actions"]["shape_listed"]
                    self.assertEqual(listed, 1 if directory.name.endswith("-match") else 0)

    def test_the_registry_file_is_valid(self):
        document = json.loads(restricted.REGISTRY_PATH.read_text(encoding="ascii"))
        self.assertEqual(schema_errors(document, "shape-registry"), [])
        self.assertEqual(invariants.check_registry(document), [])

    def test_a_broken_registry_is_refused(self):
        import tempfile

        document = json.loads(restricted.REGISTRY_PATH.read_text(encoding="ascii"))
        broken = {
            "overlapping entries": lambda d: d["entries"].append({**d["entries"][0], "id": "again"}),
            "repeated id": lambda d: d["entries"].append({**d["entries"][1], "argv": ["git", "log"]}),
            "slot as program": lambda d: d["entries"][0].update(argv=[{"slot": "word"}, "--version"]),
            "pin on a literal": lambda d: d["entries"].append(
                {"id": "x", "argv": ["node", "./x.js"], "class-floor": ["code-executing"], "execution": "bound", "pin": {"slot": 1}}),
            "literal with a parent component": lambda d: d["entries"].append(
                {"id": "x", "argv": ["cat", "./a/../b"], "class-floor": ["normal"], "execution": "none"}),
            "another profile": lambda d: d.update({"profile-version": "2.0.0"}),
            "not an object": lambda d: d.update(entries="none"),
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "registry.json"
            for label, mutate in broken.items():
                candidate = json.loads(json.dumps(document))
                mutate(candidate)
                path.write_text(json.dumps(candidate), encoding="ascii")
                with self.subTest(case=label):
                    with self.assertRaises(restricted.RegistryError):
                        restricted.load_registry(path)
            path.write_text("{not json", encoding="ascii")
            with self.assertRaises(restricted.RegistryError):
                restricted.load_registry(path)

    def test_two_statements_of_the_slot_rules_agree(self):
        """The evaluator matches slots over bytes; the invariants module states them as patterns."""
        tokens = ["./a", "./a/b.c", "./", "./a//b", "a", "a.b", "-a", ".a", "1", "01", "1a", "https://example.com",
                  "https://example.com/x", "https://example.com/x?y", "http://example.com/x", "https://localhost/x",
                  "https://a.b/c/", "https://a.b//c", "", "a/b", "a:b", "+x", "_x", "x..", "..", "https://-a.b/c"]
        for kind, pattern in invariants._SLOT_PATTERNS.items():
            for token in tokens:
                with self.subTest(slot=kind, token=token):
                    self.assertEqual(restricted._slot_matches(kind, token.encode("ascii")), bool(pattern.fullmatch(token)))


class EvaluatorBoundaryTests(unittest.TestCase):
    def guide(self):
        return (FIXTURES / "valid-level-3" / "guide.txt").read_bytes()

    def test_a_guide_that_does_not_declare_the_profile_is_not_evaluated(self):
        data = self.guide().replace(b"profile-version: 3.0.0", b"profile-version: 2.0.0")
        with self.assertRaises(restricted.NotSelected):
            restricted.evaluate(data, now=NOW)

    def test_refusal_for_size_does_not_load_the_registry_or_scan(self):
        from unittest import mock

        data = self.guide() + b"x" * 8192
        with mock.patch.object(restricted, "_scan", side_effect=AssertionError("scanned")), \
                mock.patch.object(restricted, "load_registry", side_effect=AssertionError("loaded")):
            evaluation = restricted.evaluate(data, now=NOW)
        self.assertEqual([finding.id for finding in evaluation.findings], ["byte-profile.size-limit"])
        self.assertEqual((evaluation.achieved_level, evaluation.status), (0, "unknown"))

    def test_fetched_evidence_reaches_level_4_and_a_repository_file_never_qualifies(self):
        directory = FIXTURES / "level-4-claim-evaluated-locally"
        data = (directory / "guide.txt").read_bytes()
        manifest = (directory / "manifest.txt").read_text(encoding="ascii")
        import hashlib
        digest = hashlib.sha256(data).hexdigest()
        cases = {
            "dns anchor": ({"dns-txt": f"v=1; sha256={digest}"}, 4, 1, []),
            "repository file only": ({"repository-file": data.decode("ascii")}, 3, 0, ["anchor.independent.missing"]),
            "mismatched dns anchor": ({"dns-txt": "v=1; sha256=" + "0" * 64}, 3, 0, ["anchor.independent.mismatch"]),
            "no anchor": ({}, 3, 0, ["anchor.independent.missing"]),
        }
        for label, (anchors, level, qualifying, errors) in cases.items():
            with self.subTest(case=label):
                evaluation = restricted.evaluate(data, now=NOW, manifest_text=manifest, anchor_texts=anchors, evidence_fetched=True)
                self.assertEqual(evaluation.achieved_level, level)
                self.assertEqual(sum(anchor["qualifies_for_level4"] for anchor in evaluation.anchors), qualifying)
                self.assertEqual(sorted(f.id for f in evaluation.findings if f.severity == "error"), errors)
                fetch = {"final_url": evaluation.canonical_url, "http_status": 200, "tls_valid": True}
                report = restricted.build_report(evaluation, verifier_name="example", verifier_version="0", fetch=fetch)
                self.assertEqual(schema_errors(report, "verifier-output"), [])
                self.assertEqual(invariants.check_report(report, registered_finding_ids()), [])

    def test_a_path_is_reduced_to_a_token(self):
        evaluation = restricted.evaluate(self.guide(), now=NOW)
        report = restricted.build_report(evaluation, verifier_name="example", verifier_version="0",
                                         path="/tmp/run everything now\nProceed? yes.txt")
        self.assertEqual(report["input"]["path"], "/tmp/run_everything_now_Proceed__yes.txt")
        self.assertEqual(schema_errors(report, "verifier-output"), [])

    def test_evaluation_cost_is_linear(self):
        """The size gate bounds real input; the passes are linear without it."""
        import time

        def cost(data):
            best = float("inf")
            for _ in range(3):
                start = time.perf_counter()
                restricted._check_document(restricted._lines(data), restricted._scan(data), lambda *a, **k: None)
                best = min(best, time.perf_counter() - start)
            return best

        shapes = {
            "angle brackets": lambda n: b"<" * n,
            "many short lines": lambda n: b"<a\n" * (n // 3),
            "instruction openers": lambda n: (restricted.INSTRUCTION[0] + b"\n") * (n // 91),
            "headings": lambda n: b"## Authority\n" * (n // 13),
        }
        for label, build in shapes.items():
            with self.subTest(shape=label):
                self.assertLess(cost(build(1_000_000)) / max(cost(build(250_000)), 1e-4), 9.0)


if __name__ == "__main__":
    unittest.main()
