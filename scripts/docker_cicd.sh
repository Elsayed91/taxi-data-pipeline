#!/bin/bash

set -e
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)

gcloud components install gke-gcloud-auth-plugin
gcloud container clusters get-credentials $GKE_CLUSTER_NAME --project=$PROJECT --region=$GCP_ZONE

# Loop through the changed components and build their images
for component in "${CHANGED_COMPONENTS[@]}"; do
  echo "Building image for $component..."
  #   cd ${PWD}/components/$component/docker
  #   # Build cloudbuild.yaml for each component
  #   cat >cloudbuild.yaml <<EOL
  # steps:
  #   - id: "$component"
  #     name: "gcr.io/kaniko-project/executor:latest"
  #     args:
  #       [
  #         "--context=.",
  #         "--cache=true",
  #         "--cache-ttl=6h",
  #         "--destination=eu.gcr.io/${PROJECT}/$component",
  #       ]
  # EOL

  # Submit the build to Google Cloud Build
  # gcloud builds submit .

  echo "Image for $component built and pushed to registry."
  if [[ -d ${PWD}/components/$component/manifests ]]; then
    echo "Rolling out deployment for $component..."
    kubectl rollout restart deployment $component
    echo "Deployment for $component rolled out."
  else
    echo "No Attached Kubernetes Deployment to restart."
  fi
done
