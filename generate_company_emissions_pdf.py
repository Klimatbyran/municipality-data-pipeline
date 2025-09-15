import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.backends.backend_pdf as pdf_backend
import numpy as np


def load_company_trends_data(json_file_path):
    """
    Load company emissions trends data from JSON file.

    Parameters:
    - json_file_path (str): Path to the company-emissions-trends.json file

    Returns:
    - pandas.DataFrame: DataFrame with company emissions and trends data
    """
    with open(json_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return pd.DataFrame(data)


def extract_emissions_and_trends(company_row):
    """
    Extract historical emissions and trend data for a single company.

    Parameters:
    - company_row (pandas.Series): Row containing company data

    Returns:
    - tuple: (historical_years, historical_emissions, trend_years, trend_emissions)
    """
    # Extract historical emissions (year columns that are integers)
    historical_data = {}
    trend_data = {}

    for col in company_row.index:
        if isinstance(col, (int, str)) and str(col).isdigit():
            year = int(col)
            value = company_row[col]
            if pd.notna(value) and value is not None:
                historical_data[year] = value
        elif isinstance(col, str) and col.startswith("trend_"):
            year = int(col.split("_")[1])
            value = company_row[col]
            if pd.notna(value) and value is not None:
                trend_data[year] = value

    # Sort by year
    historical_years = sorted(historical_data.keys())
    historical_emissions = [historical_data[year] for year in historical_years]

    trend_years = sorted(trend_data.keys())
    trend_emissions = [trend_data[year] for year in trend_years]

    return historical_years, historical_emissions, trend_years, trend_emissions


def extract_scope12_emissions_and_trends(company_row):
    """
    Extract scope 1+2 historical emissions and trend data for a single company.

    Parameters:
    - company_row (pandas.Series): Row containing company data

    Returns:
    - tuple: (historical_years, historical_emissions, trend_years, trend_emissions)
    """
    # Extract scope 1+2 historical emissions (columns ending with _scope12)
    historical_data = {}
    trend_data = {}

    for col in company_row.index:
        if (
            isinstance(col, str)
            and col.endswith("_scope12")
            and not col.startswith("trend_")
        ):
            year = int(col.split("_")[0])
            value = company_row[col]
            if pd.notna(value) and value is not None:
                historical_data[year] = value
        elif (
            isinstance(col, str)
            and col.startswith("trend_")
            and col.endswith("_scope12")
        ):
            year = int(col.split("_")[1])
            value = company_row[col]
            if pd.notna(value) and value is not None:
                trend_data[year] = value

    # Sort by year
    historical_years = sorted(historical_data.keys())
    historical_emissions = [historical_data[year] for year in historical_years]

    trend_years = sorted(trend_data.keys())
    trend_emissions = [trend_data[year] for year in trend_years]

    return historical_years, historical_emissions, trend_years, trend_emissions


def create_company_emissions_plot(company_row, ax):
    """
    Create an emissions plot for a single company.
    Now includes base year highlighting.

    Parameters:
    - company_row (pandas.Series): Row containing company data
    - ax (matplotlib.axes.Axes): Matplotlib axes object to plot on

    Returns:
    - None
    """
    company_name = company_row.get("company_name", "Unknown Company")
    base_year = company_row.get("base_year")

    # Extract data
    hist_years, hist_emissions, trend_years, trend_emissions = (
        extract_emissions_and_trends(company_row)
    )

    if not hist_years and not trend_years:
        ax.text(
            0.5,
            0.5,
            f"{company_name}\nNo data available",
            ha="center",
            va="center",
            transform=ax.transAxes,
            fontsize=12,
        )
        ax.set_title(company_name, fontsize=14, fontweight="bold")
        return

    # Plot historical emissions
    if hist_years:
        ax.plot(
            hist_years,
            hist_emissions,
            "o-",
            linewidth=2,
            markersize=6,
            label="Historical Emissions",
            color="#2E86C1",
            alpha=0.8,
        )

        # Highlight base year if it exists in the data
        if base_year and base_year in hist_years:
            base_year_idx = hist_years.index(base_year)
            base_year_emission = hist_emissions[base_year_idx]
            ax.plot(
                base_year,
                base_year_emission,
                "s",  # square marker
                markersize=10,
                label=f"Base Year ({base_year})",
                color="#F39C12",
                markeredgecolor="black",
                markeredgewidth=2,
                alpha=0.9,
            )

    # Plot trend line
    if trend_years:
        ax.plot(
            trend_years,
            trend_emissions,
            "--",
            linewidth=2,
            label="Predicted Trend",
            color="#E74C3C",
            alpha=0.8,
        )

    # Formatting
    ax.set_title(company_name, fontsize=14, fontweight="bold", pad=20)
    ax.set_xlabel("Year", fontsize=11)
    ax.set_ylabel("Emissions (tCO2e)", fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10)

    # Format y-axis to show thousands separators
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{x:,.0f}"))

    if all_emissions := hist_emissions + trend_emissions:
        y_min = min(all_emissions)
        y_max = max(all_emissions)
        y_range = y_max - y_min
        if y_range > 0:
            ax.set_ylim(max(0, y_min - 0.1 * y_range), y_max + 0.1 * y_range)
        else:
            # Handle case where all values are the same
            ax.set_ylim(max(0, y_min - 0.1 * abs(y_min)), y_max + 0.1 * abs(y_max))

    # Get emission slope for additional info and add base year info
    slope = company_row.get("emission_slope")
    info_text_lines = []

    if pd.notna(slope):
        trend_text = (
            "↗ Increasing" if slope > 0 else "↘ Decreasing" if slope < 0 else "→ Stable"
        )
        info_text_lines.extend(
            (f"Trend: {trend_text}", f"Slope: {slope:,.0f} tCO2e/year")
        )
    if base_year:
        if base_year in hist_years:
            info_text_lines.append(f"Base Year: {base_year} ✓")
        else:
            info_text_lines.append(f"Base Year: {base_year} (no data)")

    if info_text_lines:
        ax.text(
            0.02,
            0.98,
            "\n".join(info_text_lines),
            transform=ax.transAxes,
            fontsize=9,
            verticalalignment="top",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.8),
        )


