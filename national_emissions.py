# -*- coding: utf-8 -*-
"""
National and regional emissions data processor for Sweden.

This module fetches emission data from SMHI and organizes it into
structured JSON formats with emissions per year, sectors, and subsectors
for both national and regional (län) levels.
"""

from typing import Dict
import json
import pandas as pd

from kpis.emissions.historical_data_calculations import get_smhi_data


def extract_national_total_emissions(input_df: pd.DataFrame) -> Dict:
    """
    Extract national total emissions data across all years.

    Args:
        input_df: DataFrame containing SMHI emissions data

    Returns:
        Dictionary with total national emissions by year
    """
    # Filter for national total emissions (all sectors, all subsectors)
    df_national_total = input_df[
        (input_df["Huvudsektor"] == "Alla")
        & (input_df["Undersektor"] == "Alla")
        & (input_df["Län"] == "Alla")
        & (input_df["Kommun"] == "Alla")
    ]

    if df_national_total.empty:
        return {}

    # Get the first (and should be only) row
    row = df_national_total.iloc[0]

    total_emissions = {
        str(col): round(float(row[col]), 2)
        for col in df_national_total.columns[4:]
        if pd.notna(row[col])
    }
    return total_emissions


def extract_national_sector_emissions(input_df: pd.DataFrame) -> Dict:
    """
    Extract national emissions data by main sectors.

    Args:
        input_df: DataFrame containing SMHI emissions data

    Returns:
        Dictionary with emissions by year and sector
    """
    # Get all main sectors (excluding "Alla")
    sectors = set(input_df["Huvudsektor"]) - {"Alla"}

    sector_emissions = {}

    for sector in sectors:
        # Filter for this sector at national level (all subsectors)
        df_sector = input_df[
            (input_df["Huvudsektor"] == sector)
            & (input_df["Undersektor"] == "Alla")
            & (input_df["Län"] == "Alla")
            & (input_df["Kommun"] == "Alla")
        ]

        if not df_sector.empty:
            row = df_sector.iloc[0]

            # Extract year data for this sector
            for col in df_sector.columns[4:]:
                if pd.notna(row[col]):
                    year = str(col)
                    if year not in sector_emissions:
                        sector_emissions[year] = {}
                    sector_emissions[year][sector] = round(float(row[col]), 2)

    return sector_emissions


def extract_national_subsector_emissions(input_df: pd.DataFrame) -> Dict:
    """
    Extract national emissions data by subsectors.
    
    Args:
        input_df: DataFrame containing SMHI emissions data
        
    Returns:
        Dictionary with emissions by year, sector, and subsector
    """
    sectors = set(input_df["Huvudsektor"]) - {"Alla"}
    subsector_emissions = {}

    for sector in sectors:
        subsectors = set(input_df[input_df["Huvudsektor"] == sector]["Undersektor"]) - {"Alla"}
        for subsector in subsectors:
            _process_subsector_data(input_df, sector, subsector, subsector_emissions)

    return subsector_emissions


def _process_subsector_data(input_df: pd.DataFrame, sector: str, subsector: str,
                           subsector_emissions: Dict) -> None:
    """Process emissions data for a specific subsector."""
    df_subsector = input_df[
        (input_df["Huvudsektor"] == sector)
        & (input_df["Undersektor"] == subsector)
        & (input_df["Län"] == "Alla")
        & (input_df["Kommun"] == "Alla")
    ]

    if df_subsector.empty:
        return

    row = df_subsector.iloc[0]
    for col in df_subsector.columns[4:]:
        if pd.notna(row[col]):
            year = str(col)
            if year not in subsector_emissions:
                subsector_emissions[year] = {}
            if sector not in subsector_emissions[year]:
                subsector_emissions[year][sector] = {}
            subsector_emissions[year][sector][subsector] = round(float(row[col]), 2)


