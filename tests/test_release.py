"""Tests for tools/build_release.py."""
from __future__ import annotations

import hashlib
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD_PY = ROOT / "tools" / "build_release.py"


class BuildReleaseTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.out_dir = Path(self._tmp.name) / "dist"

    def tearDown(self):
        self._tmp.cleanup()

    def _build(self) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(BUILD_PY), "--out-dir", str(self.out_dir)],
            capture_output=True,
            text=True,
        )

    def test_build_succeeds_and_produces_zip_and_checksums(self):
        result = self._build()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        zip_path = self.out_dir / f"industry-research-v{version}.zip"
        sums_path = self.out_dir / "SHA256SUMS.txt"
        self.assertTrue(zip_path.exists())
        self.assertTrue(sums_path.exists())

    def test_zip_has_single_top_level_dir_with_skill_md_directly_inside(self):
        self._build()
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        zip_path = self.out_dir / f"industry-research-v{version}.zip"
        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
        top_levels = {n.split("/")[0] for n in names}
        self.assertEqual(top_levels, {"industry-research"})
        self.assertIn("industry-research/SKILL.md", names)

    def test_zip_excludes_dev_only_paths(self):
        self._build()
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        zip_path = self.out_dir / f"industry-research-v{version}.zip"
        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
        for name in names:
            for dev_dir in ("tests/", "tools/", "evals/", "docs/", "examples/", ".github/"):
                self.assertFalse(
                    name.startswith(f"industry-research/{dev_dir}"), f"{name} should not be in the release zip"
                )

    def test_checksums_file_matches_actual_file_contents(self):
        self._build()
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        zip_path = self.out_dir / f"industry-research-v{version}.zip"
        sums_path = self.out_dir / "SHA256SUMS.txt"

        recorded = {}
        for line in sums_path.read_text(encoding="utf-8").splitlines():
            digest, name = line.split("  ", 1)
            recorded[name] = digest

        self.assertIn(zip_path.name, recorded)
        self.assertEqual(hashlib.sha256(zip_path.read_bytes()).hexdigest(), recorded[zip_path.name])

        with zipfile.ZipFile(zip_path) as zf:
            for arcname in zf.namelist():
                if arcname not in recorded:
                    continue
                content = zf.read(arcname)
                self.assertEqual(hashlib.sha256(content).hexdigest(), recorded[arcname])

    def test_extracted_zip_relative_references_resolve(self):
        """SKILL.md's relative links (to references/, assets/) must still
        resolve once the zip is extracted standalone, not just inside the repo."""
        import re

        self._build()
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        zip_path = self.out_dir / f"industry-research-v{version}.zip"
        extract_dir = self.out_dir / "extracted"
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(extract_dir)

        skill_md = extract_dir / "industry-research" / "SKILL.md"
        text = skill_md.read_text(encoding="utf-8")
        links = re.findall(r"\]\(([^)]+)\)", text)
        for link in links:
            if link.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = (skill_md.parent / link).resolve()
            self.assertTrue(target.exists(), f"broken link after extraction: {link}")


if __name__ == "__main__":
    unittest.main()