def create_scope12_emissions_plot(company_row, ax):
    """
    Create a scope 1+2 emissions plot for a single company.

    Parameters:
    - company_row (pandas.Series): Row containing company data
    - ax (matplotlib.axes.Axes): Matplotlib axes object to plot on

    Returns:
    - None
    """
    base_year = company_row.get("base_year")

    # Extract scope 1+2 data
    hist_years, hist_emissions, trend_years, trend_emissions = (
        extract_scope12_emissions_and_trends(company_row)
    )

    if not hist_years and not trend_years:
        ax.text(
            0.5,
            0.5,
            f"No Scope 1+2 data available",
            ha="center",
            va="center",
            transform=ax.transAxes,
            fontsize=12,
        )
        ax.set_title("Scope 1+2 Emissions", fontsize=14, fontweight="bold")
        return

    # Plot historical scope 1+2 emissions
    if hist_years:
        ax.plot(
            hist_years,
            hist_emissions,
            "o-",
            linewidth=2,
            markersize=6,
            label="Historical Scope 1+2",
            color="#27AE60",
            alpha=0.8,
        )

        # Highlight base year if it exists in the data
        if base_year and base_year in hist_years:
            base_year_idx = hist_years.index(base_year)
            base_year_emission = hist_emissions[base_year_idx]
            ax.plot(
                base_year,
                base_year_emission,
                "s",  # square marker
                markersize=10,
                label=f"Base Year ({base_year})",
                color="#F39C12",
                markeredgecolor="black",
                markeredgewidth=2,
                alpha=0.9,
            )

    # Plot trend line
    if trend_years:
        ax.plot(
            trend_years,
            trend_emissions,
            "--",
            linewidth=2,
            label="Predicted Trend",
            color="#E67E22",
            alpha=0.8,
        )

    # Formatting
    ax.set_title("Scope 1+2 Emissions", fontsize=14, fontweight="bold", pad=20)
    ax.set_xlabel("Year", fontsize=11)
    ax.set_ylabel("Scope 1+2 Emissions (tCO2e)", fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10)

    # Format y-axis to show thousands separators
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{x:,.0f}"))

    if all_emissions := hist_emissions + trend_emissions:
        y_min = min(all_emissions)
        y_max = max(all_emissions)
        y_range = y_max - y_min
        if y_range > 0:
            ax.set_ylim(max(0, y_min - 0.1 * y_range), y_max + 0.1 * y_range)
        else:
            # Handle case where all values are the same
            ax.set_ylim(max(0, y_min - 0.1 * abs(y_min)), y_max + 0.1 * abs(y_max))

    # Get emission slope for additional info
    slope = company_row.get("emission_slope_scope12")
    info_text_lines = []

    if pd.notna(slope):
        trend_text = (
            "↗ Increasing" if slope > 0 else "↘ Decreasing" if slope < 0 else "→ Stable"
        )
        info_text_lines.extend(
            (f"Trend: {trend_text}", f"Slope: {slope:,.0f} tCO2e/year")
        )

    if info_text_lines:
        ax.text(
            0.02,
            0.98,
            "\n".join(info_text_lines),
            transform=ax.transAxes,
            fontsize=9,
            verticalalignment="top",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgreen", alpha=0.8),
        )


