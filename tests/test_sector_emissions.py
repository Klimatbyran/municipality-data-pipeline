"""Test cases for sector emissions data processing and file generation."""
import unittest
import json
import pandas as pd
from sector_emissions import (
    create_sector_emissions_dict,
    extract_national_sector_data,
    extract_regional_sector_data,
    extract_sector_data,
)
from kpis.emissions.historical_data_calculations import (
    get_smhi_data,
)


class TestSectorEmissions(unittest.TestCase):
    """Test cases for sector emissions data processing and file generation."""

    def setUp(self):
        """Set up test data that will be used in multiple tests."""
        self.input_df = pd.DataFrame(
            {
                "Kommun": ["Ale", "Alingsås"],
                "2020_Transport": [56224.7124, 54756.95],
                "2020_Industri": [72722.13, 3492.44],
                "2021_Transport": [55911.56, 54401.87],
                "2021_Industri": [79064.9, 141.82],
            }
        )

    def test_create_sector_emissions_dict(self):
        """Test the creation of sector emissions dictionary with sample data."""
        result = create_sector_emissions_dict(self.input_df, name_column="Kommun")

        self.assertEqual(len(result), 2)
        self._assert_territory_names(result, ["Ale", "Alingsås"])

        # Check Ale's 2020 data
        self._assert_sector_value(result, "Ale", ("2020", "Transport"), expected_value=56224.71)
        self._assert_sector_value(result, "Ale", ("2020", "Industri"), expected_value=72722.13)

        # Check Alingsås's 2021 data
        self._assert_sector_value(
            result, "Alingsås", ("2021", "Transport"), expected_value=54401.87
        )
        self._assert_sector_value(result, "Alingsås", ("2021", "Industri"), expected_value=141.82)

        # Test with different number of decimals
        result_3_decimals = create_sector_emissions_dict(
            self.input_df, name_column="Kommun", num_decimals=3
        )
        self._assert_sector_value(
            result_3_decimals, "Ale", ("2020", "Transport"), expected_value=56224.712
        )

    def test_create_sector_emissions_dict_with_nulls(self):
        """Test sector emissions dictionary creation with null values in input data."""
        # Test data with null values
        input_df = pd.DataFrame(
            {
                "Kommun": ["Ale"],
                "2020_Transport": [56224.712],
                "2020_Industri": [None],
            }
        )

        result = create_sector_emissions_dict(input_df, name_column="Kommun")
        self._assert_sector_value(result, "Ale", ("2020", "Transport"), expected_value=56224.71)
        self.assertIsNone(self._get_territory_data(result, "Ale")["sectors"]["2020"]["Industri"])

    def test_karlshamn_jordbruk_2023_integration(self):
        """Integration test to verify Karlshamn's jordbruk sector value for 2023."""
        # This test runs the actual functions without mocking to verify real data
        df_raw = get_smhi_data()
        df_sectors = extract_sector_data(df_raw)

        # Create the sector emissions dictionary with 2 decimal places
        result = create_sector_emissions_dict(df_sectors, name_column="Kommun", num_decimals=2)

        karlshamn_data = self._get_territory_data(result, "Karlshamn")
        # Assert that Karlshamn exists in the data
        self.assertIsNotNone(karlshamn_data)

        # Assert that 2023 data exists
        self.assertIn("2023", karlshamn_data["sectors"])

        # Assert that jordbruk sector exists for 2023
        self.assertIn("Jordbruk", karlshamn_data["sectors"]["2023"])

        # Assert the expected value
        self._assert_sector_value(
            result, "Karlshamn", ("2023", "Jordbruk"), expected_value=14786.0
        )

    def test_national_sector_emissions(self):
        """Test extraction of national sector emissions."""
        df_raw = get_smhi_data()
        df_sectors = extract_national_sector_data(df_raw)
        result = create_sector_emissions_dict(df_sectors, name_column="Land", num_decimals=2)
        self.assertEqual(len(result), 1)
        self._assert_sector_value(
            result, "Sverige", ("2023", "Jordbruk"), expected_value=6238768.44
        )

    def test_regional_sector_emissions(self):
        """Test extraction of regional sector emissions."""
        df_raw = get_smhi_data()
        df_sectors = extract_regional_sector_data(df_raw)
        result = create_sector_emissions_dict(df_sectors, name_column="Län", num_decimals=2)
        self.assertEqual(len(result), 21)
        self._assert_sector_value(
            result, "Blekinge län", ("2023", "Jordbruk"), expected_value=100263.07
        )

    def _verify_generated_file(self, output_file):
        """Verify the generated file exists and contains correct data."""
        self.assertTrue(output_file.exists())
        with open(output_file, "r", encoding="utf8") as file:
            data = json.load(file)
        self.assertEqual(len(data), 1)
        self._assert_territory_names(data, ["Ale"])
        self._assert_sector_value(data, "Ale", ("2020", "Transport"), expected_value=56224.71)
        self._assert_sector_value(data, "Ale", ("2020", "Industri"), expected_value=72722.13)

    def _get_territory_data(self, result, territory_name):
        """Get territory data from result list by name."""
        return next(
            (territory for territory in result if territory["name"] == territory_name),
            None,
        )

    def _assert_territory_names(self, result, expected_names):
        """Assert that result contains territories with expected names."""
        for i, expected_name in enumerate(expected_names):
            self.assertEqual(result[i]["name"], expected_name)

    def _assert_sector_value(self, result, territory_name, year_sector_pair, *, expected_value):
        """Assert that a territory's sector value matches expected value.
        
        Args:
            result: List of territory data dictionaries
            territory_name: Name of the territory to check
            year_sector_pair: Tuple of (year, sector) to check
            expected_value: Expected value for the sector
        """
        year, sector = year_sector_pair
        territory_data = self._get_territory_data(result, territory_name)
        self.assertIsNotNone(territory_data, f"Territory '{territory_name}' not found")
        self.assertEqual(territory_data["sectors"][year][sector], expected_value)


if __name__ == "__main__":
    unittest.main()
