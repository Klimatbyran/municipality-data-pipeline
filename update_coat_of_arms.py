#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Script to update coat of arms URLs for all municipalities from Wikidata."""

from facts.coatOfArms.coat_of_arms import get_coat_of_arms
from facts.municipalities_counties import get_municipalities
from helpers import clean_kommun


def main():
    """Retrieve and display coat of arms URLs for all municipalities and regions."""
    print("Loading municipalities...")
    municipalities_df = get_municipalities()

    print(f"Updating coat of arms for {len(municipalities_df)} municipalities...")
    print("-" * 60)

    found_count = 0
    not_found_count = 0

    for idx, row in municipalities_df.iterrows():
        kommun = row["Kommun"]
        cleaned_kommun = clean_kommun(kommun)

        coat_of_arms_url = get_coat_of_arms(cleaned_kommun)
        if coat_of_arms_url:
            municipalities_df.at[idx, "coatOfArms"] = coat_of_arms_url
            found_count += 1
        else:
            municipalities_df.at[idx, "coatOfArms"] = None
            not_found_count += 1

    municipalities_df.to_csv("facts/municipalities_coat_of_arms.csv", index=False)
    print("-" * 60)
    print(f"Summary: {found_count} municipality coat of arms found, {not_found_count} not found")

    print("Loading regions...")
    # Extract unique regions from municipalities dataframe
    regions_df = municipalities_df[["Län"]].drop_duplicates().reset_index(drop=True)

    print(f"Updating coat of arms for {len(regions_df)} regions...")
    print("-" * 60)

    found_count = 0
    not_found_count = 0

    for idx, row in regions_df.iterrows():
        region = row["Län"]

        coat_of_arms_url = get_coat_of_arms(region)
        if coat_of_arms_url:
            regions_df.at[idx, "coatOfArms"] = coat_of_arms_url
            found_count += 1
        else:
            regions_df.at[idx, "coatOfArms"] = None
            not_found_count += 1

    regions_df.to_csv("facts/regions_coat_of_arms.csv", index=False)
    print("-" * 60)
    print(f"Summary: {found_count} region coat of arms found, {not_found_count} not found")

if __name__ == "__main__":
    main()
