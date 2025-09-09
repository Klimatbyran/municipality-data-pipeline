# pylint: disable=invalid-name
# -*- coding: utf-8 -*-

from datetime import datetime

import numpy as np

from kpis.emissions.cement_deductions import CEMENT_DEDUCTION_VALUES
from kpis.emissions.historical_data_calculations import get_n_prep_data_from_smhi
from kpis.emissions.trend_calculations import calculate_trend
from kpis.emissions.carbon_law_calculations import calculate_carbon_law_total


CURRENT_YEAR = datetime.now().year  # current year
LAST_YEAR_WITH_SMHI_DATA = (
    2023  # last year for which the National Emission database has data
)
END_YEAR = 2050

CARBON_LAW_REDUCTION_RATE = 0.1172

PATH_SMHI = (
    "https://nationellaemissionsdatabasen.smhi.se/api/"
    + "getexcelfile/?county=0&municipality=0&sub=GGT"
)


CEMENT_DEDUCTION = CEMENT_DEDUCTION_VALUES


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
            # Only deduct if the year column exists in the DataFrame
            if j in df_cem.columns:
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


def calculate_meets_paris_goal(total_trend, total_carbon_law_path):
    """
    Calculate if the municipality meets the Paris goal.
    """
    return total_trend <= total_carbon_law_path


def emission_calculations(df):
    """
    Perform emission calculations based on the given dataframe.

    Parameters:
    - df (pandas.DataFrame): The input dataframe containing municipality data.

    Returns:
    - (pandas.DataFrame): The resulting dataframe with emissions data.
    """

    df_smhi = get_n_prep_data_from_smhi(df)

    df_cem = deduct_cement(df_smhi, CEMENT_DEDUCTION)

    df_trend_and_approximated = calculate_trend(df_cem, CURRENT_YEAR, END_YEAR)

    df_trend_and_approximated["totalTrend"] = df_trend_and_approximated.apply(
        lambda row: row[[col for col in row.index if "trend_" in str(col)]].sum(),
        axis=1,
    )

    df_historical_change_percent = calculate_historical_change_percent(
        df_trend_and_approximated, LAST_YEAR_WITH_SMHI_DATA
    )

    df_carbon_law = calculate_carbon_law_total(
        df_historical_change_percent,
        CURRENT_YEAR,
        END_YEAR,
        CARBON_LAW_REDUCTION_RATE,
    )

    df_carbon_law["meetsParisGoal"] = df_carbon_law.apply(
        lambda row: calculate_meets_paris_goal(
            row["totalTrend"], row["totalCarbonLawPath"]
        ),
        axis=1,
    )

    return df_carbon_law
