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


def calculate_carbon_law_total(
    input_df,
    current_year,
    end_year,
    reduction_rate,
):
    """
    Perform all Carbon Law calculations for the given DataFrame.

    Args:
        input_df (pandas.DataFrame): DataFrame containing municipality emission data
        current_year (int): The current year
        end_year (int): End year for projections (default 2050)
        reduction_rate (float): Annual reduction rate (default 11.72% = 0.1172)

    Returns:
        pandas.DataFrame: DataFrame with all Carbon Law calculations added
    """
    # Initialize the totalCarbonLawPath column
    input_df["totalCarbonLawPath"] = 0.0

    # Calculate carbon law path and total future emissions for each municipality
    for i in range(len(input_df)):
        # Get the latest emission value
        latest_emission = get_latest_emission_value(input_df.iloc[i], current_year)

        # Calculate the carbon law path
        df_carbon_law_future = calculate_carbon_law_future_emissions(
            latest_emission, current_year, reduction_rate, end_year
        )

        # Sum the total future emissions
        input_df.loc[i, "totalCarbonLawPath"] = sum_carbon_law_total_future_emissions(
            df_carbon_law_future
        )

    return input_df
