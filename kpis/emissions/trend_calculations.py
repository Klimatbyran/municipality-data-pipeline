import numpy as np


def calculate_trend_coefficients(input_df, last_year_with_smhi_data):
    """
    Calculate linear trend coefficients for each municipality based on SMHI data from 2015 onwards.

    Parameters:
    - df: DataFrame containing the data for each municipality.
    - last_year_with_smhi_data: The last year for which SMHI data is available.

    Returns:
    - df: DataFrame with an additional column 'trendCoefficients' containing
          the calculated trend coefficients for each municipality.
    """

    temp = []  # temporary list that we will append to
    input_df = input_df.sort_values("Kommun", ascending=True)
    for i in range(len(input_df)):
        # NOTE: Years range can be changed
        years_range = np.arange(2015, last_year_with_smhi_data + 1)
        # Get the emissions from the years specified in the line above
        emissions_data = np.array(input_df.iloc[i][years_range], dtype=float)
        # Fit a straight line to the data defined above using least squares
        fit = np.polyfit(years_range, emissions_data, 1)
        temp.append(fit)

    input_df["trendCoefficients"] = temp

    return input_df


def calculate_trend(input_df, last_year_with_smhi_data, correct_year):
    """
    Calculate the trend line for future years up to 2050 using interpolation
    and previously calculated linear trend coefficients.

    Args:
        df (pandas.DataFrame): The input DataFrame containing the data.
        last_year_with_smhi_data (int): The last year with SMHI data available.
        correct_year (int): The correct year to start the trend line from.

    Returns:
        pandas.DataFrame: The input DataFrame with additional columns
                          for the trend line and trend emission values.
    """

    # Calculate trend line for future years up to 2050
    # This is done by interpolation using previously calculated linear trend coefficients

    # Get years between next year and 2050
    future_years = range(correct_year + 1, 2050 + 1)

    temp = []  # temporary list that we will append to
    input_df = input_df.sort_values("Kommun", ascending=True)
    for i in range(len(input_df)):
        # We'll store the future trend line for each municipality in a dictionary where the keys
        # are the years. The last recorded data point is initially added to the dict.
        last_year_with_data_dict = {
            last_year_with_smhi_data: input_df.iloc[i][last_year_with_smhi_data]
        }

        # If approximated historical values exist, overwrite trend dict to start from current year
        if correct_year > last_year_with_smhi_data:
            last_year_with_data_dict = {
                correct_year: input_df.iloc[i]["approximatedHistorical"][correct_year]
            }

        # Get the trend coefficients
        fit = input_df.iloc[i]["trendCoefficients"]

        for year in future_years:
            # Add the trend value for each year using the trend line coefficients.
            # Max function so we don't get negative values
            last_year_with_data_dict[year] = max(0, fit[0] * year + fit[1])
        temp.append(last_year_with_data_dict)

    input_df["trend"] = temp

    temp = [
        np.trapz(
            list(input_df.iloc[i]["trend"].values()),
            list(input_df.iloc[i]["trend"].keys()),
        )
        for i in range(len(input_df))
    ]
    input_df["trendEmission"] = temp

    return input_df
