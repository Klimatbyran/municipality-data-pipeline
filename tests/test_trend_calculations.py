# -*- coding: utf-8 -*-
import unittest
import pandas as pd

from kpis.emissions.trend_calculations import (
    extract_year_columns,
    generate_prediction_years,
    calculate_total_trend,
    calculate_trend,
    apply_zero_floor,
)

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

    def test_extract_year_columns(self):
        """Test the extract_year_columns function"""
        DF_INPUT["2001_test"] = [190]

        years, last_data_year = extract_year_columns(DF_INPUT)

        self.assertEqual(
            years.tolist(),
            [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
            "Years are not equal",
        )
        self.assertEqual(last_data_year, 2025, "Last data year is not equal")

    def test_generate_prediction_years(self):
        """Test the generate_prediction_years function"""
        years_approximated, years_trend = generate_prediction_years(2025, 2029, 2035)
        self.assertEqual(years_approximated.tolist(), [2025, 2026, 2027, 2028, 2029])
        self.assertEqual(
            years_trend.tolist(), [2029, 2030, 2031, 2032, 2033, 2034, 2035]
        )

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

        self.assertIn("emission_slope", df_result.columns)

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

    def test_approximated_trend_cut_at_zero(self):
        """Test the trend cut at zero"""
        df_expected = pd.DataFrame(
            {
                "Kommun": ["Norrköping"],
                "approximated_2027": [100],
                "approximated_2028": [50],
                "approximated_2029": [0],
                "approximated_2030": [-10],
                "approximated_2031": [-20],
            }
        )

        df_expected = pd.DataFrame(
            {
                "Kommun": ["Norrköping"],
                "approximated_2027": [100],
                "approximated_2028": [50],
                "approximated_2029": [0],
                "approximated_2030": [0],
                "approximated_2031": [0],
            }
        )

        apprixmated_cols = [
            col for col in df_expected.columns if "approximated_" in col
        ]
        df_result = apply_zero_floor(df_expected, apprixmated_cols)

        pd.testing.assert_frame_equal(df_result, df_expected)

    def test_future_trend_cut_at_zero(self):
        """Test the trend cut at zero"""
        df_input = pd.DataFrame(
            {
                "Kommun": ["Norrköping"],
                "approximated_2026": [110],
                "approximated_2027": [100],
                "approximated_2028": [50],
                "approximated_2029": [0],
                "approximated_2030": [-10],
                "trend_2030": [150],
                "trend_2031": [100],
                "trend_2032": [50],
                "trend_2033": [0],
                "trend_2034": [-50],
                "trend_2035": [-150],
            }
        )

        df_expected = pd.DataFrame(
            {
                "Kommun": ["Norrköping"],
                "approximated_2026": [110],
                "approximated_2027": [100],
                "approximated_2028": [50],
                "approximated_2029": [0],
                "approximated_2030": [-10],
                "trend_2030": [150],
                "trend_2031": [100],
                "trend_2032": [50],
                "trend_2033": [0],
                "trend_2034": [0],
                "trend_2035": [0],
            }
        )

        trend_cols = [col for col in df_input.columns if "trend_" in col]
        df_result = apply_zero_floor(df_input, trend_cols)
        pd.testing.assert_frame_equal(df_result, df_expected)

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

    def test_total_trend(self):
        """Test the total trend"""

        df_input = pd.DataFrame(
            {
                "Kommun": ["Norrköping"],
                "trend_2029": [100],
                "trend_2030": [150],
                "trend_2031": [200],
                "trend_2032": [250],
                "trend_2033": [300],
                "trend_2034": [350],
                "trend_2035": [400],
            }
        )

        expected_total_trend = 1750

        resulting_value = calculate_total_trend(df_input)

        self.assertEqual(resulting_value, expected_total_trend)


if __name__ == "__main__":
    unittest.main()
