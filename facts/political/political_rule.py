"""Module for retrieving political rule for municipalities and regions."""
# -*- coding: utf-8 -*-

import pandas as pd


PATH_POLITICAL_RULE = "facts/political/politicalRule2022.xlsx"
PATH_POLITICAL_RULE_REGIONS = "facts/political/politicalRuleRegions2022.xlsx"


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
            "Alingsås",
            "Bengtsfors",
            "Bollnäs",
            "Borås",
            "Degerfors",
            "Grums",
            "Hagfors",
            "Hällefors",
            "Hofors",
            "Höganäs",
            "Kramfors",
            "Mönsterås",
            "Munkfors",
            "Robertsfors",
            "Sotenäs",
            "Storfors",
            "Strängnäs",
            "Torsås",
            "Tranås",
            "Västerås",
            "Vännäs",
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


def map_region_name(name):
    """
    Clean the region name by removing whitespace and mapping to standardized names.
    """

    # Mapping from various region name formats to standardized names
    region_mapping = {
        "Region Stockholm": "Stockholms län",
        "Region Uppsala": "Uppsala län",
        "Region Sörmland": "Södermanlands län",
        "Region Östergötland": "Östergötlands län",
        "Region Jönköpings län": "Jönköpings län",
        "Region Kronoberg": "Kronobergs län",
        "Region Kalmar län": "Kalmar län",
        "Region Gotland (kommun)": "Gotlands län",
        "Region Gotland": "Gotlands län",
        "Region Blekinge": "Blekinge län",
        "Region Skåne": "Skåne län",
        "Region Halland": "Hallands län",
        "Västra Götalandsregionen": "Västra Götalands län",
        "Region Värmland": "Värmlands län",
        "Region Örebro län": "Örebro län",
        "Region Västmanland": "Västmanlands län",
        "Region Dalarna": "Dalarnas län",
        "Region Gävleborg": "Gävleborgs län",
        "Region Västernorrland": "Västernorrlands län",
        "Region Jämtland Härjedalen": "Jämtlands län",
        "Region Västerbotten": "Västerbottens län",
        "Region Norrbotten": "Norrbottens län",
    }

    return region_mapping.get(name)

def clean_political_rule(rule):
    """
    Clean the political rule by removing whitespace and returning as a list.
    """
    return [item.strip() for item in rule.split(",") if item.strip()]


def get_political_rule_municipalities():
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


def get_political_rule_regions():
    """Get the political rule for each region.

    Returns:
        political_rule_df (pd.DataFrame): DataFrame with the political rule for each region.
    """
    raw_data_df = pd.read_excel(PATH_POLITICAL_RULE_REGIONS)

    raw_data_df["Region"] = raw_data_df["Unnamed: 1"]
    raw_data_df["RSO"] = raw_data_df["Parti RSO"]
    raw_data_df["Other"] = raw_data_df["Annat parti, ange vilket eller vilka"]

    # Party columns are numbered: 2022, 2022.1, 2022.2, etc.
    party_columns = [col for col in raw_data_df.columns if str(col).startswith("2022")]
    party_columns.append("Other")

    regions = []
    rules = []
    rsos = []

    for _, row in raw_data_df.iterrows():
        region_name = row["Region"]
        if pd.isna(region_name):
            continue

        mapped_region = map_region_name(region_name)
        if mapped_region:
            regions.append(mapped_region)
        else:
            regions.append(region_name)

        political_rule = ",".join(
            str(row[col]) for col in party_columns if not pd.isna(row[col])
        )
        rules.append(clean_political_rule(political_rule))

        rsos.append("" if pd.isna(row["RSO"]) else row["RSO"])

    return pd.DataFrame({"Län": regions, "Rule": rules, "RSO": rsos})
