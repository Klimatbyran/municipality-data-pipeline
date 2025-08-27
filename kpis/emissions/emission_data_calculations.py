# pylint: disable=invalid-name
# -*- coding: utf-8 -*-

import numpy as np

from kpis.emissions.approximated_data_calculations import (
    calculate_approximated_historical,
)
from kpis.emissions.historical_data_calculations import get_n_prep_data_from_smhi
from kpis.emissions.trend_calculations import (
    calculate_trend_coefficients,
    calculate_trend,
)
from kpis.emissions.carbon_law_calculations import calculate_carbon_law_total


CURRENT_YEAR = 2025  # current year
LAST_YEAR_WITH_SMHI_DATA = (
    2023  # last year for which the National Emission database has data
)
END_YEAR = 2050

CARBON_LAW_REDUCTION_RATE = 0.1172

PATH_SMHI = (
    "https://nationellaemissionsdatabasen.smhi.se/api/"
    + "getexcelfile/?county=0&municipality=0&sub=GGT"
)

# ------- CEMENT CARBON EMISSIONS -------

# Sources for cement deduction (use CO2 totalt)
# Mörbylånga: https://utslappisiffror.naturvardsverket.se/sv/Sok/Anlaggningssida/?pid=1441
# Skövde: https://utslappisiffror.naturvardsverket.se/sv/Sok/Anlaggningssida/?pid=5932
# Gotland: https://utslappisiffror.naturvardsverket.se/sv/Sok/Anlaggningssida/?pid=834

CEMENT_DEDUCTION = {
    "Mörbylånga": {
        2010: 248025000 / 1000,
        2015: 255970000 / 1000,
        2016: 239538000 / 1000,
        2017: 255783000 / 1000,
        2018: 241897000 / 1000,
        2019: 65176000 / 1000,
        2020: 0,
        2021: 0,
        2022: 0,
        2023: 0,
        2024: 0,
    },
    "Skövde": {
        2010: 356965000 / 1000,
        2015: 358634000 / 1000,
        2016: 384926000 / 1000,
        2017: 407633130 / 1000,
        2018: 445630340 / 1000,
        2019: 440504330 / 1000,
        2020: 459092473 / 1000,
        2021: 439174727 / 1000,
        2022: 406856000 / 1000,
        2023: 340611000 / 1000,
        2024: 260927000 / 1000,
    },
    "Gotland": {
        2010: 1579811000 / 1000,
        2015: 1926036000 / 1000,
        2016: 1903887000 / 1000,
        2017: 1757110000 / 1000,
        2018: 1740412000 / 1000,
        2019: 1536480000 / 1000,
        2020: 1624463000 / 1000,
        2021: 1621211000 / 1000,
        2022: 1514132000 / 1000,
        2023: 1511971000 / 1000,
        2024: 1387575500 / 1000,
    },
}


def deduct_cement(df, cement_deduction):
    """
    Deducts cement emissions from the given DataFrame based on the provided cement deduction values.

    Args:
        df (pandas.DataFrame): The DataFrame containing the emission data.
        cement_deduction (dict): A dictionary specifying the cement
                                 deduction values for each municipality.

    Returns:
        pandas.DataFrame: The DataFrame with the cement emissions deducted.
    """

    df_cem = df.copy()

    # Deduct cement from given municipalities
    for i in cement_deduction.keys():
        for j in cement_deduction[i].keys():
            df_cem.loc[df_cem["Kommun"] == i, j] = (
                df_cem.loc[df_cem["Kommun"] == i, j].values - cement_deduction[i][j]
            )

    return df_cem


def calculate_historical_change_percent(df, last_year_in_range):
    """
    Calculate the historical average emission level change based on SMHI data from 2015 onwards.

    Args:
        df (pandas.DataFrame): The input DataFrame containing emission data.

    Returns:
        pandas.DataFrame: The input DataFrame with an additional column
                          'historicalEmissionChangePercent' representing
                          the historical average emission level change in percent for each row.
    """

    temp = []
    df = df.sort_values("Kommun", ascending=True)
    for i in range(len(df)):
        # Get the years we will use for the average
        years = np.arange(2015, last_year_in_range + 1)
        # Get the emissions from the years specified in the line above
        emissions = np.array(df.iloc[i][years], dtype=float)
        # Calculate diff (in percent) between each successive year
        diffs_in_percent = [
            (x - emissions[i - 1]) / emissions[i - 1] for i, x in enumerate(emissions)
        ][1:]
        # Calculate average diff
        avg_diff_in_percent = 100 * sum(diffs_in_percent) / len(diffs_in_percent)

        temp.append(avg_diff_in_percent)

    df["historicalEmissionChangePercent"] = temp

    return df


def emission_calculations(df):
    """
    Perform emission calculations based on the given dataframe.

    Parameters:
    - df (pandas.DataFrame): The input dataframe containing municipality data.

    Returns:
    - df_budget_runs_out (pandas.DataFrame): The resulting dataframe with emissions data.
    """

    df_smhi = get_n_prep_data_from_smhi(df)

    df_cem = deduct_cement(df_smhi, CEMENT_DEDUCTION)

    df_trend_coefficients = calculate_trend_coefficients(
        df_cem, LAST_YEAR_WITH_SMHI_DATA
    )

    df_approxmimated_historical_total = calculate_approximated_historical(
        df_trend_coefficients, LAST_YEAR_WITH_SMHI_DATA, CURRENT_YEAR
    )

    df_trend = calculate_trend(
        df_approxmimated_historical_total, LAST_YEAR_WITH_SMHI_DATA, CURRENT_YEAR
    )

    df_historical_change_percent = calculate_historical_change_percent(
        df_trend, LAST_YEAR_WITH_SMHI_DATA
    )

    df_carbon_law = calculate_carbon_law_total(
        df_historical_change_percent,
        CURRENT_YEAR,
        END_YEAR,
        CARBON_LAW_REDUCTION_RATE,
    )

    return df_carbon_law
