import json
from datetime import datetime
import pandas as pd
import numpy as np

import statsmodels.api as sm

from kpis.emissions.trend_calculations import (
    extract_year_columns,
)


def load_companies_data(json_file_path):
    """
    Load companies data from JSON file.

    Parameters:
    - json_file_path (str): Path to the companies.json file

    Returns:
    - list: List of company data dictionaries
    """
    with open(json_file_path, "r", encoding="utf-8") as file:
        companies_data = json.load(file)
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
        if company_record := _process_single_company(company):
            company_emissions.append(company_record)

    df = pd.DataFrame(company_emissions)
    return _convert_columns_to_numeric(df)


def _process_single_company(company):
    """Process a single company's emissions data."""
    company_name = company.get("name", "Unknown")
    company_id = company.get("wikidataId", None)
    base_year = _extract_base_year(company)

    if "reportingPeriods" not in company or not company["reportingPeriods"]:
        return None

    emissions_by_year, scope12_by_year = _extract_emissions_by_year(company["reportingPeriods"])

    # Only include companies with at least 2 years of data for trend analysis
    if not ((emissions_by_year and len(emissions_by_year) >= 2) or
            (scope12_by_year and len(scope12_by_year) >= 2)):
        return None

    company_record = {
        "company_name": company_name,
        "company_id": company_id,
        "base_year": base_year,
        **emissions_by_year,
    }

    # Add scope 1+2 data with suffix
    for year, scope12_value in scope12_by_year.items():
        company_record[f"{year}_scope12"] = scope12_value

    return company_record


def _extract_base_year(company):
    """Extract base year from company data."""
    if "baseYear" in company and company["baseYear"] is not None:
        return company["baseYear"].get("year")
    return None


def _extract_emissions_by_year(reporting_periods):
    """Extract emissions data from reporting periods."""
    emissions_by_year = {}
    scope12_by_year = {}

    for period in reporting_periods:
        year, emissions, scope12_sum = _process_reporting_period(period)
        if year is None:
            continue

        if emissions is not None and emissions > 0:
            emissions_by_year[year] = emissions
        if scope12_sum is not None and scope12_sum > 0:
            scope12_by_year[year] = scope12_sum

    return emissions_by_year, scope12_by_year


def _process_reporting_period(period):
    """Process a single reporting period to extract year and emissions."""
    start_date = period.get("startDate", "")
    if not start_date:
        return None, None, None

    try:
        return _extract_year_total_emissions_and_sum_of_scope_emissions(start_date, period)
    except (ValueError, TypeError):
        return None, None, None


def _extract_year_total_emissions_and_sum_of_scope_emissions(start_date, period):
    year = datetime.fromisoformat(start_date.replace("Z", "+00:00")).year
    emissions_data = period.get("emissions")

    if emissions_data is None:
        return year, None, None

    emissions = emissions_data.get("calculatedTotalEmissions")
    scope12_sum = _calculate_scope12_sum(emissions_data)

    return year, emissions, scope12_sum


def _calculate_scope12_sum(emissions_data):
    """Calculate scope 1+2 sum from emissions data."""
    scope1_data = emissions_data.get("scope1")
    scope1 = scope1_data.get("total") if scope1_data else None

    scope2_data = emissions_data.get("scope2")
    scope2 = scope2_data.get("calculatedTotalEmissions") if scope2_data else None

    if scope1 is not None and scope2 is not None:
        return scope1 + scope2
    elif scope1 is not None:
        return scope1
    elif scope2 is not None:
        return scope2
    return None


