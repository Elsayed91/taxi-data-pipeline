#!/bin/bash
# this integration test requires localstack, terraform and kubectl installed.
# get localstack here python3 -m pip install localstack

set -e

# SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
cd $SCRIPT_DIR
# rm -rf ${SCRIPT_DIR}/files/*
# cp ${SCRIPT_DIR}/../../../components/lambda/* ${SCRIPT_DIR}/files/
# python -m pip install --target ${SCRIPT_DIR}/files -r ${SCRIPT_DIR}/files/requirements.txt

SERVICES=lambda,iam,secretsmanager,s3 nohup localstack start &

# kubectl exec -t $(kubectl get pods -o name --field-selector=status.phase=Running | grep airflow) -c scheduler -- airflow dags list-runs -d lambda_integration_test

process_id=$(ps aux | grep nohup | awk '{print $2}')
kill $process_id

dag_id | run_id | state | execution_date | start_date | end_date
========================+======================================+=========+===========================+==================================+=================================
lambda_integration_test | manual__2023-01-05T13:51:18+00:00 | success | 2023-01-05T13:51:18+00:00 | 2023-01-05T13:51:18.968473+00:00 | 2023-01-05T13:51:20.898639+00:00
lambda_integration_test | manual__2023-01-05T13:49:46+00:00 | success | 2023-01-05T13:49:46+00:00 | 2023-01-05T13:49:47.499795+00:00 | 2023-01-05T13:49:49.425352+00:00
lambda_integration_test | manual__2023-01-05T13:38:57+00:00 | failed | 2023-01-05T13:38:57+00:00 | 2023-01-05T13:38:57.803725+00:00 | 2023-01-05T13:38:59.688730+00:00
lambda_integration_test | scheduled__2023-01-04T00:00:00+00:00 | success | 2023-01-04T00:00:00+00:00 | 2023-01-05T13:38:49.412232+00:00 | 2023-01-05T13:38:52.038676+00:00
lambda_integration_test | scheduled__2023-01-03T00:00:00+00:00 | success | 2023-01-03T00:00:00+00:00 | 2023-01-05T13:38:49.228748+00:00 | 2023-01-05T13:38:52.062426+00:

grep run id and status
