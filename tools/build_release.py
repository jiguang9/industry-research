#!/usr/bin/env python3
"""Build a release zip for the industry-research Skill.

Packages exactly the files listed by tools/_manifest.py under a single
top-level `industry-research/` directory (so `SKILL.md` sits directly inside
it), and writes a SHA256SUMS.txt alongside the zip. No dev-only files
(tests/, tools/, evals/, docs/, examples/, .github/, .git) are included.

Usage:
    python3 tools/build_release.py [--out-dir dist]
"""
from __future__ import annotations

import argparse
import hashlib
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _manifest import iter_manifest_files  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_NAME = "industry-research"


def build(out_dir: Path) -> tuple[Path, Path]:
    version = (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_path = out_dir / f"{SKILL_NAME}-v{version}.zip"
    sums_path = out_dir / "SHA256SUMS.txt"

    files = iter_manifest_files(REPO_ROOT)
    if not files:
        raise SystemExit("error: manifest resolved to zero files; refusing to build an empty release")

    digests: dict[str, str] = {}
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel in files:
            src = REPO_ROOT / rel
            arcname = f"{SKILL_NAME}/{rel.as_posix()}"
            zf.write(src, arcname)
            digests[arcname] = hashlib.sha256(src.read_bytes()).hexdigest()

    zip_digest = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    with sums_path.open("w", encoding="utf-8") as f:
        f.write(f"{zip_digest}  {zip_path.name}\n")
        for arcname in sorted(digests):
            f.write(f"{digests[arcname]}  {arcname}\n")

    return zip_path, sums_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out-dir", type=Path, default=REPO_ROOT / "dist")
    args = parser.parse_args()

    zip_path, sums_path = build(args.out_dir)
    print(f"Built {zip_path}")
    print(f"Checksums at {sums_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
