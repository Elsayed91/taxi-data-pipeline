#!/bin/bash
# Prompts the user to log in to their Google Cloud account
# Creates a Google Cloud project with a specified project name
# Makes the created project the default project
# Links the billing account with the project
# Enables various Google Cloud APIs for the project
# Authorizes Google Cloud Transfer Service, sets the default compute zone, and enables Docker and Kaniko build
# Configures the AWS profile with the specified access key ID, secret access key, and region.

set -e

echo "Setting Up Google Cloud Components"
echo "you will be prompted to login to your gcloud account, kindly do so."
gcloud auth application-default login -q

echo "Creating project $PROJECT"
gcloud projects create $PROJECT >/dev/null

echo "Setting the project as default project"
gcloud config set project $PROJECT >/dev/null

export GOOGLE_APPLICATION_CREDENTIALS="/home/$USER/.config/gcloud/application_default_credentials.json"

echo "Linking the billing account with the project"
gcloud beta billing projects link $PROJECT --billing-account=$GCP_BILLING_ACCOUNT >/dev/null

echo "turning on APIs needed for the project"
API_LIST=(iam iamcredentials compute storagetransfer servicemanagement
    bigqueryconnection bigqueryconnection cloudresourcemanager cloudfunctions
    artifactregistry containerregistry container cloudbuild eventarc dataproc
    secretmanager cloudresourcemanager bigquery)

for SERVICE in "${API_LIST[@]}"; do
    gcloud services enable ${SERVICE}.googleapis.com --async --project $PROJECT >/dev/null
done
echo "sleep 60 seconds to ensure that apis are turned on"
sleep 60

echo "setting up transfer service permissions, default compute zone, docker and kaniko build."
gcloud transfer authorize --add-missing >/dev/null
gcloud config set compute/zone $GCP_ZONE >/dev/null
gcloud auth configure-docker "${GCP_REGION}-docker.pkg.dev" -q >/dev/null
gcloud config set builds/use_kaniko True

echo "configuring your AWS profile"
aws configure set aws_access_key_id $AWS_ACCESS_KEY_ID
aws configure set aws_secret_access_key $AWS_SECRET_ACCESS_KEY
aws configure set aws_region $AWS_REGION
