from pathlib import Path

import unittest  # noqa
import json  # noqa
import functools  # noqa
from unittest.mock import patch  # noqa
import pandas as pd  # noqa
from sector_emissions import (
    create_sector_emissions_dict,
    extract_sector_data,
    generate_sector_emissions_file,
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
        self._assert_municipality_names(result, ["Ale", "Alingsås"])

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
        self.assertIsNone(self._get_municipality_data(result, "Ale")["sectors"]["2020"]["Industri"])

    def test_generate_sector_emissions_file(self):
        """Test the generation of sector emissions JSON file with mocked data."""
        output_file = Path("test-sector-emissions.json")
        mock_df = pd.DataFrame(
            {
                "Kommun": ["Ale"],
                "2020_Transport": [56224.71],
                "2020_Industri": [72722.13],
            }
        )

        with patch("sector_emissions.get_smhi_data", return_value=mock_df), patch(
            "sector_emissions.extract_sector_data", return_value=mock_df
        ):
            generate_sector_emissions_file(
                extract_sector_data,
                functools.partial(create_sector_emissions_dict, name_column="Kommun"),
                str(output_file)
            )
            self._verify_generated_file(output_file)
            output_file.unlink()

    def test_karlshamn_jordbruk_2023_integration(self):
        """Integration test to verify Karlshamn's jordbruk sector value for 2023."""
        # This test runs the actual functions without mocking to verify real data
        df_raw = get_smhi_data()
        df_sectors = extract_sector_data(df_raw)

        # Create the sector emissions dictionary with 2 decimal places
        result = create_sector_emissions_dict(df_sectors, name_column="Kommun", num_decimals=2)

        karlshamn_data = self._get_municipality_data(result, "Karlshamn")
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

    def _verify_generated_file(self, output_file):
        """Verify the generated file exists and contains correct data."""
        self.assertTrue(output_file.exists())
        with open(output_file, "r", encoding="utf8") as file:
            data = json.load(file)
        self.assertEqual(len(data), 1)
        self._assert_municipality_names(data, ["Ale"])
        self._assert_sector_value(data, "Ale", ("2020", "Transport"), expected_value=56224.71)
        self._assert_sector_value(data, "Ale", ("2020", "Industri"), expected_value=72722.13)

    def _get_municipality_data(self, result, municipality_name):
        """Get municipality data from result list by name."""
        return next(
            (municipality for municipality in result if municipality["name"] == municipality_name),
            None,
        )

    def _assert_municipality_names(self, result, expected_names):
        """Assert that result contains municipalities with expected names."""
        for i, expected_name in enumerate(expected_names):
            self.assertEqual(result[i]["name"], expected_name)

    def _assert_sector_value(self, result, municipality_name, year_sector_pair, *, expected_value):
        """Assert that a municipality's sector value matches expected value.
        
        Args:
            result: List of municipality data dictionaries
            municipality_name: Name of the municipality to check
            year_sector_pair: Tuple of (year, sector) to check
            expected_value: Expected value for the sector
        """
        year, sector = year_sector_pair
        municipality_data = self._get_municipality_data(result, municipality_name)
        self.assertIsNotNone(municipality_data, f"Municipality '{municipality_name}' not found")
        self.assertEqual(municipality_data["sectors"][year][sector], expected_value)


if __name__ == "__main__":
    unittest.main()
