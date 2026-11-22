#!/usr/bin/env python3
"""Gate a release build on the tag that triggered it.

The release workflow signs whatever a pushed tag points at. This check runs
before anything is built and refuses the tag unless all of these hold:

- the tag name is exactly v<major>.<minor>.<patch>;
- it equals the software version in scripts/guidecheck_constants.py;
- RELEASE_NOTES-<version>.md exists in the tagged tree;
- the tag is an annotated tag object, not a lightweight ref;
- it resolves to the commit the workflow checked out, when one is given;
- that commit is an ancestor of the main branch;
- the tag carries a signature that verifies against the allowed signers read
  from the main branch, not from the tagged tree.

Limit, stated plainly: this script and the workflow that calls it live in the
tagged tree. Someone able to push both a tag and workflow changes can remove
the gate. It stops mistakes, mislabeled versions, tags on unmerged commits and
tags pushed with a credential that cannot sign; repository rules and credential
scoping are what stop the rest.

Standard library and git only. Exit 0 when every check passes, 1 otherwise.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess
import sys
import tempfile

TAG_PATTERN = re.compile(r"v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)")
VERSION_ASSIGNMENT = re.compile(r'^GUIDECHECK_VERSION = "([^"\n]+)"$', re.M)
ALLOWED_SIGNERS_PATH = ".github/allowed_signers"


def git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)


def software_version(repo: Path) -> str | None:
    """Read the version by pattern; the tagged tree is not imported or run."""
    try:
        text = (repo / "scripts" / "guidecheck_constants.py").read_text(encoding="utf-8")
    except OSError:
        return None
    matches = VERSION_ASSIGNMENT.findall(text)
    return matches[0] if len(matches) == 1 else None


def check_release_ref(repo: Path, tag: str, main_ref: str, expect_commit: str | None) -> list[tuple[str, bool, str]]:
    results: list[tuple[str, bool, str]] = []

    def record(name: str, ok: bool, detail: str = "") -> bool:
        results.append((name, ok, detail))
        return ok

    if not record("tag-grammar", TAG_PATTERN.fullmatch(tag) is not None,
                  "the tag must be exactly v<major>.<minor>.<patch>"):
        return results  # the name is not safe to hand to later checks
    version = tag[1:]
    ref = "refs/tags/" + tag

    declared = software_version(repo)
    record("tag-matches-software-version", declared == version,
           f"tag says {version}; scripts/guidecheck_constants.py says {declared}")
    record("release-notes-present", (repo / f"RELEASE_NOTES-{version}.md").is_file(),
           f"RELEASE_NOTES-{version}.md is missing")

    object_type = git(repo, "cat-file", "-t", ref).stdout.strip()
    annotated = record("tag-is-annotated", object_type == "tag",
                       f"{ref} is a {object_type or 'missing ref'}, not an annotated tag object")

    commit = git(repo, "rev-parse", "--verify", "--quiet", ref + "^{commit}").stdout.strip()
    if not record("tag-resolves-to-commit", bool(commit), f"{ref} does not resolve to a commit"):
        return results
    if expect_commit is not None:
        record("tag-is-the-built-commit", commit == expect_commit,
               f"tag points at {commit}; the build checked out {expect_commit}")

    main_commit = git(repo, "rev-parse", "--verify", "--quiet", main_ref + "^{commit}").stdout.strip()
    on_main = bool(main_commit) and git(repo, "merge-base", "--is-ancestor", commit, main_commit).returncode == 0
    record("commit-is-on-main", on_main, f"{commit} is not an ancestor of {main_ref}")

    signers = git(repo, "show", f"{main_ref}:{ALLOWED_SIGNERS_PATH}")
    if not record("allowed-signers-on-main", signers.returncode == 0 and bool(signers.stdout.strip()),
                  f"{ALLOWED_SIGNERS_PATH} could not be read from {main_ref}"):
        return results
    if annotated:
        with tempfile.TemporaryDirectory() as scratch:
            signers_file = Path(scratch) / "allowed_signers"
            signers_file.write_text(signers.stdout, encoding="utf-8")
            verified = git(repo, "-c", "gpg.format=ssh", "-c", f"gpg.ssh.allowedSignersFile={signers_file}",
                           "verify-tag", ref)
        record("tag-signature-verifies", verified.returncode == 0,
               "the tag is unsigned or not signed by a key in the allowed signers on " + main_ref)
    else:
        record("tag-signature-verifies", False, "a lightweight tag cannot carry a signature")
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Refuse a release tag that is not a signed, merged, correctly named version tag.")
    parser.add_argument("tag", help="tag name, for example v2.0.1")
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1], help="repository to check")
    parser.add_argument("--main-ref", default="origin/main", help="ref that holds merged history and the allowed signers")
    parser.add_argument("--expect-commit", help="full commit id the build checked out")
    args = parser.parse_args(argv)

    results = check_release_ref(args.repo, args.tag, args.main_ref, args.expect_commit)
    failed = 0
    for name, ok, detail in results:
        if ok:
            print(f"PASS {name}")
        else:
            failed += 1
            print(f"FAIL {name}: {detail}")
    if failed:
        print(f"Release ref refused: {failed} check(s) failed. Nothing was built or signed.")
        return 1
    print(f"Release ref accepted: {len(results)} checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
