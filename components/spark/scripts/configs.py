import os

yellow_schema_mapping = {
    "VendorID": "integer",
    "tpep_pickup_datetime": "timestamp",
    "tpep_dropoff_datetime": "timestamp",
    "passenger_count": "integer",
    "trip_distance": "float",
    "RatecodeID": "integer",
    "store_and_fwd_flag": "string",
    "PULocationID": "integer",
    "DOLocationID": "integer",
    "payment_type": "integer",
    "fare_amount": "float",
    "extra": "float",
    "mta_tax": "float",
    "tip_amount": "float",
    "tolls_amount": "float",
    "improvement_surcharge": "float",
    "total_amount": "float",
    "congestion_surcharge": "float",
    "airport_fee": "float",
}

yellow_historical_transformation = """
    SELECT
        VendorID,
        payment_type,
        store_and_fwd_flag,
        PULocationID as pickup_zone,
        DOLocationID as dropoff_zone,
        trunc(tpep_pickup_datetime, 'month') as first_day_of_month,
        sum(fare_amount) as monthly_fare_amount,
        sum(total_amount) as monthly_total_amount,
        sum(extra) as monthly_extra_amount,
        sum(mta_tax) as monthly_mta_tax,
        sum(tip_amount) as monthly_tip_amount,
        sum(tolls_amount) as monthly_tolls_amount,
        sum(improvement_surcharge) as monthly_improvement_surcharge,
        sum(congestion_surcharge) as monthly_congestion_surcharge,
        sum(airport_fee) as monthly_airport_fee,
        avg(passenger_count) as average_passenger_count,
        avg(trip_distance) as average_trip_distance,
        count(*) as trip_count,
        avg((unix_timestamp(tpep_dropoff_datetime) - unix_timestamp(tpep_pickup_datetime)) / 60) as avg_duration_minutes,
        cast(sum(unix_timestamp(tpep_dropoff_datetime)-unix_timestamp(tpep_pickup_datetime)) as float) as total_duration_hours,
        (
            SELECT
            extract(HOUR FROM tpep_pickup_datetime) AS pickup_hour
            FROM temp_table
            GROUP BY pickup_hour
            ORDER BY count(*) DESC
            LIMIT 1
        ) as busiest_hour_of_day
        
        
    FROM temp_table
    GROUP BY
        VendorID,
        payment_type,
        store_and_fwd_flag,
        pickup_zone,
        dropoff_zone,
        first_day_of_month
    """


yellow_filter_conditions = """
    tpep_pickup_datetime < tpep_dropoff_datetime 
    AND passenger_count BETWEEN 1 AND 8 
    AND VendorID BETWEEN 1 AND 3 
    AND RatecodeID BETWEEN 1 AND 7 
    AND payment_type BETWEEN 1 AND 7 
    AND fare_amount >= 2.5 AND fare_amount < 250 
    AND DOLocationID IS NOT NULL AND PULocationID IS NOT NULL 
    AND fare_amount IS NOT NULL AND trip_distance IS NOT NULL 
    AND tpep_dropoff_datetime IS NOT NULL AND tpep_pickup_datetime IS NOT NULL
    AND tpep_pickup_datetime < CURRENT_TIMESTAMP()
    AND tpep_dropoff_datetime < CURRENT_TIMESTAMP()
    """


options = {
    "yellow": {
        "mapping": yellow_schema_mapping,
        "filters": yellow_filter_conditions,
        "summary_query": yellow_historical_transformation,
        "historical_table": os.getenv("YELLOW_SUMMARY"),
        "staging_table": os.getenv("YELLOW_STAGING"),
        "triage_table": os.getenv("YELLOW_TRIAGE"),
        "cf_hist": os.getenv("YELLOW_HIST_CLUSTERING_COL"),
        "cf_current": os.getenv("YELLOW_CLUSTERING_COL"),
        "partition_col": os.getenv("YELLOW_PART_COL"),
        "partition_col_hist": os.getenv("YELLOW_HIST_PART_COL"),
    }
}