def extract_regional_total_emissions(input_df: pd.DataFrame) -> Dict:
    """
    Extract regional total emissions data by län across all years.

    Args:
        input_df: DataFrame containing SMHI emissions data

    Returns:
        Dictionary with total emissions by län and year
    """
    # Filter for regional total emissions (all sectors, all subsectors, specific län)
    df_regional_total = input_df[
        (input_df["Huvudsektor"] == "Alla")
        & (input_df["Undersektor"] == "Alla")
        & (input_df["Län"] != "Alla")
        & (input_df["Kommun"] == "Alla")
    ]

    regional_emissions = {}

    for _, row in df_regional_total.iterrows():
        lan = row["Län"]
        if lan not in regional_emissions:
            regional_emissions[lan] = {}

        # Extract year data for this län
        for col in df_regional_total.columns[4:]:
            if pd.notna(row[col]):
                year = str(col)
                regional_emissions[lan][year] = round(float(row[col]), 2)

    return regional_emissions


def extract_regional_sector_emissions(input_df: pd.DataFrame) -> Dict:
    """
    Extract regional emissions data by main sectors and län.

    Args:
        input_df: DataFrame containing SMHI emissions data

    Returns:
        Dictionary with emissions by län, year, and sector
    """
    # Get all main sectors (excluding "Alla") and län
    sectors = set(input_df["Huvudsektor"]) - {"Alla"}
    lans = set(input_df["Län"]) - {"Alla"}

    regional_sector_emissions = {}

    for lan in lans:
        regional_sector_emissions[lan] = {}
        
        for sector in sectors:
            # Filter for this sector and län (all subsectors)
            df_sector = input_df[
                (input_df["Huvudsektor"] == sector)
                & (input_df["Undersektor"] == "Alla")
                & (input_df["Län"] == lan)
                & (input_df["Kommun"] == "Alla")
            ]

            if not df_sector.empty:
                row = df_sector.iloc[0]

                # Extract year data for this sector and län
                for col in df_sector.columns[4:]:
                    if pd.notna(row[col]):
                        year = str(col)
                        if year not in regional_sector_emissions[lan]:
                            regional_sector_emissions[lan][year] = {}
                        regional_sector_emissions[lan][year][sector] = round(float(row[col]), 2)

    return regional_sector_emissions


def extract_regional_subsector_emissions(input_df: pd.DataFrame) -> Dict:
    """
    Extract regional emissions data by subsectors and län.
    
    Args:
        input_df: DataFrame containing SMHI emissions data
        
    Returns:
        Dictionary with emissions by län, year, sector, and subsector
    """
    sectors = set(input_df["Huvudsektor"]) - {"Alla"}
    lans = set(input_df["Län"]) - {"Alla"}
    
    regional_subsector_emissions = {}

    for lan in lans:
        regional_subsector_emissions[lan] = {}
        
        for sector in sectors:
            subsectors = set(input_df[input_df["Huvudsektor"] == sector]["Undersektor"]) - {"Alla"}
            for subsector in subsectors:
                _process_regional_subsector_data(input_df, lan, sector, subsector, regional_subsector_emissions)

    return regional_subsector_emissions


def _process_regional_subsector_data(input_df: pd.DataFrame, lan: str, sector: str, 
                                   subsector: str, regional_subsector_emissions: Dict) -> None:
    """Process emissions data for a specific subsector and län."""
    df_subsector = input_df[
        (input_df["Huvudsektor"] == sector)
        & (input_df["Undersektor"] == subsector)
        & (input_df["Län"] == lan)
        & (input_df["Kommun"] == "Alla")
    ]

    if df_subsector.empty:
        return

    row = df_subsector.iloc[0]
    for col in df_subsector.columns[4:]:
        if pd.notna(row[col]):
            year = str(col)
            if year not in regional_subsector_emissions[lan]:
                regional_subsector_emissions[lan][year] = {}
            if sector not in regional_subsector_emissions[lan][year]:
                regional_subsector_emissions[lan][year][sector] = {}
            regional_subsector_emissions[lan][year][sector][subsector] = round(float(row[col]), 2)


def create_national_emissions_dict(input_df: pd.DataFrame) -> Dict:
    """
    Create a comprehensive dictionary with all national emissions data.

    Args:
        input_df: DataFrame containing SMHI emissions data

    Returns:
        Dictionary with structured national emissions data
    """
    total_emissions = extract_national_total_emissions(input_df)
    sector_emissions = extract_national_sector_emissions(input_df)
    subsector_emissions = extract_national_subsector_emissions(input_df)

    # Get all available years
    all_years = set()
    all_years.update(total_emissions.keys())
    all_years.update(sector_emissions.keys())
    all_years.update(subsector_emissions.keys())

    # Create the final structure
    national_data = {
        "country": "Sverige",
    }

    for year in sorted(all_years):
        year_data = {
            "year": int(year),
            "total_emissions": total_emissions.get(year),
            "sectors": sector_emissions.get(year, {}),
            "subsectors": subsector_emissions.get(year, {})
        }
        national_data[year] = year_data

    return national_data


