# -*- coding: utf-8 -*-

import argparse
import json
from typing import Any, Dict, List

import pandas as pd

from facts.coatOfArms.coat_of_arms import get_region_coat_of_arms_from_csv
from facts.political.political_rule import get_political_rule_regions
from kpis.emissions.regional_emissions import regional_emission_calculations
from kpis.cars.electric_vehicle_per_charge_points import get_electric_vehicle_per_charge_points

def create_regional_dataframe() -> pd.DataFrame:
    """Create a comprehensive climate dataframe by merging multiple data sources"""

    regions_df = regional_emission_calculations()
    print("1. Regional climate data and calculations added")

    evcp_source_path = "kpis/cars/sources/powercircle_regional_data_dec_2025.csv"
    evpc_df = get_electric_vehicle_per_charge_points("Län", evcp_source_path)
    regions_df = regions_df.merge(evpc_df, on="Län", how="left")
    print("2. CPEV for December 2023 added")

    regions_df["coatOfArms"] = regions_df["Län"].apply(get_region_coat_of_arms_from_csv)
    print("3. Coat of arms added")

    political_rule_df = get_political_rule_regions()
    regions_df = regions_df.merge(political_rule_df, on="Län", how="left")
    print("4. Political rule added")

    return regions_df


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
        "region": row["Län"],
        "logoUrl": row["coatOfArms"],
        "emissions": {str(year): row[year] for year in historical_columns},
        "total_trend": row["total_trend"],
        "totalCarbonLaw": row["totalCarbonLawPath"],
        "approximatedHistoricalEmission": {
            year.replace("approximated_", ""): row[year]
            for year in approximated_columns
        },
        "trend": {year.replace("trend_", ""): row[year] for year in trend_columns},
        "emissionsSlope": row["trend_emissions_slope"],
        "historicalEmissionChangePercent": row["historicalEmissionChangePercent"],
        "meetsParis": row["total_trend"]/row["totalCarbonLawPath"] < 1,
        "municipalities": row["municipalities"],
        "politicalRule": row["Rule"],
        "politicalRSO": row["RSO"],
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
        if "trend_" in str(col) and "coefficient" not in str(col) and "slope" not in str(col)
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
    parser = argparse.ArgumentParser(description="Climate data calculations")
    parser.add_argument(
        "-o",
        "--outfile",
        default="output/regional-data.json",
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

    df = create_regional_dataframe()

    temp = df_to_dict(df, args.num_decimals)

    output_file = args.outfile

    with open(output_file, "w", encoding="utf8") as json_file:
        # save dataframe as json file
        json.dump(temp, json_file, ensure_ascii=False, default=str)

    print("Regional data JSON file created and saved")
