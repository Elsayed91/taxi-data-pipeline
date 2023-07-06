from typing import Optional

import pandas as pd


def load_data(
    dataset: Optional[str] = None,
    table: Optional[str] = None,
    sample_size: Optional[int] = 800000,
    query: Optional[str] = None,
) -> pd.DataFrame:
    """
    This function loads data from a BigQuery table using pandas `read_gbq`. The function
    accepts parameters for the dataset, table, and an optional sample size. It returns a
    pandas DataFrame of the loaded data.

    Args:
    - dataset (str, optional): The name of the BigQuery dataset.
    - table (str, optional): The name of the BigQuery table.
    - sample_size (int, optional): The size of the sample to be loaded. The default value
    is 800,000.
    - query (str, optional): Specific query to run, a default query is in place if this is
    not provided.

    Returns:
    - pandas DataFrame: A DataFrame of the loaded data from the BigQuery table.

    Note:
    The function should ideally be used using `TABLESAMPLE SYSTEM` which is more
    efficient and doesn't cause a full table read when sampling, however it returns
    inconsistent number of rows, so limiting rows using read_gbp is used.
    """

    # query = f"""SELECT * EXCEPT(date) FROM
    #         ( SELECT * FROM `{dataset}`.`{table}`
    #         TABLESAMPLE SYSTEM ({sample_size} PERCENT) )"""
    if not query:
        query = f"""SELECT * EXCEPT(date) FROM `{dataset}`.`{table}` 
                WHERE RAND() < 0.1"""
    df = pd.read_gbq(
        query, progress_bar_type="tqdm", use_bqstorage_api=True, max_results=sample_size
    )
    return df


# hehehexdxxxd
