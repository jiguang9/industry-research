"""Shared definition of which files belong in the published Skill payload.

Used by tools/install.py, tools/build_release.py, and tools/check_skill.py so
the three never disagree about what "the skill" consists of. Development-only
material (tests/, tools/, evals/, docs/, examples/, .github/, .git) is
intentionally excluded -- installing or releasing the skill must never pull
those in.
"""
from __future__ import annotations

from pathlib import Path

TOP_LEVEL_INCLUDES = [
    "SKILL.md",
    "VERSION",
    "LICENSE",
    "README.md",
    "README.en.md",
    "CHANGELOG.md",
    "agents",
    "references",
    "assets",
    "scripts",
]

EXCLUDE_NAMES = {"__pycache__", ".DS_Store"}
EXCLUDE_SUFFIXES = {".pyc"}


def iter_manifest_files(root: Path) -> list[Path]:
    """Return the sorted list of paths (relative to root) that make up the
    installable/releasable skill payload. Only includes files that actually
    exist under root; a missing optional entry is silently skipped.
    """
    root = Path(root)
    files: list[Path] = []
    for entry in TOP_LEVEL_INCLUDES:
        p = root / entry
        if not p.exists():
            continue
        if p.is_file():
            files.append(p.relative_to(root))
        elif p.is_dir():
            for sub in sorted(p.rglob("*")):
                if sub.is_dir():
                    continue
                if sub.name in EXCLUDE_NAMES or sub.suffix in EXCLUDE_SUFFIXES:
                    continue
                if any(part in EXCLUDE_NAMES for part in sub.parts):
                    continue
                files.append(sub.relative_to(root))
    return sorted(set(files))
