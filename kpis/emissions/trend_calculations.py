import numpy as np
import statsmodels.api as sm


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