def generate_company_emissions_pdf(
    df, output_path="output/company_emissions_graphs.pdf"
):
    """
    Generate a PDF with individual emissions graphs for each company.
    Now includes both total emissions and scope 1+2 emissions graphs.

    Parameters:
    - df (pandas.DataFrame): DataFrame with company emissions data
    - output_path (str): Path for the output PDF file

    Returns:
    - None
    """
    print(f"Generating PDF with {len(df)} company graphs...")

    # Set up matplotlib style
    plt.style.use("default")

    with pdf_backend.PdfPages(output_path) as pdf:
        # One company per page with two subplots (total emissions + scope 1+2)
        for i in range(len(df)):
            # Create a new page with two subplots
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 8.5))

            company_row = df.iloc[i]
            company_name = company_row.get("company_name", "Unknown Company")

            # Create total emissions plot (top)
            create_company_emissions_plot(company_row, ax1)

            # Create scope 1+2 emissions plot (bottom)
            create_scope12_emissions_plot(company_row, ax2)

            # Add company name as main title
            fig.suptitle(company_name, fontsize=16, fontweight="bold", y=0.95)

            # Adjust layout
            plt.tight_layout()
            plt.subplots_adjust(top=0.90, hspace=0.4)

            # Save page to PDF
            pdf.savefig(fig, bbox_inches="tight", dpi=300)
            plt.close(fig)

            # Progress indicator
            if (i + 1) % 10 == 0 or (i + 1) >= len(df):
                print(f"  Processed {i + 1}/{len(df)} companies...")

    print(f"PDF saved to: {output_path}")


def main():
    """
    Main function to generate company emissions PDF.
    """
    print("Loading company emissions trends data...")

    # Load the data
    json_file = "output/company-emissions-trends.json"
    df = load_company_trends_data(json_file)

    print(f"Loaded data for {len(df)} companies")

    # Filter out companies without sufficient data for meaningful plots
    # Only keep companies that have at least some historical or trend data
    def has_meaningful_data(row):
        # Check for historical emissions
        hist_count = sum(
            bool(
                (
                    isinstance(col, (int, str))
                    and str(col).isdigit()
                    and pd.notna(row[col])
                    and row[col] is not None
                )
            )
            for col in row.index
        )

        # Check for trend data
        trend_count = sum(
            bool(
                (
                    isinstance(col, str)
                    and col.startswith("trend_")
                    and pd.notna(row[col])
                    and row[col] is not None
                )
            )
            for col in row.index
        )

        return hist_count > 0 or trend_count > 0

    df_filtered = df[df.apply(has_meaningful_data, axis=1)].copy()

    print(f"Filtered to {len(df_filtered)} companies with meaningful emission data")

    if len(df_filtered) == 0:
        print("No companies found with meaningful emissions data!")
        return

    # Sort by company name for better organization
    df_filtered = df_filtered.sort_values("company_name").reset_index(drop=True)

    # Generate the PDF
    output_path = "output/company_emissions_graphs.pdf"
    generate_company_emissions_pdf(df_filtered, output_path)

    print(
        f"\nSuccessfully generated PDF with {len(df_filtered)} company emission graphs!"
    )
    print(f"Output saved to: {output_path}")


if __name__ == "__main__":
    main()
