FROM python:3.10-slim-buster

WORKDIR /mlflow/

RUN pip install \
        mlflow \
        gcsfs \
        psycopg2-binary \
        google-cloud-storage

COPY --chmod=0755 entrypoint.sh .
EXPOSE 5000

ENTRYPOINT ["/bin/bash", "entrypoint.sh"]


