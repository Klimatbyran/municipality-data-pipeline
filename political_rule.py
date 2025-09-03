# -*- coding: utf-8 -*-

import json
import pandas as pd


PATH_POLITICAL_RULE = "facts/political/politicalRule2022.xlsx"


def clean_municipality_name(name):
    """
    Clean the municipality name by removing whitespace and specific keywords.
    """
    if name == "Falu kommun":
        return "Falun"
    if name == "Region Gotland (kommun)":
        return "Gotland"
    if name == "Stockholms stad":
        return "Stockholm"
    return name.replace(" kommun", "")


df = pd.read_excel(PATH_POLITICAL_RULE)

df["Kommun"] = df["Unnamed: 1"]
df["Other"] = df["Annat parti, ange vilket eller vilka"]
df = df.filter(
    [
        "Kommun",
        "SD 2022",
        "M 2022",
        "KD 2022",
        "L 2022",
        "C 2022",
        "MP 2022",
        "S 2022",
        "V 2022",
        "ÖP 2022",
        "Other",
    ]
)

RawPoliticalRule = []
for i, row in df.iterrows():
    municipality_name = row["Kommun"]
    political_rule = ",".join(
        [str(row[col]) if not pd.isna(row[col]) else "" for col in df.columns[1:-1]]
    )
    other = row["Other"] if not pd.isna(row["Other"]) else ""
    RawPoliticalRule.append(
        {"kommun": municipality_name, "styre": political_rule, "other": other}
    )

with open("output/political-rule.json", "w", encoding="utf-8") as f:
    json.dump(RawPoliticalRule, f)
