SHELL=/bin/bash
include .env
.PHONY: resize spark test lambda_test t dbt r

VARS:=$(shell sed -ne 's/ *\#.*$$//; /./ s/=.*$$// p' .env )
$(foreach v,$(VARS),$(eval $(shell echo export $(v)="$($(v))")))


t: 
	@bash scripts/setup.sh

resize:
	@bash -c 'source scripts/functions.sh; resize $(arg)'

git:
	@bash -c 'source scripts/functions.sh; gitpush'

r:
	@kubectl delete -f ${arg} && cat ${arg} | envsubst | kubectl apply -f -

make rr: 
	@cat ${arg} | envsubst | kubectl apply -f -

gitex:
	@bash -c 'source scripts/functions.sh; gitpush; kill_failed; sleep 6'


schema:
	@bq show --schema --format=prettyjson $$PROJECT:$$ML_DATASET.dbt__ml__yellow_fare > myschema.json


trigger_batch_dag:
	@aws s3 cp "s3://nyc-tlc/trip data/yellow_tripdata_2022-10.parquet" s3://$$AWS_DUMMY_BUCKET

run_lambda_integration_test:
	@bash tests/integration/lambda/run_integration_test.sh

run_kafka:
	@bash scripts/run_kafka.sh

destory_kafka:
	@bash scripts/run_kafka.sh --kill