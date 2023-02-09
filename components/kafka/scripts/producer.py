"""
This module attempts to simulate a real-time streaming data source that can be consumed by
other applications.
The data is sent one record at a time, with a sleep interval between each record.
Data here is read from a parquet file and sent to a kafka broker in JSON format. 
"""
import pandas as pd
import time
from kafka import KafkaProducer
import json
import logging
import os

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)


KAFKA_BROKER_URL = "localhost:9092"
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC")
PARQUET_URL = (
    "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2022-11.parquet"
)
SLEEP_DURATION = int(os.getenv("SLEEP_DURATION"))

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER_URL,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

df = pd.read_parquet(PARQUET_URL)
logger.info(f"loaded dataframe (shape: {df.shape})into memory.")
df[["tpep_pickup_datetime", "tpep_dropoff_datetime"]] = df[
    ["tpep_pickup_datetime", "tpep_dropoff_datetime"]
].astype(str)
logger.info("Converted timestamps to string type due to JSON serialization limitation.")
logger.info("Streaming the data.")

for index, row in df.iterrows():
    producer.send(KAFKA_TOPIC, value=row.to_dict())
    logger.info(f"{row.to_dict()} -> sent")
    time.sleep(SLEEP_DURATION)

producer.flush()
