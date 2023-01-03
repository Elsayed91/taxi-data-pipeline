import pyspark.sql.functions as F


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
        avg(trip_distance) as average_trip_distance
    FROM df_view
    GROUP BY
        VendorID,
        payment_type,
        store_and_fwd_flag,
        pickup_zone,
        dropoff_zone,
        first_day_of_month
    """


# def yellow_filter_conditions(df):
#     return (
#         (F.col("tpep_pickup_datetime") < F.col("tpep_dropoff_datetime"))
#         & (F.col("passenger_count").between(1, 8))
#         & (F.col("VendorID").between(1, 3))
#         & (F.col("RatecodeID").between(1, 7))
#         & (F.col("payment_type").between(1, 7))
#         & (F.col("fare_amount").between(2.5, 250))
#         & (F.col("DOLocationID").isNotNull())
#         & (F.col("PULocationID").isNotNull())
#         & (F.col("fare_amount").isNotNull())
#         & (F.col("trip_distance").isNotNull())
#         & (F.col("tpep_dropoff_datetime").isNotNull())
#         & (F.col("tpep_pickup_datetime").isNotNull())
#     )


def get_filter_condition():
    cond = (
        (F.col("tpep_pickup_datetime") < F.col("tpep_dropoff_datetime"))
        & (F.col("passenger_count").between(1, 8))
        & (F.col("VendorID").between(1, 3))
        & (F.col("RatecodeID").between(1, 7))
        & (F.col("payment_type").between(1, 7))
        & (F.col("fare_amount") >= 2.5)
        & (F.col("fare_amount") < 250)
        & (F.col("DOLocationID").isNotNull())
        & (F.col("PULocationID").isNotNull())
        & (F.col("fare_amount").isNotNull())
        & (F.col("trip_distance").isNotNull())
        & (F.col("tpep_dropoff_datetime").isNotNull())
        & (F.col("tpep_pickup_datetime").isNotNull())
    )
    return cond


options = {
    "yellow": {
        "mapping": yellow_schema_mapping,
        # "filter_conditions": yellow_filter_conditions(),
        "transformation_query": yellow_historical_transformation,
    }
}
