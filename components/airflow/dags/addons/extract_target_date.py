import re


def extract_target_date(filename="yellow_tripdata_2022-08.parquet"):
    match = re.search(r"\d{4}-\d{2}", filename)
    date_string = match.group(0)
    date_parts = date_string.split("-")
    formatted_date = f"{date_parts[0]}-{date_parts[1]}-01"
    return formatted_date
