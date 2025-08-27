import numpy as np
import statsmodels.api as sm


def calculate_trend(input_df, current_year):
    """
    LAD (median/quantile) regression, with years centered at the last
    observed year for numerical stability. Returns predictions anchored
    to the last observed emission value.

    Parameters:
    - input_df (pandas.DataFrame): The input dataframe containing municipality data.
    - years_future (list): The years of the future emissions data.

    Returns:
    - input_df (pandas.DataFrame): DataFrame with added trend coefficients, aprroximated data
                                   until current year and future predictions.
    """

    # Extract numerical columns (year columns) from the dataframe
    numerical_cols = input_df.select_dtypes(include=[np.number]).columns
    year_cols = [
        col for col in numerical_cols if str(col).isdigit() and len(str(col)) == 4
    ]
    year_cols = sorted(year_cols)  # Sort years in ascending order

    # Convert year column names to actual years
    years = np.array([int(col) for col in year_cols], dtype=float)

    # Generate future years from last year with data from SMHI+1 to current_year
    years_future = np.arange(numerical_cols[-1] + 1, current_year + 1, dtype=float)

    # Process each municipality row
    for idx in range(len(input_df)):
        # Extract emissions data for this municipality from year columns
        emissions = np.array(
            [input_df.iloc[idx][col] for col in year_cols], dtype=float
        )

        # Sort by year just in case
        order = np.argsort(years)
        years_sorted, emissions_sorted = years[order], emissions[order]

        # Center years at the last observed year (e.g., 2023 -> 0)
        historical_years_centered = years_sorted - years_sorted[-1]
        future_years_centered = years_future - years_sorted[-1]

        historical_design_matrix = sm.add_constant(
            historical_years_centered
        )  # shape (n, 2)
        future_design_matrix = sm.add_constant(future_years_centered)  # shape (m, 2)

        res = sm.QuantReg(emissions_sorted, historical_design_matrix).fit(q=0.5)
        preds = res.predict(future_design_matrix)

        intercept_at_last = res.predict([1.0, 0.0])[0]  # x=0 == last year
        shift = emissions_sorted[-1] - intercept_at_last

        # Store results in the dataframe
        input_df.at[idx, "trend_coefficient"] = res.params[1]
        input_df.at[idx, "trend_predictions"] = list(preds + shift)

    return input_df
