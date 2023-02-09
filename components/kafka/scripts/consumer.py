from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    IntegerType,
    TimestampType,
    FloatType,
)

# Create a Spark session
spark = SparkSession.builder.appName("NYTaxiConsumer").getOrCreate()

json_schema = StructType(
    [
        StructField("VendorID", IntegerType(), True),
        StructField("tpep_pickup_datetime", TimestampType(), True),
        StructField("tpep_dropoff_datetime", TimestampType(), True),
        StructField("passenger_count", IntegerType(), True),
        StructField("trip_distance", FloatType(), True),
        StructField("RatecodeID", IntegerType(), True),
        StructField("store_and_fwd_flag", StringType(), True),
        StructField("PULocationID", IntegerType(), True),
        StructField("DOLocationID", IntegerType(), True),
        StructField("payment_type", IntegerType(), True),
        StructField("fare_amount", FloatType(), True),
        StructField("extra", FloatType(), True),
        StructField("mta_tax", FloatType(), True),
        StructField("tip_amount", FloatType(), True),
        StructField("tolls_amount", FloatType(), True),
        StructField("improvement_surcharge", FloatType(), True),
        StructField("total_amount", FloatType(), True),
        StructField("congestion_surcharge", FloatType(), True),
        StructField("airport_fee", FloatType(), True),
    ]
)

# create a DataFrame that reads from the Kafka topic
df = (
    spark.readStream.format("kafka")
    .option("kafka.bootstrap.servers", "localhost:9092")
    .option("subscribe", "nytaxi_topic")
    .load()
)

parsed_df = (
    df.selectExpr("CAST(value AS STRING) as value")
    .select(from_json(col("value"), json_schema).alias("data"))
    .select("data.*")
)

# write the DataFrame to BigQuery
query = (
    parsed_df.writeStream.outputMode("append")
    .option("checkpointLocation", "gs://<your-gcs-bucket>/checkpoints/")
    .option("path", "gs://<your-gcs-bucket>/nytaxi_data/")
    .format("bigquery")
    .option("table", "nytaxi_data.nytaxi_data")
    .start()
)

query.awaitTermination()
