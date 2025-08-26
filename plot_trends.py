# -*- coding: utf-8 -*-

from datetime import datetime
import warnings
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
from statsmodels.nonparametric.smoothers_lowess import lowess
from matplotlib.backends.backend_pdf import PdfPages

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)

OUTPUT_PATH = f"municipality_trends_{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.pdf"
EXCEL_OUTPUT_PATH = (
    f"municipality_slopes_{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.xlsx"
)


def load_climate_data(json_path):
    """Load climate data from JSON file and organize it by municipality."""
    with open(json_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    municipality_dict = {}

    count = 0
    for municipality in data:
        if count >= 290:
            break

        name = municipality["name"]
        all_emissions = {}
        for year_str, value in municipality["emissions"].items():
            year = int(year_str)
            if 2015 <= year <= 2023:
                all_emissions[year] = value

        municipality_dict[name] = all_emissions
        count += 1

    return municipality_dict


def create_municipality_sets(municipality_data, municipalities_per_set=5):
    """Split municipalities into sets for plotting."""
    municipality_names = list(municipality_data.keys())
    sets = []

    for idx in range(0, len(municipality_names), municipalities_per_set):
        set_names = municipality_names[idx : idx + municipalities_per_set]
        set_data = {name: municipality_data[name] for name in set_names}
        sets.append(set_data)

    return sets


def polyfit_anchored(years, emissions, years_future):
    """Polyfit anchored at last year."""
    # Use numpy polyfit to get coefficients
    fit = np.polyfit(years, emissions, 1)

    # Calculate predictions for all years_future
    predictions = []
    for year in years_future:
        if year <= years[-1]:
            # For historical years, interpolate actual data
            predictions.append(np.interp(year, years, emissions))
        else:
            # For future years, use trend line but ensure non-negative
            pred_value = max(0, fit[0] * year + fit[1])
            predictions.append(pred_value)

    return np.array(predictions), fit[0]


def lad_anchored(years, emissions, years_future):
    """
    LAD (median/quantile) regression, with years centered at the last
    observed year for numerical stability. Returns predictions anchored
    to the last observed emission value.
    """
    years = np.asarray(years, dtype=float)
    emissions = np.asarray(emissions, dtype=float)
    years_future = np.asarray(years_future, dtype=float)

    # Sort by year just in case
    order = np.argsort(years)
    years, emissions = years[order], emissions[order]

    # Center years at the last observed year (e.g., 2023 -> 0)
    historical_years_centered = years - years[-1]
    future_years_centered = years_future - years[-1]

    historical_design_matrix = sm.add_constant(
        historical_years_centered
    )  # shape (n, 2)
    future_design_matrix = sm.add_constant(future_years_centered)  # shape (m, 2)

    res = sm.QuantReg(emissions, historical_design_matrix).fit(q=0.5)
    preds = res.predict(future_design_matrix)

    intercept_at_last = res.predict([1.0, 0.0])[0]  # x=0 == last year
    shift = emissions[-1] - intercept_at_last
    return preds + shift, res.params[1]  # res.params[1] is slope


def lowess_anchored(years, emissions, years_future, frac=0.6, iterations=3):
    """
    LOWESS smoother (robust, local), with a conservative linear tail
    and anchored to last observed value.
    """
    fit = lowess(emissions, years, frac=frac, it=iterations, return_sorted=False)

    number_of_years = len(years)
    slope = (fit[-1] - fit[-number_of_years]) / (years[-1] - years[-number_of_years])

    tail = fit[-1] + slope * (years_future - years[-1])
    pred = np.where(
        years_future <= years.max(), np.interp(years_future, years, fit), tail
    )
    # anchor to last year
    delta = emissions[-1] - np.interp(years[-1], years, fit)
    return pred + delta, slope, number_of_years


def plot_municipality(axis, name, data):
    """Plot a single municipality's data and trends."""
    years = np.array(list(data.keys()))
    emissions = np.array(list(data.values()))
    years_future = np.arange(years.min(), 2051)

    # Calculate predictions
    y_polyfit, polyfit_slope = polyfit_anchored(years, emissions, years_future)
    y_lad, lad_slope = lad_anchored(years, emissions, years_future)
    y_lowless, lowless_slope, number_of_years = lowess_anchored(
        years, emissions, years_future
    )

    axis.scatter(years, emissions, color="black", label="Data", zorder=3)
    axis.plot(
        years_future,
        y_polyfit,
        label=f"polyfit, slope {round(polyfit_slope)}",
        linestyle="--",
    )
    axis.plot(
        years_future,
        y_lad,
        label=f"LAD, slope {round(lad_slope)}",
        linestyle="-.",
    )
    axis.plot(
        years_future,
        y_lowless,
        label=f"LOWESS, trend based on {number_of_years} years, slope {round(lowless_slope)}",
        linestyle="-",
    )

    axis.set_ylim(
        0,
        max(emissions.max(), y_polyfit.max(), y_lad.max(), y_lowless.max()) * 1.1,
    )

    axis.axvline(years[-1], linestyle=":", alpha=0.6, label=f"Last data: {years[-1]}")
    axis.set_title(f"{name}")
    axis.set_xlabel("Year")
    axis.set_ylabel("CO2")
    axis.legend()
    axis.grid(True, alpha=0.3)

    # Return slope data for Excel export
    return {
        "municipality": name,
        "polyfit_slope": polyfit_slope,
        "lad_slope": lad_slope,
        "lowess_slope": lowless_slope,
    }


def plot_set(datasets, pdf_writer):
    """Plot municipalities in a vertical stack with polyfit, LAD, LOWESS."""
    if not datasets:
        return []

    fig, axes = plt.subplots(len(datasets), 1, figsize=(12, 5 * len(datasets)))

    # Handle case where there's only one municipality (axes won't be a list)
    if len(datasets) == 1:
        axes = [axes]

    set_slope_data = []
    for axis, (name, data) in zip(axes, datasets.items()):
        if not data:  # Skip if no data
            continue
        slopes = plot_municipality(axis, name, data)
        set_slope_data.append(slopes)

    plt.tight_layout()
    pdf_writer.savefig(fig)
    plt.close(fig)

    return set_slope_data


if __name__ == "__main__":
    # Load data from JSON file
    JSON_FILE_PATH = "top_n_bottom.json"
    municipalities = load_climate_data(JSON_FILE_PATH)

    print(f"Loaded data for {len(municipalities)} municipalities")

    # Create sets of municipalities for plotting
    municipality_sets = create_municipality_sets(municipalities)

    # Collect all slope data
    all_slope_data = []
    with PdfPages(OUTPUT_PATH) as pdf:
        for i, municipality_set in enumerate(municipality_sets, 1):
            if municipality_set:  # Only plot if the set has data
                set_slopes = plot_set(municipality_set, pdf)
                all_slope_data.extend(set_slopes)

    # Create Excel file with slope data
    if all_slope_data:
        df = pd.DataFrame(all_slope_data)
        df.to_excel(EXCEL_OUTPUT_PATH, index=False)
        print(f"Saved slopes data: {EXCEL_OUTPUT_PATH}")

    print(f"Saved plots: {OUTPUT_PATH}")
    print(
        f"Generated {len(municipality_sets)} sets with {len(municipalities)} total municipalities"
    )
