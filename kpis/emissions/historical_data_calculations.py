import pandas as pd

from kpis.emissions.cache_utilities import cache_df

PATH_SMHI = (
    "https://nationellaemissionsdatabasen.smhi.se/api/"
    + "getexcelfile/?county=0&municipality=0&sub=GGT"
)


@cache_df(path=PATH_SMHI)
def get_smhi_data(path=PATH_SMHI):
    """
    Downloads data from SMHI and loads it into a pandas dataframe.

    Returns:
        pandas.DataFrame: The dataframe containing the SMHI data.
    """

    df_raw = pd.read_excel(path, engine="openpyxl")
    #
    # Remove the first 4 rows and reset the index
    df_raw = df_raw.drop(range(4)).reset_index(drop=True)

    # Put the first 4 elements in row 1 in to row 0
    df_raw.iloc[0, range(4)] = df_raw.iloc[1, range(4)]

    df_raw = df_raw.drop([1]).reset_index(drop=True)  # remove row 1 and reset the index

    # Change the column names to the first rows entries
    df_raw = df_raw.rename(columns=df_raw.iloc[0])
    df_raw = df_raw.drop([0])  # remove row 0
    return df_raw


def get_n_prep_data_from_smhi(input_df):
    """
    Retrieves and prepares municipality CO2 emission data from SMHI.

    Args:
        df (pandas.DataFrame): The input dataframe.

    Returns:
        pandas.DataFrame: The cleaned dataframe.
    """

    df_raw = get_smhi_data()

    # Extract total emissions from the SMHI data
    df_total = df_raw[
        (df_raw["Huvudsektor"] == "Alla")
        & (df_raw["Undersektor"] == "Alla")
        & (df_raw["Län"] != "Alla")
        & (df_raw["Kommun"] != "Alla")
    ]
    df_total = df_total.reset_index(drop=True)

    # Remove said columns
    df_total = df_total.drop(columns=["Huvudsektor", "Undersektor", "Län"])
    df_total = df_total.sort_values(by=["Kommun"])  # sort by Kommun
    df_total = df_total.reset_index(drop=True)

    return input_df.merge(df_total, on="Kommun", how="left")

def get_n_prep_regional_data_from_smhi():
    """
    Retrieves and prepares regional CO2 emission data from SMHI.

    Returns:
        pandas.DataFrame: The cleaned dataframe.
    """

    df_raw = get_smhi_data()

    # Extract total emissions from the SMHI data
    df_total = df_raw[
        (df_raw["Huvudsektor"] == "Alla")
        & (df_raw["Undersektor"] == "Alla")
        & (df_raw["Län"] != "Alla")
        & (df_raw["Kommun"] == "Alla")
    ]
    df_total = df_total.reset_index(drop=True)

    # Collect municipalities per län
    df_municipalities = df_raw[
        (df_raw["Huvudsektor"] == "Alla")
        & (df_raw["Undersektor"] == "Alla")
        & (df_raw["Län"] != "Alla")
        & (df_raw["Kommun"] != "Alla")
    ][["Län", "Kommun"]].drop_duplicates()

    kommun_per_lan = (
        df_municipalities.groupby("Län")["Kommun"]
        .apply(lambda kommuner: sorted(kommuner.unique()))
        .reset_index()
    )

    # Remove categorical columns we no longer need
    df_total = df_total.drop(columns=["Huvudsektor", "Undersektor", "Kommun"])

    df_total = df_total.merge(
        kommun_per_lan.rename(columns={"Kommun": "municipalities"}),
        on="Län",
        how="left",
    )

    df_total = df_total.sort_values(by=["Län"]).reset_index(drop=True)

    return df_total
