# -*- coding: utf-8 -*-

import pandas as pd


PATH_POLITICAL_RULE = "facts/political/politicalRule2022.xlsx"


def clean_municipality_name(name):
    """
    Clean the municipality name by removing whitespace and specific keywords.
    """
    # Configuration for cleaning rules
    cleaning_config = {
        "special_cases": {
            "Falu kommun": "Falun",
            "Region Gotland (kommun)": "Gotland",
            "Stockholms stad": "Stockholm",
        },
        "names_ending_with_s": {
            "Vännäs",
            "Robertsfors",
            "Kramfors",
            "Bollnäs",
            "Hofors",
            "Hällefors",
            "Degerfors",
            "Hagfors",
            "Grums",
            "Munkfors",
            "Storfors",
            "Bengtsfors",
            "Sotenäs",
            "Höganäs",
            "Mönsterås",
            "Torsås",
            "Tranås",
            "Västerås",
            "Strängnäs",
            "Borås",
        },
        "suffixes": [" kommun", " stad"],
    }

    # Handle special cases
    if name in cleaning_config["special_cases"]:
        return cleaning_config["special_cases"][name]

    # Remove suffixes and handle 's' ending logic
    cleaned = name
    for suffix in cleaning_config["suffixes"]:
        cleaned = cleaned.replace(suffix, "")

    # Remove trailing 's' only if not in the special list
    if cleaned.endswith("s") and cleaned not in cleaning_config["names_ending_with_s"]:
        cleaned = cleaned[:-1]

    return cleaned


def clean_political_rule(rule):
    """
    Clean the political rule by removing whitespace and returning as a list.
    """
    return [item.strip() for item in rule.split(",") if item.strip()]


def get_political_rule():
    """Get the political rule for each municipality.

    Returns:
        political_rule_df (pd.DataFrame): DataFrame with the political rule for each municipality.
    """
    raw_data_df = pd.read_excel(PATH_POLITICAL_RULE)

    raw_data_df["Kommun"] = raw_data_df["Unnamed: 1"]
    raw_data_df["KSO"] = raw_data_df["Parti KSO"]
    raw_data_df["Other"] = raw_data_df["Annat parti, ange vilket eller vilka"]
    raw_data_df = raw_data_df.filter(
        [
            "Kommun",
            "KSO",
            "SD 2022",
            "M 2022",
            "KD 2022",
            "L 2022",
            "C 2022",
            "MP 2022",
            "S 2022",
            "V 2022",
            "Other",
        ]
    )

    municipalities = []
    rules = []
    ksos = []

    party_columns = raw_data_df.columns[2:]

    for _, row in raw_data_df.iterrows():
        municipalities.append(clean_municipality_name(row["Kommun"]))

        political_rule = ",".join(
            str(row[col]) for col in party_columns if not pd.isna(row[col])
        )
        rules.append(clean_political_rule(political_rule))

        ksos.append("" if pd.isna(row["KSO"]) else row["KSO"])

    return pd.DataFrame({"Kommun": municipalities, "Rule": rules, "KSO": ksos})
