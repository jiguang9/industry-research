"""Tests for scripts/validate_evidence.py."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
FIXTURES = ROOT / "tests" / "fixtures"

import validate_evidence as ve  # noqa: E402


def load(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def error_messages(result: ve.Result) -> list[str]:
    return [e["message"] for e in result.errors]


class ValidEvidenceTests(unittest.TestCase):
    def test_valid_fixture_passes_with_no_errors(self):
        evidence = load("valid_evidence.json")
        result = ve.validate(evidence, None)
        self.assertEqual(result.errors, [])

    def test_valid_fixture_with_report_cross_reference(self):
        evidence = load("valid_evidence.json")
        result = ve.validate(evidence, FIXTURES / "valid_report.md")
        self.assertEqual(result.errors, [])

    def test_report_referencing_unknown_claim_id_fails(self):
        evidence = load("valid_evidence.json")
        result = ve.validate(evidence, FIXTURES / "report_with_unknown_claim.md")
        self.assertTrue(any("C999" in m for m in error_messages(result)))

    def test_report_may_reference_gap_ids_not_just_claim_ids(self):
        # valid_evidence.json's only gap is G001; a report citing it should be fine.
        import tempfile

        evidence = load("valid_evidence.json")
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "report.md"
            report.write_text("门店扩张计划仍不明确，见证据缺口 [G001]。", encoding="utf-8")
            result = ve.validate(evidence, report)
            self.assertEqual(result.errors, [])

    def test_cli_exit_codes(self):
        import subprocess

        valid = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "validate_evidence.py"), str(FIXTURES / "valid_evidence.json")],
            capture_output=True,
        )
        self.assertEqual(valid.returncode, 0)

        invalid = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "validate_evidence.py"), str(FIXTURES / "invalid_cycle.json")],
            capture_output=True,
        )
        self.assertEqual(invalid.returncode, 1)

        missing = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "validate_evidence.py"), str(FIXTURES / "does_not_exist.json")],
            capture_output=True,
        )
        self.assertEqual(missing.returncode, 2)

        bad_args = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "validate_evidence.py")],
            capture_output=True,
        )
        self.assertEqual(bad_args.returncode, 2)


class StructuralRuleTests(unittest.TestCase):
    def test_duplicate_source_id_fails(self):
        result = ve.validate(load("invalid_duplicate_ids.json"), None)
        self.assertTrue(any("duplicate source id" in m for m in error_messages(result)))

    def test_dangling_source_reference_fails(self):
        result = ve.validate(load("invalid_dangling_reference.json"), None)
        self.assertTrue(any("unknown source id" in m for m in error_messages(result)))

    def test_inference_cycle_detected(self):
        result = ve.validate(load("invalid_cycle.json"), None)
        self.assertTrue(any("circular basis_claim_ids" in m for m in error_messages(result)))

    def test_unknown_cannot_be_supported(self):
        result = ve.validate(load("invalid_unknown_supported.json"), None)
        self.assertTrue(any("cannot have evidence_status" in m for m in error_messages(result)))

    def test_fact_supported_needs_a_read_source(self):
        result = ve.validate(load("invalid_fact_snippet_only.json"), None)
        self.assertTrue(any("no referenced source has access_status" in m for m in error_messages(result)))

    def test_missing_dimension_must_be_declared(self):
        result = ve.validate(load("invalid_missing_dimension.json"), None)
        self.assertTrue(any("not declared in missing_dimensions" in m for m in error_messages(result)))

    def test_estimated_metric_requires_method(self):
        result = ve.validate(load("invalid_calculated_no_method.json"), None)
        self.assertTrue(any("required when value_type='estimated'" in m for m in error_messages(result)))

    def test_comparable_true_with_mismatched_dimensions_is_contradiction(self):
        result = ve.validate(load("invalid_comparison_contradiction.json"), None)
        self.assertTrue(any("contradiction" in m for m in error_messages(result)))


class LegitimateUnverifiedStateTests(unittest.TestCase):
    """Unknown claims and honest 'insufficient evidence' states must be allowed to
    save successfully -- the schema should not pressure the writer into fabricating
    support just to pass validation."""

    def test_unknown_claim_with_no_sources_is_valid(self):
        evidence = load("valid_evidence.json")
        # C003 in the fixture is already kind=unknown / evidence_status=unverified
        # with empty source_ids -- confirm it produces no error on its own.
        result = ve.validate(evidence, None)
        claim_paths = [e["path"] for e in result.errors if "claims[2]" in e["path"]]
        self.assertEqual(claim_paths, [])

    def test_research_status_insufficient_evidence_is_a_valid_enum_value(self):
        evidence = load("valid_evidence.json")
        evidence["research"]["status"] = "insufficient_evidence"
        result = ve.validate(evidence, None)
        self.assertEqual(
            [e for e in result.errors if "research.status" in e["path"]],
            [],
        )


class TimeSeriesVsCrossSectionComparisonTests(unittest.TestCase):
    """A time-series comparison may legitimately span different periods; a
    cross-sectional comparison claiming comparability must not silently paper
    over unit/currency/scope differences."""

    def test_time_series_with_different_periods_can_be_marked_comparable(self):
        evidence = load("valid_evidence.json")
        evidence["claims"][0]["metrics"][0] = {
            "name": "门店数", "value": 100, "unit": "家", "period": "2024",
            "region": "示例市", "scope": "该企业直营门店", "value_type": "reported",
            "source_ids": ["S001"], "missing_dimensions": [],
        }
        evidence["claims"].append({
            "id": "C010", "statement": "对比年份", "kind": "fact", "evidence_status": "supported",
            "source_ids": ["S001"], "counter_source_ids": [], "basis_claim_ids": [], "rationale": None,
            "confidence": "high", "limitations": [],
            "metrics": [{
                "name": "门店数", "value": 140, "unit": "家", "period": "2025",
                "region": "示例市", "scope": "该企业直营门店", "value_type": "reported",
                "source_ids": ["S001"], "missing_dimensions": [],
            }],
        })
        evidence["comparisons"] = [{
            "id": "CMP010", "metric_refs": ["C001.0", "C010.0"],
            "purpose": "同一企业跨年度门店数趋势对比",
            "comparable": True, "mismatched_dimensions": [], "adjustment_note": None,
        }]
        result = ve.validate(evidence, None)
        self.assertEqual(result.errors, [])

    def test_cross_sectional_currency_mismatch_cannot_claim_comparable(self):
        result = ve.validate(load("invalid_comparison_contradiction.json"), None)
        self.assertTrue(any("contradiction" in m for m in error_messages(result)))


class CurrencyAndScopeMergeTests(unittest.TestCase):
    """CNY/USD or GMV/revenue differences must not be silently merged."""

    def test_metric_with_declared_currency_and_no_conversion_is_fine(self):
        evidence = load("valid_evidence.json")
        evidence["claims"][0]["metrics"][0]["currency"] = "CNY"
        result = ve.validate(evidence, None)
        self.assertEqual(result.errors, [])

    def test_comparison_across_currencies_without_adjustment_note_is_flagged_by_mismatch(self):
        evidence = load("invalid_comparison_contradiction.json")
        # Fix the contradiction but keep the currency mismatch declared -- this
        # should now pass structurally (comparable=false, mismatch declared),
        # proving the validator doesn't require adjustment_note to silently
        # reconcile CNY vs USD.
        evidence["comparisons"][0]["comparable"] = False
        result = ve.validate(evidence, None)
        self.assertEqual(result.errors, [])


class SameOriginSourcesTests(unittest.TestCase):
    """Reprints of the same underlying report should be group-able via
    origin_id without the validator inferring or asserting independence."""

    def test_three_sources_sharing_origin_id_is_structurally_valid(self):
        evidence = load("valid_evidence.json")
        for i in range(3):
            evidence["sources"].append({
                "id": f"S10{i}", "title": f"转载 {i}", "publisher": None,
                "url": f"https://example.com/reprint-{i}", "file_ref": None,
                "source_type": "media", "access_status": "fetched", "published_at": None,
                "accessed_at": "2026-09-03", "data_period": None,
                "origin_id": "ORIGIN-REPORT-X", "location": None, "excerpt": None, "access_note": None,
            })
        result = ve.validate(evidence, None)
        self.assertEqual(result.errors, [])


class FixtureInventoryTests(unittest.TestCase):
    def test_fixtures_directory_has_expected_files(self):
        expected = {
            "valid_evidence.json", "valid_report.md", "report_with_unknown_claim.md",
            "invalid_duplicate_ids.json", "invalid_dangling_reference.json",
            "invalid_cycle.json", "invalid_unknown_supported.json",
            "invalid_fact_snippet_only.json", "invalid_missing_dimension.json",
            "invalid_calculated_no_method.json", "invalid_comparison_contradiction.json",
        }
        present = {p.name for p in FIXTURES.iterdir()}
        self.assertTrue(expected.issubset(present))


if __name__ == "__main__":
    unittest.main()
