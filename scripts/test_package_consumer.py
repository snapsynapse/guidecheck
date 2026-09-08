#!/usr/bin/env python3
"""Build and install the wheel, then exercise dispatch outside the checkout."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import venv

ROOT = Path(__file__).resolve().parents[1]


def run(args, cwd, env):
    result = subprocess.run(args, cwd=cwd, env=env, text=True,
                            capture_output=True, timeout=240)
    if result.returncode:
        raise RuntimeError(f"{args!r} exited {result.returncode}\n{result.stdout}\n{result.stderr}")
    return result.stdout


def main():
    with tempfile.TemporaryDirectory(prefix="guidecheck-package-") as directory:
        temp = Path(directory)
        source = temp / "source"
        source.mkdir()
        for name in ("pyproject.toml", "README.md", "LICENSE", "LICENSE-MIT"):
            shutil.copy2(ROOT / name, source / name)
        shutil.copytree(ROOT / "scripts", source / "scripts",
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.egg-info"))
        env = dict(os.environ)
        env.pop("PYTHONPATH", None)
        env.pop("PYTHONHOME", None)
        environment = temp / "environment"
        venv.EnvBuilder(with_pip=True).create(environment)
        python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        wheels = temp / "wheels"
        run([str(python), "-m", "pip", "wheel", str(source), "--no-deps",
             "--wheel-dir", str(wheels)], temp, env)
        wheel, = wheels.glob("guidecheck-*.whl")
        run([str(python), "-m", "pip", "install", "--no-deps", str(wheel)], temp, env)
        run([str(python), "-I", "-c", "import guidecheck_corrected"], temp, env)
        # Exercise the actual installed console entry point outside the checkout.
        entrypoint = environment / ("Scripts/guidecheck.exe" if os.name == "nt" else "bin/guidecheck")
        invoke = [str(entrypoint)]
        original = (ROOT / "fixtures/valid/level-3/guide.txt").read_text()
        for version in ("0.7.1", "1.0.0", "2.0.0"):
            guide = temp / (version + ".txt")
            text = re.sub(r"(?m)^profile-version: .*", "profile-version: " + version, original)
            text = re.sub(r"(?m)^verifier-conformance: .*",
                          "verifier-conformance: human-verifiable-assistant-guide-verifier >=0.7.0, <3.0.0", text)
            if version == "2.0.0":
                # Adopting a corrected profile is a guide migration, not a header-only change.
                text = (ROOT / "fixtures/profiles/2.0.0/corrected-safe-negation/guide.txt").read_text()
                text = re.sub(r"(?m)^manifest-url: .*\n", "", text)
            guide.write_text(text)
            report = json.loads(run(invoke + ["verify", str(guide)], temp, env))
            assert report["guide"]["achieved_level"] == 3, report
            if version == "2.0.0":
                assert report["profile_selection"]["content_policy"] == "corrected-content-1"
            print(f"PASS installed wheel: profile {version}")
        scanned = temp / "README.md"
        scanned.write_text("# Public instructions\nRead the documented workflow.\n")
        json.loads(run(invoke + ["scan", str(scanned), "--json"], temp, env))
        print("PASS installed wheel: scanner dispatch")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
