"""
- This module converts shapefiles of taxi zones in New York City to a CSV file containing
relevant information on the zones. 
- The shapefile is read using the shapefile library and the resulting data is processed and
stored in a pandas DataFrame. 
- The DataFrame is then exported as a CSV file, containing the following columns:
"LocationID", "borough", "zone", "longitude", and "latitude". 
- The get_lat_lon function is used to extract the longitude and latitude values of each
zone based on its shape data.
- This is used to create a seed file for DBT.
- The shapedata can be found online and you can use a tool/website like disq.us to 
conver it to proper coordinates format.
Reference for processing shapefile: https://chih-ling-hsu.github.io/2018/05/14/NYC
"""
import pandas as pd
import shapefile
import os


def get_lat_lon(sf: shapefile.Reader) -> pd.DataFrame:
    """
    Extracts latitude and longitude information from shapefile records.

    Args: sf (shapefile.Reader): shapefile reader object

    Returns: pd.DataFrame: dataframe containing 'LocationID', 'longitude', and 'latitude'
    information
    """
    content = []
    for sr in sf.shapeRecords():
        shape = sr.shape
        rec = sr.record
        loc_id = rec[shp_dic["LocationID"]]

        x = (shape.bbox[0] + shape.bbox[2]) / 2
        y = (shape.bbox[1] + shape.bbox[3]) / 2

        content.append((loc_id, x, y))
    return pd.DataFrame(content, columns=["LocationID", "longitude", "latitude"])


script_dir = os.path.abspath("")
shp_file_path = os.path.join(script_dir, "../data/ny_geo_shape_data/taxi_zones.shp")
target_path = os.path.join(script_dir, "../components/dbt/app/seeds/seed.csv")

if not os.path.exists(shp_file_path):
    shp_file_path = "data/ny_geo_shape_data/taxi_zones.shp"
    target_path = "components/dbt/app/seeds/seed.csv"


sf = shapefile.Reader(shp_file_path)

fields_name = [field[0] for field in sf.fields[1:]]
shp_dic = dict(zip(fields_name, list(range(len(fields_name)))))
attributes = sf.records()
shp_attr = [dict(zip(fields_name, attr)) for attr in attributes]
seed = pd.DataFrame(shp_attr).join(
    get_lat_lon(sf).set_index("LocationID"), on="LocationID"
)
seed = seed[["LocationID", "borough", "zone", "longitude", "latitude"]]

seed.to_csv(target_path, index=False)
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
