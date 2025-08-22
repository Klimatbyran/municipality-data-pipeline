# -*- coding: utf-8 -*-
import unittest
import pandas as pd

from kpis.emissions.emission_data_calculations import (
    calculate_historical_change_percent,
    deduct_cement,
)
from kpis.emissions.trend_calculations import (
    calculate_trend_coefficients,
    calculate_trend,
)
from kpis.emissions.approximated_data_calculations import (
    calculate_approximated_historical,
)


LAST_YEAR_WITH_SMHI_DATA = 2021
CURRENT_YEAR = 2024
NATIONAL_BUDGET = 80e6
BUDGET_YEAR = 2024


class TestEmissionCalculations(unittest.TestCase):
    """Test the emission calculations"""

    def test_deduct_cement(self):
        """Test the cement deduction"""
        # Sample data frame for Skövde and Gotland
        df_input = pd.DataFrame(
            {
                "Kommun": ["Skövde", "Gotland"],
                2010: [546338.699134178, 1981476.17399167],
                2015: [494776.01973774, 2195403.90927869],
                2016: [532612.492354495, 2124789.02188846],
                2017: [543896.716984358, 2024382.31793093],
                2018: [586444.17315306, 2143010.50127022],
                2019: [576595.998007861, 1966304.75819611],
                2020: [567399.427902324, 1820053.10059352],
                2021: [571141.947070738, 1741013.9429687],
            }
        )

        df_expected = pd.DataFrame(
            {
                "Kommun": ["Skövde", "Gotland"],
                2010: [189373.699134178, 401665.17399167],
                2015: [136142.01973774, 269367.90927869],
                2016: [147686.492354495, 220902.02188846],
                2017: [136263.586984358, 267272.31793093],
                2018: [140813.83315306, 402598.50127022],
                2019: [136091.668007861, 429824.75819611],
                2020: [108306.954902324, 195590.10059352],
                2021: [131967.220070738, 119802.9429687],
            }
        )

        cement_deduction = {
            "Skövde": {
                2010: 356965000 / 1000,
                2015: 358634000 / 1000,
                2016: 384926000 / 1000,
                2017: 407633130 / 1000,
                2018: 445630340 / 1000,
                2019: 440504330 / 1000,
                2020: 459092473 / 1000,
                2021: 439174727 / 1000,
            },
            "Gotland": {
                2010: 1579811000 / 1000,
                2015: 1926036000 / 1000,
                2016: 1903887000 / 1000,
                2017: 1757110000 / 1000,
                2018: 1740412000 / 1000,
                2019: 1536480000 / 1000,
                2020: 1624463000 / 1000,
                2021: 1621211000 / 1000,
            },
        }

        df_result = deduct_cement(df_input, cement_deduction)

        pd.testing.assert_frame_equal(df_result, df_expected, check_dtype=False)

    def test_calculate_trend_coefficients(self):
        """Test the trend coefficients"""
        # Sample data frame for Norrköping
        df_input = pd.DataFrame(
            {
                "Kommun": ["Norrköping"],
                2015: [575029.197615897],
                2016: [587981.674412033],
                2017: [562126.750235607],
                2018: [567506.055574675],
                2019: [561072.598453251],
                2020: [511529.0569374],
                2021: [543303.129520453],
            }
        )

        df_expected = df_input.copy()
        df_expected["trendCoefficients"] = [[-8.89777111e03, 1.85140662e07]]

        df_result = calculate_trend_coefficients(df_input, LAST_YEAR_WITH_SMHI_DATA)

        pd.testing.assert_frame_equal(df_result, df_expected, check_exact=False)

    def test_calculate_approximated_historical(self):
        """Test the approximated historical"""
        # Sample data frame for Norrköping
        df_input = pd.DataFrame(
            {
                "Kommun": ["Norrköping"],
                2015: [575029.197615897],
                2016: [587981.674412033],
                2017: [562126.750235607],
                2018: [567506.055574675],
                2019: [561072.598453251],
                2020: [511529.0569374],
                2021: [543303.129520453],
                "trendCoefficients": [[-8.89777111e03, 1.85140662e07]],
            }
        )

        df_expected = df_input.copy()
        df_expected["approximatedHistorical"] = [
            {
                2021: 543303.129520453,
                2022: 522772.98167590424,
                2023: 513875.21056812257,
                2024: 504977.43946033716,
            }
        ]
        df_expected["totalApproximatedHistorical"] = [1560788.47673442]

        df_result = calculate_approximated_historical(
            df_input, LAST_YEAR_WITH_SMHI_DATA, CURRENT_YEAR
        )

        pd.testing.assert_frame_equal(df_result, df_expected, check_exact=False)

    def test_calculate_trend(self):
        """Test the trend"""
        # Sample data frame for Norrköping
        df_input = pd.DataFrame(
            {
                "Kommun": ["Norrköping"],
                2015: [575029.197615897],
                2016: [587981.674412033],
                2017: [562126.750235607],
                2018: [567506.055574675],
                2019: [561072.598453251],
                2020: [511529.0569374],
                2021: [543303.129520453],
                "trendCoefficients": [[-8.89777111e03, 1.85140662e07]],
                "approximatedHistorical": [
                    {
                        2021: 543303.129520453,
                        2022: 522772.98167590424,
                        2023: 513875.21056812257,
                        2024: 504977.43946033716,
                    }
                ],
            }
        )

        df_expected = df_input.copy()
        df_expected["trend"] = [
            {
                2024: 504977.43946033716,
                2025: 496079.66835255176,
                2026: 487181.8972447701,
                2027: 478284.1261369847,
                2028: 469386.355029203,
                2029: 460488.5839214176,
                2030: 451590.8128136322,
                2031: 442693.0417058505,
                2032: 433795.2705980651,
                2033: 424897.4994902797,
                2034: 415999.728382498,
                2035: 407101.9572747126,
                2036: 398204.18616693094,
                2037: 389306.41505914554,
                2038: 380408.64395136014,
                2039: 371510.87284357846,
                2040: 362613.10173579305,
                2041: 353715.33062800765,
                2042: 344817.559520226,
                2043: 335919.78841244057,
                2044: 327022.0173046589,
                2045: 318124.2461968735,
                2046: 309226.4750890881,
                2047: 300328.7039813064,
                2048: 291430.932873521,
                2049: 282533.1617657356,
                2050: 273635.3906579539,
            }
        ]
        df_expected["trendEmission"] = [10121967.672179997]

        df_result = calculate_trend(df_input, LAST_YEAR_WITH_SMHI_DATA, CURRENT_YEAR)

        pd.testing.assert_frame_equal(df_result, df_expected, check_exact=False)

    def test_calculate_historical_change_percent(self):
        """Test the historical change percent"""
        # Sample data frame for Östersund
        df_input = pd.DataFrame(
            {
                "Kommun": ["Östersund"],
                2015: [143786.390451667],
                2016: [136270.272900585],
                2017: [134890.137836385],
                2018: [123096.170608436],
                2019: [113061.651497606],
                2020: [94746.1396597532],
                2021: [95248.2864179093],
            }
        )

        df_expected = df_input.copy()
        df_expected["historicalEmissionChangePercent"] = [-6.46746990789292]

        df_result = calculate_historical_change_percent(
            df_input, LAST_YEAR_WITH_SMHI_DATA
        )

        pd.testing.assert_frame_equal(df_result, df_expected, check_exact=False)


if __name__ == "__main__":
    unittest.main()
