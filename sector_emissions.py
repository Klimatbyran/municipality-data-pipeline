# -*- coding: utf-8 -*-
from typing import Callable, Dict, List
import argparse
import functools
import json
import pandas as pd

from kpis.emissions.historical_data_calculations import get_smhi_data


def extract_sector_data(input_df):
    """
    Extracts sector emissions.

    Args:
        df (pandas.DataFrame): The input DataFrame containing sector data.

    Returns:
        pandas.DataFrame: A DataFrame containing the extracted sector data.
    """

    df_sectors = pd.DataFrame()
    sectors = set(input_df["Huvudsektor"])
    sectors -= {"Alla"}
    first_sector = list(sectors)[0]

    for sector in sectors:
        df_sector = input_df[
            (input_df["Huvudsektor"] == sector)
            & (input_df["Undersektor"] == "Alla")
            & (input_df["Län"] != "Alla")
            & (input_df["Kommun"] != "Alla")
        ]
        df_sector.reset_index(drop=True)

        first_row = df_sector.iloc[0]
        df_sector_copy = df_sector.copy()

        # Iterate over the columns of the DataFrame within the current sector
        for col in df_sector_copy.columns[4:]:
            # Rename each column by concatenating the year with the 'Huvudsektor' value
            new_col_name = f"{col}_{first_row['Huvudsektor']}"
            df_sector_copy.rename(columns={col: new_col_name}, inplace=True)

        # Drop unnecessary columns
        df_sector_copy = df_sector_copy.drop(
            columns=["Huvudsektor", "Undersektor", "Län"]
        )

        # Merge df_sector_copy with df_sectors
        if sector == first_sector:  # edge case for first sector
            df_sectors = df_sector_copy
        else:
            df_sectors = df_sectors.merge(df_sector_copy, on="Kommun", how="left")

    return df_sectors


def extract_regional_sector_data(input_df):
    """
    Extracts regional sector emissions.

    Args:
        df (pandas.DataFrame): The input DataFrame containing sector data.

    Returns:
        pandas.DataFrame: A DataFrame containing the extracted regional sector data.
    """

    df_sectors = pd.DataFrame()
    sectors = set(input_df["Huvudsektor"])
    sectors -= {"Alla"}
    first_sector = list(sectors)[0]

    for sector in sectors:
        df_sector = input_df[
            (input_df["Huvudsektor"] == sector)
            & (input_df["Undersektor"] == "Alla")
            & (input_df["Län"] != "Alla")
            & (input_df["Kommun"] == "Alla")
        ]
        df_sector.reset_index(drop=True)

        first_row = df_sector.iloc[0]
        df_sector_copy = df_sector.copy()

        # Iterate over the columns of the DataFrame within the current sector
        for col in df_sector_copy.columns[4:]:
            # Rename each column by concatenating the year with the 'Huvudsektor' value
            new_col_name = f"{col}_{first_row['Huvudsektor']}"
            df_sector_copy.rename(columns={col: new_col_name}, inplace=True)

        # Drop unnecessary columns
        df_sector_copy = df_sector_copy.drop(
            columns=["Huvudsektor", "Undersektor", "Kommun"]
        )

        # Merge df_sector_copy with df_sectors
        if sector == first_sector:  # edge case for first sector
            df_sectors = df_sector_copy
        else:
            df_sectors = df_sectors.merge(df_sector_copy, on="Län", how="left")

    return df_sectors


