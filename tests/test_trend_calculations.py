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

    def _compare_approximated_results(
        self, df_result, column_name, expected_value, test_string
    ):
        result = df_result.iloc[0][column_name]
        self.assertEqual(
            result,
            expected_value,
            f"{test_string}{result - expected_value}",
        )

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

        self._compare_approximated_results(
            df_result,
            "trend_2034",
            282.85714395918365,
            "Trend 2034 is off by ",
        )

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

        self._compare_approximated_results(
            df_result,
            "approximated_2025",
            180,
            "Approximated value for 2025 is off by ",
        )
        self._compare_approximated_results(
            df_result,
            "approximated_2029",
            225.71428620408162,
            "Approximated value for 2029 is off by ",
        )


if __name__ == "__main__":
    unittest.main()
