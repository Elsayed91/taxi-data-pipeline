import pandas as pd
import time
from kafka import KafkaProducer
import json
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

KAFKA_BROKER_URL = "localhost:9092"  # replace with your Kafka broker URL
KAFKA_TOPIC = "nytaxi_topic"  # replace with your Kafka topic name
PARQUET_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2022-11.parquet"  # replace with your Parquet URL

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER_URL,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

# read the data from the Parquet file
df = pd.read_parquet(PARQUET_URL)
logger.info(f"loaded dataframe (shape: {df.shape})into memory.")
df[["tpep_pickup_datetime", "tpep_dropoff_datetime"]] = df[
    ["tpep_pickup_datetime", "tpep_dropoff_datetime"]
].astype(
    str
)  #

logger.info("Converted timestamps to string type due to serialization limitation.")
logger.info("Streaming the data.")
# stream the data one row at a time
for index, row in df.iterrows():
    logger.info(f"{row.to_dict()} -> sent")
    producer.send(KAFKA_TOPIC, value=row.to_dict())
    logger.info(f"{row.to_dict()} -> sent")
    time.sleep(2)  # wait for one minute

producer.flush()
json.dumps(msg).encode("utf-8")
