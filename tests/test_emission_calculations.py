# -*- coding: utf-8 -*-
import unittest
import pandas as pd

from kpis.emissions.emission_data_calculations import (
    calculate_historical_change_percent,
    deduct_cement,
    calculate_meets_paris_goal,
    emission_calculations,
)


LAST_YEAR_WITH_SMHI_DATA = 2021
CURRENT_YEAR = 2024


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
                2022: 406856000 / 1000,
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

    def test_does_meets_paris_goal(self):
        """Test the meets Paris goal"""
        df_input = pd.DataFrame(
            {
                "totalTrend": [100],
                "totalCarbonLawPath": [110],
            }
        )

        df_expected = df_input.copy()
        df_expected["meetsParisGoal"] = [True]

        df_result = df_input.copy()
        df_result["meetsParisGoal"] = calculate_meets_paris_goal(
            df_input["totalTrend"].iloc[0], df_input["totalCarbonLawPath"].iloc[0]
        )

        pd.testing.assert_frame_equal(df_result, df_expected)

    def test_does_not_meets_paris_goal(self):
        """Test the meets Paris goal"""
        df_input = pd.DataFrame(
            {
                "totalTrend": [120],
                "totalCarbonLawPath": [110],
            }
        )

        df_expected = df_input.copy()
        df_expected["meetsParisGoal"] = [False]

        df_result = df_input.copy()
        df_result["meetsParisGoal"] = calculate_meets_paris_goal(
            df_input["totalTrend"].iloc[0], df_input["totalCarbonLawPath"].iloc[0]
        )

        pd.testing.assert_frame_equal(df_result, df_expected)

    def test_does_exactly_meets_paris_goal(self):
        """Test the meets Paris goal"""
        df_input = pd.DataFrame(
            {
                "totalTrend": [100],
                "totalCarbonLawPath": [100],
            }
        )

        df_expected = df_input.copy()
        df_expected["meetsParisGoal"] = [True]

        df_result = df_input.copy()
        df_result["meetsParisGoal"] = calculate_meets_paris_goal(
            df_input["totalTrend"].iloc[0], df_input["totalCarbonLawPath"].iloc[0]
        )

        pd.testing.assert_frame_equal(df_result, df_expected)

    def test_emission_calculations_for_ale(self):
        """Test the emission calculations"""
        df_input = pd.DataFrame(
            {
                "Kommun": ["Ale"],
            }
        )

        df_expected = pd.DataFrame(
            {
                "Kommun": ["Ale"],
                1990: [122479.269721],
                2000: [149847.593565],
                2005: [137858.649371],
                2010: [162048.314627],
                2015: [153825.085295],
                2016: [152178.7955],
                2017: [155980.925217],
                2018: [162008.760113],
                2019: [168504.59322],
                2020: [151960.022899],
                2021: [157751.287931],
                2022: [142529.055614],
                2023: [136223.552398],
                "approximated_2023": [136223.552398],
                "approximated_2024": [137338.050884],
                "approximated_2025": [138452.54937],
                "trend_2025": [138452.54937],
                "trend_2026": [139567.047856],
                "trend_2027": [140681.546342],
                "trend_2028": [141796.044829],
                "trend_2029": [142910.543315],
                "trend_2030": [144025.041801],
                "trend_2031": [145139.540287],
                "trend_2032": [146254.038773],
                "trend_2033": [147368.537259],
                "trend_2034": [148483.035745],
                "trend_2035": [149597.534231],
                "trend_2036": [150712.032718],
                "trend_2037": [151826.531204],
                "trend_2038": [152941.02969],
                "trend_2039": [154055.528176],
                "trend_2040": [155170.026662],
                "trend_2041": [156284.525148],
                "trend_2042": [157399.023634],
                "trend_2043": [158513.52212],
                "trend_2044": [159628.020607],
                "trend_2045": [160742.519093],
                "trend_2046": [161857.017579],
                "trend_2047": [162971.516065],
                "trend_2048": [164086.014551],
                "trend_2049": [165200.513037],
                "trend_2050": [166315.011523],
                "emission_slope": [1114.498486],
                "totalTrend": [3961978.291616],
                "historicalEmissionChangePercent": [-1.347337],
                "totalCarbonLawPath": [1135119.593573],
                "meetsParisGoal": [False],
            }
        )

        df_result = emission_calculations(df_input)

        pd.testing.assert_frame_equal(df_result, df_expected)

    def test_emission_calculations_for_aneby(self):
        """Test the emission calculations"""
        df_input = pd.DataFrame(
            {
                "Kommun": ["Aneby"],
            }
        )

        df_expected = pd.DataFrame(
            {
                "Kommun": ["Aneby"],
                1990: [60302.63],
                2000: [55810.58],
                2005: [56298.36],
                2010: [49617.91],
                2015: [44739.82],
                2016: [44035.07],
                2017: [46900.28],
                2018: [44444.87],
                2019: [44118.53],
                2020: [43112.83],
                2021: [42734.47],
                2022: [41061.31],
                2023: [42384.8],
                "approximated_2023": [42384.8],
                "approximated_2024": [41762.13],
                "approximated_2025": [41139.46],
                "trend_2025": [41139.46],
                "trend_2026": [40516.79],
                "trend_2027": [39894.11],
                "trend_2028": [39271.44],
                "trend_2029": [38648.77],
                "trend_2030": [38026.1],
                "trend_2031": [37403.43],
                "trend_2032": [36780.75],
                "trend_2033": [36158.08],
                "trend_2034": [35535.41],
                "trend_2035": [34912.74],
                "trend_2036": [34290.07],
                "trend_2037": [33667.39],
                "trend_2038": [33044.72],
                "trend_2039": [32422.05],
                "trend_2040": [31799.38],
                "trend_2041": [31176.7],
                "trend_2042": [30554.03],
                "trend_2043": [29931.36],
                "trend_2044": [29308.69],
                "trend_2045": [28686.02],
                "trend_2046": [28063.34],
                "trend_2047": [27440.67],
                "trend_2048": [26818.0],
                "trend_2049": [26195.33],
                "trend_2050": [25572.66],
                "emission_slope": [-622.67211],
                "totalTrend": [867257.487553],
                "historicalEmissionChangePercent": [-0.610923],
                "totalCarbonLawPath": [337286.714681],
                "meetsParisGoal": [False],
            }
        )

        df_result = emission_calculations(df_input)

        pd.testing.assert_frame_equal(df_result, df_expected)


if __name__ == "__main__":
    unittest.main()
