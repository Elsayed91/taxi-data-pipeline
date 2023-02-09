import pandas as pd
import time
from kafka import KafkaProducer
import json

KAFKA_BROKER_URL = "localhost:9092"  # replace with your Kafka broker URL
KAFKA_TOPIC = "nytaxi_topic"  # replace with your Kafka topic name
PARQUET_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2022-11.parquet"  # replace with your Parquet URL

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER_URL,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

# read the data from the Parquet file
df = pd.read_parquet(PARQUET_URL)


# stream the data one row at a time
for index, row in df.iterrows():
    producer.send(KAFKA_TOPIC, value=row.to_dict())
    print(f"{row.to_dict()} -> sent")
    time.sleep(60)  # wait for one minute

producer.flush()
json.dumps(msg).encode("utf-8")
