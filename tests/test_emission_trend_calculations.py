# -*- coding: utf-8 -*-
import unittest
import pandas as pd

from kpis.emissions.trend_calculations import calculate_trend


LAST_YEAR_WITH_SMHI_DATA = 2021
CURRENT_YEAR = 2024


class TestEmissionTrendCalculations(unittest.TestCase):
    """Test the emission trend calculations"""

    def test_calculate_lad_anchored(self):
        """Test the LAD anchored regression"""
        emissions = [100, 150, 120, 130, 140, 160, 170, 180]
        years = list(range(2018, 2026))

        input_df = pd.DataFrame(
            {
                "Kommun": ["Ale"],
                **{year: [emission] for year, emission in zip(years, emissions)},
            }
        )

        current_year = 2029
        result_df = calculate_trend(input_df, current_year)

        self.assertIn("trend", result_df.columns)
        self.assertIn("trend_coefficient", result_df.columns)

        predictions = result_df.iloc[0]["trend"]
        self.assertEqual(len(predictions), 4)

    def test_calculate_approximated_historical(self):
        """Test the approximated historical emissions"""
        # Sample data frame for Norrköping
        df_input = pd.DataFrame(
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

        df_expected = df_input.copy()
        df_expected["approximatedHistorical"] = [
            {
                2025: 180,
                2026: 522772.98167590424,
                2027: 513875.21056812257,
                2028: 504977.43946033716,
                2029: 496079.66835255175,
            }
        ]

        current_year = 2029
        df_result = calculate_trend(df_input, current_year)

        print(df_result.columns)
        print(df_result.head())
        print(df_result["trend"])
        print(df_result["trend_coefficient"])
        pd.testing.assert_frame_equal(df_result, df_expected, check_exact=False)


if __name__ == "__main__":
    unittest.main()
