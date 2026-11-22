#!/usr/bin/env python3
"""Hermetic tests for the release ref gate.

Each test builds a throwaway repository with throwaway SSH signing keys in a
temporary directory. Nothing reads the developer's git configuration, keys or
agent, and nothing touches this repository's refs or the network.
"""

from __future__ import annotations

from contextlib import redirect_stdout
import io
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

import check_release_ref as gate

NEEDS = [tool for tool in ("git", "ssh-keygen") if shutil.which(tool) is None]


def run(cwd: Path, *args: str, env: dict[str, str]) -> str:
    done = subprocess.run(list(args), cwd=cwd, env=env, capture_output=True, text=True)
    if done.returncode != 0:
        raise AssertionError(f"{args} failed: {done.stderr}")
    return done.stdout.strip()


@unittest.skipIf(NEEDS, "missing tools: " + ", ".join(NEEDS))
class ReleaseRefGateTests(unittest.TestCase):
    def setUp(self):
        self.scratch = Path(tempfile.mkdtemp(prefix="guidecheck-release-gate-"))
        self.addCleanup(shutil.rmtree, self.scratch, ignore_errors=True)
        self.repo = self.scratch / "repo"
        self.repo.mkdir()
        self.env = {
            "PATH": os.environ.get("PATH", ""),
            "HOME": str(self.scratch),
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_AUTHOR_NAME": "Release Gate Test", "GIT_AUTHOR_EMAIL": "maintainer@example.test",
            "GIT_COMMITTER_NAME": "Release Gate Test", "GIT_COMMITTER_EMAIL": "maintainer@example.test",
        }
        self.maintainer = self.keypair("maintainer")
        self.stranger = self.keypair("stranger")
        self.g("init", "--quiet", "--initial-branch=main")
        self.write("scripts/guidecheck_constants.py", 'GUIDECHECK_VERSION = "3.1.4"\n')
        self.write("RELEASE_NOTES-3.1.4.md", "notes\n")
        self.write(gate.ALLOWED_SIGNERS_PATH, self.signer_line(self.maintainer))
        self.main_commit = self.commit("release 3.1.4")
        # The gate reads merged history and signers through a named ref, as the
        # workflow does with origin/main.
        self.g("update-ref", "refs/remotes/origin/main", self.main_commit)

    def g(self, *args: str) -> str:
        return run(self.repo, "git", *args, env=self.env)

    def keypair(self, name: str) -> Path:
        key = self.scratch / name
        run(self.scratch, "ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", name, "-f", str(key), env=self.env)
        return key

    def signer_line(self, key: Path) -> str:
        kind, material = key.with_suffix(".pub").read_text().split()[:2]
        return f'maintainer@example.test namespaces="git" {kind} {material}\n'

    def write(self, relative: str, text: str) -> None:
        path = self.repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def commit(self, message: str) -> str:
        self.g("add", "-A")
        self.g("commit", "--quiet", "--no-gpg-sign", "-m", message)
        return self.g("rev-parse", "HEAD")

    def signed_tag(self, name: str, key: Path, target: str = "HEAD") -> None:
        self.g("-c", "gpg.format=ssh", "-c", f"user.signingkey={key}", "tag", "-s", "-m", name, name, target)

    def outcome(self, tag: str, expect_commit: str | None = None) -> dict[str, bool]:
        return {name: ok for name, ok, _ in gate.check_release_ref(self.repo, tag, "origin/main", expect_commit)}

    def cli(self, *args: str) -> tuple[int, str]:
        out = io.StringIO()
        with redirect_stdout(out):
            code = gate.main([*args, "--repo", str(self.repo)])
        return code, out.getvalue()

    def failed(self, tag: str, expect_commit: str | None = None) -> set[str]:
        return {name for name, ok in self.outcome(tag, expect_commit).items() if not ok}

    def test_signed_merged_matching_tag_is_accepted(self):
        self.signed_tag("v3.1.4", self.maintainer)
        result = self.outcome("v3.1.4", self.main_commit)
        self.assertEqual(len(result), 9)
        self.assertTrue(all(result.values()), result)
        code, text = self.cli("v3.1.4", "--expect-commit", self.main_commit)
        self.assertEqual(code, 0)
        self.assertIn("Release ref accepted: 9 checks passed.", text)
        self.assertNotIn("FAIL", text)

    def test_names_that_are_not_plain_versions_are_refused_before_git_runs(self):
        for name in ("vercel-test", "v3.1", "v3.1.4-rc1", "v3.1.4+build", "v03.1.4", "3.1.4", "v3.1.4\n",
                     "v3.1.4 --force", "--upload-pack=x", "v3.1.4^{commit}", "v3.1.4/../../main", ""):
            with self.subTest(name):
                self.assertEqual(gate.check_release_ref(self.repo, name, "origin/main", None),
                                 [("tag-grammar", False, "the tag must be exactly v<major>.<minor>.<patch>")])

    def test_tag_that_disagrees_with_the_software_version(self):
        self.signed_tag("v3.1.5", self.maintainer)
        self.assertEqual(self.failed("v3.1.5"), {"tag-matches-software-version", "release-notes-present"})

    def test_missing_release_notes(self):
        (self.repo / "RELEASE_NOTES-3.1.4.md").unlink()
        self.signed_tag("v3.1.4", self.maintainer)
        self.assertEqual(self.failed("v3.1.4"), {"release-notes-present"})

    def test_ambiguous_or_missing_version_constant(self):
        self.write("scripts/guidecheck_constants.py", 'GUIDECHECK_VERSION = "3.1.4"\nGUIDECHECK_VERSION = "9.9.9"\n')
        self.signed_tag("v3.1.4", self.maintainer)
        self.assertIn("tag-matches-software-version", self.failed("v3.1.4"))

    def test_lightweight_tag(self):
        self.g("tag", "v3.1.4")
        self.assertEqual(self.failed("v3.1.4"), {"tag-is-annotated", "tag-signature-verifies"})

    def test_unsigned_annotated_tag(self):
        self.g("tag", "-a", "--no-sign", "-m", "v3.1.4", "v3.1.4")
        self.assertEqual(self.failed("v3.1.4"), {"tag-signature-verifies"})

    def test_tag_signed_by_a_key_that_is_not_allowed(self):
        self.signed_tag("v3.1.4", self.stranger)
        self.assertEqual(self.failed("v3.1.4"), {"tag-signature-verifies"})

    def test_signer_added_only_in_the_tagged_tree_does_not_count(self):
        # A commit that is not on main adds the stranger's key to the allowed
        # signers and is tagged with that key. Signers are read from main.
        self.g("checkout", "--quiet", "-b", "side")
        self.write(gate.ALLOWED_SIGNERS_PATH, self.signer_line(self.maintainer) + self.signer_line(self.stranger))
        side = self.commit("add a signer off main")
        self.signed_tag("v3.1.4", self.stranger)
        self.assertEqual(self.failed("v3.1.4", side), {"commit-is-on-main", "tag-signature-verifies"})

    def test_correctly_signed_tag_on_an_unmerged_commit(self):
        self.g("checkout", "--quiet", "-b", "side")
        self.write("extra.txt", "not reviewed\n")
        side = self.commit("unmerged work")
        self.signed_tag("v3.1.4", self.maintainer)
        self.assertEqual(self.failed("v3.1.4", side), {"commit-is-on-main"})

    def test_tag_that_is_not_the_commit_being_built(self):
        self.signed_tag("v3.1.4", self.maintainer)
        self.assertEqual(self.failed("v3.1.4", "0" * 40), {"tag-is-the-built-commit"})

    def test_missing_tag(self):
        self.assertEqual(self.failed("v3.1.4"), {"tag-is-annotated", "tag-resolves-to-commit"})
        code, text = self.cli("v3.1.4")
        self.assertEqual(code, 1)
        self.assertIn("Nothing was built or signed.", text)

    def test_branch_with_the_same_name_does_not_stand_in_for_the_tag(self):
        self.g("branch", "v3.1.4")
        self.assertEqual(self.failed("v3.1.4"), {"tag-is-annotated", "tag-resolves-to-commit"})

    def test_allowed_signers_missing_from_main(self):
        self.g("rm", "--quiet", gate.ALLOWED_SIGNERS_PATH)
        commit = self.commit("drop signers")
        self.g("update-ref", "refs/remotes/origin/main", commit)
        self.signed_tag("v3.1.4", self.maintainer)
        self.assertEqual(self.failed("v3.1.4"), {"allowed-signers-on-main"})


if __name__ == "__main__":
    unittest.main()
