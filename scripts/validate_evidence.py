#!/usr/bin/env python3
"""Validate an industry-research evidence.json file.

Checks structure, enum values, cross-references, and a set of internal
consistency rules described in references/evidence-schema.md and
references/evidence-rules.md. This script does NOT and CANNOT verify that:

  - a source's content is real or was actually read as described,
  - a citation genuinely supports the claim it is attached to,
  - every number appearing in report.md has a matching claim,
  - the underlying industry conclusions are correct.

A "passed" result means the evidence file is internally well-formed and
does not contain the specific contradictions this script checks for. It is
not proof that the research itself is accurate.

Usage:
    python3 scripts/validate_evidence.py path/to/evidence.json \
        [--report path/to/report.md] [--output path/to/validation.json]

Exit codes:
    0 - structural validation passed (warnings are allowed)
    1 - structural or contract errors found
    2 - could not read input / bad arguments
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

# 1.1: comparisons[].comparison_type became required (v0.1.2) -- a
# backward-incompatible addition, hence the version bump rather than keeping
# this at 1.0. Any file whose declared schema_version doesn't match this
# constant fails validation (see validate()) instead of silently passing
# under rules it was never written against.
SCHEMA_VERSION = "1.1"

SOURCE_TYPES = {
    "official", "company", "association", "research",
    "media", "public_feedback", "user_supplied", "other",
}
ACCESS_STATUSES = {"fetched", "supplied", "snippet_only", "failed"}
READ_ACCESS_STATUSES = {"fetched", "supplied"}
CLAIM_KINDS = {"fact", "inference", "unknown"}
EVIDENCE_STATUSES = {"supported", "partial", "conflicted", "unverified"}
CONFIDENCE_LEVELS = {"high", "medium", "low"}
VALUE_TYPES = {"reported", "calculated", "estimated"}
PURPOSES = {"overview", "client-prep", "opportunity"}
DEPTHS = {"quick", "deep"}
RESEARCH_STATUSES = {"complete", "partial", "insufficient_evidence"}
DIMENSION_FIELDS = ("period", "region", "scope")

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
CLAIM_ID_IN_TEXT_RE = re.compile(r"\[([A-Za-z]+\d+)\]")
METRIC_REF_RE = re.compile(r"^(?P<claim_id>[A-Za-z0-9_]+)\.(?P<index>\d+)$")


class Result:
    def __init__(self) -> None:
        self.errors: list[dict[str, str]] = []
        self.warnings: list[dict[str, str]] = []
        self.manual_review_required: list[dict[str, str]] = []

    def error(self, path: str, message: str) -> None:
        self.errors.append({"path": path, "message": message})

    def warning(self, path: str, message: str) -> None:
        self.warnings.append({"path": path, "message": message})

    def review(self, path: str, message: str) -> None:
        self.manual_review_required.append({"path": path, "message": message})

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version_checked": SCHEMA_VERSION,
            "structural_ok": len(self.errors) == 0,
            "errors": self.errors,
            "warnings": self.warnings,
            "manual_review_required": self.manual_review_required,
            "disclaimer": (
                "This report only confirms internal structure and declared "
                "consistency. It does not verify source authenticity, citation "
                "accuracy, or the correctness of any industry conclusion."
            ),
        }


def _is_str(v: Any) -> bool:
    return isinstance(v, str)


def _is_nullable_str(v: Any) -> bool:
    return v is None or isinstance(v, str)


def _require(obj: dict, field: str, path: str, result: Result, checker, required=True) -> Any:
    if field not in obj:
        if required:
            result.error(path, f"missing required field '{field}'")
        return None
    val = obj[field]
    if not checker(val):
        result.error(f"{path}.{field}", f"field '{field}' has an invalid type or value: {val!r}")
    return val


def validate_research(research: Any, result: Result) -> None:
    path = "research"
    if not isinstance(research, dict):
        result.error(path, "'research' must be an object")
        return

    _require(research, "industry", path, result, _is_str)
    _require(research, "region", path, result, _is_str)
    _require(research, "scope", path, result, _is_str)
    _require(research, "exclusions", path, result, _is_str)

    purpose = _require(research, "purpose", path, result, _is_str)
    if purpose is not None and purpose not in PURPOSES:
        result.error(f"{path}.purpose", f"must be one of {sorted(PURPOSES)}, got {purpose!r}")

    depth = _require(research, "depth", path, result, _is_str)
    if depth is not None and depth not in DEPTHS:
        result.error(f"{path}.depth", f"must be one of {sorted(DEPTHS)}, got {depth!r}")

    research_date = _require(research, "research_date", path, result, _is_str)
    if research_date is not None and not DATE_RE.match(research_date):
        result.error(f"{path}.research_date", "must match YYYY-MM-DD")

    _require(research, "data_cutoff", path, result, _is_nullable_str)

    assumptions = _require(research, "assumptions", path, result, lambda v: isinstance(v, list))
    if isinstance(assumptions, list) and not all(_is_str(a) for a in assumptions):
        result.error(f"{path}.assumptions", "all entries must be strings")

    status = _require(research, "status", path, result, _is_str)
    if status is not None and status not in RESEARCH_STATUSES:
        result.error(f"{path}.status", f"must be one of {sorted(RESEARCH_STATUSES)}, got {status!r}")

    caps = _require(research, "capabilities", path, result, lambda v: isinstance(v, dict))
    if isinstance(caps, dict):
        for cap_field in ("web_search", "file_read", "file_write", "code_execution"):
            if cap_field not in caps:
                result.error(f"{path}.capabilities", f"missing required field '{cap_field}'")
            elif not isinstance(caps[cap_field], bool):
                result.error(f"{path}.capabilities.{cap_field}", "must be a boolean")


def validate_sources(sources: Any, result: Result) -> dict[str, dict]:
    by_id: dict[str, dict] = {}
    if not isinstance(sources, list):
        result.error("sources", "'sources' must be an array")
        return by_id

    for i, src in enumerate(sources):
        path = f"sources[{i}]"
        if not isinstance(src, dict):
            result.error(path, "each source must be an object")
            continue

        sid = _require(src, "id", path, result, _is_str)
        if sid is not None:
            if sid in by_id:
                result.error(path, f"duplicate source id '{sid}'")
            else:
                by_id[sid] = src

        _require(src, "title", path, result, _is_str)
        _require(src, "publisher", path, result, _is_nullable_str)

        url = _require(src, "url", path, result, _is_nullable_str)
        file_ref = _require(src, "file_ref", path, result, _is_nullable_str)
        if not url and not file_ref:
            result.error(path, "at least one of 'url' or 'file_ref' must be set")

        source_type = _require(src, "source_type", path, result, _is_str)
        if source_type is not None and source_type not in SOURCE_TYPES:
            result.error(f"{path}.source_type", f"must be one of {sorted(SOURCE_TYPES)}, got {source_type!r}")

        access_status = _require(src, "access_status", path, result, _is_str)
        if access_status is not None and access_status not in ACCESS_STATUSES:
            result.error(f"{path}.access_status", f"must be one of {sorted(ACCESS_STATUSES)}, got {access_status!r}")

        for nullable_field in ("published_at", "data_period", "origin_id", "location", "excerpt", "access_note"):
            _require(src, nullable_field, path, result, _is_nullable_str)

        accessed_at = _require(src, "accessed_at", path, result, _is_str)
        if accessed_at is not None and not DATE_RE.match(accessed_at):
            result.error(f"{path}.accessed_at", "must match YYYY-MM-DD")

    return by_id


def validate_metric(metric: Any, path: str, result: Result, source_ids: set[str]) -> None:
    if not isinstance(metric, dict):
        result.error(path, "each metric must be an object")
        return

    _require(metric, "name", path, result, _is_str)

    if "value" in metric:
        value = metric["value"]
        ok = value is None or isinstance(value, (int, float)) and not isinstance(value, bool)
        if isinstance(value, dict):
            ok = "min" in value and "max" in value and all(
                isinstance(value[k], (int, float)) and not isinstance(value[k], bool) for k in ("min", "max")
            )
            if ok and value["min"] > value["max"]:
                result.error(f"{path}.value", "'min' must not be greater than 'max'")
        if not ok:
            result.error(f"{path}.value", "must be a number, {min,max} object, or null")
    else:
        result.error(path, "missing required field 'value'")

    unit = _require(metric, "unit", path, result, _is_str)

    for dim_field in DIMENSION_FIELDS:
        _require(metric, dim_field, path, result, _is_nullable_str)

    value_type = _require(metric, "value_type", path, result, _is_str)
    if value_type is not None and value_type not in VALUE_TYPES:
        result.error(f"{path}.value_type", f"must be one of {sorted(VALUE_TYPES)}, got {value_type!r}")

    m_source_ids = _require(metric, "source_ids", path, result, lambda v: isinstance(v, list))
    if isinstance(m_source_ids, list):
        for sid in m_source_ids:
            if sid not in source_ids:
                result.error(f"{path}.source_ids", f"references unknown source id '{sid}'")

    missing_dims = _require(metric, "missing_dimensions", path, result, lambda v: isinstance(v, list) and all(_is_str(d) for d in v))
    if not isinstance(missing_dims, list):
        missing_dims = []
    missing_set = set(missing_dims)

    for dim_field in DIMENSION_FIELDS:
        val = metric.get(dim_field)
        if val is None and dim_field not in missing_set:
            result.error(
                f"{path}.{dim_field}",
                f"'{dim_field}' is null but not declared in missing_dimensions",
            )
        if val is not None and dim_field in missing_set:
            result.warning(
                f"{path}.{dim_field}",
                f"'{dim_field}' has a value but is also listed in missing_dimensions",
            )

    if isinstance(unit, str) and unit.strip() == "" and "unit" not in missing_set:
        result.error(f"{path}.unit", "unit is empty but not declared in missing_dimensions")

    if value_type in ("calculated", "estimated"):
        method = metric.get("method")
        inputs = metric.get("inputs")
        if not method or not _is_str(method):
            result.error(f"{path}.method", f"required when value_type='{value_type}'")
        if not isinstance(inputs, list) or len(inputs) == 0 or not all(_is_str(x) for x in inputs):
            result.error(f"{path}.inputs", f"must be a non-empty array of strings when value_type='{value_type}'")
        assumptions = metric.get("assumptions")
        if not isinstance(assumptions, list) or not all(_is_str(x) for x in assumptions):
            result.error(f"{path}.assumptions", f"must be an array of strings when value_type='{value_type}'")


def validate_claims(claims: Any, result: Result, source_ids: set[str]) -> dict[str, dict]:
    by_id: dict[str, dict] = {}
    if not isinstance(claims, list):
        result.error("claims", "'claims' must be an array")
        return by_id

    for i, claim in enumerate(claims):
        path = f"claims[{i}]"
        if not isinstance(claim, dict):
            result.error(path, "each claim must be an object")
            continue
        cid = _require(claim, "id", path, result, _is_str)
        if cid is not None:
            if cid in by_id:
                result.error(path, f"duplicate claim id '{cid}'")
            else:
                by_id[cid] = claim

    for i, claim in enumerate(claims):
        path = f"claims[{i}]"
        if not isinstance(claim, dict):
            continue
        cid = claim.get("id", f"<index {i}>")

        _require(claim, "statement", path, result, _is_str)

        kind = _require(claim, "kind", path, result, _is_str)
        if kind is not None and kind not in CLAIM_KINDS:
            result.error(f"{path}.kind", f"must be one of {sorted(CLAIM_KINDS)}, got {kind!r}")

        evidence_status = _require(claim, "evidence_status", path, result, _is_str)
        if evidence_status is not None and evidence_status not in EVIDENCE_STATUSES:
            result.error(f"{path}.evidence_status", f"must be one of {sorted(EVIDENCE_STATUSES)}, got {evidence_status!r}")

        if kind == "unknown" and evidence_status == "supported":
            result.error(path, f"claim '{cid}': kind='unknown' cannot have evidence_status='supported'")

        rationale = _require(claim, "rationale", path, result, _is_nullable_str)
        if kind == "inference" and not rationale:
            result.error(f"{path}.rationale", f"claim '{cid}': rationale must be non-empty when kind='inference'")

        c_source_ids = _require(claim, "source_ids", path, result, lambda v: isinstance(v, list))
        resolved_source_ids: list[str] = []
        if isinstance(c_source_ids, list):
            for sid in c_source_ids:
                if sid not in source_ids:
                    result.error(f"{path}.source_ids", f"claim '{cid}' references unknown source id '{sid}'")
                else:
                    resolved_source_ids.append(sid)
        if kind != "unknown" and isinstance(c_source_ids, list) and len(c_source_ids) == 0 and evidence_status != "unverified":
            result.warning(path, f"claim '{cid}': no source_ids but evidence_status='{evidence_status}'")

        counter_ids = _require(claim, "counter_source_ids", path, result, lambda v: isinstance(v, list))
        if isinstance(counter_ids, list):
            for sid in counter_ids:
                if sid not in source_ids:
                    result.error(f"{path}.counter_source_ids", f"claim '{cid}' references unknown source id '{sid}'")

        basis_ids = _require(claim, "basis_claim_ids", path, result, lambda v: isinstance(v, list))
        if isinstance(basis_ids, list):
            for bid in basis_ids:
                if bid not in by_id:
                    result.error(f"{path}.basis_claim_ids", f"claim '{cid}' references unknown claim id '{bid}'")

        confidence = _require(claim, "confidence", path, result, _is_str)
        if confidence is not None and confidence not in CONFIDENCE_LEVELS:
            result.error(f"{path}.confidence", f"must be one of {sorted(CONFIDENCE_LEVELS)}, got {confidence!r}")

        _require(claim, "limitations", path, result, lambda v: isinstance(v, list) and all(_is_str(x) for x in v))

        if evidence_status == "supported":
            has_read_source = any(
                by_id_src.get("access_status") in READ_ACCESS_STATUSES
                for sid, by_id_src in ((s, _SOURCE_LOOKUP.get(s)) for s in resolved_source_ids)
                if by_id_src is not None
            )
            if resolved_source_ids and not has_read_source:
                result.error(
                    path,
                    f"claim '{cid}': evidence_status='supported' but no referenced source has "
                    f"access_status in {sorted(READ_ACCESS_STATUSES)} (only failed/snippet_only sources)",
                )
            if kind == "fact" and not resolved_source_ids:
                result.error(path, f"claim '{cid}': kind='fact' and evidence_status='supported' requires source_ids")

        if evidence_status == "conflicted":
            result.review(path, f"claim '{cid}' is marked conflicted; verify the report presents both sides")
        if confidence == "low" and evidence_status == "supported":
            result.review(path, f"claim '{cid}' has confidence='low' but evidence_status='supported'; verify wording matches")

        metrics = _require(claim, "metrics", path, result, lambda v: isinstance(v, list))
        if isinstance(metrics, list):
            for j, metric in enumerate(metrics):
                validate_metric(metric, f"{path}.metrics[{j}]", result, source_ids)

    return by_id


def detect_cycles(claims_by_id: dict[str, dict], result: Result) -> None:
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {cid: WHITE for cid in claims_by_id}

    def visit(cid: str, stack: list[str]) -> None:
        color[cid] = GRAY
        stack.append(cid)
        for bid in claims_by_id[cid].get("basis_claim_ids", []) or []:
            if bid not in claims_by_id:
                continue
            if color.get(bid) == GRAY:
                cycle = stack[stack.index(bid):] + [bid]
                result.error("claims", f"circular basis_claim_ids reference: {' -> '.join(cycle)}")
            elif color.get(bid) == WHITE:
                visit(bid, stack)
        stack.pop()
        color[cid] = BLACK

    for cid in list(claims_by_id.keys()):
        if color[cid] == WHITE:
            visit(cid, [])


# Dimensions compared directly between the metrics a comparison references.
# 'period' is checked unless comparison_type='time_series' -- a time-series
# trend comparison is the one legitimate case where comparable=true across
# different periods is correct (the whole point is showing change over time).
# A cross-sectional comparison declaring comparable=true must match on period
# too, or the "same point in time" premise of comparing two things side by
# side doesn't hold. 'name' and 'price_basis' catch GMV-vs-revenue and
# nominal-vs-real mismatches respectively. Everything here is cross-checked
# against the actual referenced metrics, not just the author's self-report.
COMPARISON_TYPES = {"time_series", "cross_sectional"}
ALWAYS_COMPARED_FIELDS = ("name", "unit", "currency", "region", "scope", "value_type", "price_basis")


def validate_comparisons(comparisons: Any, result: Result, claims_by_id: dict[str, dict]) -> None:
    seen_ids: set[str] = set()
    if not isinstance(comparisons, list):
        result.error("comparisons", "'comparisons' must be an array (use [] if empty)")
        return

    for i, comp in enumerate(comparisons):
        path = f"comparisons[{i}]"
        if not isinstance(comp, dict):
            result.error(path, "each comparison must be an object")
            continue

        cid = _require(comp, "id", path, result, _is_str)
        if cid is not None:
            if cid in seen_ids:
                result.error(path, f"duplicate comparison id '{cid}'")
            else:
                seen_ids.add(cid)

        _require(comp, "purpose", path, result, _is_str)

        comparison_type = _require(comp, "comparison_type", path, result, _is_str)
        if comparison_type is not None and comparison_type not in COMPARISON_TYPES:
            result.error(f"{path}.comparison_type", f"must be one of {sorted(COMPARISON_TYPES)}, got {comparison_type!r}")

        metric_refs = _require(comp, "metric_refs", path, result, lambda v: isinstance(v, list))
        resolved_metrics: list[dict] = []
        if isinstance(metric_refs, list):
            for ref in metric_refs:
                if not _is_str(ref):
                    result.error(f"{path}.metric_refs", f"ref must be a string, got {ref!r}")
                    continue
                m = METRIC_REF_RE.match(ref)
                if not m:
                    result.error(f"{path}.metric_refs", f"ref '{ref}' must look like '<claim_id>.<index>'")
                    continue
                claim = claims_by_id.get(m.group("claim_id"))
                if claim is None:
                    result.error(f"{path}.metric_refs", f"ref '{ref}' points to unknown claim id")
                    continue
                idx = int(m.group("index"))
                metrics = claim.get("metrics", [])
                if idx >= len(metrics) or not isinstance(metrics[idx], dict):
                    result.error(f"{path}.metric_refs", f"ref '{ref}' index out of range")
                    continue
                resolved_metrics.append(metrics[idx])

        comparable = _require(comp, "comparable", path, result, lambda v: isinstance(v, bool))
        mismatched = _require(comp, "mismatched_dimensions", path, result, lambda v: isinstance(v, list) and all(_is_str(x) for x in v))
        if not isinstance(mismatched, list):
            mismatched = []
        elif comparable is True and len(mismatched) > 0:
            result.error(path, "comparable=true but mismatched_dimensions is non-empty (contradiction)")
        elif comparable is False and len(mismatched) == 0:
            result.warning(path, "comparable=false but mismatched_dimensions is empty; consider explaining why")

        # Cross-check the actual referenced metrics against the declared
        # comparable/mismatched_dimensions instead of trusting the author's
        # self-report: if the underlying metrics genuinely differ, comparable=true
        # is wrong regardless of what mismatched_dimensions claims. A
        # cross_sectional comparison also requires period to match; a
        # time_series comparison is specifically allowed to span periods.
        fields_to_check = ALWAYS_COMPARED_FIELDS
        if comparison_type == "cross_sectional":
            fields_to_check = ALWAYS_COMPARED_FIELDS + ("period",)

        if len(resolved_metrics) >= 2 and comparable is True:
            baseline = resolved_metrics[0]
            for field in fields_to_check:
                baseline_val = baseline.get(field)
                for other in resolved_metrics[1:]:
                    other_val = other.get(field)
                    if baseline_val != other_val and field not in mismatched:
                        result.error(
                            path,
                            f"comparable=true but referenced metrics actually differ in '{field}' "
                            f"({baseline_val!r} vs {other_val!r}); this was not declared in mismatched_dimensions",
                        )

        _require(comp, "adjustment_note", path, result, _is_nullable_str)


def validate_gaps(gaps: Any, result: Result, claims_by_id: dict[str, dict]) -> set[str]:
    gap_ids: set[str] = set()
    if not isinstance(gaps, list):
        result.error("gaps", "'gaps' must be an array (use [] if empty)")
        return gap_ids
    for i, gap in enumerate(gaps):
        path = f"gaps[{i}]"
        if not isinstance(gap, dict):
            result.error(path, "each gap must be an object")
            continue
        gid = _require(gap, "id", path, result, _is_str)
        if gid is not None:
            if gid in gap_ids:
                result.error(path, f"duplicate gap id '{gid}'")
            else:
                gap_ids.add(gid)
        _require(gap, "description", path, result, _is_str)
        next_step = gap.get("next_step")
        if not next_step or not _is_str(next_step):
            result.error(f"{path}.next_step", "must be a non-empty string describing a concrete next verification step")
        affected = _require(gap, "affected_claim_ids", path, result, lambda v: isinstance(v, list))
        if isinstance(affected, list):
            for cid in affected:
                if cid not in claims_by_id:
                    result.error(f"{path}.affected_claim_ids", f"references unknown claim id '{cid}'")
    return gap_ids


def validate_checks(checks: Any, result: Result) -> None:
    if checks is None:
        result.error("checks", "missing required top-level field 'checks'")
        return
    if not isinstance(checks, dict):
        result.error("checks", "'checks' must be an object")
        return

    sem = _require(checks, "semantic_review", "checks", result, lambda v: isinstance(v, dict))
    if isinstance(sem, dict):
        _require(sem, "performed", "checks.semantic_review", result, lambda v: isinstance(v, bool))
        _require(sem, "notes", "checks.semantic_review", result, _is_str)

    mach = _require(checks, "machine_validation", "checks", result, lambda v: isinstance(v, dict))
    if isinstance(mach, dict):
        performed = _require(mach, "performed", "checks.machine_validation", result, lambda v: isinstance(v, bool))
        _require(mach, "tool", "checks.machine_validation", result, _is_str)
        _require(mach, "tool_version", "checks.machine_validation", result, _is_nullable_str)
        mach_result = _require(
            mach, "result", "checks.machine_validation",
            result, lambda v: v is None or v in ("passed", "passed_with_warnings", "failed"),
        )
        if performed is False and mach_result is not None:
            result.error(
                "checks.machine_validation",
                f"performed=false but result={mach_result!r}; a validator that was not run cannot have a result "
                "(if you are about to run it, set performed=true and result after the run, not before)",
            )
        if performed is True and mach_result not in ("passed", "passed_with_warnings", "failed"):
            result.error(
                "checks.machine_validation",
                f"performed=true requires result to be one of passed/passed_with_warnings/failed, got {mach_result!r}",
            )


def validate_report_references(report_path: Path, known_ids: set[str], result: Result) -> None:
    if not report_path.exists():
        result.error("report", f"report file not found: {report_path}")
        return
    text = report_path.read_text(encoding="utf-8")
    ids_in_text = set(CLAIM_ID_IN_TEXT_RE.findall(text))
    for ref_id in sorted(ids_in_text):
        if ref_id not in known_ids:
            result.error("report", f"report.md references id '{ref_id}' which does not exist in evidence.json (claims/gaps)")
    if not ids_in_text:
        result.warning("report", "no [C###]-style id references found in report.md")


_SOURCE_LOOKUP: dict[str, dict] = {}


def validate(evidence: Any, report_path: Path | None) -> Result:
    global _SOURCE_LOOKUP
    result = Result()

    if not isinstance(evidence, dict):
        result.error("$", "top-level evidence.json must be an object")
        return result

    if "schema_version" not in evidence:
        result.error("schema_version", "missing required field 'schema_version'")
    elif evidence["schema_version"] != SCHEMA_VERSION:
        # This validator has no multi-version rule branching -- it always
        # applies SCHEMA_VERSION's rules. A file declaring any other version
        # (old, newer, or garbage) can't be vouched for as compliant with
        # the rules actually being run, so this is an error, not a warning.
        result.error("schema_version", f"expected '{SCHEMA_VERSION}', got {evidence['schema_version']!r}")

    validate_research(evidence.get("research"), result)

    sources_by_id = validate_sources(evidence.get("sources"), result)
    _SOURCE_LOOKUP = sources_by_id
    source_ids = set(sources_by_id.keys())

    claims_by_id = validate_claims(evidence.get("claims"), result, source_ids)
    detect_cycles(claims_by_id, result)

    validate_comparisons(evidence.get("comparisons"), result, claims_by_id)
    gap_ids = validate_gaps(evidence.get("gaps"), result, claims_by_id)
    validate_checks(evidence.get("checks"), result)

    if report_path is not None:
        known_ids = set(claims_by_id.keys()) | gap_ids
        validate_report_references(report_path, known_ids, result)

    if not result.errors:
        result.review("$", "structural validation passed; source authenticity and citation accuracy still require human review")

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("evidence_path", type=Path, help="path to evidence.json")
    parser.add_argument("--report", type=Path, default=None, help="path to report.md, for claim-id cross-referencing")
    parser.add_argument("--output", type=Path, default=None, help="write validation.json here instead of stdout")
    args = parser.parse_args()

    try:
        raw = args.evidence_path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"error: could not read {args.evidence_path}: {exc}", file=sys.stderr)
        return 2

    try:
        evidence = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"error: {args.evidence_path} is not valid JSON: {exc}", file=sys.stderr)
        return 2

    result = validate(evidence, args.report)
    output = json.dumps(result.to_dict(), ensure_ascii=False, indent=2)

    if args.output is not None:
        args.output.write_text(output + "\n", encoding="utf-8")
    else:
        print(output)

    return 1 if result.errors else 0


if __name__ == "__main__":
    sys.exit(main())
