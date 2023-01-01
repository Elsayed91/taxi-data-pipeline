#!/bin/bash
set -e
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)

if [[ $1 == "lambda" ]]; then
    rm -rf ${SCRIPT_DIR}/lambda/*
    cp ${SCRIPT_DIR}/lambda_key.json ${SCRIPT_DIR}/lambda/
    python -m pip install --target ${SCRIPT_DIR}/lambda -r ${SCRIPT_DIR}/../../../components/lambda/requirements.txt
    cp ${SCRIPT_DIR}/../../../components/lambda/* ${SCRIPT_DIR}/lambda/
elif [[ $1 == "cloud_function" ]]; then
    rm -rf ${SCRIPT_DIR}/cloud_function/*
    rm -f ${SCRIPT_DIR}/cfn_dependencies.zip
    cp ${SCRIPT_DIR}/../../../components/airflow_trigger_cloud_fn/* ${SCRIPT_DIR}/cloud_function/
    cd ${SCRIPT_DIR}/cloud_function/ && zip -r ${SCRIPT_DIR}/cfn_dependencies.zip ./* && cd -
    gsutil cp ${SCRIPT_DIR}/cfn_dependencies.zip gs://${2}
else
    echo "please enter the type of the serverless function as 1st argument"
fi
