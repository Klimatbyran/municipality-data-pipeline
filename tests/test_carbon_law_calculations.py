# -*- coding: utf-8 -*-
import unittest
import pandas as pd

from kpis.emissions.carbon_law_calculations import (
    get_latest_emission_value,
    calculate_carbon_law_future_emissions,
    calculate_carbon_law_total_future_emissions,
    calculate_carbon_law_net_zero_date,
    carbon_law_calculations,
)


class TestCarbonLawCalculations(unittest.TestCase):

    def test_get_latest_emission_value(self):
        latest_emission_value_expected = 5

        approximated_data_row = {
            2019: 1,
            2020: 1,
            "approximatedHistorical": {2020: 1, 2021: 2, 2022: 4, 2023: 3, 2024: 5},
        }
        latest_emission_value_result = get_latest_emission_value(
            approximated_data_row, 2024
        )

        self.assertEqual(latest_emission_value_result, latest_emission_value_expected)

    def test_calculate_carbon_law_future_emissions(self):
        dict_expected = {
            2025: 5.0,
            2026: 4.5,
            2027: 4.05,
            2028: 3.645,
            2029: 3.2805,
            2030: 2.9525,
            2031: 2.6573,
            2032: 2.3916,
            2033: 2.1525,
            2034: 1.9372,
            2035: 1.7435,
            2036: 1.5691,
            2037: 1.4122,
            2038: 1.2710,
            2039: 1.1439,
            2040: 1.0295,
            2041: 0.9266,
            2042: 0.8339,
            2043: 0.7505,
            2044: 0.6755,
            2045: 0.6079,
            2046: 0.5471,
            2047: 0.4924,
            2048: 0.4432,
            2049: 0.3989,
            2050: 0.3590,
        }

        dict_result = calculate_carbon_law_future_emissions(5, 2025, 2050, 0.10)

        self.assertEqual(dict_result, dict_expected)

    # def test_calculate_carbon_law_total_future_emissions(self):
    #     df_expected = pd.DataFrame(
    #         {
    #             "Kommun": ["Ale", "Alingsås", "Alvesta"],
    #             "x": [
    #                 1,
    #                 1,
    #                 1,
    #             ],
    #         }
    #     )

    #     df_result = calculate_carbon_law_total_future_emissions()

    #     pd.testing.assert_frame_equal(
    #         df_result.iloc[:3], df_expected, check_dtype=False
    #     )

    # def test_calculate_carbon_law_net_zero_date(self):
    #     df_expected = pd.DataFrame(
    #         {
    #             "Kommun": ["Ale", "Alingsås", "Alvesta"],
    #             "x": [
    #                 1,
    #                 1,
    #                 1,
    #             ],
    #         }
    #     )

    #     df_result = calculate_carbon_law_net_zero_date()

    #     pd.testing.assert_frame_equal(
    #         df_result.iloc[:3], df_expected, check_dtype=False
    #     )

    # def test_carbon_law_calculations(self):
    #     df_expected = pd.DataFrame(
    #         {
    #             "Kommun": ["Ale", "Alingsås", "Alvesta"],
    #             "x": [
    #                 1,
    #                 1,
    #                 1,
    #             ],
    #         }
    #     )

    #     df_result = carbon_law_calculations()

    #     pd.testing.assert_frame_equal(
    #         df_result.iloc[:3], df_expected, check_dtype=False
    #     )


if __name__ == "__main__":
    unittest.main()
