#!/bin/bash
mlflow server \
    --backend-store-uri postgresql://${MLFLOW_DB_USER:=mlflow}:${MLFLOW_DB_PASSWORD:=mlflow}@${POSTGRES_HOST:=localhost}:5432/${MLFLOW_DB:=mlflow} \
    --default-artifact-root "gs://${MLFLOW_BUCKET}" \
    --host 0.0.0.0 \
    --port ${MLFLOW_PORT:=6000}
