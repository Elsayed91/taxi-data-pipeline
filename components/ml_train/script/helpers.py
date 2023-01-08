from typing import Optional
import pandas as pd


def load_data(
    dataset: str,
    table: str,
    sample_size: Optional[int] = 100,
) -> pd.DataFrame:
    """
    given a dataset and table and optionally, a sample size, this function loads data from
    a big query table using pandas read_gbq. returns a pandas DataFrame.
    """

    query = f"SELECT * FROM `{dataset}`.`{table}` \
            TABLESAMPLE SYSTEM ({sample_size} PERCENT)"
    df = pd.read_gbq(query)
    return df
