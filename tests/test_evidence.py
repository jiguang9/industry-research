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


class CrossMetricComparisonIntegrityTests(unittest.TestCase):
    """The validator must not just trust an author's self-declared
    comparable/mismatched_dimensions -- it must resolve the referenced
    metrics and check whether they actually agree."""

    def _two_claims_with_metrics(self, evidence, metric_a, metric_b):
        evidence["claims"] = []
        evidence["gaps"] = []
        evidence["claims"].append({
            "id": "C001", "statement": "A", "kind": "fact", "evidence_status": "supported",
            "source_ids": ["S001"], "counter_source_ids": [], "basis_claim_ids": [], "rationale": None,
            "confidence": "high", "limitations": [], "metrics": [metric_a],
        })
        evidence["claims"].append({
            "id": "C002", "statement": "B", "kind": "fact", "evidence_status": "supported",
            "source_ids": ["S001"], "counter_source_ids": [], "basis_claim_ids": [], "rationale": None,
            "confidence": "high", "limitations": [], "metrics": [metric_b],
        })
        return evidence

    def test_undeclared_currency_mismatch_with_comparable_true_is_rejected(self):
        """Exact adversarial case from review: CNY vs USD, same-ish period,
        declared comparable=true. The validator must catch this by actually
        comparing the metrics, not just by trusting mismatched_dimensions=[]."""
        evidence = load("valid_evidence.json")
        metric_a = {
            "name": "revenue", "value": 100, "unit": "亿元", "period": "2024", "region": "中国",
            "scope": "公司整体", "value_type": "reported", "source_ids": ["S001"],
            "missing_dimensions": [], "currency": "CNY",
        }
        metric_b = {
            "name": "revenue", "value": 14, "unit": "billion", "period": "2025", "region": "中国",
            "scope": "公司整体", "value_type": "reported", "source_ids": ["S001"],
            "missing_dimensions": [], "currency": "USD",
        }
        evidence = self._two_claims_with_metrics(evidence, metric_a, metric_b)
        evidence["comparisons"] = [{
            "id": "CMP999", "metric_refs": ["C001.0", "C002.0"],
            "purpose": "adversarial: undeclared CNY vs USD and unit mismatch, claimed comparable",
            "comparable": True, "mismatched_dimensions": [], "adjustment_note": None,
        }]
        result = ve.validate(evidence, None)
        messages = error_messages(result)
        self.assertTrue(any("currency" in m and "comparable=true" in m for m in messages), messages)
        self.assertTrue(any("unit" in m and "comparable=true" in m for m in messages), messages)

    def test_declaring_the_real_mismatch_in_mismatched_dimensions_is_accepted(self):
        """The same mismatch, but honestly declared with comparable=false,
        must not be rejected -- proving this isn't just a blanket ban on
        differing units."""
        evidence = load("valid_evidence.json")
        metric_a = {
            "name": "revenue", "value": 100, "unit": "亿元", "period": "2024", "region": "中国",
            "scope": "公司整体", "value_type": "reported", "source_ids": ["S001"],
            "missing_dimensions": [], "currency": "CNY",
        }
        metric_b = {
            "name": "revenue", "value": 14, "unit": "billion", "period": "2025", "region": "中国",
            "scope": "公司整体", "value_type": "reported", "source_ids": ["S001"],
            "missing_dimensions": [], "currency": "USD",
        }
        evidence = self._two_claims_with_metrics(evidence, metric_a, metric_b)
        evidence["comparisons"] = [{
            "id": "CMP999", "metric_refs": ["C001.0", "C002.0"],
            "purpose": "honestly declared currency/unit mismatch",
            "comparable": False, "mismatched_dimensions": ["currency", "unit"], "adjustment_note": None,
        }]
        result = ve.validate(evidence, None)
        self.assertEqual(result.errors, [])


class DuplicateComparisonAndGapIdTests(unittest.TestCase):
    def test_duplicate_comparison_id_is_rejected(self):
        evidence = load("valid_evidence.json")
        comp = {
            "id": "CMP001", "metric_refs": ["C001.0"], "purpose": "dup test A",
            "comparable": True, "mismatched_dimensions": [], "adjustment_note": None,
        }
        evidence["comparisons"] = [dict(comp), dict(comp, purpose="dup test B")]
        result = ve.validate(evidence, None)
        self.assertTrue(any("duplicate comparison id" in m for m in error_messages(result)))

    def test_duplicate_gap_id_is_rejected(self):
        evidence = load("valid_evidence.json")
        gap = {"id": "G001", "description": "dup", "affected_claim_ids": [], "next_step": "check X"}
        evidence["gaps"] = [dict(gap), dict(gap, description="dup again")]
        result = ve.validate(evidence, None)
        self.assertTrue(any("duplicate gap id" in m for m in error_messages(result)))

    def test_gap_missing_next_step_is_an_error_not_just_a_warning(self):
        evidence = load("valid_evidence.json")
        evidence["gaps"] = [{"id": "G001", "description": "no next step given", "affected_claim_ids": [], "next_step": ""}]
        result = ve.validate(evidence, None)
        self.assertTrue(any("next_step" in e["path"] for e in result.errors))


class MachineValidationConsistencyTests(unittest.TestCase):
    def test_performed_false_with_a_result_is_rejected(self):
        evidence = load("valid_evidence.json")
        evidence["checks"]["machine_validation"] = {
            "performed": False, "tool": "scripts/validate_evidence.py", "tool_version": None, "result": "passed",
        }
        result = ve.validate(evidence, None)
        self.assertTrue(any("performed=false but result=" in m for m in error_messages(result)))

    def test_performed_true_without_a_valid_result_is_rejected(self):
        evidence = load("valid_evidence.json")
        evidence["checks"]["machine_validation"] = {
            "performed": True, "tool": "scripts/validate_evidence.py", "tool_version": "0.1.0", "result": None,
        }
        result = ve.validate(evidence, None)
        self.assertTrue(any("performed=true requires result" in m for m in error_messages(result)))

    def test_performed_true_with_passed_result_is_accepted(self):
        evidence = load("valid_evidence.json")
        evidence["checks"]["machine_validation"] = {
            "performed": True, "tool": "scripts/validate_evidence.py", "tool_version": "0.1.0", "result": "passed",
        }
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
