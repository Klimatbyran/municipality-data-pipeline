# pylint: disable=invalid-name
# -*- coding: utf-8 -*-

from datetime import datetime

import pandas as pd

from kpis.emissions.trend_calculations import calculate_trend
from kpis.emissions.carbon_law_calculations import calculate_carbon_law_total
from kpis.emissions.emission_data_calculations import (
    calculate_historical_change_percent,
    calculate_meets_paris_goal,
)


CURRENT_YEAR = datetime.now().year  # current year
END_YEAR = 2050

CARBON_LAW_REDUCTION_RATE = 0.1172

# European country codes (excluding EUA which is EU aggregate)
EUROPEAN_COUNTRIES = [
    "AT",  # Austria
    "BE",  # Belgium
    "BG",  # Bulgaria
    "CH",  # Switzerland
    "CY",  # Cyprus
    "CZ",  # Czechia
    "DE",  # Germany
    "DK",  # Denmark
    "EE",  # Estonia
    "ES",  # Spain
    "FI",  # Finland
    "FR",  # France
    "GR",  # Greece
    "HR",  # Croatia
    "HU",  # Hungary
    "IE",  # Ireland
    "IS",  # Iceland
    "IT",  # Italy
    "LT",  # Lithuania
    "LU",  # Luxembourg
    "LV",  # Latvia
    "MT",  # Malta
    "NL",  # Netherlands
    "NO",  # Norway
    "PL",  # Poland
    "PT",  # Portugal
    "RO",  # Romania
    "SE",  # Sweden
    "SI",  # Slovenia
    "SK",  # Slovakia
]

PATH_UNFCCC = "kpis/emissions/sources/UNFCCC_v28.csv"


def get_n_prep_european_data_from_unfccc():
    """
    Retrieves and prepares European CO2e emission data from UNFCCC CSV file.
    Excludes LULUCF (Land Use, Land-Use Change and Forestry) and biogenic emissions.

    Returns:
        pandas.DataFrame: The cleaned dataframe with European emissions data by country and year.
    """
    # Read the UNFCCC CSV file
    df_raw = pd.read_csv(PATH_UNFCCC)

    # Filter for:
    # 1. European countries
    # 2. "All greenhouse gases - (CO2 equivalent)" pollutant
    # 3. Get totals excluding LULUCF (Sectors/Totals_excl already excludes LULUCF)
    # Note: Biogenic emissions (1.D.3) are typically reported separately and 
    # are not included in Sectors/Totals_excl, so we don't need to subtract them
    
    # Get totals excluding LULUCF (Sectors/Totals_excl)
    df_filtered = df_raw[
        (df_raw["Country_code"].isin(EUROPEAN_COUNTRIES))
        & (df_raw["Pollutant_name"] == "All greenhouse gases - (CO2 equivalent)")
        & (df_raw["Sector_code"] == "Sectors/Totals_excl")
        & (df_raw["emissions"].notna())
    ].copy()

    # Convert emissions to numeric
    df_filtered["emissions"] = pd.to_numeric(df_filtered["emissions"], errors="coerce")
    df_filtered = df_filtered[df_filtered["emissions"].notna()]
    
    df_merged = df_filtered
    
    # Pivot the data to have years as columns
    df_pivoted = df_merged.pivot_table(
        index=["Country_code", "Country"],
        columns="Year",
        values="emissions",
        aggfunc="sum",  # Sum in case of duplicates
    ).reset_index()

    # Rename columns to match expected format (year columns should be integers)
    df_pivoted.columns.name = None

    # Rename Country_code to Country for consistency (or keep both)
    df_pivoted = df_pivoted.rename(columns={"Country": "Land"})

    # Sort by country name
    df_pivoted = df_pivoted.sort_values(by="Land").reset_index(drop=True)

    return df_pivoted


def european_emission_calculations():
    """
    Perform emission calculations for European countries.

    Returns:
        pandas.DataFrame: The resulting dataframe with emissions data.
    """

    total_emissions_df = get_n_prep_european_data_from_unfccc()

    # Calculate the last year with data dynamically
    year_columns = [col for col in total_emissions_df.columns if str(col).isdigit()]
    last_year_with_data = max([int(col) for col in year_columns]) if year_columns else CURRENT_YEAR

    df_trend_and_approximated = calculate_trend(
        total_emissions_df, CURRENT_YEAR, END_YEAR
    )

    df_trend_and_approximated["total_trend"] = df_trend_and_approximated.apply(
        lambda row: row[
            [col for col in row.index if "trend_" in str(col)]
        ].sum(),
        axis=1,
    )

    df_historical_change_percent = calculate_historical_change_percent(
        df_trend_and_approximated, "Land", last_year_with_data
    )

    df_carbon_law = calculate_carbon_law_total(
        df_historical_change_percent,
        CURRENT_YEAR,
        END_YEAR,
        CARBON_LAW_REDUCTION_RATE,
    )

    df_carbon_law["meetsParisGoal"] = df_carbon_law.apply(
        lambda row: calculate_meets_paris_goal(
            row["total_trend"], row["totalCarbonLawPath"]
        ),
        axis=1,
    )

    return df_carbon_law
