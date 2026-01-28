# -*- coding: utf-8 -*-

import pandas as pd


def get_electric_vehicle_per_charge_points(entity_type: str, source_path: str):
    """
    This function loads data from a CSV file provided by PowerCircle and extracts
    a DataFrame with the entity namesn in title case and their corresponding electric
    vehicles per charge points values for December 2023.

    Returns:
        df_evpc (DataFrame): A pandas DataFrame with two columns,
        entity_type and 'EVPC', containing the entity names and their
        corresponding electric vehicles per charge points values.
    """

    # Load CPEV data from PowerCircle
    df_evpc_raw = pd.read_csv(source_path)

    # Rename the unnamed column to entity_type and convert entity_type to title case
    df_evpc_raw = df_evpc_raw.rename(columns={"Unnamed: 0": entity_type})
    df_evpc_raw[entity_type] = df_evpc_raw[entity_type].str.title()

    # Calculate reciprocals of CPEV values
    df_evpc_raw["EVPC"] = df_evpc_raw.apply(
        lambda row: (
            row["Antal laddbara fordon"] / row["Antal laddpunkter"]
            if row["Antal laddpunkter"] != 0
            else None
        ),
        axis=1,
    )

    # Extract the entity_type and 'CPEV' columns
    df_evpc = df_evpc_raw[[entity_type, "EVPC"]]

    return df_evpc
