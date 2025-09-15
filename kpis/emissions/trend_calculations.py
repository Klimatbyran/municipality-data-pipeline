import numpy as np
import pandas as pd
import statsmodels.api as sm


def extract_year_columns(input_df, cutoff_year):
    """
    Extract and sort year columns from the input dataframe. Exclude years before cutoff_year (default 2015).

    Parameters:
    - input_df (pandas.DataFrame): The input dataframe containing municipality data.

    Returns:
    - years, last_data_year (tuple: (numpy.ndarray, int)): Years and the last year with data
    """
    numerical_cols = input_df.select_dtypes(include=[np.number]).columns
    year_cols = [
        col
        for col in numerical_cols
        if str(col).isdigit() and len(str(col)) == 4 and int(col) >= cutoff_year
    ]
    year_cols = sorted(year_cols)  # Sort years in ascending order

    # Convert year column names to numerical years
    years = np.array([int(col) for col in year_cols], dtype=float)

    last_data_year = int(year_cols[-1])

    return years, last_data_year


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
    years_trend = np.arange(current_year, end_year + 1, dtype=float)
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
    new_columns_data["emission_slope"] = [None] * num_rows

    return new_columns_data


def apply_zero_floor(input_df, relevant_cols):
    """
    Cut the trend at zero.

    Parameters:
    - input_df (pandas.DataFrame): The input dataframe containing municipality data.

    Returns:
    - numpy.ndarray: Predictions for trend cut at zero
    """
    df_result = input_df.copy()

    for col in relevant_cols:
        df_result[col] = np.maximum(df_result[col], 0)

    return df_result


def perform_regression_and_predict(
    emissions,
    historical_years_centered,
    approximated_years_centered,
    trend_years_centered,
):
    """
    Perform LAD (least absolute deviations) regression and generate predictions.
    LAD equals median regression with q=0.5.
    Predictions are anchored to the last historical data point.

    Parameters:
    - emissions (numpy.ndarray): Emissions data
    - historical_years_centered (numpy.ndarray): Historical years centered at last observed year
    - approximated_years_centered (numpy.ndarray): Approximated years centered at last observed year
    - trend_years_centered (numpy.ndarray): Trend years centered at last observed year

    Returns:
    - tuple: (preds_approximated, preds_trend, shift, emission_slope)
    """
    historical_design_matrix = sm.add_constant(historical_years_centered)
    approximated_design_matrix = sm.add_constant(approximated_years_centered)
    trend_design_matrix = sm.add_constant(trend_years_centered)

    res = sm.QuantReg(emissions, historical_design_matrix).fit(q=0.5)

    # Get raw predictions from the regression
    preds_approximated_raw = res.predict(approximated_design_matrix)
    preds_trend_raw = res.predict(trend_design_matrix)

    # Calculate the predicted value at the last historical year (x=0 in centered coordinates)
    predicted_at_last_year = res.predict([1.0, 0.0])[0]

    # Calculate shift to anchor predictions to actual last historical data point
    last_historical_value = emissions[-1]
    shift = last_historical_value - predicted_at_last_year

    # Apply shift to anchor all predictions to the last historical data point
    preds_approximated = preds_approximated_raw + shift
    preds_trend = preds_trend_raw + shift

    emission_slope = res.params[1]

    return preds_approximated, preds_trend, emission_slope


def fit_regression_per_municipality(
    input_df, years, years_approximated, years_trend, new_columns_data
):
    """
    Process each municipality's data to calculate trends and predictions.

    Parameters:
    - input_df (pandas.DataFrame): The input dataframe
    - years (numpy.ndarray): Array of years
    - years_approximated (numpy.ndarray): Years for approximated data
    - years_trend (numpy.ndarray): Years for trend predictions
    - new_columns_data (dict): Dictionary to store new column data
    """
    for idx in range(len(input_df)):
        emissions = np.array([input_df.iloc[idx][col] for col in years], dtype=float)

        # Center years at the last observed year to improve stability of following regression
        # Regression models work better with smaller numbers closer to zero and
        # all time series are aligned to the same reference point
        historical_years_centered = years - years[-1]
        approximated_years_centered = years_approximated - years[-1]
        trend_years_centered = years_trend - years[-1]

        preds_approximated, preds_trend, emission_slope = (
            perform_regression_and_predict(
                emissions,
                historical_years_centered,
                approximated_years_centered,
                trend_years_centered,
            )
        )

        # Store approximated historical data (already anchored)
        for i, year in enumerate(years_approximated):
            column_name = f"approximated_{int(year)}"
            new_columns_data[column_name][idx] = preds_approximated[i]

        # Store trend data (already anchored)
        for i, year in enumerate(years_trend):
            column_name = f"trend_{int(year)}"
            new_columns_data[column_name][idx] = preds_trend[i]

        new_columns_data["emission_slope"][idx] = emission_slope


def calculate_total_trend(input_df):
    """
    Calculate the total trend for the input dataframe.

    Parameters:
    - input_df (pandas.DataFrame): The input dataframe containing municipality data.

    Returns:
    - total trend (int): Total trend for the input dataframe.
    """
    trend_columns = [col for col in input_df.columns if "trend_" in str(col)]
    trend_values = input_df[trend_columns].values
    return trend_values.sum()


def calculate_trend(input_df, current_year, end_year, cutoff_year=2015):
    """
    LAD (least absolute deviations) regression, with years centered at the last
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
    years, last_data_year = extract_year_columns(input_df, cutoff_year)

    # Generate prediction year ranges
    years_approximated, years_trend = generate_prediction_years(
        last_data_year, current_year, end_year
    )

    # Create structure for new columns
    new_columns_data = create_new_columns_structure(
        years_approximated, years_trend, len(input_df)
    )

    # Process each municipality's data
    fit_regression_per_municipality(
        input_df, years, years_approximated, years_trend, new_columns_data
    )

    # Create new columns DataFrame and concatenate with original
    new_columns_df = pd.DataFrame(new_columns_data)

    approximated_cols = [f"approximated_{int(year)}" for year in years_approximated]
    floored_approximated_df = apply_zero_floor(new_columns_df, approximated_cols)

    trend_cols = [f"trend_{int(year)}" for year in years_trend]
    floored_future_trend_df = apply_zero_floor(floored_approximated_df, trend_cols)

    return pd.concat([input_df, floored_future_trend_df], axis=1)
