# -*- coding: utf-8 -*-
import unittest
import pandas as pd

from kpis.emissions.emission_data_calculations import (
    calculate_historical_change_percent,
    deduct_cement,
)
from kpis.emissions.trend_calculations import calculate_trend


LAST_YEAR_WITH_SMHI_DATA = 2021
CURRENT_YEAR = 2024


class TestEmissionCalculations(unittest.TestCase):
    """Test the emission calculations"""

    def test_deduct_cement(self):
        """Test the cement deduction"""
        # Sample data frame for Skövde and Gotland
        df_input = pd.DataFrame(
            {
                "Kommun": ["Skövde", "Gotland"],
                2010: [546338.699134178, 1981476.17399167],
                2015: [494776.01973774, 2195403.90927869],
                2016: [532612.492354495, 2124789.02188846],
                2017: [543896.716984358, 2024382.31793093],
                2018: [586444.17315306, 2143010.50127022],
                2019: [576595.998007861, 1966304.75819611],
                2020: [567399.427902324, 1820053.10059352],
                2021: [571141.947070738, 1741013.9429687],
            }
        )

        df_expected = pd.DataFrame(
            {
                "Kommun": ["Skövde", "Gotland"],
                2010: [189373.699134178, 401665.17399167],
                2015: [136142.01973774, 269367.90927869],
                2016: [147686.492354495, 220902.02188846],
                2017: [136263.586984358, 267272.31793093],
                2018: [140813.83315306, 402598.50127022],
                2019: [136091.668007861, 429824.75819611],
                2020: [108306.954902324, 195590.10059352],
                2021: [131967.220070738, 119802.9429687],
            }
        )

        cement_deduction = {
            "Skövde": {
                2010: 356965000 / 1000,
                2015: 358634000 / 1000,
                2016: 384926000 / 1000,
                2017: 407633130 / 1000,
                2018: 445630340 / 1000,
                2019: 440504330 / 1000,
                2020: 459092473 / 1000,
                2021: 439174727 / 1000,
                2022: 406856000 / 1000,
            },
            "Gotland": {
                2010: 1579811000 / 1000,
                2015: 1926036000 / 1000,
                2016: 1903887000 / 1000,
                2017: 1757110000 / 1000,
                2018: 1740412000 / 1000,
                2019: 1536480000 / 1000,
                2020: 1624463000 / 1000,
                2021: 1621211000 / 1000,
            },
        }

        df_result = deduct_cement(df_input, cement_deduction)

        pd.testing.assert_frame_equal(df_result, df_expected, check_dtype=False)

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

    def test_calculate_historical_change_percent(self):
        """Test the historical change percent"""
        # Sample data frame for Östersund
        df_input = pd.DataFrame(
            {
                "Kommun": ["Östersund"],
                2015: [143786.390451667],
                2016: [136270.272900585],
                2017: [134890.137836385],
                2018: [123096.170608436],
                2019: [113061.651497606],
                2020: [94746.1396597532],
                2021: [95248.2864179093],
            }
        )

        df_expected = df_input.copy()
        df_expected["historicalEmissionChangePercent"] = [-6.46746990789292]

        df_result = calculate_historical_change_percent(
            df_input, LAST_YEAR_WITH_SMHI_DATA
        )

        pd.testing.assert_frame_equal(df_result, df_expected, check_exact=False)


if __name__ == "__main__":
    unittest.main()
