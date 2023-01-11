#!/bin/bash

set -e
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
COMONENTS_DIR=${SCRIPT_DIR}/../components
gcloud components install gke-gcloud-auth-plugin
# Get the changed components and set them as env variable
echo $CHANGED_COMPONENTS
# Loop through the changed components and build their images
for component in "${CHANGED_COMPONENTS[@]}"; do
  echo "Building image for $component..."

  # Build cloudbuild.yaml for each component
  cat >cloudbuild.yaml <<EOL
steps:
  - id: "$component"
    name: "gcr.io/kaniko-project/executor:latest"
    args:
      [
        "--context=dir://${COMONENTS_DIR}/$component/docker",
        "--cache=true",
        "--cache-ttl=6h",
        "--destination=eu.gcr.io/${PROJECT}/$component",
      ]
EOL

  # Submit the build to Google Cloud Build
  gcloud builds submit .

  echo "Image for $component built and pushed to registry."
done

gcloud container clusters get-credentials $GKE_CLUSTER_NAME --project=$PROJECT --region=$GCP_ZONE
# Loop through the changed components and rollout the deployments
for component in $CHANGED_COMPONENTS; do
  echo "Rolling out deployment for $component..."

  # Use kubectl to rollout the deployment
  kubectl rollout restart deployment $component

  echo "Deployment for $component rolled out."
done
