"""Tests for the existing add-on scoring rules in main.rank_add_ons.

Run from the backend folder:  python -m unittest discover -s tests -v

These pin down the rule-based score that the frontend's Acquisition Fit Engine
shows as a *reference* number. The Fit Engine uses a different, continuous model
and never adds the two scores together.
"""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import rank_add_ons  # noqa: E402

CASES_PATH = os.path.join(os.path.dirname(__file__), "industry_cases.json")


def company(row_id, **fields):
    return {"_row_id": row_id, "company_name": f"Company {row_id}", **fields}


def score_for(platform, candidate):
    results = rank_add_ons([platform, candidate], platform["_row_id"])
    return results[0] if results else None


class AddOnScoringRules(unittest.TestCase):
    def test_exact_industry_adds_60(self):
        result = score_for(company(0, industry="HVAC"), company(1, industry="hvac"))
        self.assertEqual(result["add_on_fit_score"], 60)
        self.assertEqual(result["evidence"][0]["reason"], "Exact industry match")

    def test_similar_industry_adds_30(self):
        result = score_for(company(0, industry="Home Services"), company(1, industry="Home Service"))
        self.assertEqual(result["add_on_fit_score"], 30)
        self.assertEqual(result["evidence"][0]["reason"], "Similar industry labels")

    def test_employees_at_or_below_platform_adds_20(self):
        result = score_for(company(0, employees=50), company(1, employees=50))
        self.assertEqual(result["add_on_fit_score"], 20)

    def test_employees_above_platform_adds_nothing_and_is_omitted(self):
        self.assertIsNone(score_for(company(0, employees=50), company(1, employees=51)))

    def test_revenue_at_or_below_platform_adds_20(self):
        result = score_for(company(0, revenue_estimate="$5M"), company(1, revenue_estimate=2_000_000))
        self.assertEqual(result["add_on_fit_score"], 20)

    def test_maximum_score_is_100(self):
        platform = company(0, industry="HVAC", employees=50, revenue_estimate=5_000_000)
        candidate = company(1, industry="HVAC", employees=10, revenue_estimate=1_000_000)
        self.assertEqual(score_for(platform, candidate)["add_on_fit_score"], 100)

    def test_missing_data_adds_zero_and_candidate_without_evidence_is_omitted(self):
        platform = company(0, industry="HVAC", employees=50, revenue_estimate=5_000_000)
        self.assertIsNone(score_for(platform, company(1)))
        partial = score_for(platform, company(2, industry="HVAC"))
        self.assertEqual(partial["add_on_fit_score"], 60)

    def test_platform_is_never_recommended_to_itself(self):
        records = [company(0, industry="HVAC"), company(1, industry="HVAC")]
        ids = [r["candidate_company_id"] for r in rank_add_ons(records, 0)]
        self.assertEqual(ids, [1])

    def test_results_sorted_by_score_descending(self):
        records = [
            company(0, industry="HVAC", employees=50),
            company(1, employees=10),
            company(2, industry="HVAC", employees=10),
        ]
        scores = [r["add_on_fit_score"] for r in rank_add_ons(records, 0)]
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertEqual(scores, [80, 20])

    def test_unknown_platform_raises(self):
        with self.assertRaises(Exception):
            rank_add_ons([company(0)], 99)


class SharedIndustryContract(unittest.TestCase):
    """The same cases are asserted against the frontend Fit Engine."""

    def test_industry_label_classification(self):
        with open(CASES_PATH, encoding="utf-8") as handle:
            cases = json.load(handle)["cases"]
        for case in cases:
            with self.subTest(case=case):
                result = score_for(
                    company(0, industry=case["platform"]),
                    company(1, industry=case["candidate"]),
                )
                if case["expected"] == "exact":
                    self.assertEqual(result["add_on_fit_score"], 60)
                elif case["expected"] == "similar":
                    self.assertEqual(result["add_on_fit_score"], 30)
                else:
                    self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
