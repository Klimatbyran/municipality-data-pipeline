# -*- coding: utf-8 -*-
import unittest
import pandas as pd

from kpis.emissions.historical_data_calculations import get_n_prep_national_data_from_smhi
from kpis.emissions.national_emissions import national_emission_calculations


LAST_YEAR_WITH_SMHI_DATA = 2023
CURRENT_YEAR = 2025


class TestNationalEmissions(unittest.TestCase):
    """Test fetching and calculations of national emission data"""

    def test_get_n_prep_national_data_from_smhi(self):
        """Test that the national SMHI data has the correct structure and expected year range."""
        df_result = get_n_prep_national_data_from_smhi()

        # Check that we have exactly one row (national level)
        self.assertEqual(len(df_result), 1, "National data should have exactly one row")

        # Check that Land column exists and has correct value
        self.assertTrue("Land" in df_result.columns, "Land column should exist")
        self.assertEqual(df_result["Land"].iloc[0], "Sverige", "Land should be 'Sverige'")

        # Check that categorical columns exist (they are kept in the dataframe)
        self.assertTrue("Huvudsektor" in df_result.columns, "Huvudsektor column should exist")
        self.assertTrue("Undersektor" in df_result.columns, "Undersektor column should exist")
        self.assertTrue("Län" in df_result.columns, "Län column should exist")
        self.assertTrue("Kommun" in df_result.columns, "Kommun column should exist")

        # Check that categorical columns have expected values
        self.assertEqual(df_result["Huvudsektor"].iloc[0], "Alla", "Huvudsektor should be 'Alla'")
        self.assertEqual(df_result["Undersektor"].iloc[0], "Alla", "Undersektor should be 'Alla'")
        self.assertEqual(df_result["Län"].iloc[0], "Alla", "Län should be 'Alla'")
        self.assertEqual(df_result["Kommun"].iloc[0], "Alla", "Kommun should be 'Alla'")

        # Check for expected year columns
        result_columns = [col for col in df_result.columns if str(col).isdigit()]
        expected_columns = [
            1990,
            2000,
            2005,
            2010,
            2015,
            2016,
            2017,
            2018,
            2019,
            2020,
            2021,
            2022,
            2023,
        ]

        # Check that the expected columns are in the dataframe
        self.assertEqual(
            result_columns,
            expected_columns,
            f"Expected year columns {expected_columns}, got {result_columns}",
        )

        # Each of the column values should all be greater than 0.0
        self.assertTrue(
            (df_result[expected_columns] > 0.0).all().all(),
            "All emission values should be greater than 0",
        )

    def test_national_emission_calculations(self):
        """Test that national emission calculations return the expected structure and columns."""
        df_result = national_emission_calculations()

        # Check that we have exactly one row (national level)
        self.assertEqual(len(df_result), 1, "National calculations should have exactly one row")

        # Check that Land column exists
        self.assertTrue("Land" in df_result.columns, "Land column should exist")
        self.assertEqual(df_result["Land"].iloc[0], "Sverige", "Land should be 'Sverige'")

        # Check for expected year columns
        expected_year_columns = [
          1990, 2000, 2005, 2010, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023
        ]
        missing_columns = set(expected_year_columns) - set(df_result.columns)
        self.assertEqual(
            len(missing_columns),
            0,
            f"Missing year columns: {missing_columns}",
        )

        # Check that calculated columns exist
        self.assertTrue("total_trend" in df_result.columns, "total_trend column should exist")
        self.assertTrue(
            "totalCarbonLawPath" in df_result.columns,
            "totalCarbonLawPath column should exist",
        )
        self.assertTrue(
            "historicalEmissionChangePercent" in df_result.columns,
            "historicalEmissionChangePercent column should exist",
        )
        self.assertTrue(
            "meetsParisGoal" in df_result.columns,
            "meetsParisGoal column should exist",
        )

        # Check that approximated columns exist
        approximated_columns = [
            col for col in df_result.columns if "approximated_" in str(col)
        ]
        self.assertGreater(
            len(approximated_columns),
            0,
            "Should have at least one approximated column",
        )

        # Check that trend columns exist
        trend_columns = [
            col
            for col in df_result.columns
            if "trend_" in str(col) and "coefficient" not in str(col) and "slope" not in str(col)
        ]
        self.assertGreater(len(trend_columns), 0, "Should have at least one trend column")

        # Check that total_trend is positive
        self.assertGreater(
            df_result["total_trend"].iloc[0],
            0,
            "total_trend should be positive",
        )

        # Check that totalCarbonLawPath is positive
        self.assertGreater(
            df_result["totalCarbonLawPath"].iloc[0],
            0,
            "totalCarbonLawPath should be positive",
        )

        # Check that meetsParisGoal is boolean (can be numpy bool or Python bool)
        meets_paris_value = df_result["meetsParisGoal"].iloc[0]
        # numpy.bool_ is a subclass of bool, so isinstance(..., bool) works
        self.assertTrue(
            isinstance(
              meets_paris_value, bool) or pd.api.types.is_bool_dtype(type(meets_paris_value)
            ),
            f"meetsParisGoal should be a boolean, got {type(meets_paris_value)}",
        )


if __name__ == "__main__":
    unittest.main()
