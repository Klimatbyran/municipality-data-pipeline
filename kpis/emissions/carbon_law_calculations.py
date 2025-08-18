import numpy as np


# Carbon Law reduction rate: 11.72% per year
CARBON_LAW_REDUCTION_RATE = 0.1172
# This means each year should be (1 - 0.1172) = 0.8828 of the previous year
CARBON_LAW_ANNUAL_FACTOR = 1 - CARBON_LAW_REDUCTION_RATE


def get_latest_emission_value(df_row, current_year):
    """
    Get the latest emission value for a municipality,
    either from approximated historical data or historical data.

    Args:
        df_row: A row from the DataFrame representing a municipality
        current_year (int): The current year

    Returns:
        float: The latest emission value for the municipality
    """
    # If there is approximated historical data for the current year, use that
    if (
        "approximatedHistorical" in df_row
        and df_row["approximatedHistorical"]
        and current_year in df_row["approximatedHistorical"]
    ):
        return df_row["approximatedHistorical"][current_year]

    # Otherwise, use the latest SMHI data
    return df_row[current_year]


def calculate_carbon_law_future_emissions(
    latest_emission, current_year, reduction_rate, end_year=2050
):
    """
    Calculate future emissions for each municipality following the Carbon Law
    with a specified reduction rate per year.

    Args:
        latest_emission (int): Emission value for current year
        current_year (int): The current year to start projections from
        end_year (int): End year for projections (default 2050)
        reduction_rate (float): Annual reduction rate

    Returns:
        pandas.DataFrame: DataFrame with added 'carbonLawFuture' column containing
                          dictionaries of year-emission pairs for future projections
    """
    # Create dictionary to store future emissions
    carbon_law_dict = {current_year: latest_emission}

    # Calculate emissions for each future year
    current_emission = latest_emission
    for year in range(current_year + 1, end_year + 1):
        # Apply annual reduction using reduction_rate directly
        current_emission = max(0, current_emission * (1 - reduction_rate))
        carbon_law_dict[year] = current_emission

    return carbon_law_dict


def sum_carbon_law_total_future_emissions(input_dict):
    """
    Sum the total cumulative future emissions following the Carbon Law reduction path.

    Args:
        input_dict (dict): Dict with year as key and emission as value for carbon law path

    Returns:
        Value of total emissions of carbon law path
    """
    return sum(input_dict.values())


def calculate_carbon_law_net_zero_date(
    input_df,
    current_year=2025,
    last_year_with_smhi_data=2023,
    reduction_rate=CARBON_LAW_REDUCTION_RATE,
):
    """
    Calculate when each municipality would reach net zero emissions
    following the Carbon Law reduction path.

    Args:
        df (pandas.DataFrame): DataFrame containing municipality emission data
        current_year (int): The current year
        last_year_with_smhi_data (int): Last year with recorded SMHI data
        reduction_rate (float): Annual reduction rate (default 11.72% = 0.1172)

    Returns:
        pandas.DataFrame: DataFrame with added 'carbonLawNetZeroYear' column
                         containing the year when net zero is reached (or None if never)
    """
    annual_factor = 1 - reduction_rate
    temp = []

    for i in range(len(input_df)):
        # Get the latest emission value
        latest_emission, latest_year = get_latest_emission_value(
            input_df.iloc[i], current_year, last_year_with_smhi_data
        )

        # Calculate how many years it takes to reach near zero (< 1 tonne)
        if latest_emission <= 1:  # Already at net zero
            temp.append(latest_year)
        else:
            # Calculate years needed: emission * (annual_factor)^years < 1
            # Solving: years > log(1/emission) / log(annual_factor)
            years_to_net_zero = np.log(1 / latest_emission) / np.log(annual_factor)
            net_zero_year = latest_year + int(np.ceil(years_to_net_zero))
            temp.append(net_zero_year)

    input_df["carbonLawNetZeroYear"] = temp
    return input_df


def carbon_law_calculations(
    input_df,
    current_year=2025,
    last_year_with_smhi_data=2023,
    end_year=2050,
    reduction_rate=CARBON_LAW_REDUCTION_RATE,
):
    """
    Perform all Carbon Law calculations for the given DataFrame.

    Args:
        df (pandas.DataFrame): DataFrame containing municipality emission data
        current_year (int): The current year
        last_year_with_smhi_data (int): Last year with recorded SMHI data
        end_year (int): End year for projections (default 2050)
        reduction_rate (float): Annual reduction rate (default 11.72% = 0.1172)

    Returns:
        pandas.DataFrame: DataFrame with all Carbon Law calculations added
    """
    # Calculate future emissions following Carbon Law
    df_carbon_law_future = calculate_carbon_law_future_emissions(
        input_df, current_year, last_year_with_smhi_data, end_year, reduction_rate
    )

    # Calculate total future emissions
    df_carbon_law_total = sum_carbon_law_total_future_emissions(
        df_carbon_law_future,
        current_year,
        last_year_with_smhi_data,
        end_year,
        reduction_rate,
    )

    # Calculate net zero dates
    df_carbon_law_complete = calculate_carbon_law_net_zero_date(
        df_carbon_law_total, current_year, last_year_with_smhi_data, reduction_rate
    )

    return df_carbon_law_complete
