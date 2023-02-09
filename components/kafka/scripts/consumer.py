from google.cloud import bigquery
import json
from kafka import KafkaConsumer
import os
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

KAFKA_TOPIC = os.getenv("KAFKA_TOPIC")
DESTINATION = os.getenv("DESTINATION")
# Set up a Kafka Consumer to subscribe to the topic
consumer = KafkaConsumer(
    KAFKA_TOPIC,
    bootstrap_servers=["kafka-service:9092"],
    value_deserializer=lambda x: json.loads(x.decode("utf-8")),
)

# Construct a BigQuery client object.
client = bigquery.Client()

table_id = DESTINATION

errors = []

# Continuously poll for new messages from the Kafka Consumer
for msg in consumer:
    rows_to_insert = [msg.value]
    errors = client.insert_rows_json(table_id, rows_to_insert)  # Make an API request.
    logger.info(f"attempted to insert {errors}")
    if errors != []:
        print("Encountered errors while inserting rows: {}".format(errors))

if errors == []:
    print("New rows have been added.")


# from pyspark.sql import SparkSession
# import os
# from pyspark.sql.functions import from_json, col
# from pyspark.sql.types import (
#     StructType,
#     StructField,
#     StringType,
#     IntegerType,
#     TimestampType,
#     FloatType,
# )

# DESTINATION = os.getenv("DESTINATION")
# TEMP_BUCKET = os.getenv("TEMP_BUCKET")
# KAFKA_TOPIC = os.getenv("KAFKA_TOPIC")
# spark = SparkSession.builder.appName("NYTaxiConsumer").getOrCreate()

# json_schema = StructType(
#     [
#         StructField("VendorID", IntegerType(), True),
#         StructField("tpep_pickup_datetime", TimestampType(), True),
#         StructField("tpep_dropoff_datetime", TimestampType(), True),
#         StructField("passenger_count", IntegerType(), True),
#         StructField("trip_distance", FloatType(), True),
#         StructField("RatecodeID", IntegerType(), True),
#         StructField("store_and_fwd_flag", StringType(), True),
#         StructField("PULocationID", IntegerType(), True),
#         StructField("DOLocationID", IntegerType(), True),
#         StructField("payment_type", IntegerType(), True),
#         StructField("fare_amount", FloatType(), True),
#         StructField("extra", FloatType(), True),
#         StructField("mta_tax", FloatType(), True),
#         StructField("tip_amount", FloatType(), True),
#         StructField("tolls_amount", FloatType(), True),
#         StructField("improvement_surcharge", FloatType(), True),
#         StructField("total_amount", FloatType(), True),
#         StructField("congestion_surcharge", FloatType(), True),
#         StructField("airport_fee", FloatType(), True),
#     ]
# )

# # create a DataFrame that reads from the Kafka topic
# df = (
#     spark.readStream.format("kafka")
#     .option("kafka.bootstrap.servers", "kafka-service:9092")
#     .option("subscribe", KAFKA_TOPIC)
#     .option("startingOffsets", "earliest")
#     .load()
# )

# parsed_df = (
#     df.selectExpr("CAST(value AS STRING) as value")
#     .select(from_json(col("value"), json_schema).alias("data"))
#     .select("data.*")
# )

# # write the DataFrame to BigQuery
# query = (
#     parsed_df.writeStream.outputMode("append")
#     .format("bigquery")
#     .option("checkpointLocation", f"gs://{TEMP_BUCKET}/checkpoints/")
#     .option("table", DESTINATION)
#     .start()
# )

# query.awaitTermination()
