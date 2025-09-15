import json
from datetime import datetime
import pandas as pd
import numpy as np

import statsmodels.api as sm

from kpis.emissions.trend_calculations import (
    extract_year_columns,
    apply_zero_floor,
)


def load_companies_data(json_file_path):
    """
    Load companies data from JSON file.

    Parameters:
    - json_file_path (str): Path to the companies.json file

    Returns:
    - list: List of company data dictionaries
    """
    with open(json_file_path, "r", encoding="utf-8") as f:
        companies_data = json.load(f)
    return companies_data


def extract_company_emissions_timeseries(companies_data):
    """
    Extract emissions time series data from companies and transform into DataFrame format.
    Now includes base year information.

    Parameters:
    - companies_data (list): List of company data dictionaries

    Returns:
    - pandas.DataFrame: DataFrame with companies as rows and years as columns
    """
    company_emissions = []

    for company in companies_data:
        company_name = company.get("name", "Unknown")
        company_id = company.get("wikidataId", None)

        # Extract base year if available
        base_year = None
        if "baseYear" in company and company["baseYear"] is not None:
            base_year = company["baseYear"].get("year")

        # Skip if no reporting periods
        if "reportingPeriods" not in company or not company["reportingPeriods"]:
            continue

        # Extract emissions data for each reporting period
        emissions_by_year = {}
        scope12_by_year = {}

        for period in company["reportingPeriods"]:
            if start_date := period.get("startDate", ""):
                try:
                    year = datetime.fromisoformat(
                        start_date.replace("Z", "+00:00")
                    ).year
                    emissions_data = period.get("emissions")
                    if emissions_data is not None:
                        emissions = emissions_data.get("calculatedTotalEmissions")

                        # Fix: Access nested properties correctly
                        scope1_data = emissions_data.get("scope1")
                        scope1 = scope1_data.get("total") if scope1_data else None

                        scope2_data = emissions_data.get("scope2")
                        scope2 = (
                            scope2_data.get("calculatedTotalEmissions")
                            if scope2_data
                            else None
                        )

                        # Calculate scope 1+2 sum if both are available
                        scope12_sum = None
                        if scope1 is not None and scope2 is not None:
                            scope12_sum = scope1 + scope2
                        elif scope1 is not None:
                            scope12_sum = scope1
                        elif scope2 is not None:
                            scope12_sum = scope2
                    else:
                        emissions = None
                        scope12_sum = None

                    if (
                        emissions is not None and emissions > 0
                    ):  # Only include positive emissions
                        emissions_by_year[year] = emissions

                    if (
                        scope12_sum is not None and scope12_sum > 0
                    ):  # Only include positive scope 1+2 emissions
                        scope12_by_year[year] = scope12_sum

                except (ValueError, TypeError):
                    continue

        # Only include companies with at least 2 years of data for trend analysis
        if (emissions_by_year and len(emissions_by_year) >= 2) or (
            scope12_by_year and len(scope12_by_year) >= 2
        ):
            company_record = {
                "company_name": company_name,
                "company_id": company_id,
                "base_year": base_year,
                **emissions_by_year,
            }

            # Add scope 1+2 data with suffix
            for year, scope12_value in scope12_by_year.items():
                company_record[f"{year}_scope12"] = scope12_value

            company_emissions.append(company_record)

    # Convert to DataFrame
    df = pd.DataFrame(company_emissions)

    # Convert to numeric types and handle missing values properly
    # First, ensure all year columns are numeric
    year_columns = [
        col
        for col in df.columns
        if isinstance(col, int) or (isinstance(col, str) and col.isdigit())
    ]
    scope12_columns = [
        col for col in df.columns if isinstance(col, str) and col.endswith("_scope12")
    ]

    for col in year_columns + scope12_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def filter_companies_with_sufficient_data(df, min_years=3):
    """
    Filter companies that have sufficient years of data for trend analysis.

    Parameters:
    - df (pandas.DataFrame): Input DataFrame with companies and emissions
    - min_years (int): Minimum number of years required for trend analysis

    Returns:
    - pandas.DataFrame: Filtered DataFrame
    """
    # Count non-null emissions data per company (excluding name and id columns)
    year_columns = [
        col
        for col in df.columns
        if isinstance(col, int) or (isinstance(col, str) and col.isdigit())
    ]
    df["data_years_count"] = df[year_columns].notna().sum(axis=1)

    # Filter companies with sufficient data
    filtered_df = df[df["data_years_count"] >= min_years].copy()
    filtered_df = filtered_df.drop("data_years_count", axis=1)

    # Ensure year columns are properly typed as integers
    for col in year_columns:
        if col in filtered_df.columns and isinstance(col, str):
            new_col_name = int(col)
            filtered_df = filtered_df.rename(columns={col: new_col_name})

    return filtered_df