def create_regional_emissions_dict(input_df: pd.DataFrame) -> Dict:
    """
    Create a comprehensive dictionary with all regional emissions data by län.

    Args:
        input_df: DataFrame containing SMHI emissions data

    Returns:
        Dictionary with structured regional emissions data by län
    """
    total_emissions = extract_regional_total_emissions(input_df)
    sector_emissions = extract_regional_sector_emissions(input_df)
    subsector_emissions = extract_regional_subsector_emissions(input_df)

    # Get all available years across all län
    all_years = set()
    for lan_data in total_emissions.values():
        all_years.update(lan_data.keys())
    for lan_data in sector_emissions.values():
        for year_data in lan_data.values():
            all_years.add(str(year_data) if isinstance(year_data, dict) else str(year_data))
    for lan_data in subsector_emissions.values():
        all_years.update(lan_data.keys())

    # Create the final structure
    regional_data = {}

    for lan in total_emissions.keys():
        regional_data[lan] = {}
        
        # Get years for this län
        lan_years = set()
        lan_years.update(total_emissions.get(lan, {}).keys())
        lan_years.update(sector_emissions.get(lan, {}).keys())
        lan_years.update(subsector_emissions.get(lan, {}).keys())

        for year in sorted(lan_years):
            year_data = {
                "year": int(year),
                "total_emissions": total_emissions.get(lan, {}).get(year),
                "sectors": sector_emissions.get(lan, {}).get(year, {}),
                "subsectors": subsector_emissions.get(lan, {}).get(year, {})
            }
            regional_data[lan][year] = year_data

    return regional_data


def generate_national_emissions_file(
    output_file: str = "output/national-emissions.json"
) -> None:
    """
    Generate a JSON file containing national emissions data for Sweden.

    Args:
        output_file: Path to output JSON file
    """
    print("Fetching SMHI national emissions data...")
    df_raw = get_smhi_data()

    print("Processing national emissions data...")
    national_data = create_national_emissions_dict(df_raw)

    print(f"Writing national emissions data to {output_file}...")
    with open(output_file, "w", encoding="utf8") as json_file:
        json.dump(national_data, json_file, ensure_ascii=False, indent=2)

    print("National emissions file generated successfully!")


def generate_regional_emissions_file(
    output_file: str = "output/regional-emissions.json"
) -> None:
    """
    Generate a JSON file containing regional emissions data for Swedish län.

    Args:
        output_file: Path to output JSON file
    """
    print("Fetching SMHI regional emissions data...")
    df_raw = get_smhi_data()

    print("Processing regional emissions data...")
    regional_data = create_regional_emissions_dict(df_raw)

    print(f"Writing regional emissions data to {output_file}...")
    with open(output_file, "w", encoding="utf8") as json_file:
        json.dump(regional_data, json_file, ensure_ascii=False, indent=2)

    print("Regional emissions file generated successfully!")


def generate_emissions_files(
    national_output: str = "output/national-emissions.json",
    regional_output: str = "output/regional-emissions.json"
) -> None:
    """
    Generate both national and regional emissions JSON files.

    Args:
        national_output: Path to national emissions output JSON file
        regional_output: Path to regional emissions output JSON file
    """
    print("Fetching SMHI emissions data...")
    df_raw = get_smhi_data()

    print("Processing national emissions data...")
    national_data = create_national_emissions_dict(df_raw)

    print("Processing regional emissions data...")
    regional_data = create_regional_emissions_dict(df_raw)

    print(f"Writing national emissions data to {national_output}...")
    with open(national_output, "w", encoding="utf8") as json_file:
        json.dump(national_data, json_file, ensure_ascii=False, indent=2)

    print(f"Writing regional emissions data to {regional_output}...")
    with open(regional_output, "w", encoding="utf8") as json_file:
        json.dump(regional_data, json_file, ensure_ascii=False, indent=2)

    print("Both national and regional emissions files generated successfully!")


if __name__ == "__main__":
    generate_emissions_files()