def extract_national_sector_data(input_df):
    """
    Extracts national sector emissions.

    Args:
        df (pandas.DataFrame): The input DataFrame containing sector data.

    Returns:
        pandas.DataFrame: A DataFrame containing the extracted national sector data.
    """

    df_sectors = pd.DataFrame()
    sectors = set(input_df["Huvudsektor"])
    sectors -= {"Alla"}
    first_sector = list(sectors)[0]

    for sector in sectors:
        df_sector = input_df[
            (input_df["Huvudsektor"] == sector)
            & (input_df["Undersektor"] == "Alla")
            & (input_df["Län"] == "Alla")
            & (input_df["Kommun"] == "Alla")
        ]
        df_sector.reset_index(drop=True)

        first_row = df_sector.iloc[0]
        df_sector_copy = df_sector.copy()

        # Iterate over the columns of the DataFrame within the current sector
        for col in df_sector_copy.columns[4:]:
            # Rename each column by concatenating the year with the 'Huvudsektor' value
            new_col_name = f"{col}_{first_row['Huvudsektor']}"
            df_sector_copy.rename(columns={col: new_col_name}, inplace=True)

        # Drop unnecessary columns
        df_sector_copy = df_sector_copy.drop(
            columns=["Huvudsektor", "Undersektor", "Län", "Kommun"]
        )

        # Add Land column
        df_sector_copy["Land"] = "Sverige"

        # Merge df_sector_copy with df_sectors
        if sector == first_sector:  # edge case for first sector
            df_sectors = df_sector_copy
        else:
            df_sectors = df_sectors.merge(df_sector_copy, on="Land", how="left")

    return df_sectors


def create_sector_emissions_dict(
    input_df: pd.DataFrame, name_column: str, num_decimals: int = 2
) -> List[Dict]:
    """Create a list of dictionaries containing sector emissions data.

    Args:
        input_df: DataFrame containing sector emissions data
        name_column: Column name to use for the "name" field (e.g., "Kommun", "Län", "Land")
        num_decimals: Number of decimal places to round to (default: 2)

    Returns:
        List of dictionaries with sector emissions data
    """
    result = []

    for _, row in input_df.iterrows():
        data = {"name": row[name_column], "sectors": {}}

        # Get all columns that contain sector data (they have '_' in their name)
        sector_columns = [col for col in row.index if "_" in str(col)]

        for col in sector_columns:
            # Split column name to get year and sector
            year, sector = col.split("_")
            if year not in data["sectors"]:
                data["sectors"][year] = {}

            # Round the value to specified decimals
            value = round(float(row[col]), num_decimals) if pd.notna(row[col]) else None
            data["sectors"][year][sector] = value

        # Sort sectors alphabetically for each year
        for year in data["sectors"]:
            data["sectors"][year] = dict(
                sorted(data["sectors"][year].items())
            )

        result.append(data)

    return result


def generate_sector_emissions_file(
    extract_func: Callable[[pd.DataFrame], pd.DataFrame],
    create_func: Callable[[pd.DataFrame], List[Dict]],
    output_file: str,
    num_decimals: int = 2
    ) -> None:
    """Generate a JSON file containing sector emissions data.

    Args:
        output_file: path to output JSON file
        num_decimals: number of decimal places to round to
    """
    df_raw = get_smhi_data()

    df_sectors = extract_func(df_raw)

    sector_data = create_func(df_sectors, num_decimals)

    with open(output_file, "w", encoding="utf8") as json_file:
        json.dump(sector_data, json_file, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate sector emissions data")
    parser.add_argument(
        "--regions",
        action="store_true",
        help="Generate regional sector emissions data instead of municipal",
    )
    parser.add_argument(
        "--national",
        action="store_true",
        help="Generate national sector emissions data instead of municipal",
    )
    parser.add_argument(
        "-o",
        "--outfile",
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

    if args.national:
        output_path = args.outfile or "output/national-sector-emissions.json"
        generate_sector_emissions_file(
            extract_national_sector_data,
            functools.partial(create_sector_emissions_dict, name_column="Land"),
            output_path,
            args.num_decimals
        )
        print("National sector emissions JSON file created and saved")
    elif args.regions:
        output_path = args.outfile or "output/region-sector-emissions.json"
        generate_sector_emissions_file(
            extract_regional_sector_data,
            functools.partial(create_sector_emissions_dict, name_column="Län"),
            output_path,
            args.num_decimals
        )
        print("Regional sector emissions JSON file created and saved")
    else:
        output_path = args.outfile or "output/municipality-sector-emissions.json"
        generate_sector_emissions_file(
            extract_sector_data,
            functools.partial(create_sector_emissions_dict, name_column="Kommun"),
            output_path,
            args.num_decimals
        )
        print("Sector emissions JSON file created and saved")
