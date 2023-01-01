import logging
import os

from flask import Flask, render_template, send_from_directory
from google.cloud import storage

app = Flask(__name__)
VALIDATION_BUCKET = os.environ["VALIDATION_BUCKET"]
DBT_DOCS_BUCKET = os.environ["DBT_DOCS_BUCKET"]
ELEMENTARY_BUCKET = os.environ["ELEMENTARY_BUCKET"]


# @app.route("/", defaults={"path": "docs/index.html"})


@app.route("/dbt")
def dbtdocs():
    import io

    file_obj = io.BytesIO()
    gcs = storage.Client()
    bucket = gcs.get_bucket(DBT_DOCS_BUCKET)
    blob = bucket.blob("index2.html")
    blob.download_to_file(file_obj)
    file_obj.seek(0)
    return file_obj


# @app.route("/dbt")
# def dbtdocs():
#     gcs = storage.Client()
#     bucket = gcs.get_bucket(DBT_DOCS_BUCKET)
#     try:
#         blob = bucket.get_blob("index2.html")
#         content = blob.download_as_string()
#         if blob.content_encoding:
#             resource = content.decode(blob.content_encoding)
#         else:
#             resource = content
#     return resource


@app.route("/elementary")
def elementary():
    gcs = storage.Client()
    bucket = gcs.get_bucket(ELEMENTARY_BUCKET)
    blob = bucket.get_blob("docs/index.html")
    content = blob.download_as_string()
    if blob.content_encoding:
        resource = content.decode(blob.content_encoding)
    else:
        resource = content
    return resource


# @app.route("/ge")
# def great_expectations():
#     gcs = storage.Client()
#     bucket = gcs.get_bucket(VALIDATION_BUCKET)
#     try:
#         blob = bucket.get_blob("index.html")
#         content = blob.download_as_string()
#         if blob.content_encoding:
#             resource = content.decode(blob.content_encoding)
#         else:
#             resource = content
#     except Exception as e:
#         logging.exception("couldn't get blob")
#         resource = "<p></p>"
#     return resource


if __name__ == "__main__":
    app.run()
