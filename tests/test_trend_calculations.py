# -*- coding: utf-8 -*-
import unittest
import pandas as pd

from kpis.emissions.trend_calculations import (
    extract_year_columns,
    generate_prediction_years,
    create_new_columns_structure,
    apply_zero_floor,
    perform_regression_and_predict,
    calculate_total_trend,
    calculate_trend,
)

# Sample data frame for Norrköping
DF_INPUT = pd.DataFrame(
    {
        "Kommun": ["Norrköping"],
        2017: [1000],
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
CUTOFF_YEAR = 2018


class TestTrendCalculations(unittest.TestCase):
    """Test the emission trend calculations"""

    def test_extract_year_columns(self):
        """Test the extract_year_columns function"""
        DF_INPUT["2001_test"] = [190]

        years, last_data_year = extract_year_columns(DF_INPUT, CUTOFF_YEAR)

        self.assertEqual(
            years.tolist(), [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
        )
        self.assertEqual(last_data_year, 2025)

    def test_generate_prediction_years(self):
        """Test the generate_prediction_years function"""
        years_approximated, years_trend = generate_prediction_years(2025, 2029, 2035)
        self.assertEqual(years_approximated.tolist(), [2025, 2026, 2027, 2028, 2029])
        self.assertEqual(
            years_trend.tolist(), [2029, 2030, 2031, 2032, 2033, 2034, 2035]
        )

    def test_create_new_columns_structure(self):
        """Test the create_new_columns_structure function"""
        new_columns_data = create_new_columns_structure(
            [2025, 2026, 2027, 2028, 2029],
            [2029, 2030, 2031, 2032, 2033, 2034, 2035],
            1,
        )
        self.assertEqual(
            new_columns_data,
            {
                "approximated_2025": [None],
                "approximated_2026": [None],
                "approximated_2027": [None],
                "approximated_2028": [None],
                "approximated_2029": [None],
                "trend_2029": [None],
                "trend_2030": [None],
                "trend_2031": [None],
                "trend_2032": [None],
                "trend_2033": [None],
                "trend_2034": [None],
                "trend_2035": [None],
                "emission_slope": [None],
            },
        )

    def _compare_predicted_results(
        self, df_result, column_name, expected_value, test_string
    ):
        result = df_result.iloc[0][column_name]
        self.assertEqual(
            round(result, 4),
            round(expected_value, 4),
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

        df_result = calculate_trend(DF_INPUT, CURRENT_YEAR, END_YEAR, CUTOFF_YEAR)

        self.assertIn("emission_slope", df_result.columns)

        self.assertTrue(
            all(col in df_result.columns for col in expected_trend),
            f"Missing trend columns: {set(expected_trend) - set(df_result.columns)}",
        )

        self._compare_predicted_results(
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

    def test_perform_regression_and_predict(self):
        """Test the perform_regression_and_predict function"""
        preds_approximated, preds_trend, shift, emission_slope = (
            perform_regression_and_predict(
                [100, 110, 120, 130, 140, 150, 160, 170],
                [0, 1, 2, 3, 4, 5, 6, 7],
                [7, 8, 9],
                [9, 10, 11],
            )
        )

        rounded_preds_approximated_list = preds_approximated.round(4).tolist()
        rounded_preds_trend_list = preds_trend.round(4).tolist()
        rounded_shift = round(shift, 4)
        rounded_emission_slope = round(emission_slope, 4)

        self.assertListEqual(rounded_preds_approximated_list, [170, 180, 190])
        self.assertListEqual(rounded_preds_trend_list, [190, 200, 210])
        self.assertEqual(rounded_shift, 70.0)
        self.assertEqual(rounded_emission_slope, 10.0)

    def test_calculate_approximated_historical(self):
        """Test the LAD anchored regression for approximated historical emissions"""

        df_result = calculate_trend(DF_INPUT, CURRENT_YEAR, END_YEAR, CUTOFF_YEAR)

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

        self._compare_predicted_results(
            df_result,
            "approximated_2025",
            180,
            "Approximated value for 2025 is off by ",
        )
        self._compare_predicted_results(
            df_result,
            "approximated_2029",
            225.7143,
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
