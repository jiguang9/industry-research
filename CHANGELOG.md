# Changelog

All notable changes to this project are documented in this file.

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
