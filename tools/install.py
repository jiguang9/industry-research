#!/usr/bin/env python3
"""Local installer for the industry-research Skill.

This is a project-provided convenience tool, not an official platform
installer. It copies this repository's Skill payload (SKILL.md + agents/,
references/, assets/, scripts/) into a target directory on disk. It never
downloads anything, never modifies platform configuration/trust settings,
and only touches the platform you explicitly select.

Usage:
    python3 tools/install.py --platform claude
    python3 tools/install.py --platform codex
    python3 tools/install.py --platform openclaw
    python3 tools/install.py --platform hermes
    python3 tools/install.py --platform codex --dest /absolute/path/industry-research
    python3 tools/install.py --platform claude --replace

Default target directories (see docs/platform-compatibility.md for how these
were verified):
    claude    ~/.claude/skills/industry-research
    codex     ~/.agents/skills/industry-research
    openclaw  ~/.openclaw/skills/industry-research
    hermes    ~/.hermes/skills/industry-research

If your setup uses a custom profile, workspace, or remote environment, pass
--dest with the exact target directory instead of relying on the platform
default -- this tool cannot introspect another program's active profile.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _manifest import iter_manifest_files  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_NAME = "industry-research"

DEFAULT_TARGETS = {
    "claude": Path.home() / ".claude" / "skills" / SKILL_NAME,
    "codex": Path.home() / ".agents" / "skills" / SKILL_NAME,
    "openclaw": Path.home() / ".openclaw" / "skills" / SKILL_NAME,
    "hermes": Path.home() / ".hermes" / "skills" / SKILL_NAME,
}

# Overridable so tests (and unusual $HOME setups) don't have to write into the
# real home directory. Not a supported user-facing configuration surface.
BACKUP_ROOT = Path(os.environ.get("INDUSTRY_RESEARCH_BACKUP_ROOT", str(Path.home() / ".industry-research-backups")))


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def build_payload_hashes(root: Path) -> dict[str, str]:
    return {rel.as_posix(): sha256_of(root / rel) for rel in iter_manifest_files(root)}


def existing_target_hashes(target: Path) -> dict[str, str]:
    if not target.exists():
        return {}
    hashes: dict[str, str] = {}
    for p in target.rglob("*"):
        if p.is_file() and p.name != "MANIFEST.sha256":
            hashes[p.relative_to(target).as_posix()] = sha256_of(p)
    return hashes


def stage_payload(tmp_dir: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for rel in iter_manifest_files(REPO_ROOT):
        src = REPO_ROOT / rel
        dst = tmp_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        hashes[rel.as_posix()] = sha256_of(dst)

    manifest_lines = [f"{h}  {rel}" for rel, h in sorted(hashes.items())]
    (tmp_dir / "MANIFEST.sha256").write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")
    return hashes


def guard_path_safety(target: Path) -> None:
    resolved_target = target.resolve()
    resolved_source = REPO_ROOT.resolve()

    if resolved_target == resolved_source:
        raise SystemExit("error: install target is the same as the source repository; refusing to proceed")

    try:
        resolved_target.relative_to(resolved_source)
        raise SystemExit(f"error: install target {resolved_target} is inside the source repository; refusing")
    except ValueError:
        pass

    try:
        resolved_source.relative_to(resolved_target)
        raise SystemExit(f"error: install target {resolved_target} contains the source repository; refusing")
    except ValueError:
        pass

    if target.is_symlink():
        raise SystemExit(
            f"error: install target {target} is a symlink; remove it manually first if you intend to replace it "
            "(refusing to follow an existing symlink automatically)"
        )


def print_next_steps(platform: str, target: Path) -> None:
    hints = {
        "claude": f'Invoke with "/industry-research" or by describing the task in Claude Code. Personal-scope target: {target}',
        "codex": f'Mention with "$industry-research" in Codex CLI/IDE, or "@industry-research" in ChatGPT Work. Target: {target}',
        "openclaw": f'Run "openclaw skills list" to confirm discovery, then "/skill industry-research <task>". Target: {target}',
        "hermes": f'Ask the current Hermes agent to list/describe its skills to confirm discovery, then "/industry-research <task>". Target: {target}',
    }
    print(hints.get(platform, f"Installed to {target}"))


def install(platform: str, dest: Path | None, replace: bool) -> int:
    if dest is not None:
        target = dest
    else:
        target = DEFAULT_TARGETS[platform]

    guard_path_safety(target)

    version = (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()

    with tempfile.TemporaryDirectory(prefix="industry-research-payload-") as tmp:
        tmp_path = Path(tmp)
        new_hashes = stage_payload(tmp_path)

        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(tmp_path, target)
            print(f"Installed industry-research v{version} to {target}")
            print_next_steps(platform, target)
            return 0

        old_hashes = existing_target_hashes(target)
        if old_hashes == new_hashes:
            print(f"industry-research v{version} is already installed and up to date at {target}")
            print_next_steps(platform, target)
            return 0

        added = sorted(set(new_hashes) - set(old_hashes))
        removed = sorted(set(old_hashes) - set(new_hashes))
        changed = sorted(k for k in set(new_hashes) & set(old_hashes) if new_hashes[k] != old_hashes[k])

        if not replace:
            print(f"A different installation already exists at {target}:")
            if added:
                print(f"  would add:    {', '.join(added)}")
            if removed:
                print(f"  would remove: {', '.join(removed)}")
            if changed:
                print(f"  would change: {', '.join(changed)}")
            print("Re-run with --replace to overwrite (a backup will be kept outside any skill-scan directory).")
            return 1

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup_dir = BACKUP_ROOT / f"{platform}-{timestamp}"
        backup_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(target), str(backup_dir))
        try:
            shutil.copytree(tmp_path, target)
        except Exception:
            # copytree can fail partway through and leave `target` existing
            # again as a partial directory. shutil.move() onto an existing
            # directory nests the source *inside* it rather than replacing
            # it, so the backup would end up buried at
            # target/<backup_dir_name>/... instead of restored to `target`
            # itself. Clear the partial directory first so the restore lands
            # exactly where the original was.
            if target.exists():
                shutil.rmtree(target)
            shutil.move(str(backup_dir), str(target))
            raise
        print(f"Replaced existing installation at {target} (backup kept at {backup_dir})")
        print(f"Installed industry-research v{version} to {target}")
        print_next_steps(platform, target)
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--platform", choices=sorted(DEFAULT_TARGETS.keys()), required=True)
    parser.add_argument("--dest", type=Path, default=None, help="exact target skill directory (overrides platform default)")
    parser.add_argument("--replace", action="store_true", help="overwrite an existing, differing installation (keeps a backup)")
    args = parser.parse_args()

    try:
        return install(args.platform, args.dest, args.replace)
    except SystemExit as exc:
        if isinstance(exc.code, str):
            print(exc.code, file=sys.stderr)
            return 1
        raise


if __name__ == "__main__":
    sys.exit(main())
