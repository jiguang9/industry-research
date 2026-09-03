# industry-research

An Agent Skill that helps marketing, consulting, and business professionals quickly understand an unfamiliar industry, producing an evidence-backed industry map, business-model explanation, and next research steps. Default output language is Chinese; the skill follows the user's explicit language/region/purpose instead.

This README is a short pointer for English-speaking readers. **The full documentation lives in [README.md](README.md) (Chinese)** — install instructions, the Quick/Deep depth model, capability degradation table, output format, and the validator's actual limits are all there.

## Quick facts

- **Minimum input**: one identifiable industry or sub-segment. Everything else (materials, region, purpose, timeframe) is optional and defaults sensibly — see [SKILL.md](SKILL.md).
- **Not for**: head-to-head comparison of a few named companies (use `competitor-analysis` for that), securities valuation / buy-sell advice, or pure literature review.
- **Real example**: [examples/public-industry-case/](examples/public-industry-case/) — a Quick-depth study of China's collaborative-robot industry, with `report.md`, `evidence.json`, and an actual `validation.json` run.
- **Install** (four platforms share one payload):
  ```bash
  git clone https://github.com/jiguang9/industry-research.git
  cd industry-research
  python3 tools/install.py --platform claude   # or codex / openclaw / hermes
  ```
  Per-platform verification status (structural / discovery / behavioral / networked) is tracked honestly in [docs/platform-compatibility.md](docs/platform-compatibility.md) — installability is not the same claim as "verified working."
- **Evidence validator**: `python3 scripts/validate_evidence.py evidence.json --report report.md` checks structure and internal consistency only. It does not and cannot verify that a source is real, that a citation actually supports its claim, or that the industry conclusions are correct — see the disclaimer field it prints.

MIT License. See [LICENSE](LICENSE).
