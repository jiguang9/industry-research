#!/usr/bin/env python3
"""Build a release zip for the industry-research Skill.

Packages exactly the files listed by tools/_manifest.py under a single
top-level `industry-research/` directory (so `SKILL.md` sits directly inside
it). No dev-only files (tests/, tools/, evals/, docs/, examples/, .github/,
.git) are included.

Produces two separate checksum artifacts, deliberately not merged into one
file, because they verify two different things at two different times:

  - SHA256SUMS.txt (next to the zip): the hash of the *downloaded zip
    itself*. Run `shasum -a 256 -c SHA256SUMS.txt` right after downloading,
    before extracting anything -- it only lists the zip, so it does not fail
    with "no such file" errors for paths that don't exist yet.
  - industry-research/MANIFEST.sha256 (inside the zip): per-file hashes of
    the extracted payload, meant to be run *after* extracting, from inside
    the extracted industry-research/ directory
    (`cd industry-research && shasum -a 256 -c MANIFEST.sha256`).

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
    for rel in files:
        digests[rel.as_posix()] = hashlib.sha256((REPO_ROOT / rel).read_bytes()).hexdigest()

    manifest_lines = [f"{digests[rel]}  {rel}" for rel in sorted(digests)]
    manifest_content = "\n".join(manifest_lines) + "\n"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel in files:
            zf.write(REPO_ROOT / rel, f"{SKILL_NAME}/{rel.as_posix()}")
        zf.writestr(f"{SKILL_NAME}/MANIFEST.sha256", manifest_content)

    zip_digest = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    sums_path.write_text(f"{zip_digest}  {zip_path.name}\n", encoding="utf-8")

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
