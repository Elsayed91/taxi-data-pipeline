#!/bin/bash
# set -e
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
source ${SCRIPT_DIR}/functions.sh

generate_random_env secrets/generate_random.csv
# # bash  ${SCRIPT_DIR}/init.sh
# cd terraform && terraform init && terraform apply -auto-approve -compact-warnings && cd ..
bash ${SCRIPT_DIR}/k8s.sh
