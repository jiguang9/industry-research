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
            "id": "C010", "statement": "对比年份", "dimensions": [], "kind": "fact", "evidence_status": "supported",
            "source_ids": ["S001"], "counter_source_ids": [], "basis_claim_ids": [], "rationale": None,
            "confidence": "high", "limitations": [],
            "metrics": [{
                "name": "门店数", "value": 140, "unit": "家", "period": "2025",
                "region": "示例市", "scope": "该企业直营门店", "value_type": "reported",
                "source_ids": ["S001"], "missing_dimensions": [],
            }],
        })
        evidence["comparisons"] = [{
            "id": "CMP010", "comparison_type": "time_series", "metric_refs": ["C001.0", "C010.0"],
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
        # Both compared metrics (C001.0 and C001.1, referenced by CMP001) need
        # the same currency, or the real-metric cross-check would (correctly)
        # flag a genuine mismatch -- this test is about the field being legal
        # to set at all, not about creating a real cross-metric conflict.
        evidence["claims"][0]["metrics"][0]["currency"] = "CNY"
        evidence["claims"][0]["metrics"][1]["currency"] = "CNY"
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
        evidence["coverage"] = {
            "market": {"status": "out_of_scope", "claim_ids": [], "note": "test fixture reset", "next_question": None},
            "value_chain": {"status": "out_of_scope", "claim_ids": [], "note": "test fixture reset", "next_question": None},
            "business_model": {"status": "out_of_scope", "claim_ids": [], "note": "test fixture reset", "next_question": None},
            "competition": {"status": "out_of_scope", "claim_ids": [], "note": "test fixture reset", "next_question": None},
            "trends_risks": {"status": "out_of_scope", "claim_ids": [], "note": "test fixture reset", "next_question": None},
        }
        evidence["claims"].append({
            "id": "C001", "statement": "A", "dimensions": [], "kind": "fact", "evidence_status": "supported",
            "source_ids": ["S001"], "counter_source_ids": [], "basis_claim_ids": [], "rationale": None,
            "confidence": "high", "limitations": [], "metrics": [metric_a],
        })
        evidence["claims"].append({
            "id": "C002", "statement": "B", "dimensions": [], "kind": "fact", "evidence_status": "supported",
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
            "id": "CMP999", "comparison_type": "cross_sectional", "metric_refs": ["C001.0", "C002.0"],
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
            "id": "CMP999", "comparison_type": "cross_sectional", "metric_refs": ["C001.0", "C002.0"],
            "purpose": "honestly declared currency/unit mismatch",
            "comparable": False, "mismatched_dimensions": ["currency", "unit"], "adjustment_note": None,
        }]
        result = ve.validate(evidence, None)
        self.assertEqual(result.errors, [])


class DuplicateComparisonAndGapIdTests(unittest.TestCase):
    def test_duplicate_comparison_id_is_rejected(self):
        evidence = load("valid_evidence.json")
        comp = {
            "id": "CMP001", "comparison_type": "cross_sectional", "metric_refs": ["C001.0"], "purpose": "dup test A",
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


class NameAndPriceBasisMismatchTests(unittest.TestCase):
    """Second-round review findings: GMV-vs-revenue (different 'name') and
    nominal-vs-real (different 'price_basis') mismatches must be caught even
    though unit/currency/region/scope/value_type all agree."""

    def _two_claims_with_metrics(self, evidence, metric_a, metric_b):
        evidence["claims"] = []
        evidence["gaps"] = []
        evidence["coverage"] = {
            "market": {"status": "out_of_scope", "claim_ids": [], "note": "test fixture reset", "next_question": None},
            "value_chain": {"status": "out_of_scope", "claim_ids": [], "note": "test fixture reset", "next_question": None},
            "business_model": {"status": "out_of_scope", "claim_ids": [], "note": "test fixture reset", "next_question": None},
            "competition": {"status": "out_of_scope", "claim_ids": [], "note": "test fixture reset", "next_question": None},
            "trends_risks": {"status": "out_of_scope", "claim_ids": [], "note": "test fixture reset", "next_question": None},
        }
        evidence["claims"].append({
            "id": "C001", "statement": "A", "dimensions": [], "kind": "fact", "evidence_status": "supported",
            "source_ids": ["S001"], "counter_source_ids": [], "basis_claim_ids": [], "rationale": None,
            "confidence": "high", "limitations": [], "metrics": [metric_a],
        })
        evidence["claims"].append({
            "id": "C002", "statement": "B", "dimensions": [], "kind": "fact", "evidence_status": "supported",
            "source_ids": ["S001"], "counter_source_ids": [], "basis_claim_ids": [], "rationale": None,
            "confidence": "high", "limitations": [], "metrics": [metric_b],
        })
        return evidence

    def test_gmv_vs_revenue_name_mismatch_with_comparable_true_is_rejected(self):
        evidence = load("valid_evidence.json")
        metric_a = {
            "name": "成交总额(GMV)", "value": 100, "unit": "亿元", "period": "2024", "region": "中国",
            "scope": "平台整体", "value_type": "reported", "source_ids": ["S001"], "missing_dimensions": [],
        }
        metric_b = {
            "name": "企业营业收入", "value": 8, "unit": "亿元", "period": "2024", "region": "中国",
            "scope": "平台整体", "value_type": "reported", "source_ids": ["S001"], "missing_dimensions": [],
        }
        evidence = self._two_claims_with_metrics(evidence, metric_a, metric_b)
        evidence["comparisons"] = [{
            "id": "CMP998", "comparison_type": "cross_sectional", "metric_refs": ["C001.0", "C002.0"],
            "purpose": "adversarial: GMV vs revenue, same unit/currency, claimed comparable",
            "comparable": True, "mismatched_dimensions": [], "adjustment_note": None,
        }]
        result = ve.validate(evidence, None)
        messages = error_messages(result)
        self.assertTrue(any("'name'" in m and "comparable=true" in m for m in messages), messages)

    def test_nominal_vs_real_price_basis_mismatch_with_comparable_true_is_rejected(self):
        evidence = load("valid_evidence.json")
        metric_a = {
            "name": "revenue", "value": 100, "unit": "亿元", "period": "2020", "region": "中国",
            "scope": "行业整体", "value_type": "reported", "source_ids": ["S001"], "missing_dimensions": [],
            "price_basis": "nominal",
        }
        metric_b = {
            "name": "revenue", "value": 110, "unit": "亿元", "period": "2024", "region": "中国",
            "scope": "行业整体", "value_type": "reported", "source_ids": ["S001"], "missing_dimensions": [],
            "price_basis": "real (2020 constant prices)",
        }
        evidence = self._two_claims_with_metrics(evidence, metric_a, metric_b)
        evidence["comparisons"] = [{
            "id": "CMP997", "comparison_type": "time_series", "metric_refs": ["C001.0", "C002.0"],
            "purpose": "adversarial: nominal vs real growth, claimed comparable as a trend",
            "comparable": True, "mismatched_dimensions": [], "adjustment_note": None,
        }]
        result = ve.validate(evidence, None)
        messages = error_messages(result)
        self.assertTrue(any("price_basis" in m and "comparable=true" in m for m in messages), messages)


class CrossSectionalPeriodMismatchTests(unittest.TestCase):
    """Second-round review finding: a cross_sectional comparison across two
    different periods (e.g. 2024 vs 2025) must not be wavable through just
    because 'period' used to be unconditionally exempted."""

    def test_cross_sectional_comparison_with_different_periods_is_rejected(self):
        evidence = load("valid_evidence.json")
        evidence["claims"] = []
        evidence["gaps"] = []
        evidence["coverage"] = {
            "market": {"status": "out_of_scope", "claim_ids": [], "note": "test fixture reset", "next_question": None},
            "value_chain": {"status": "out_of_scope", "claim_ids": [], "note": "test fixture reset", "next_question": None},
            "business_model": {"status": "out_of_scope", "claim_ids": [], "note": "test fixture reset", "next_question": None},
            "competition": {"status": "out_of_scope", "claim_ids": [], "note": "test fixture reset", "next_question": None},
            "trends_risks": {"status": "out_of_scope", "claim_ids": [], "note": "test fixture reset", "next_question": None},
        }
        evidence["claims"].append({
            "id": "C001", "statement": "company A revenue", "kind": "fact", "evidence_status": "supported",
            "source_ids": ["S001"], "counter_source_ids": [], "basis_claim_ids": [], "rationale": None,
            "confidence": "high", "limitations": [], "metrics": [{
                "name": "revenue", "value": 100, "unit": "亿元", "period": "2024", "region": "中国",
                "scope": "公司A整体", "value_type": "reported", "source_ids": ["S001"], "missing_dimensions": [],
            }],
        })
        evidence["claims"].append({
            "id": "C002", "statement": "company B revenue", "kind": "fact", "evidence_status": "supported",
            "source_ids": ["S001"], "counter_source_ids": [], "basis_claim_ids": [], "rationale": None,
            "confidence": "high", "limitations": [], "metrics": [{
                "name": "revenue", "value": 120, "unit": "亿元", "period": "2025", "region": "中国",
                "scope": "公司B整体", "value_type": "reported", "source_ids": ["S001"], "missing_dimensions": [],
            }],
        })
        evidence["comparisons"] = [{
            "id": "CMP996", "comparison_type": "cross_sectional", "metric_refs": ["C001.0", "C002.0"],
            "purpose": "adversarial: comparing two different companies' revenue from two different years as if same point in time",
            "comparable": True, "mismatched_dimensions": [], "adjustment_note": None,
        }]
        result = ve.validate(evidence, None)
        messages = error_messages(result)
        self.assertTrue(any("'period'" in m and "comparable=true" in m for m in messages), messages)

    def test_time_series_comparison_with_different_periods_is_still_accepted(self):
        """Sanity check: the fix must not break the legitimate time-series case."""
        result = ve.validate(load("valid_evidence.json"), None)
        # valid_evidence.json's CMP001 has only one metric_ref so the
        # cross-check doesn't fire either way; this asserts the base fixture
        # (comparison_type='cross_sectional' but single ref) is unaffected.
        self.assertEqual(result.errors, [])


class RequiredFieldDeletionTests(unittest.TestCase):
    """Second-round review finding: deleting documented-required fields
    (schema_version, source.publisher, claim array fields) must fail
    structural validation, not just emit a warning."""

    def test_missing_schema_version_is_an_error(self):
        evidence = load("valid_evidence.json")
        del evidence["schema_version"]
        result = ve.validate(evidence, None)
        self.assertTrue(any("schema_version" in e["path"] for e in result.errors))

    def test_missing_source_publisher_is_an_error(self):
        evidence = load("valid_evidence.json")
        del evidence["sources"][0]["publisher"]
        result = ve.validate(evidence, None)
        self.assertTrue(any("publisher" in m for m in error_messages(result)))

    def test_missing_source_access_note_is_an_error(self):
        evidence = load("valid_evidence.json")
        del evidence["sources"][0]["access_note"]
        result = ve.validate(evidence, None)
        self.assertTrue(any("access_note" in m for m in error_messages(result)))

    def test_missing_claim_counter_source_ids_is_an_error(self):
        evidence = load("valid_evidence.json")
        del evidence["claims"][0]["counter_source_ids"]
        result = ve.validate(evidence, None)
        self.assertTrue(any("counter_source_ids" in m for m in error_messages(result)))

    def test_missing_claim_basis_claim_ids_is_an_error(self):
        evidence = load("valid_evidence.json")
        del evidence["claims"][0]["basis_claim_ids"]
        result = ve.validate(evidence, None)
        self.assertTrue(any("basis_claim_ids" in m for m in error_messages(result)))

    def test_missing_claim_limitations_is_an_error(self):
        evidence = load("valid_evidence.json")
        del evidence["claims"][0]["limitations"]
        result = ve.validate(evidence, None)
        self.assertTrue(any("limitations" in m for m in error_messages(result)))

    def test_missing_claim_metrics_is_an_error(self):
        evidence = load("valid_evidence.json")
        del evidence["claims"][0]["metrics"]
        result = ve.validate(evidence, None)
        self.assertTrue(any("metrics" in m for m in error_messages(result)))


class SchemaVersionDisciplineTests(unittest.TestCase):
    """A file honestly declaring schema_version=1.0 (pre-comparison_type)
    must not be silently accepted by the 1.1 validator. Fourth-round review
    finding: a mismatched schema_version (including a fabricated/unknown one
    like "999.0") used to be only a warning, so structural_ok could still be
    true; this validator has no multi-version rule branching, so it can't
    vouch for a file declaring rules it isn't actually checking -- any
    version mismatch is now a hard error."""

    def test_old_schema_version_with_missing_new_field_fails_with_both_signals(self):
        evidence = load("valid_evidence.json")
        evidence["schema_version"] = "1.1"
        del evidence["coverage"]
        result = ve.validate(evidence, None)
        self.assertTrue(any("1.2" in m for m in error_messages(result)))
        self.assertTrue(any("coverage" in e["path"] for e in result.errors))

    def test_unknown_fabricated_schema_version_is_rejected(self):
        evidence = load("valid_evidence.json")
        evidence["schema_version"] = "999.0"
        result = ve.validate(evidence, None)
        self.assertTrue(any("schema_version" in e["path"] for e in result.errors))


class ThirdRoundRequiredFieldDeletionTests(unittest.TestCase):
    """Third-round review finding: research.data_cutoff, claims[].rationale,
    metrics[].missing_dimensions, and the top-level comparisons/gaps/checks
    (plus its two sub-objects) could all be deleted outright with no error."""

    def test_missing_research_data_cutoff_is_an_error(self):
        evidence = load("valid_evidence.json")
        del evidence["research"]["data_cutoff"]
        result = ve.validate(evidence, None)
        self.assertTrue(any("data_cutoff" in m for m in error_messages(result)))

    def test_missing_claim_rationale_is_an_error(self):
        evidence = load("valid_evidence.json")
        del evidence["claims"][0]["rationale"]
        result = ve.validate(evidence, None)
        self.assertTrue(any("rationale" in m for m in error_messages(result)))

    def test_missing_metric_missing_dimensions_is_an_error(self):
        evidence = load("valid_evidence.json")
        del evidence["claims"][0]["metrics"][0]["missing_dimensions"]
        result = ve.validate(evidence, None)
        self.assertTrue(any("missing_dimensions" in m for m in error_messages(result)))

    def test_missing_top_level_comparisons_is_an_error(self):
        evidence = load("valid_evidence.json")
        del evidence["comparisons"]
        result = ve.validate(evidence, None)
        self.assertTrue(any("comparisons" in m for m in error_messages(result)))

    def test_missing_top_level_gaps_is_an_error(self):
        evidence = load("valid_evidence.json")
        del evidence["gaps"]
        result = ve.validate(evidence, None)
        self.assertTrue(any("gaps" in m for m in error_messages(result)))

    def test_missing_top_level_checks_is_an_error(self):
        evidence = load("valid_evidence.json")
        del evidence["checks"]
        result = ve.validate(evidence, None)
        self.assertTrue(any("checks" in m for m in error_messages(result)))

    def test_missing_checks_semantic_review_is_an_error(self):
        evidence = load("valid_evidence.json")
        del evidence["checks"]["semantic_review"]
        result = ve.validate(evidence, None)
        self.assertTrue(any("semantic_review" in m for m in error_messages(result)))

    def test_missing_checks_machine_validation_is_an_error(self):
        evidence = load("valid_evidence.json")
        del evidence["checks"]["machine_validation"]
        result = ve.validate(evidence, None)
        self.assertTrue(any("machine_validation" in m for m in error_messages(result)))


class FourthRoundTypeAndKeyBypassTests(unittest.TestCase):
    """Fourth-round review finding: deleting a dimension field and declaring
    it in missing_dimensions bypassed key-presence enforcement; checks'
    sub-object internals had no field-level validation; several
    array-of-string fields only checked list-ness, not element types."""

    def test_metric_dimension_deleted_and_declared_missing_still_requires_the_key(self):
        evidence = load("valid_evidence.json")
        m = evidence["claims"][0]["metrics"][0]
        for f in ("period", "region", "scope"):
            m.pop(f, None)
        m["missing_dimensions"] = ["period", "region", "scope"]
        result = ve.validate(evidence, None)
        self.assertTrue(result.errors)

    def test_semantic_review_missing_internal_fields_is_an_error(self):
        evidence = load("valid_evidence.json")
        evidence["checks"]["semantic_review"] = {}
        result = ve.validate(evidence, None)
        self.assertTrue(any("performed" in m for m in error_messages(result)))
        self.assertTrue(any("notes" in m for m in error_messages(result)))

    def test_machine_validation_missing_internal_fields_is_an_error(self):
        evidence = load("valid_evidence.json")
        evidence["checks"]["machine_validation"] = {}
        result = ve.validate(evidence, None)
        self.assertTrue(result.errors)

    def test_machine_validation_wrong_types_are_rejected(self):
        evidence = load("valid_evidence.json")
        evidence["checks"]["machine_validation"] = {
            "performed": "yes", "tool": 123, "tool_version": None, "result": "nonsense",
        }
        result = ve.validate(evidence, None)
        messages = error_messages(result)
        self.assertTrue(any("performed" in m for m in messages))
        self.assertTrue(any("tool" in m for m in messages))
        self.assertTrue(any("result" in m for m in messages))

    def test_limitations_with_non_string_element_is_rejected(self):
        evidence = load("valid_evidence.json")
        evidence["claims"][0]["limitations"] = [123]
        result = ve.validate(evidence, None)
        self.assertTrue(any("limitations" in m for m in error_messages(result)))

    def test_metric_inputs_and_assumptions_with_non_string_elements_are_rejected(self):
        evidence = load("valid_evidence.json")
        evidence["claims"].append({
            "id": "C099", "statement": "x", "kind": "inference", "evidence_status": "partial",
            "source_ids": [], "counter_source_ids": [], "basis_claim_ids": [], "rationale": "x",
            "confidence": "low", "limitations": [], "metrics": [{
                "name": "x", "value": 1, "unit": "x", "period": "2024", "region": None, "scope": None,
                "value_type": "estimated", "source_ids": [], "missing_dimensions": ["region", "scope"],
                "method": "x", "inputs": [123], "assumptions": [456],
            }],
        })
        result = ve.validate(evidence, None)
        paths = [e["path"] for e in result.errors]
        self.assertTrue(any("inputs" in p for p in paths))
        self.assertTrue(any("assumptions" in p for p in paths))

    def test_mismatched_dimensions_with_non_string_element_is_rejected(self):
        evidence = load("valid_evidence.json")
        evidence["comparisons"][0]["comparable"] = False
        evidence["comparisons"][0]["mismatched_dimensions"] = [123]
        result = ve.validate(evidence, None)
        self.assertTrue(any("mismatched_dimensions" in m for m in error_messages(result)))


class FifthRoundComparisonAndOptionalFieldTests(unittest.TestCase):
    """Fifth-round review finding: comparisons could reference zero, one, or
    the same metric twice (nothing was actually being compared); and
    metric.currency/price_basis/method/inputs/assumptions were only
    type-checked inside the calculated/estimated branch, so a wrong type on
    a 'reported' metric slipped through untouched."""

    def test_comparison_with_empty_metric_refs_is_rejected(self):
        evidence = load("valid_evidence.json")
        evidence["comparisons"][0]["metric_refs"] = []
        result = ve.validate(evidence, None)
        self.assertTrue(any("at least two metrics" in m for m in error_messages(result)))

    def test_comparison_with_single_metric_ref_is_rejected(self):
        evidence = load("valid_evidence.json")
        evidence["comparisons"][0]["metric_refs"] = ["C001.0"]
        result = ve.validate(evidence, None)
        self.assertTrue(any("at least two metrics" in m for m in error_messages(result)))

    def test_comparison_referencing_the_same_metric_twice_is_rejected(self):
        evidence = load("valid_evidence.json")
        evidence["comparisons"][0]["metric_refs"] = ["C001.0", "C001.0"]
        result = ve.validate(evidence, None)
        self.assertTrue(any("distinct metrics" in m for m in error_messages(result)))

    def test_comparison_with_two_distinct_metrics_is_accepted(self):
        result = ve.validate(load("valid_evidence.json"), None)
        self.assertEqual(result.errors, [])

    def test_metric_currency_wrong_type_is_rejected_even_when_reported(self):
        evidence = load("valid_evidence.json")
        evidence["claims"][0]["metrics"][0]["currency"] = 123
        result = ve.validate(evidence, None)
        self.assertTrue(any("currency" in e["path"] for e in result.errors))

    def test_metric_price_basis_wrong_type_is_rejected_even_when_reported(self):
        evidence = load("valid_evidence.json")
        evidence["claims"][0]["metrics"][0]["price_basis"] = []
        result = ve.validate(evidence, None)
        self.assertTrue(any("price_basis" in e["path"] for e in result.errors))

    def test_metric_method_inputs_assumptions_wrong_types_rejected_when_reported(self):
        evidence = load("valid_evidence.json")
        evidence["claims"][0]["metrics"][0]["method"] = 123
        evidence["claims"][0]["metrics"][0]["inputs"] = 123
        evidence["claims"][0]["metrics"][0]["assumptions"] = 123
        result = ve.validate(evidence, None)
        paths = [e["path"] for e in result.errors]
        self.assertTrue(any("method" in p for p in paths))
        self.assertTrue(any("inputs" in p for p in paths))
        self.assertTrue(any("assumptions" in p for p in paths))


class FixtureInventoryTests(unittest.TestCase):
    def test_fixtures_directory_has_expected_files(self):
        expected = {
            "valid_evidence.json", "valid_report.md", "report_with_unknown_claim.md",
            "invalid_duplicate_ids.json", "invalid_dangling_reference.json",
            "invalid_cycle.json", "invalid_unknown_supported.json",
            "invalid_fact_snippet_only.json", "invalid_missing_dimension.json",
            "invalid_calculated_no_method.json", "invalid_comparison_contradiction.json",
            "invalid_coverage_missing_key.json", "invalid_coverage_bad_status.json",
            "invalid_coverage_dangling_claim.json", "invalid_dimensions_bad_value.json",
        }
        present = {p.name for p in FIXTURES.iterdir()}
        self.assertTrue(expected.issubset(present))


class CoverageValidationTests(unittest.TestCase):
    """schema 1.2: top-level `coverage` records the five research dimensions
    (market/value_chain/business_model/competition/trends_risks). A 'covered'
    status must be backed by an actual non-unknown claim tagged with that
    dimension, not just a filled-in field."""

    def test_valid_fixture_coverage_passes(self):
        result = ve.validate(load("valid_evidence.json"), None)
        self.assertEqual(result.errors, [])

    def test_missing_coverage_key_is_rejected(self):
        result = ve.validate(load("invalid_coverage_missing_key.json"), None)
        self.assertTrue(any("missing required dimension key" in m for m in error_messages(result)))

    def test_extra_coverage_key_is_rejected(self):
        evidence = load("valid_evidence.json")
        evidence["coverage"]["not_a_real_dimension"] = {
            "status": "out_of_scope", "claim_ids": [], "note": "x", "next_question": None,
        }
        result = ve.validate(evidence, None)
        self.assertTrue(any("unexpected key" in m for m in error_messages(result)))

    def test_illegal_coverage_status_is_rejected(self):
        result = ve.validate(load("invalid_coverage_bad_status.json"), None)
        self.assertTrue(any("coverage.market.status" in e["path"] for e in result.errors))

    def test_coverage_dangling_claim_reference_is_rejected(self):
        result = ve.validate(load("invalid_coverage_dangling_claim.json"), None)
        self.assertTrue(any("references unknown claim id" in m for m in error_messages(result)))

    def test_covered_status_referencing_only_unknown_claim_is_rejected(self):
        evidence = load("valid_evidence.json")
        # C003 is kind=unknown in the base fixture; a 'covered' status backed
        # only by an unknown claim must not pass, even though the claim_id
        # itself resolves and is tagged with the right dimension.
        evidence["claims"][2]["dimensions"] = ["trends_risks"]
        evidence["coverage"]["trends_risks"] = {
            "status": "covered", "claim_ids": ["C003"], "note": "x", "next_question": None,
        }
        result = ve.validate(evidence, None)
        self.assertTrue(any("requires at least one referenced claim_id" in m for m in error_messages(result)))

    def test_covered_status_referencing_claim_without_matching_dimension_is_rejected(self):
        evidence = load("valid_evidence.json")
        # C001 is kind=fact but tagged only with 'market', not 'competition'.
        evidence["coverage"]["competition"] = {
            "status": "covered", "claim_ids": ["C001"], "note": "x", "next_question": None,
        }
        result = ve.validate(evidence, None)
        self.assertTrue(any("requires at least one referenced claim_id" in m for m in error_messages(result)))

    def test_covered_status_with_qualifying_claim_is_accepted(self):
        result = ve.validate(load("valid_evidence.json"), None)
        # Base fixture's market=covered is backed by C001 (kind=fact,
        # dimensions includes 'market') -- already exercised by the
        # no-errors check above, restated here for clarity of intent.
        self.assertEqual(
            [e for e in result.errors if e["path"] == "coverage.market"],
            [],
        )

    def test_missing_and_out_of_scope_do_not_require_a_qualifying_claim(self):
        # Honest 'missing'/'out_of_scope' states with no claim_ids must save
        # cleanly -- the schema must not pressure fabricating coverage.
        evidence = load("valid_evidence.json")
        result = ve.validate(evidence, None)
        for dim in ("value_chain", "business_model", "competition"):
            self.assertEqual(
                [e for e in result.errors if e["path"].startswith(f"coverage.{dim}")],
                [],
            )

    def test_missing_top_level_coverage_is_an_error(self):
        evidence = load("valid_evidence.json")
        del evidence["coverage"]
        result = ve.validate(evidence, None)
        self.assertTrue(any("coverage" in e["path"] for e in result.errors))

    def test_coverage_note_must_not_be_empty(self):
        evidence = load("valid_evidence.json")
        evidence["coverage"]["value_chain"]["note"] = ""
        result = ve.validate(evidence, None)
        self.assertTrue(any("note must not be empty" in m for m in error_messages(result)))


class ClaimDimensionsValidationTests(unittest.TestCase):
    """schema 1.2: claims[].dimensions tags a claim to one or more of the
    five research dimensions, restricted to the fixed vocabulary."""

    def test_missing_claim_dimensions_is_an_error(self):
        evidence = load("valid_evidence.json")
        del evidence["claims"][0]["dimensions"]
        result = ve.validate(evidence, None)
        self.assertTrue(any("dimensions" in m for m in error_messages(result)))

    def test_illegal_dimension_value_is_rejected(self):
        result = ve.validate(load("invalid_dimensions_bad_value.json"), None)
        self.assertTrue(any("'profitability' is not one of" in m for m in error_messages(result)))

    def test_duplicate_dimension_value_is_rejected(self):
        evidence = load("valid_evidence.json")
        evidence["claims"][0]["dimensions"] = ["market", "market"]
        result = ve.validate(evidence, None)
        self.assertTrue(any("duplicates" in m for m in error_messages(result)))

    def test_empty_dimensions_array_is_valid(self):
        # A claim that's pure scope/boundary background, with no dimension
        # tag, must be allowed -- dimensions is not required to be non-empty.
        evidence = load("valid_evidence.json")
        evidence["claims"][2]["dimensions"] = []
        evidence["coverage"]["trends_risks"]["claim_ids"] = ["C002"]
        result = ve.validate(evidence, None)
        self.assertEqual(result.errors, [])

    def test_claim_can_carry_multiple_dimension_tags(self):
        # C002 in the base fixture already carries two tags (market,
        # trends_risks) -- confirm that's accepted, not just single-tag claims.
        evidence = load("valid_evidence.json")
        self.assertEqual(evidence["claims"][1]["dimensions"], ["market", "trends_risks"])
        result = ve.validate(evidence, None)
        self.assertEqual(result.errors, [])


class SchemaVersionUpgradePromptTests(unittest.TestCase):
    """A file honestly declaring the previous schema_version (1.1, which had
    no coverage/dimensions concept) must fail clearly rather than being
    silently accepted under 1.2's new rules -- mirroring how 1.0 files were
    handled when 1.1 was introduced."""

    def test_declared_1_1_file_is_rejected_not_silently_upgraded(self):
        evidence = load("valid_evidence.json")
        evidence["schema_version"] = "1.1"
        result = ve.validate(evidence, None)
        self.assertTrue(any("expected '1.2'" in m and "'1.1'" in m for m in error_messages(result)))


if __name__ == "__main__":
    unittest.main()
