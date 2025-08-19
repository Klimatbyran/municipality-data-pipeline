# -*- coding: utf-8 -*-
import unittest
import pandas as pd

from kpis.emissions.carbon_law_calculations import (
    get_latest_emission_value,
    calculate_carbon_law_future_emissions,
    sum_carbon_law_total_future_emissions,
    carbon_law_calculations,
)


class TestCarbonLawCalculations(unittest.TestCase):
    """Test cases for carbon law calculation functions."""

    def test_get_latest_emission_value(self):
        """Test that get_latest_emission_value returns correct data."""
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
        """Test that calculate_carbon_law_future_emissions returns correct data."""
        dict_expected = {
            2025: 5,
            2026: 4.50000000,
            2027: 4.05000000,
            2028: 3.64500000,
            2029: 3.28050000,
            2030: 2.95250000,
            2031: 2.65720500,
            2032: 2.39148450,
            2033: 2.15233605,
            2034: 1.93710245,
            2035: 1.74339220,
            2036: 1.56905298,
            2037: 1.41214768,
            2038: 1.27093291,
            2039: 1.14383962,
            2040: 1.02945566,
        }

        dict_result = calculate_carbon_law_future_emissions(5, 2025, 0.10, 2040)

        # Round both dictionaries to 4 decimal places and compare
        dict_result_rounded = {k: round(v, 4) for k, v in dict_result.items()}
        dict_expected_rounded = {k: round(v, 4) for k, v in dict_expected.items()}

        self.assertEqual(dict_result_rounded, dict_expected_rounded)

    def test_sum_carbon_law_total_future_emissions(self):
        """Test that calculate_carbon_law_total_future_emissions returns correct data."""
        value_expected = 40.73494905

        dict_input = {
            2025: 5,
            2026: 4.50000000,
            2027: 4.05000000,
            2028: 3.64500000,
            2029: 3.28050000,
            2030: 2.95250000,
            2031: 2.65720500,
            2032: 2.39148450,
            2033: 2.15233605,
            2034: 1.93710245,
            2035: 1.74339220,
            2036: 1.56905298,
            2037: 1.41214768,
            2038: 1.27093291,
            2039: 1.14383962,
            2040: 1.02945566,
        }
        value_result = sum_carbon_law_total_future_emissions(dict_input)

        self.assertEqual(value_result, value_expected)

    def test_carbon_law_calculations(self):
        """Test that carbon_law_calculations returns correct data."""
        expected_value = 40.7349

        input_df = pd.DataFrame(
            {
                "Kommun": ["Ale"],
                2021: [1],
                2022: [2],
                "approximatedHistorical": [{2023: 4, 2024: 3, 2025: 5}],
            }
        )

        df_result = carbon_law_calculations(input_df, 2025, 2040, 0.10)

        # Get the totalCarbonLawPath value for the row where Kommun equals "Ale"
        ale_result = df_result[df_result["Kommun"] == "Ale"]["totalCarbonLawPath"].iloc[
            0
        ]

        self.assertEqual(round(ale_result, 4), expected_value)


if __name__ == "__main__":
    unittest.main()