def _convert_columns_to_numeric(df):
    """Convert year and scope12 columns to numeric types."""
    if df.empty:
        return df

    year_columns = [
        col for col in df.columns
        if isinstance(col, int) or (isinstance(col, str) and col.isdigit())
    ]
    scope12_columns = [
        col for col in df.columns
        if isinstance(col, str) and col.endswith("_scope12")
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
    years, _ = extract_year_columns(df, cutoff_year)
    scope12_years = _extract_scope12_years(df, cutoff_year)

    new_columns_data = _initialize_trend_columns(len(df))

    for idx in range(len(df)):
        effective_cutoff = _get_effective_cutoff(df.iloc[idx], cutoff_year)

        # Process regular emissions
        _process_company_emissions(
            df, idx, years, effective_cutoff, end_year, new_columns_data
        )

        # Process scope 1+2 emissions
        _process_company_scope12_emissions(
            df, idx, scope12_years, effective_cutoff, end_year, new_columns_data
        )

    new_columns_df = pd.DataFrame(new_columns_data)
    return pd.concat([df, new_columns_df], axis=1)


def _extract_scope12_years(df, cutoff_year):
    """Extract scope12 years from column names."""
    scope12_year_columns = [
        col for col in df.columns
        if isinstance(col, str) and col.endswith("_scope12") and not col.startswith("trend_")
    ]

    scope12_years = []
    for col in scope12_year_columns:
        year_str = col.split("_")[0]
        if year_str.isdigit() and int(year_str) >= cutoff_year:
            scope12_years.append(int(year_str))

    return sorted(scope12_years) if scope12_years else []


def _initialize_trend_columns(num_companies):
    """Initialize new columns data structure."""
    return {
        "emission_slope": [None] * num_companies,
        "emission_slope_scope12": [None] * num_companies,
    }


def _get_effective_cutoff(company_row, cutoff_year):
    """Get effective cutoff year for a company based on base year."""
    base_year = company_row.get("base_year")
    if base_year is not None and pd.notna(base_year):
        return max(int(base_year), cutoff_year)
    return cutoff_year


def _process_company_emissions(df, idx, years, effective_cutoff, end_year, new_columns_data):
    """Process regular emissions for a single company."""
    emissions_data, years_data = _extract_emissions_data(df, idx, years, effective_cutoff)

    if len(emissions_data) < 2:
        new_columns_data["emission_slope"][idx] = None
        return

    try:
        emissions_array = np.array(emissions_data, dtype=float)
        years_array = np.array(years_data, dtype=float)
        company_last_year = int(years_array[-1])

        slope, predictions = _calculate_trends(
            emissions_array, years_array, company_last_year, end_year
        )

        _store_trend_predictions(
            new_columns_data, predictions, company_last_year, end_year,
            len(df), idx, emissions_array[-1]
        )
        new_columns_data["emission_slope"][idx] = slope

    except (ValueError, np.linalg.LinAlgError, RuntimeError) as e:
        print(f"Error processing company {df.iloc[idx]['company_name']}: {str(e)}")
        new_columns_data["emission_slope"][idx] = None


def _process_company_scope12_emissions(
    df, idx, scope12_years, effective_cutoff, end_year, new_columns_data
    ):
    """Process scope 1+2 emissions for a single company."""
    scope12_data, scope12_years_data = _extract_scope12_data(
        df, idx, scope12_years, effective_cutoff
    )

    if len(scope12_data) < 2:
        new_columns_data["emission_slope_scope12"][idx] = None
        return

    try:
        scope12_array = np.array(scope12_data, dtype=float)
        scope12_years_array = np.array(scope12_years_data, dtype=float)
        company_last_year = int(scope12_years_array[-1])

        slope, predictions = _calculate_trends(
            scope12_array, scope12_years_array, company_last_year, end_year
        )

        _store_trend_predictions(
            new_columns_data, predictions, company_last_year, end_year,
            len(df), idx, scope12_array[-1], "_scope12"
        )
        new_columns_data["emission_slope_scope12"][idx] = slope

    except (ValueError, np.linalg.LinAlgError, RuntimeError) as e:
        print(f"Error processing scope 1+2 emissions for {df.iloc[idx]['company_name']}: {str(e)}")
        new_columns_data["emission_slope_scope12"][idx] = None


def _extract_emissions_data(df, idx, years, effective_cutoff):
    """Extract emissions data for a company."""
    emissions_data = []
    years_data = []

    for year in years:
        if year < effective_cutoff:
            continue
        emission_value = df.iloc[idx][year]
        if pd.notna(emission_value) and emission_value is not None:
            emissions_data.append(float(emission_value))
            years_data.append(year)

    return emissions_data, years_data


def _extract_scope12_data(df, idx, scope12_years, effective_cutoff):
    """Extract scope 1+2 data for a company."""
    scope12_data = []
    scope12_years_data = []

    for year in scope12_years:
        if year < effective_cutoff:
            continue
        scope12_col = f"{year}_scope12"
        if scope12_col in df.columns:
            scope12_value = df.iloc[idx][scope12_col]
            if pd.notna(scope12_value) and scope12_value is not None:
                scope12_data.append(float(scope12_value))
                scope12_years_data.append(year)

    return scope12_data, scope12_years_data


def _calculate_trends(emissions_array, years_array, company_last_year, end_year):
    """Calculate trend slope and predictions for emissions data."""
    company_years_trend = np.arange(company_last_year, end_year + 1, dtype=float)

    # Center years at the last observed year for numerical stability
    historical_years_centered = years_array - company_last_year
    trend_years_centered = company_years_trend - company_last_year

    predictions, slope = perform_regression_and_predict_simplified(
        emissions_array, historical_years_centered, trend_years_centered
    )

    return slope, predictions


def _store_trend_predictions(new_columns_data, predictions, company_last_year, end_year,
                           num_companies, idx, last_historical_value, suffix=""):
    """Store trend predictions in the new columns data structure."""
    company_years_trend = np.arange(company_last_year, end_year + 1, dtype=float)

    for i, year in enumerate(company_years_trend):
        column_name = f"trend_{int(year)}{suffix}"

        # Initialize column if it doesn't exist
        if column_name not in new_columns_data:
            new_columns_data[column_name] = [None] * num_companies

        # For the last historical year, use the actual historical value
        if year == company_last_year:
            new_columns_data[column_name][idx] = last_historical_value
        else:
            new_columns_data[column_name][idx] = predictions[i]


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

        # Check scope1+2 statistics
        slope_col_scope12 = "emission_slope_scope12"
        if slope_col_scope12 in trends_df.columns:
            slopes_scope12 = trends_df[slope_col_scope12].dropna()
            print("\nScope 1+2 Statistics:")
            print(f"Companies with scope 1+2 trends: {len(slopes_scope12)}")
            if len(slopes_scope12) > 0:
                print(
                    f"Average scope 1+2 slope: {slopes_scope12.mean():.2f} tCO2e/year"
                )
                print(
                    f"Median scope 1+2 slope: {slopes_scope12.median():.2f} tCO2e/year"
                )
                print(
                    f"Companies with increasing scope 1+2 emissions: {(slopes_scope12 > 0).sum()}"
                )
                print(
                    f"Companies with decreasing scope 1+2 emissions: {(slopes_scope12 < 0).sum()}"
                )

        # Check how many companies have scope1+2 data
        scope12_cols = [
            col
            for col in trends_df.columns
            if "_scope12" in str(col) and not col.startswith("trend_")
        ]
        if scope12_cols:
            companies_with_scope12 = 0
            for _, row in trends_df.iterrows():
                has_scope12_data = any(
                    pd.notna(row[col]) and row[col] is not None for col in scope12_cols
                )
                if has_scope12_data:
                    companies_with_scope12 += 1
            print(f"Companies with any scope 1+2 data: {companies_with_scope12}")

        # Show sample of results
        print("\nSample results (first 5 companies):")
        display_cols = ["company_name"] + [
            col for col in trends_df.columns if "trend_" in str(col)
        ][:5]
        if "emission_slope" in trends_df.columns:
            display_cols.append("emission_slope")
        if "emission_slope_scope12" in trends_df.columns:
            display_cols.append("emission_slope_scope12")
        print(trends_df[display_cols].head())

    except (ValueError, KeyError, TypeError) as e:
        print(f"Error calculating trends: {str(e)}")
        print("This might be due to insufficient data or formatting issues")


if __name__ == "__main__":
    main()
