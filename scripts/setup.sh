#!/bin/bash
set -e
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
source ${SCRIPT_DIR}/functions.sh

## generate environmental variables that include random values
generate_random_env ${SCRIPT_DIR}/../data/random_env.csv

# ## setup GCP
# echo "Setting Up Google Cloud Components"
# echo "you will be prompted to login to your gcloud account, kindly do so."
# gcloud auth application-default login --project $PROJECT -q

# echo "Creating project $PROJECT"
# gcloud projects create $PROJECT >/dev/null

# echo "Setting the project as default project"
# gcloud config set project $PROJECT >/dev/null

# echo "Linking the billing account with the project"
# gcloud beta billing projects link $PROJECT --billing-account=$GCP_BILLING_ACCOUNT >/dev/null

# echo "turning on APIs needed for the project"
# API_LIST=(iam iamcredentials compute storagetransfer servicemanagement storage
#     bigqueryconnection cloudresourcemanager artifactregistry containerregistry
#     container cloudbuild cloudresourcemanager bigquery)

# for SERVICE in "${API_LIST[@]}"; do
#     gcloud services enable ${SERVICE}.googleapis.com --async --project $PROJECT >/dev/null
# done
# echo "sleep 60 seconds to ensure that apis are turned on"
# sleep 60

# echo "setting up transfer service permissions, default compute zone, docker and kaniko build."
# gcloud transfer authorize --add-missing >/dev/null
# gcloud config set compute/zone $GCP_ZONE >/dev/null
# gcloud auth configure-docker "${GCP_REGION}-docker.pkg.dev" -q >/dev/null
# gcloud config set builds/use_kaniko True

# ## Setup AWS
# echo "configuring your AWS profile"
# aws configure set aws_access_key_id $AWS_ACCESS_KEY_ID
# aws configure set aws_secret_access_key $AWS_SECRET_ACCESS_KEY
# aws configure set aws_region $AWS_REGION

# Terraform does not allow variables in remote bucket names, so we will use bash to
# change it directly
# sed -i 's/bucket =.*/bucket = '"\"$TF_STATE_BUCKET\""'/' ${SCRIPT_DIR}/../terraform/versions.tf
# gsutil mb -c standard -l "$GCP_REGION" "gs://$TF_STATE_BUCKET"
# gsutil versioning set on gs://$TF_STATE_BUCKET
# sleep 10
# setup infrastructure with terraform
# if [[ ! -f "terraform/modules/files/lambda_key.json" ]]; then
#     echo "creating placeholder file to circumvent terraform file() function limitations"
#     cat terraform/modules/files/lambda_key.json
# else
#     echo "lambda_key.json already exists"
# fi
# cd terraform && terraform init && terraform apply -auto-approve -compact-warnings && cd ..

# build docker images
# gcloud builds submit

# setup kubernetes
# gcloud container clusters get-credentials $GKE_CLUSTER_NAME \
#     --project=$PROJECT --region=$GCP_ZONE
# kubectl create secret generic gcsfs-creds \
#     --from-file=key.json=terraform/modules/files/gcp_key_spark.json
# kubectl annotate serviceaccount $CLUSTER_KSA \
#     --overwrite iam.gke.io/gcp-service-account="${CLUSTER_SA}@${PROJECT}.iam.gserviceaccount.com"
# kubectl create secret docker-registry gcr-json-key \
#     --docker-server="${DOCKER_SERVER}" --docker-username="${DOCKER_USERNAME}" \
#     --docker-password="$(gcloud auth print-access-token)" --docker-email=any@valid.email
# kubectl patch serviceaccount $CLUSTER_KSA \
#     -p '{"imagePullSecrets": [{"name": "gcr-json-key"}]}'
# kubectl create clusterrolebinding admin-role \
#     --clusterrole=cluster-admin --serviceaccount=default:default
# kubectl apply -f https://raw.githubusercontent.com/stakater/Reloader/master/deployments/kubernetes/reloader.yaml

# mass_kubectl "components/k8s_common/*.yaml"
# mass_kubectl "components/*/manifests/*_service.yaml"
# mass_kubectl "components/*/manifests/*_configmap.yaml"
# mass_kubectl "components/*/manifests/*_secrets.yaml"
# sleep 10
# mass_kubectl "components/*/manifests/*_deployment.yaml"
# clean_complete
# sleep 120

airflow_pod=$(kubectl get pods -o name --field-selector=status.phase=Running | grep airflow)
kubectl exec -t $airflow_pod -c scheduler -- airflow dags unpause full-refresh 
kubectl exec -t $airflow_pod -c scheduler -- airflow dags trigger full-refresh
# example batch dag run
# kubectl exec -t $airflow_pod -c scheduler -- airflow dags trigger batch-dag --conf '{"URI":"s3://nyc-tlc/trip data/yellow_tripdata_2022-10.parquet", "FILENAME":"yellow_tripdata_2022-10.parquet", "RUN_DATE": "2022-10-01", "CATEGORY": "yellow"}'
