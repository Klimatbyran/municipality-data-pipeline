# -*- coding: utf-8 -*-
import unittest
import pandas as pd

from facts.political.political_rule import (
    clean_municipality_name,
    clean_political_rule,
    get_political_rule_municipalities,
)


class TestPoliticalRule(unittest.TestCase):
    """Test the political rule"""

    def test_clean_municipality_name(self):
        """Test that clean_municipality_name returns correct data."""
        name_ending_with_s = "Upplands Väsby kommun"
        expected = "Upplands Väsby"
        result = clean_municipality_name(name_ending_with_s)
        self.assertEqual(result, expected)

        name_ending_with_stad = "Stockholms stad"
        expected = "Stockholm"
        result = clean_municipality_name(name_ending_with_stad)
        self.assertEqual(result, expected)

        name_ending_with_s = "Hofors kommun"
        expected = "Hofors"
        result = clean_municipality_name(name_ending_with_s)
        self.assertEqual(result, expected)

        special_case_name = "Falu kommun"
        expected = "Falun"
        result = clean_municipality_name(special_case_name)
        self.assertEqual(result, expected)

    def test_clean_political_rule(self):
        """Test that clean_political_rule returns correct data."""
        rule = "SD, M,,KD,,, L, C, MP,,S, Hejson"
        expected = ["SD", "M", "KD", "L", "C", "MP", "S", "Hejson"]
        result = clean_political_rule(rule)
        self.assertEqual(result, expected)

    def test_get_political_rule(self):
        """Test that get_political_rule returns correct data."""
        df_expected = pd.DataFrame(
            {
                "Kommun": ["Upplands Väsby", "Vallentuna", "Österåker"],
                "Rule": [
                    ["L", "S", "Väsbys Bästa"],
                    ["M", "KD", "L", "C"],
                    ["M", "KD", "L", "C"],
                ],
                "KSO": ["S", "M", "M"],
            }
        )

        df_result = get_political_rule_municipalities()

        pd.testing.assert_frame_equal(df_result.head(3), df_expected)


if __name__ == "__main__":
    unittest.main()
