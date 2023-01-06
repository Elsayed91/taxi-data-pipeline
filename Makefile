SHELL=/bin/bash
include .env secrets/secret.env 
.PHONY: resize spark test lambda_test t dbt r

FILES = .env secrets/secret.env  # files with environmental variables to export
VARS=$(shell cat $(FILES) | sed -ne 's/ *\#.*$$//; /./ s/=.*$$// p')
$(foreach v,$(VARS),$(eval $(shell echo export $(v)="$($(v))")))


t: 
	@bash scripts/setup.sh

resize:
	@bash -c 'source scripts/functions.sh; resize $(arg)'

git:
	@bash -c 'source scripts/functions.sh; gitpush'

r:
	@kubectl delete -f ${arg} && cat ${arg} | envsubst | kubectl apply -f -

gitex:
	@bash -c 'source scripts/functions.sh; gitpush; kill_failed; sleep 6; kubectl exec -t $$(kubectl get pods -o name | grep airflow) -c scheduler -- airflow dags trigger full-refresh'

k:
	@bash x.sh

schema:
	@bq show --schema --format=prettyjson $$PROJECT:$$STAGING_DATASET.$$YELLOW_STAGING_TABLE > myschema.json


lambda_test:
	@aws s3 cp yellow_tripdata_2019-08.parquet s3://stella-9af1e2ce16
# aws s3 cp "s3://nyc-tlc/trip data/yellow_tripdata_2022-10.parquet" s3://stella-9af1e2ce16

py:
	@python components/great_expectations/data_validation.py