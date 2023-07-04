SHELL=/bin/bash

# Include the environment variables from .env file
include .env

# List of all targets that are not files
.PHONY: trigger_batch_dag setup pc git run_lambda_integration_test run_kafka destory_kafka all clean test r rr 


# Load environment variables from .env file
VARS:=$(shell sed -ne 's/ *\#.*$$//; /./ s/=.*$$// p' .env )
$(foreach v,$(VARS),$(eval $(shell echo export $(v)="$($(v))")))


# Setup target to run the setup script
setup:
	@bash scripts/setup.sh

# Pre-commit target to run all pre-commit hooks
pc:
	@pre-commit run --all-files

# Git target to push changes to the remote repository
git:
	@bash -c 'source scripts/functions.sh; gitpush'

# Target to trigger the batch DAG
trigger_batch_dag:
	@aws s3 cp "s3://nyc-tlc/trip data/yellow_tripdata_2022-10.parquet" s3://$$AWS_DUMMY_BUCKET

# Target to run the integration test for Lambda
run_lambda_integration_test:
	@bash tests/integration/lambda/run_integration_test.sh

# Target to run Kafka
run_kafka:
	@bash scripts/run_kafka.sh

# Target to destroy the Kafka cluster
destory_kafka:
	@bash scripts/run_kafka.sh --kill

r:
	@kubectl delete -f ${arg} && cat ${arg} | envsubst | kubectl apply -f -

rr: 
	@cat ${arg} | envsubst | kubectl apply -f -
schema:
	@bq show --schema --format=prettyjson $$PROJECT:$$ML_DATASET.dbt__ml__yellow_fare > myschema.json