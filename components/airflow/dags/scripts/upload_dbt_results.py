#!/usr/bin/env python3
"""
-   This python module is used to generate a static HTML file from the artifacts 
    produced by a dbt run command, and then upload the resulting HTML file to a 
    Google Cloud Storage (GCS) bucket.
-   The module then reads in the index.html, manifest.json, and catalog.json files
    from the target directory. It stores the contents of these files in the 
    content_index, json_manifest, and json_catalog variables.
-   the contents of the json_manifest and json_catalog variables are concatenated as JSON. 
    the product is written as dbt.html, which is uploaded to a target GCS bucket.

-   props: data-banana DBT - Generate doc in one static HTML file
    https://data-banana.github.io/dbt-generate-doc-in-one-static-html-file.html

"""
import json
import os

from google.cloud import storage


if __name__ == "__main__":
    TARGET_BUCKET = os.getenv("DOCS_BUCKET")
    PROFILES_DIR = os.getenv("DBT_PROFILES_DIR")

    search_str = 'o=[i("manifest","manifest.json"+t),i("catalog","catalog.json"+t)]'
    with open(f"{PROFILES_DIR}/target/index.html", "r") as f:
        content_index = f.read()

    with open(f"{PROFILES_DIR}/target/manifest.json", "r") as f:
        json_manifest = json.loads(f.read())

    with open(f"{PROFILES_DIR}/target/catalog.json", "r") as f:
        json_catalog = json.loads(f.read())

    with open(f"{PROFILES_DIR}/target/dbt.html", "w") as f:
        new_str = (
            "o=[{label: 'manifest', data: "
            + json.dumps(json_manifest)
            + "},{label: 'catalog', data: "
            + json.dumps(json_catalog)
            + "}]"
        )
        new_content = content_index.replace(search_str, new_str)
        f.write(new_content)
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(TARGET_BUCKET)
    blob = bucket.blob("dbt/dbt.html")
    blob.upload_from_filename(f"{PROFILES_DIR}/target/dbt.html")
    print("uploaded dbt.html")
