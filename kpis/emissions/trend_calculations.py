import numpy as np
import statsmodels.api as sm


def calculate_trend(input_df, current_year):
    """
    LAD (median/quantile) regression, with years centered at the last
    observed year for numerical stability. Returns predictions anchored
    to the last observed emission value.

    Parameters:
    - input_df (pandas.DataFrame): The input dataframe containing municipality data.
    - current_year (int): The current year to predict until.

    Returns:
    - input_df (pandas.DataFrame): DataFrame with added trend coefficients, approximated data
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

    # Find the last year with actual data
    last_data_year = int(year_cols[-1])

    # Generate years for approximated historical (from last data year to current year)
    years_approximated = np.arange(last_data_year, current_year + 1, dtype=float)

    # Generate years for trend (from current year onwards to some future point)
    # Based on the test, it seems like we want to predict a few years into the future
    years_trend = np.arange(current_year, current_year + 5, dtype=float)

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
        approximated_years_centered = years_approximated - years_sorted[-1]
        trend_years_centered = years_trend - years_sorted[-1]

        historical_design_matrix = sm.add_constant(
            historical_years_centered
        )  # shape (n, 2)
        approximated_design_matrix = sm.add_constant(approximated_years_centered)
        trend_design_matrix = sm.add_constant(trend_years_centered)

        res = sm.QuantReg(emissions_sorted, historical_design_matrix).fit(q=0.5)

        # Predict for approximated historical years
        preds_approximated = res.predict(approximated_design_matrix)

        # Predict for trend years
        preds_trend = res.predict(trend_design_matrix)

        intercept_at_last = res.predict([1.0, 0.0])[0]  # x=0 == last year
        shift = emissions_sorted[-1] - intercept_at_last

        # Create columns for approximated historical data
        for i, year in enumerate(years_approximated):
            column_name = f"approximated_{int(year)}"
            input_df.at[idx, column_name] = preds_approximated[i] + shift

        # Create columns for trend data
        for i, year in enumerate(years_trend):
            column_name = f"trend_{int(year)}"
            input_df.at[idx, column_name] = preds_trend[i] + shift

        # Store results in the dataframe
        input_df.at[idx, "trend_coefficient"] = res.params[1]

        print(input_df.head())

    return input_df
