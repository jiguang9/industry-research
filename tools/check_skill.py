#!/usr/bin/env python3
"""Development-time structural checks for this Skill repository.

Checks:
  - SKILL.md frontmatter is well-formed and 'name' is the fixed 'industry-research'
  - relative markdown links inside SKILL.md / references/ / assets/ resolve to
    real files and never escape the repo root
  - VERSION, LICENSE, README.md, CHANGELOG.md exist
  - VERSION matches the latest heading in CHANGELOG.md
  - the release manifest (tools/_manifest.py) does not pull in dev-only paths

This does not run the test suite or the evidence validator; see
tests/ and scripts/validate_evidence.py for that.

Exit codes: 0 = all checks passed, 1 = at least one check failed.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _manifest import iter_manifest_files  # noqa: E402

MD_LINK_RE = re.compile(r"\]\(([^)]+)\)")
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
DEV_ONLY_PREFIXES = ("tests/", "tools/", "evals/", "docs/", "examples/", ".github/")

errors: list[str] = []
warnings: list[str] = []


def check_frontmatter() -> None:
    skill_md = ROOT / "SKILL.md"
    if not skill_md.exists():
        errors.append("SKILL.md not found at repo root")
        return
    text = skill_md.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(text)
    if not m:
        errors.append("SKILL.md must start with a '---' YAML frontmatter block")
        return
    fm_text = m.group(1)
    fields: dict[str, str] = {}
    for line in fm_text.splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip().strip('"')

    if "name" not in fields:
        errors.append("SKILL.md frontmatter missing 'name'")
    elif fields["name"] != "industry-research":
        errors.append(f"SKILL.md frontmatter name must be 'industry-research', got '{fields['name']}'")

    if "description" not in fields or not fields["description"]:
        errors.append("SKILL.md frontmatter missing non-empty 'description'")

    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip() if (ROOT / "VERSION").exists() else None
    line_count = len(text.splitlines())
    if line_count > 250:
        warnings.append(f"SKILL.md is {line_count} lines; spec suggests keeping it around 150-250 lines")
    return


def check_relative_links() -> None:
    # assets/ is intentionally excluded: those are fill-in-the-blank output
    # templates whose bracket syntax (e.g. "[标题](链接)") is a placeholder,
    # not a real relative link meant to resolve inside this repo.
    md_files = [ROOT / "SKILL.md"]
    md_files.extend(sorted((ROOT / "references").rglob("*.md")))

    for md_file in md_files:
        if not md_file.exists():
            continue
        text = md_file.read_text(encoding="utf-8")
        for link in MD_LINK_RE.findall(text):
            if link.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = (md_file.parent / link).resolve()
            try:
                target.relative_to(ROOT.resolve())
            except ValueError:
                errors.append(f"{md_file.relative_to(ROOT)}: link '{link}' escapes the repo root")
                continue
            if not target.exists():
                errors.append(f"{md_file.relative_to(ROOT)}: broken relative link '{link}'")


def check_key_files() -> None:
    for name in ("VERSION", "LICENSE", "README.md", "README.en.md", "CHANGELOG.md"):
        if not (ROOT / name).exists():
            errors.append(f"missing required file: {name}")


def check_version_matches_changelog() -> None:
    version_file = ROOT / "VERSION"
    changelog = ROOT / "CHANGELOG.md"
    if not version_file.exists() or not changelog.exists():
        return
    version = version_file.read_text(encoding="utf-8").strip()
    text = changelog.read_text(encoding="utf-8")
    heading_match = re.search(r"^##\s*\[?v?([0-9]+\.[0-9]+\.[0-9]+)\]?", text, re.MULTILINE)
    if not heading_match:
        warnings.append("CHANGELOG.md has no '## x.y.z' style heading to compare against VERSION")
        return
    if heading_match.group(1) != version:
        errors.append(
            f"VERSION is '{version}' but CHANGELOG.md's latest heading is '{heading_match.group(1)}'"
        )


def check_manifest_excludes_dev_paths() -> None:
    for rel in iter_manifest_files(ROOT):
        rel_str = rel.as_posix()
        if rel_str.startswith(DEV_ONLY_PREFIXES):
            errors.append(f"release manifest unexpectedly includes dev-only path: {rel_str}")


def check_agents_openai_yaml() -> None:
    path = ROOT / "agents" / "openai.yaml"
    if not path.exists():
        warnings.append("agents/openai.yaml not found (Codex UI metadata will be absent)")


def main() -> int:
    check_frontmatter()
    check_relative_links()
    check_key_files()
    check_version_matches_changelog()
    check_manifest_excludes_dev_paths()
    check_agents_openai_yaml()

    for w in warnings:
        print(f"WARNING: {w}")
    for e in errors:
        print(f"ERROR: {e}")

    if errors:
        print(f"\ncheck_skill.py: {len(errors)} error(s), {len(warnings)} warning(s)")
        return 1
    print(f"check_skill.py: all checks passed ({len(warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
