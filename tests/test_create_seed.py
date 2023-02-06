import shapefile
import pandas as pd
import numpy as np
import sys

sys.path.append("scripts/")
from create_seed import get_lat_lon


def test_get_lat_lon():
    """
    tests the following:
    1. function returns a pandas dataframe
    2. dataframe has correct number of columns
    3. datarame is not empty
    4. has the correct columns
    5. the columns are of correct type
    6. the values are within correct range
    """
    sf = shapefile.Reader("data/ny_geo_shape_data/taxi_zones.shp")
    result = get_lat_lon(sf)
    assert isinstance(result, pd.DataFrame)
    assert result.shape[0] > 0
    assert result.shape[1] == 3
    assert list(result.columns) == ["LocationID", "longitude", "latitude"]
    assert result["LocationID"].dtype == int
    assert result["longitude"].dtype == float
    assert result["latitude"].dtype == float
    assert result["longitude"].min() >= -74.25559
    assert result["longitude"].max() <= -73.70001
    assert result["latitude"].min() >= 40.49612
    assert result["latitude"].max() <= 40.91553
