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

# kubectl exec -t $(kubectl get pods -o name --field-selector=status.phase=Running | grep airflow) -c scheduler -- airflow dags list-runs -d batch-dag

process_id=$(ps aux | grep nohup | awk '{print $2}')
kill $process_id
