"""
This is a Flask app that provides routes for serving multiple static documentation pages from Google Cloud Storage. 
The app has four routes, /dbt, /elementary, /ge, and a default error handler route for handling server errors.
Any number of static docs can be served through this app by simply including one more load_index and route.
"""
import os
from flask import Flask, render_template, send_from_directory, send_file
import logging
from typing import Union
import gcsfs

app = Flask(__name__)


def load_index(bucket: str, index_path: str) -> Union[bytes, str]:
    """
    Load the index file from the specified bucket and index path.

    Parameters:
    - bucket: the name of the bucket in Google Cloud Storage
    - index_path: the path to the index file in the bucket

    Returns:
    - the contents of the index file as a bytes object, or a string resource if an error occurs
    """
    try:
        with gcsfs.GCSFileSystem().open(f"gs://{bucket}/{index_path}") as f:
            return f.read()
    except Exception as e:
        logging.exception("couldn't get index.")
        resource = "<p>couldn't get index page. maybe you have not created it yet?</p>"
        return resource


DOCS_BUCKET = os.getenv("DOCS_BUCKET", "docs-bffa103539")


@app.route("/dbt")
def dbtdocs():
    return load_index(DOCS_BUCKET, "dbt/dbt.html")  # change to index.html


@app.route("/elementary")
def elementary():
    return load_index(DOCS_BUCKET, "elementary/index.html")


@app.route("/ge")
def ge():
    return load_index(DOCS_BUCKET, "great_expectations/docs/index.html")


@app.route("/ge/static/<path:filename>")
def serve_static(filename):
    return load_index(DOCS_BUCKET, f"great_expectations/docs/{filename}")


@app.errorhandler(500)
def internal_error(error):
    logging.exception("An error occurred during a request.")
    return render_template("500.html"), 500


@app.errorhandler(404)
def not_found_error(error):
    logging.exception("The page doesn't exist.")
    return render_template("404.html"), 404


@app.route("/")
def index():
    return render_template("index.html")