def calculate_company_emissions_trends(df, end_year=2030, cutoff_year=2015):
    """
    Calculate LAD trends for company emissions data.
    Modified version of calculate_trend that handles missing data better.
    Predictions start directly from the last historical data point.
    If a company has a base year, only use data from base year forward.

    Parameters:
    - df (pandas.DataFrame): DataFrame with companies and emissions data
    - end_year (int): End year for trend predictions
    - cutoff_year (int): Minimum year to include in analysis

    Returns:
    - pandas.DataFrame: DataFrame with trend calculations added
    """

    # Extract year columns and data
    years, last_data_year = extract_year_columns(df, cutoff_year)

    # Generate prediction years starting from the next year after last data
    years_trend = np.arange(last_data_year, end_year + 1, dtype=float)

    # Create structure for new columns (both total and scope 1+2 trends)
    new_columns_data = {}
    for year in years_trend:
        new_columns_data[f"trend_{int(year)}"] = [None] * len(df)
        new_columns_data[f"trend_{int(year)}_scope12"] = [None] * len(df)
    new_columns_data["emission_slope"] = [None] * len(df)
    new_columns_data["emission_slope_scope12"] = [None] * len(df)

    # Process each company's data with improved missing data handling
    for idx in range(len(df)):
        # Get company's base year if available
        base_year = df.iloc[idx].get("base_year")

        # Determine the effective cutoff year for this company
        effective_cutoff = cutoff_year
        if base_year is not None and pd.notna(base_year):
            effective_cutoff = max(int(base_year), cutoff_year)

        # Extract emissions data, handling missing values and base year filtering
        emissions_data = []
        years_data = []

        for year in years:
            # Skip years before the effective cutoff (base year or global cutoff)
            if year < effective_cutoff:
                continue

            emission_value = df.iloc[idx][year]
            if pd.notna(emission_value) and emission_value is not None:
                emissions_data.append(float(emission_value))
                years_data.append(year)

        # Skip companies with insufficient data points for regression
        if len(emissions_data) < 2:
            # Fill with NaN for companies without sufficient data
            for year in years_trend:
                column_name = f"trend_{int(year)}"
                new_columns_data[column_name][idx] = None
            new_columns_data["emission_slope"][idx] = None
            continue

        # Convert to numpy arrays
        emissions_array = np.array(emissions_data, dtype=float)
        years_array = np.array(years_data, dtype=float)

        try:
            # Center years at the last observed year for numerical stability
            last_year = years_array[-1]
            historical_years_centered = years_array - last_year
            trend_years_centered = years_trend - last_year

            # Perform regression
            preds_trend, emission_slope = perform_regression_and_predict_simplified(
                emissions_array,
                historical_years_centered,
                trend_years_centered,
            )

            # Store trend data
            for i, year in enumerate(years_trend):
                column_name = f"trend_{int(year)}"
                new_columns_data[column_name][idx] = preds_trend[i]

            new_columns_data["emission_slope"][idx] = emission_slope

        except (ValueError, np.linalg.LinAlgError, RuntimeError) as e:
            print(f"Error processing company {df.iloc[idx]['company_name']}: {str(e)}")
            # Fill with NaN for companies with errors
            for year in years_trend:
                column_name = f"trend_{int(year)}"
                new_columns_data[column_name][idx] = None
            new_columns_data["emission_slope"][idx] = None

        # Process scope 1+2 emissions
        scope12_emissions_data = []
        scope12_years_data = []
        for year in years:
            if year < effective_cutoff:
                continue
            scope12_col = f"{year}_scope12"
            if scope12_col in df.columns:
                scope12_value = df.iloc[idx][scope12_col]
                if pd.notna(scope12_value) and scope12_value is not None:
                    scope12_emissions_data.append(float(scope12_value))
                    scope12_years_data.append(year)

        # Calculate trends for scope 1+2 emissions
        if scope12_emissions_data and len(scope12_emissions_data) >= 2:
            try:
                scope12_emissions_array = np.array(scope12_emissions_data, dtype=float)
                scope12_years_array = np.array(scope12_years_data, dtype=float)
                last_year_scope12 = scope12_years_array[-1]
                historical_years_centered_scope12 = (
                    scope12_years_array - last_year_scope12
                )
                trend_years_centered_scope12 = years_trend - last_year_scope12

                preds_trend_scope12, emission_slope_scope12 = (
                    perform_regression_and_predict_simplified(
                        scope12_emissions_array,
                        historical_years_centered_scope12,
                        trend_years_centered_scope12,
                    )
                )

                for i, year in enumerate(years_trend):
                    column_name = f"trend_{int(year)}_scope12"
                    new_columns_data[column_name][idx] = preds_trend_scope12[i]
                new_columns_data["emission_slope_scope12"][idx] = emission_slope_scope12

            except (ValueError, np.linalg.LinAlgError, RuntimeError) as e:
                print(
                    f"Error processing scope 1+2 emissions for company {df.iloc[idx]['company_name']}: {str(e)}"
                )
                for year in years_trend:
                    column_name = f"trend_{int(year)}_scope12"
                    new_columns_data[column_name][idx] = None
                new_columns_data["emission_slope_scope12"][idx] = None
        else:
            for year in years_trend:
                column_name = f"trend_{int(year)}_scope12"
                new_columns_data[column_name][idx] = None
            new_columns_data["emission_slope_scope12"][idx] = None

    # Create new columns DataFrame and concatenate with original
    new_columns_df = pd.DataFrame(new_columns_data)

    trend_cols = [f"trend_{int(year)}" for year in years_trend]
    scope12_trend_cols = [f"trend_{int(year)}_scope12" for year in years_trend]
    floored_future_trend_df = apply_zero_floor(
        new_columns_df, trend_cols + scope12_trend_cols
    )

    return pd.concat([df, floored_future_trend_df], axis=1)


