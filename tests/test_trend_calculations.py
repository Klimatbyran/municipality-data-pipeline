# -*- coding: utf-8 -*-
import unittest
import pandas as pd

from kpis.emissions.trend_calculations import calculate_trend

# Sample data frame for Norrköping
DF_INPUT = pd.DataFrame(
    {
        "Kommun": ["Norrköping"],
        2018: [100],
        2019: [150],
        2020: [120],
        2021: [130],
        2022: [140],
        2023: [160],
        2024: [170],
        2025: [180],
    }
)

CURRENT_YEAR = 2029
END_YEAR = 2035


class TestTrendCalculations(unittest.TestCase):
    """Test the emission trend calculations"""

    def test_calculate_future_trend(self):
        """Test the LAD anchored regression for future trend"""

        expected_trend = [
            "trend_2029",
            "trend_2030",
            "trend_2031",
            "trend_2032",
            "trend_2033",
        ]

        df_result = calculate_trend(DF_INPUT, CURRENT_YEAR, END_YEAR)

        self.assertIn("trend_coefficient", df_result.columns)

        self.assertTrue(
            all(col in df_result.columns for col in expected_trend),
            f"Missing trend columns: {set(expected_trend) - set(df_result.columns)}",
        )

        # self.assertEqual(df_result.iloc[0]["trend_2033"], 282.86)

    def test_calculate_approximated_historical(self):
        """Test the LAD anchored regression for approximated historical emissions"""

        df_result = calculate_trend(DF_INPUT, CURRENT_YEAR, END_YEAR)

        expected_approximated = [
            "approximated_2025",
            "approximated_2026",
            "approximated_2027",
            "approximated_2028",
            "approximated_2029",
        ]

        self.assertTrue(
            all(col in df_result.columns for col in expected_approximated),
            f"Missing approximated columns: {set(expected_approximated) - set(df_result.columns)}",
        )

        # self.assertEqual(df_result.iloc[0]["approximated_2025"], 180)
        # self.assertEqual(df_result.iloc[0]["approximated_2029"], 282.86)


if __name__ == "__main__":
    unittest.main()
