"""
This module sets up a KafkaConsumer that consumes stream data from a Kafka topic and loads
it into BigQuery using the BigQuery API.
"""
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


consumer = KafkaConsumer(
    KAFKA_TOPIC,
    bootstrap_servers=["kafka-service:9092"],
    value_deserializer=lambda x: json.loads(x.decode("utf-8")),
)

# Construct a BigQuery client object.
client = bigquery.Client()

table_id = DESTINATION

errors = []

for msg in consumer:
    rows_to_insert = [msg.value]
    errors = client.insert_rows_json(table_id, rows_to_insert)
    if not errors:
        logger.info("New rows have been added.")
    else:
        logger.info(f"Encountered errors while inserting rows: {errors}")
