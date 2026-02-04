# -*- coding: utf-8 -*-

import argparse
import json
from typing import Any, Dict, List

import pandas as pd
import requests

from facts.coatOfArms.coat_of_arms import get_coat_of_arms
from kpis.emissions.european_emissions import european_emission_calculations


def create_european_dataframe() -> pd.DataFrame:
    """Create a comprehensive European climate dataframe by merging multiple data sources"""

    european_df = european_emission_calculations()
    print("1. European climate data and calculations added")

    def get_coat_of_arms_safe(country_name):
        """Safely get coat of arms, returning None on error."""
        try:
            return get_coat_of_arms(country_name)
        except (requests.exceptions.RequestException, ValueError, KeyError) as e:
            print(f"Warning: Could not fetch coat of arms for {country_name}: {e}")
            return None

    european_df["coatOfArms"] = european_df["Land"].apply(get_coat_of_arms_safe)
    print("2. Coat of arms added")

    return european_df


def series_to_dict(
    row: pd.Series,
    historical_columns: List[Any],
    approximated_columns: List[Any],
    trend_columns: List[Any],
) -> Dict:
    """
    Transforms a pandas Series into a dictionary.

    Args:
    row: The pandas Series to transform.

    Returns:
    A dictionary with the transformed data.
    """

    return {
        "country": row["Land"],
        "logoUrl": row["coatOfArms"],
        "emissions": {str(year): row[year] for year in historical_columns},
        "totalTrend": row["total_trend"],
        "totalCarbonLaw": row["totalCarbonLawPath"],
        "approximatedHistoricalEmission": {
            year.replace("approximated_", ""): row[year]
            for year in approximated_columns
        },
        "trend": {year.replace("trend_", ""): row[year] for year in trend_columns},
        "emissionsSlope": row["trend_emissions_slope"],
        "historicalEmissionChangePercent": row["historicalEmissionChangePercent"],
        "meetsParis": row["total_trend"] / row["totalCarbonLawPath"] < 1,
    }


def df_to_dict(input_df: pd.DataFrame, num_decimals: int) -> dict:
    """Convert dataframe to list of dictionaries with optional decimal rounding."""
    historical_columns = [col for col in input_df.columns if str(col).isdigit()]
    approximated_columns = [
        col for col in input_df.columns if "approximated_" in str(col)
    ]
    trend_columns = [
        col
        for col in input_df.columns
        if "trend_" in str(col)
        and "coefficient" not in str(col)
        and "slope" not in str(col)
    ]

    rounded_df = input_df.round(num_decimals)

    return [
        series_to_dict(
            rounded_df.iloc[i],
            historical_columns,
            approximated_columns,
            trend_columns,
        )
        for i in range(len(input_df))
    ]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="European countries climate data calculations"
    )
    parser.add_argument(
        "-o",
        "--outfile",
        default="output/european-data.json",
        type=str,
        help="Output filename (JSON formatted)",
    )
    parser.add_argument(
        "-n",
        "--num_decimals",
        default=2,
        type=int,
        help="Number of decimals to round to",
    )

    args = parser.parse_args()

    df = create_european_dataframe()

    temp = df_to_dict(df, args.num_decimals)

    output_file = args.outfile

    with open(output_file, "w", encoding="utf8") as json_file:
        # save dataframe as json file
        json.dump(temp, json_file, ensure_ascii=False, default=str)

    print("European data JSON file created and saved")
