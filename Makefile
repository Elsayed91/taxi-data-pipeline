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