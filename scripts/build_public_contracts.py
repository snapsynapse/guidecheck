#!/usr/bin/env python3
"""Publish versioned contracts and source identity without rewriting guide bytes."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

from guidecheck_constants import (CORRECTED_ENGINE_VERSION, GUIDECHECK_VERSION,
                                  LEGACY_ENGINE_VERSION, STRICT_ENGINE_VERSION)

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    output = ROOT / 'docs'
    for name in ('schemas', 'profiles'):
        destination = output / name
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(ROOT / name, destination)
    commit = os.environ.get('VERCEL_GIT_COMMIT_SHA') or subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True
    ).strip()
    public_paths = ['index.html', 'verify/index.html', 'verify/verify.js', 'llms.txt',
                    '.well-known/assistant-guide.txt', '.well-known/assistant-guide-manifest.txt']
    public_paths += [str(p.relative_to(output)) for name in ('schemas', 'profiles')
                     for p in (output / name).rglob('*') if p.is_file()]
    # Include implementation digests so a deployment receipt can be tied to exact source.
    source_paths = ['api/verify.py', 'scripts/build_public_contracts.py'] + [str(p.relative_to(ROOT)) for p in (ROOT / 'scripts').glob('guidecheck*.py')]
    manifest = {
        'source_commit': commit,
        'dispatcher_version': GUIDECHECK_VERSION,
        'legacy_engine_version': LEGACY_ENGINE_VERSION,
        'strict_engine_version': STRICT_ENGINE_VERSION,
        'corrected_engine_version': CORRECTED_ENGINE_VERSION,
        'public_sha256': {p: hashlib.sha256((output / p).read_bytes()).hexdigest()
                          for p in sorted(public_paths)},
        'source_sha256': {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
                          for p in sorted(source_paths)},
    }
    (output / 'deploy-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'Published contracts and deployment manifest for {GUIDECHECK_VERSION} ({commit}).')


if __name__ == '__main__':
    main()
