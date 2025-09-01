import numpy as np
import pandas as pd
import statsmodels.api as sm


def extract_year_columns(input_df):
    """
    Extract and sort year columns from the input dataframe.

    Parameters:
    - input_df (pandas.DataFrame): The input dataframe containing municipality data.

    Returns:
    - tuple: (year_cols, years, last_data_year)
    """
    numerical_cols = input_df.select_dtypes(include=[np.number]).columns
    year_cols = [
        col for col in numerical_cols if str(col).isdigit() and len(str(col)) == 4
    ]
    year_cols = sorted(year_cols)  # Sort years in ascending order

    # Convert year column names to numerical years
    years = np.array([int(col) for col in year_cols], dtype=float)

    last_data_year = int(year_cols[-1])

    return year_cols, years, last_data_year


def generate_prediction_years(last_data_year, current_year, end_year):
    """
    Generate year ranges for approximated historical data and future trends.

    Parameters:
    - last_data_year (int): The last year with actual data
    - current_year (int): The current year to predict until
    - end_year (int): The number of years to predict into the future

    Returns:
    - tuple: (years_approximated, years_trend)
    """
    years_approximated = np.arange(last_data_year, current_year + 1, dtype=float)
    years_trend = np.arange(current_year, end_year, dtype=float)
    return years_approximated, years_trend


def create_new_columns_structure(years_approximated, years_trend, num_rows):
    """
    Create the structure for new columns that will be added to the dataframe.

    Parameters:
    - years_approximated (numpy.ndarray): Years for approximated historical data
    - years_trend (numpy.ndarray): Years for future trend predictions
    - num_rows (int): Number of rows in the original dataframe

    Returns:
    - dict: Dictionary structure for new columns
    """
    new_columns_data = {
        f"approximated_{int(year)}": [None] * num_rows for year in years_approximated
    }
    for year in years_trend:
        new_columns_data[f"trend_{int(year)}"] = [None] * num_rows
    new_columns_data["trend_coefficient"] = [None] * num_rows

    return new_columns_data


def perform_regression_and_predict(
    emissions_sorted,
    historical_years_centered,
    approximated_years_centered,
    trend_years_centered,
):
    """
    Perform quantile regression and generate predictions.

    Parameters:
    - emissions_sorted (numpy.ndarray): Sorted emissions data
    - historical_years_centered (numpy.ndarray): Historical years centered at last observed year
    - approximated_years_centered (numpy.ndarray): Approximated years centered at last observed year
    - trend_years_centered (numpy.ndarray): Trend years centered at last observed year

    Returns:
    - tuple: (preds_approximated, preds_trend, shift, trend_coefficient)
    """
    historical_design_matrix = sm.add_constant(historical_years_centered)
    approximated_design_matrix = sm.add_constant(approximated_years_centered)
    trend_design_matrix = sm.add_constant(trend_years_centered)

    res = sm.QuantReg(emissions_sorted, historical_design_matrix).fit(q=0.5)

    preds_approximated = res.predict(approximated_design_matrix)
    preds_trend = res.predict(trend_design_matrix)

    intercept_at_last = res.predict([1.0, 0.0])[0]  # x=0 == last year
    shift = emissions_sorted[-1] - intercept_at_last
    trend_coefficient = res.params[1]

    return preds_approximated, preds_trend, shift, trend_coefficient


def process_municipality_data(
    input_df, year_cols, years, years_approximated, years_trend, new_columns_data
):
    """
    Process each municipality's data to calculate trends and predictions.

    Parameters:
    - input_df (pandas.DataFrame): The input dataframe
    - year_cols (list): List of year column names
    - years (numpy.ndarray): Array of years
    - years_approximated (numpy.ndarray): Years for approximated data
    - years_trend (numpy.ndarray): Years for trend predictions
    - new_columns_data (dict): Dictionary to store new column data
    """
    for idx in range(len(input_df)):
        emissions = np.array(
            [input_df.iloc[idx][col] for col in year_cols], dtype=float
        )

        order = np.argsort(years)
        years_sorted, emissions_sorted = years[order], emissions[order]

        # Center years at the last observed year to improve stability of following regression
        # Regression models work better with smaller numbers closer to zero and
        # all time series are aligned to the same reference point
        historical_years_centered = years_sorted - years_sorted[-1]
        approximated_years_centered = years_approximated - years_sorted[-1]
        trend_years_centered = years_trend - years_sorted[-1]

        preds_approximated, preds_trend, shift, trend_coefficient = (
            perform_regression_and_predict(
                emissions_sorted,
                historical_years_centered,
                approximated_years_centered,
                trend_years_centered,
            )
        )

        # Store approximated historical data
        for i, year in enumerate(years_approximated):
            column_name = f"approximated_{int(year)}"
            new_columns_data[column_name][idx] = preds_approximated[i] + shift

        # Store trend data
        for i, year in enumerate(years_trend):
            column_name = f"trend_{int(year)}"
            new_columns_data[column_name][idx] = preds_trend[i] + shift

        new_columns_data["trend_coefficient"][idx] = trend_coefficient


def calculate_trend(input_df, current_year, end_year):
    """
    LAD (median/quantile) regression, with years centered at the last
    observed year for numerical stability. Returns predictions anchored
    to the last observed emission value.

    Parameters:
    - input_df (pandas.DataFrame): The input dataframe containing municipality data.
    - current_year (int): The current year to predict until.
    - end_year (int): The year to predict until.

    Returns:
    - input_df (pandas.DataFrame): DataFrame with added trend coefficients, approximated data
                                   until current year and future predictions.
    """
    # Extract year columns and data
    year_cols, years, last_data_year = extract_year_columns(input_df)

    # Generate prediction year ranges
    years_approximated, years_trend = generate_prediction_years(
        last_data_year, current_year, end_year
    )

    # Create structure for new columns
    new_columns_data = create_new_columns_structure(
        years_approximated, years_trend, len(input_df)
    )

    # Process each municipality's data
    process_municipality_data(
        input_df, year_cols, years, years_approximated, years_trend, new_columns_data
    )

    # Create new columns DataFrame and concatenate with original
    new_columns_df = pd.DataFrame(new_columns_data)

    return pd.concat([input_df, new_columns_df], axis=1)
