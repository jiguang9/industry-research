# Changelog

All notable changes to this project are documented in this file.

## 0.1.6 - 2026-09-03

Sixth round of review, but a different class of finding this time: not a validator code bug (five straight rounds of those are now closed), but semantic evidence-discipline problems in `examples/public-industry-case/` that no structural validator can catch -- exactly the boundary `scripts/validate_evidence.py`'s own disclaimer names ("does not verify... that a citation genuinely supports the claim it is attached to"). Every finding was independently verified by reading the cited claim's actual `statement` field before fixing.

- `report.md` cited `[C006]` (China's 2025 sales volume/share/export numbers) to support a sentence about collaborative welding and heavy-load palletizing being current application highlights -- `C006`'s statement has nothing to do with application scenarios. Researched and added a properly sourced claim (`C011`, from a fetched GGII-sourced article on 2024 collaborative-welding shipment data) instead of just citing something adjacent.
- The core business-model sentence about direct customers being system integrators/technically-capable manufacturers, with procurement involving production and purchasing departments, had no citation at all. Added `C016` as an explicit inference (industrial-B2B-analogy reasoning, not industry-specific research), with a new gap (`G004`) documenting that no protocol-robot-specific procurement research was found.
- Three sentences characterized as "已发生事件" (confirmed events) were actually interpretive inferences: the IPO-termination "impact" speculation (was miscited to `C001`, which is unrelated; the real supporting fact -- the 2022 Pre-IPO financing and investor names -- sat in `S001`'s excerpt but had never been promoted to its own claim), "反映国产替代和出海同步推进", and "反映行业整体仍处扩张期". Split into new claims `C012`/`C013`/`C014` with proper `basis_claim_ids` and rationale, moved out of the "已发生事件" section into "推测", and added `C015` for the previously-unclaimed financing/investor fact.
- `examples/public-industry-case/README.md` still said `schema_version 1.0` (stale since the 1.1 bump in v0.1.3) and an outdated source/search count.

No changes to `scripts/validate_evidence.py` in this release -- `structural_ok: true` before and after, because none of the above are structural violations. That's the point: they required reading the actual claim text and checking it supports what it's cited for, which the tool has never claimed to do.

## 0.1.5 - 2026-09-03

Fifth round of fixes from continued external review of v0.1.4. Every finding was independently reproduced before fixing.

- `comparisons[].metric_refs` accepted an empty array, a single ref, or the same ref repeated twice -- none of which actually compare anything -- because the real-metric cross-check only ran when `len(resolved_metrics) >= 2`, so these degenerate cases silently skipped it entirely. Now rejected explicitly: a comparison must reference at least two distinct metrics, or the research should use an empty top-level `comparisons: []` instead.
- `metrics[].currency`, `.price_basis`, `.method`, `.inputs`, `.assumptions` were only type-checked inside the `value_type in (calculated, estimated)` branch, so a `reported` metric with `currency: 123` or `inputs: 123` passed untouched. These are optional fields for any `value_type`, but now their type is checked whenever they're present, regardless of `value_type`.
- `tests/fixtures/valid_evidence.json`'s comparison referenced a single metric ("仅作格式示范") -- fixed by adding a second same-metric-different-period entry and turning it into a genuine time-series comparison.
- 14 new tests target each of the above directly (80 total, up from 73 in v0.1.4).

## 0.1.4 - 2026-09-03

Fourth round of fixes from continued external review of v0.1.3. Every finding was independently reproduced (mutating the valid fixture and confirming the validator wrongly accepted it) before fixing.

- `metrics[].period`/`region`/`scope` could be deleted outright as long as the same field name was added to `missing_dimensions` -- the key-presence check only ran when the key happened to exist. Now enforced as required keys (nullable value) via `_require`, matching the pattern used everywhere else.
- `checks.semantic_review` and `checks.machine_validation` were only checked for being present and being objects; their internal fields were never validated. A `machine_validation` of `{"performed": "yes", "tool": 123, "tool_version": null, "result": "nonsense"}` passed structural validation. Now `semantic_review.performed`/`.notes` and `machine_validation.performed`/`.tool`/`.tool_version`/`.result` are all individually required and type/enum-checked.
- Several "array of string" fields only checked list-ness, not element types: `claims[].limitations`, `metrics[].inputs`/`.assumptions` (when `value_type` is calculated/estimated), and `comparisons[].mismatched_dimensions` all accepted non-string elements (e.g. `[123]`). All now check every element is a string.
- `schema_version` mismatch (including a fabricated/unknown version like `"999.0"`) was only a warning, so `structural_ok` could still read `true` for a file the validator has no actual multi-version support for. Now a hard error -- this validator only knows how to check `SCHEMA_VERSION`'s rules, so it can't vouch for a file declaring anything else.
- `references/evidence-schema.md`: the top-of-file JSON skeleton still showed `"schema_version": "1.0"` after the header was updated to say 1.1; and the version-history note attributed both the `comparison_type` field and the version bump to v0.1.2, when the bump itself only happened in v0.1.3. Both corrected.
- 10 new tests target each of the above directly (73 total, up from 65 in v0.1.3).

## 0.1.3 - 2026-09-03

Third round of fixes from continued external review of v0.1.2. Every finding was independently reproduced (by deleting each field from the valid fixture and confirming the validator wrongly accepted it) before fixing. See `docs/validation-report.md` (section 0) for the full writeup.

- `scripts/validate_evidence.py` required-field enforcement was still incomplete: `research.data_cutoff`, `claims[].rationale`, `metrics[].missing_dimensions`, and the top-level `comparisons`/`gaps`/`checks` (plus its two sub-objects `semantic_review`/`machine_validation`) could all be deleted outright with no error -- several fell back to silent empty-list/None defaults via `.get(key, default)`, one (`checks` absent) only produced a warning. All now enforced as required via `_require`.
- `comparisons[].comparison_type` became required in v0.1.2 without a schema version bump, so a file still declaring `schema_version: "1.0"` had no way to signal it predates the new field, and the validator gave no indication the rules it was applying didn't match the file's own claimed version. Bumped `SCHEMA_VERSION` to `1.1` (documented as a deliberately breaking change in `references/evidence-schema.md`) and updated every schema_version-declaring file in this repo. A file honestly declaring `1.0` now gets both a version-mismatch warning and the real missing-field error, instead of an ambiguous silent pass.
- `docs/validation-report.md` recorded local absolute filesystem paths (`/Users/<name>/...`) for two eval-run output directories -- replaced with paths relative to the repo root, and added a note that those two runs predate the schema 1.1 bump and would need `comparison_type` added to re-validate under the current validator (the schema evolved; the recorded results were accurate for the validator version in effect at the time).
- v0.1.2's GitHub release notes said "61 total" new tests; the actual number was 56 (arithmetic error, not a code issue). Corrected via `gh release edit` on the existing v0.1.2 release (text only, no tag/artifact change).
- 9 new tests target each of the required-field cases directly, plus 1 test for the schema-version-mismatch-plus-real-failure behavior (65 total, up from 56 in v0.1.2).

## 0.1.2 - 2026-09-03

Second round of fixes from continued external review of v0.1.1. Again, every finding was independently reproduced before fixing. See `docs/validation-report.md` (section 0) for the full writeup.

- `scripts/validate_evidence.py` comparisons: the real-metric cross-check added in v0.1.1 compared `unit`/`currency`/`region`/`scope`/`value_type` but missed `name` (so a GMV-vs-revenue comparison declared `comparable=true` slipped through) and `price_basis` (nominal-vs-real). Both are now checked. Also added a required `comparison_type` field (`time_series` | `cross_sectional`): previously `period` was unconditionally exempted from the comparison, which correctly allows a trend comparison to span years but also let a genuinely invalid cross-sectional comparison (e.g. two different companies' 2024 vs 2025 figures) through undetected. `cross_sectional` comparisons now also check `period`; `time_series` comparisons keep the original exemption.
- `scripts/validate_evidence.py` required-field enforcement: several fields documented as required in `references/evidence-schema.md` (`schema_version`, `sources[].publisher`/`published_at`/`data_period`/`origin_id`/`location`/`excerpt`/`access_note`, `claims[].counter_source_ids`/`basis_claim_ids`/`limitations`/`metrics`) were only type-checked when present, so deleting the key entirely produced no error (schema_version fell back to a soft warning; the rest passed silently). All are now enforced as required keys (most remain nullable-valued, matching the schema doc) via the existing `_require` helper.
- `examples/public-industry-case/report.md`: the "三、交易、交付与商业模式" section still stated "这个细分行业目前仍处于……尚未普遍形成稳定盈利模式的阶段" as a direct conclusion, with the single-company caveat appended afterward as an aside. Reworded so the single-company scope is stated up front rather than walked back after the fact.
- 11 new tests target the exact new adversarial cases (GMV/revenue name mismatch, nominal/real price_basis mismatch, cross-sectional period mismatch, and each of the 7 field-deletion cases above).

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