def perform_regression_and_predict_simplified(
    emissions,
    historical_years_centered,
    trend_years_centered,
):
    """
    Perform LAD (least absolute deviations) regression and generate predictions.
    LAD equals median regression with q=0.5.
    Predictions are anchored to the last historical data point.

    Parameters:
    - emissions (numpy.ndarray): Emissions data
    - historical_years_centered (numpy.ndarray): Historical years centered at last observed year
    - trend_years_centered (numpy.ndarray): Trend years centered at last observed year

    Returns:
    - tuple: (preds_trend, emission_slope)
    """
    historical_design_matrix = sm.add_constant(historical_years_centered)
    trend_design_matrix = sm.add_constant(trend_years_centered)

    res = sm.QuantReg(emissions, historical_design_matrix).fit(q=0.5)

    # Get raw predictions from the regression
    preds_trend_raw = res.predict(trend_design_matrix)

    # Calculate the predicted value at the last historical year (x=0 in centered coordinates)
    predicted_at_last_year = res.predict([1.0, 0.0])[0]

    # Calculate shift to anchor predictions to actual last historical data point
    last_historical_value = emissions[-1]
    shift = last_historical_value - predicted_at_last_year

    # Apply shift to anchor all predictions to the last historical data point
    preds_trend = preds_trend_raw + shift

    emission_slope = res.params[1]

    return preds_trend, emission_slope


def main():
    """
    Main function to run company emissions trend analysis.
    """
    print("Loading companies data...")
    companies_data = load_companies_data("companies.json")
    print(f"Loaded {len(companies_data)} companies")

    print("Extracting emissions time series...")
    emissions_df = extract_company_emissions_timeseries(companies_data)
    print(f"Extracted data for {len(emissions_df)} companies with emissions data")

    print("Filtering companies with sufficient data...")
    min_years = 2
    filtered_df = filter_companies_with_sufficient_data(
        emissions_df, min_years=min_years
    )
    print(f"Found {len(filtered_df)} companies with at least {min_years} years of data")

    if len(filtered_df) == 0:
        print("No companies found with sufficient data for trend analysis")
        return

    print("Calculating LAD trends...")
    print("Sample data before trend calculation:")
    year_cols = [col for col in filtered_df.columns if isinstance(col, int)]
    print(filtered_df[["company_name"] + year_cols[:5]].head())

    try:
        trends_df = calculate_company_emissions_trends(filtered_df)
        print(f"Successfully calculated trends for {len(trends_df)} companies")

        # Save results
        output_file = "output/company-emissions-trends.json"
        trends_df.to_json(output_file, orient="records", indent=2)
        print(f"Results saved to {output_file}")

        # Save results as xlsx
        trends_df.to_excel("output/company-emissions-trends.xlsx")

        # Display summary statistics
        print("\nSummary Statistics:")
        slope_col = "emission_slope"
        if slope_col in trends_df.columns:
            slopes = trends_df[slope_col].dropna()
            print(f"Average emission slope: {slopes.mean():.2f} tCO2e/year")
            print(f"Median emission slope: {slopes.median():.2f} tCO2e/year")
            print(f"Companies with increasing emissions: {(slopes > 0).sum()}")
            print(f"Companies with decreasing emissions: {(slopes < 0).sum()}")

        # Show sample of results
        print(f"\nSample results (first 5 companies):")
        display_cols = ["company_name"] + [
            col for col in trends_df.columns if "trend_" in str(col)
        ][:5]
        if "emission_slope" in trends_df.columns:
            display_cols.append("emission_slope")
        print(trends_df[display_cols].head())

    except (ValueError, KeyError, TypeError) as e:
        print(f"Error calculating trends: {str(e)}")
        print("This might be due to insufficient data or formatting issues")


if __name__ == "__main__":
    main()
