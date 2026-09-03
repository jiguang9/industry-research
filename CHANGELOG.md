# Changelog

All notable changes to this project are documented in this file.

## 0.1.1 - 2026-09-03

Fixes from an external review of v0.1.0. See `docs/validation-report.md` for the full writeup; summary:

- `scripts/validate_evidence.py`: comparisons now cross-check the *actual* unit/currency/region/scope/value_type of the metrics a comparison references, instead of only trusting the author-declared `mismatched_dimensions` -- a `comparable=true` claim across CNY/USD or differing units is now rejected even if the author didn't flag it. Added duplicate-ID detection for `comparisons` and `gaps` (previously only `sources`/`claims` were checked). `gaps[].next_step` is now a required field (was a soft warning). `checks.machine_validation.performed`/`.result` are now checked for internal consistency (`performed=false` can no longer coexist with a `result`).
- `tools/install.py`: fixed an unsafe failure-recovery path in `--replace` -- if the copy-in step failed partway through, `shutil.move()` used to nest the restored backup one level too deep inside the partial directory instead of replacing it in place. Now clears the partial directory before restoring. Covered by a new fault-injection test.
- `tools/build_release.py`: `SHA256SUMS.txt` used to list both the zip itself and every file inside it, so running `shasum -a 256 -c SHA256SUMS.txt` immediately after download (before extracting) failed with "no such file" for the inner entries. It now lists only the zip; per-file hashes ship as `MANIFEST.sha256` inside the zip, meant to be checked after extraction.
- `examples/public-industry-case/`: reworded a key-takeaway line that generalized "the whole segment lacks a stable profit model" from a single company's data (Jaka only) -- now explicitly scoped as one company's data pending more samples. Added a properly independent, fetched source for Dobot's 2024-12-23 Hong Kong listing date (previously that fact was only loosely embedded in an inference's rationale, citing a source published before the listing happened).
- `docs/platform-compatibility.md`: corrected a factual error about Hermes' Direct URL install (it does fetch explicitly-linked `references/`/`assets/`/`scripts/` files, not just the bare `SKILL.md`); recorded the actual Claude Code version (2.1.201, from the installed VSCode extension's `package.json`) instead of an undated placeholder; relabeled the eval run that was mislabeled as "case 1" (it was actually case 4 -- the input wording triggered client-prep) and added a genuinely neutral-wording case 1 run.
- `SKILL.md`: the reference to `scripts/validate_evidence.py` is now a real Markdown link (was a bare code span), for consistency with how every other file reference works and to improve the odds of it being picked up by platforms that scan SKILL.md for linked resources.

## 0.1.0 - 2026-09-03

Initial release.

- Core `SKILL.md` covering research boundaries, Quick/Deep depth, overview/client-prep/opportunity purposes, and evidence rules.
- `references/` workflow, source-strategy, evidence-rules, evidence-schema, output-guidance, and three industry-category guides (industrial-b2b, software-services, consumer-business).
- `assets/` templates for `report.md`, `client-brief.md`, `competitor-brief.md`.
- `scripts/validate_evidence.py`: structural + cross-reference validator for `evidence.json`, with passing/failing fixtures under `tests/fixtures/`.
- `tools/install.py`, `tools/build_release.py`, `tools/check_skill.py` for local installation, release packaging, and repo structural checks.
- Installation and invocation documented for Claude Code, Codex, OpenClaw, and Hermes Agent (see `docs/platform-compatibility.md` for verification status per platform).
- One real public example research case under `examples/public-industry-case/`.
- Unit tests (`tests/`), behavioral eval cases (`evals/`), and CI (`.github/workflows/ci.yml`).
