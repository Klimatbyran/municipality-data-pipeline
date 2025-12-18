# -*- coding: utf-8 -*-
import unittest
import datetime
import pandas as pd

from kpis.emissions.emission_data_calculations import (
    calculate_historical_change_percent,
    calculate_hit_net_zero,
    calculate_meets_paris_goal,
    emission_calculations,
)


LAST_YEAR_WITH_SMHI_DATA = 2021
CURRENT_YEAR = 2024


class TestEmissionCalculations(unittest.TestCase):
    """Test the emission calculations"""

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
            df_input, "Kommun", LAST_YEAR_WITH_SMHI_DATA
        )

        pd.testing.assert_frame_equal(df_result, df_expected, check_exact=False)

    def test_does_meets_paris_goal(self):
        """Test the meets Paris goal"""
        df_input = pd.DataFrame(
            {
                "total_trend": [100],
                "totalCarbonLawPath": [110],
            }
        )

        df_expected = df_input.copy()
        df_expected["meetsParisGoal"] = [True]

        df_result = df_input.copy()
        df_result["meetsParisGoal"] = calculate_meets_paris_goal(
            df_input["total_trend"].iloc[0], df_input["totalCarbonLawPath"].iloc[0]
        )

        pd.testing.assert_frame_equal(df_result, df_expected)

    def test_calculate_hit_net_zero(self):
        """Test the hit net zero"""
        df_input = pd.DataFrame(
            {
                "Kommun": ["Ale", "Alingsås", "Gotland"],
                "approximated_2024": [1, 2, 15],
                "trend_emissions_slope": [1, -1, -5],
            }
        )

        df_expected = df_input.copy()
        df_expected["hit_net_zero"] = [None, datetime.date(2026, 1, 1), datetime.date(2027, 1, 1)]

        df_result = calculate_hit_net_zero(df_input, CURRENT_YEAR)

        pd.testing.assert_frame_equal(df_result, df_expected, check_exact=False)

    def test_does_not_meets_paris_goal(self):
        """Test the meets Paris goal"""
        df_input = pd.DataFrame(
            {
                "total_trend": [120],
                "totalCarbonLawPath": [110],
            }
        )

        df_expected = df_input.copy()
        df_expected["meetsParisGoal"] = [False]

        df_result = df_input.copy()
        df_result["meetsParisGoal"] = calculate_meets_paris_goal(
            df_input["total_trend"].iloc[0], df_input["totalCarbonLawPath"].iloc[0]
        )

        pd.testing.assert_frame_equal(df_result, df_expected)

    def test_does_exactly_meets_paris_goal(self):
        """Test the meets Paris goal"""
        df_input = pd.DataFrame(
            {
                "total_trend": [100],
                "totalCarbonLawPath": [100],
            }
        )

        df_expected = df_input.copy()
        df_expected["meetsParisGoal"] = [True]

        df_result = df_input.copy()
        df_result["meetsParisGoal"] = calculate_meets_paris_goal(
            df_input["total_trend"].iloc[0], df_input["totalCarbonLawPath"].iloc[0]
        )

        pd.testing.assert_frame_equal(df_result, df_expected)

    def test_emission_calculations_for_ale(self):
        """Test the emission calculations for Ale"""
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
                "approximated_2024": [134883.251626],
                "approximated_2025": [133542.950853],
                "trend_2025": [133542.950853],
                "trend_2026": [132202.650081],
                "trend_2027": [130862.349309],
                "trend_2028": [129522.048536],
                "trend_2029": [128181.747764],
                "trend_2030": [126841.446992],
                "trend_2031": [125501.146219],
                "trend_2032": [124160.845447],
                "trend_2033": [122820.544675],
                "trend_2034": [121480.243902],
                "trend_2035": [120139.94313],
                "trend_2036": [118799.642358],
                "trend_2037": [117459.341585],
                "trend_2038": [116119.040813],
                "trend_2039": [114778.740041],
                "trend_2040": [113438.439268],
                "trend_2041": [112098.138496],
                "trend_2042": [110757.837724],
                "trend_2043": [109417.536951],
                "trend_2044": [108077.236179],
                "trend_2045": [106736.935407],
                "trend_2046": [105396.634634],
                "trend_2047": [104056.333862],
                "trend_2048": [102716.03309],
                "trend_2049": [101375.732317],
                "trend_2050": [100035.431545],
                "trend_emissions_slope": [-1340.30077],
                "total_trend": [3035178.670407],
                "historicalEmissionChangePercent": [-1.347337],
                "hit_net_zero": [datetime.date(2124, 8, 20)],
                "totalCarbonLawPath": [1.094868e06],
                "meetsParisGoal": [False],
            }
        )

        df_result = round(emission_calculations(df_input), 6)

        pd.testing.assert_frame_equal(df_result, df_expected)

    def test_emission_calculations_for_aneby(self):
        """Test the emission calculations for Aneby"""
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
                "approximated_2023": [42384.802812],
                "approximated_2024": [42059.404713],
                "approximated_2025": [41734.006614],
                "trend_2025": [41734.006614],
                "trend_2026": [41408.608515],
                "trend_2027": [41083.210416],
                "trend_2028": [40757.812317],
                "trend_2029": [40432.414218],
                "trend_2030": [40107.016119],
                "trend_2031": [39781.61802],
                "trend_2032": [39456.219921],
                "trend_2033": [39130.821823],
                "trend_2034": [38805.423724],
                "trend_2035": [38480.025625],
                "trend_2036": [38154.627526],
                "trend_2037": [37829.229427],
                "trend_2038": [37503.831328],
                "trend_2039": [37178.433229],
                "trend_2040": [36853.03513],
                "trend_2041": [36527.637031],
                "trend_2042": [36202.238932],
                "trend_2043": [35876.840833],
                "trend_2044": [35551.442734],
                "trend_2045": [35226.044635],
                "trend_2046": [34900.646536],
                "trend_2047": [34575.248437],
                "trend_2048": [34249.850338],
                "trend_2049": [33924.452239],
                "trend_2050": [33599.054141],
                "trend_emissions_slope": [-325.398099],
                "total_trend": [979004.391711],
                "historicalEmissionChangePercent": [-0.610923],
                "hit_net_zero": [datetime.date(2153, 4, 4)],
                "totalCarbonLawPath": [342161.18693],
                "meetsParisGoal": [False],
            }
        )

        df_result = emission_calculations(df_input)
        
        print('total trend res ', df_result["total_trend"])
        print('total trend exp ', df_expected["total_trend"])

        pd.testing.assert_frame_equal(df_result, df_expected)


if __name__ == "__main__":
    unittest.main()
