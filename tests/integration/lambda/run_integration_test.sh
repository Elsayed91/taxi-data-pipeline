#!/bin/bash
# this integration test requires localstack, terraform and kubectl installed.
# get localstack here python3 -m pip install localstack

set -e

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
cd $SCRIPT_DIR

cp -r ${SCRIPT_DIR}/../../../components/lambdafn/* ${SCRIPT_DIR}/files/
python -m pip install --target ${SCRIPT_DIR}/files -r ${SCRIPT_DIR}/files/requirements.txt

SERVICES=lambda,iam,secretsmanager,s3,logs nohup localstack start &

terraform init && terraform apply --auto-approve
sleep 5
aws --endpoint-url=http://localhost:4566 secretsmanager create-secret --name gcp_key \
    --secret-string file://${SCRIPT_DIR}/../../../terraform/modules/files/lambda_key.json \
    --region eu-west-1
touch yellow_tripdata_2019-08.parquet
aws --endpoint-url=http://localhost:4566 \
    s3api put-object --bucket test-bucket \
    --key yellow_tripdata_2019-08.parquet \
    --body=yellow_tripdata_2019-08.parquet \
    --region eu-west-1

sleep 60

max_wait_time=150
wait_interval=10
elapsed_time=0

while true; do
    test_run_info=$(kubectl exec -t $(kubectl get pods -o name --field-selector=status.phase=Running | grep airflow) -c scheduler -- airflow dags list-runs -d lambda_integration_test -o yaml | head -6)
    if [[ -n "$test_run_info" ]]; then
        start_date=$(echo "$test_run_info" | grep "start_date" | awk '{print $2}' | tr -d "'")
        state=$(echo "$test_run_info" | grep "state" | awk '{print $2}')

        start_timestamp=$(date -d "$start_date" +%s)
        current_timestamp=$(date +%s)
        if ((current_timestamp - start_timestamp > 180)); then
            if ((elapsed_time >= max_wait_time)); then
                echo "Error: Waited for $elapsed_time seconds and the last run is still not within the past 3 minutes"
            fi
            echo "Last run is not within the past 3 minutes, waiting for $wait_interval seconds before trying again"
            sleep $wait_interval
            elapsed_time=$((elapsed_time + wait_interval))
            continue
        fi

        if [[ "$state" == "success" ]]; then
            echo "Dag was triggered successfully, and the assertions passed. Test succeeded"
        else
            echo "Dag was triggered successfully but the assertions failed. Test failed"
        fi
        break
    else
        if ((elapsed_time >= max_wait_time)); then
            echo "Dag was not triggered after waiting for $elapsed_time seconds, test failed. "
        fi
        echo "Dag was not triggered, waiting for $wait_interval seconds before trying again"
        sleep $wait_interval
        elapsed_time=$((elapsed_time + wait_interval))
    fi
done

echo "cleaning up & tearing infrastructure down."
rm -rf .terraform terraform.tfstate terraform.tfstate.backup .terraform.lock.hcl files/* yellow_tripdata_2019-08.parquet nohup.out
localstack stop
