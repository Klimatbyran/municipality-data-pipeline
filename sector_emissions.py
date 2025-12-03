# -*- coding: utf-8 -*-
from typing import Dict, List
import json
import pandas as pd

from kpis.emissions.historical_data_calculations import get_smhi_data
from kpis.emissions.cement_deductions import CEMENT_DEDUCTION_VALUES


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


def deduct_cement_from_industry(
    input_df: pd.DataFrame, cement_deduction: Dict[str, Dict[int, float]] = CEMENT_DEDUCTION_VALUES
) -> pd.DataFrame:
    """
    Deduct cement emissions from the industry sector for specified municipalities and years.

    This operates on the sector-structured dataframe produced by `extract_sector_data`,
    where industry emissions are stored in columns named like '<year>_Industri'.
    """

    # Deduct cement from industry sector for the given municipalities/years
    for municipality, years in cement_deduction.items():
        if municipality not in input_df["Kommun"].values:
            continue

        for year, value in years.items():
            col_name = f"{year}_Industri"
            if col_name in input_df.columns:
                mask = input_df["Kommun"] == municipality
                # Only subtract where we have a numeric value
                input_df.loc[mask, col_name] = input_df.loc[mask, col_name].astype(float) - value

    return input_df


def create_sector_emissions_dict(
    input_df: pd.DataFrame, num_decimals: int = 2
) -> List[Dict]:
    """Create a list of dictionaries containing sector emissions data for each municipality.

    Args:
        df: DataFrame containing sector emissions data
        num_decimals: Number of decimal places to round to (default: 2)

    Returns:
        List of dictionaries with municipality sector emissions data
    """
    result = []

    for _, row in input_df.iterrows():
        municipality_data = {"name": row["Kommun"], "sectors": {}}

        # Get all columns that contain sector data (they have '_' in their name)
        sector_columns = [col for col in row.index if "_" in str(col)]

        for col in sector_columns:
            # Split column name to get year and sector
            year, sector = col.split("_")
            if year not in municipality_data["sectors"]:
                municipality_data["sectors"][year] = {}

            # Round the value to specified decimals
            value = round(float(row[col]), num_decimals) if pd.notna(row[col]) else None
            municipality_data["sectors"][year][sector] = value

        # Sort sectors alphabetically for each year
        for year in municipality_data["sectors"]:
            municipality_data["sectors"][year] = dict(
                sorted(municipality_data["sectors"][year].items())
            )

        result.append(municipality_data)

    return result


def generate_sector_emissions_file(
    output_file: str = "output/sector-emissions.json", num_decimals: int = 2
) -> None:
    """Generate a JSON file containing sector emissions data for all municipalities.

    Args:
        output_file: path to output JSON file
        num_decimals: number of decimal places to round to
    """
    df_raw = get_smhi_data()

    df_sectors = extract_sector_data(df_raw)

    # Deduct cement emissions from industry sector in the sector data
    df_sectors = deduct_cement_from_industry(df_sectors)

    sector_data = create_sector_emissions_dict(df_sectors, num_decimals)

    with open(output_file, "w", encoding="utf8") as json_file:
        json.dump(sector_data, json_file, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    generate_sector_emissions_file()
