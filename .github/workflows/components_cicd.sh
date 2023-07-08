#!/bin/bash

set -e
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
gcloud components install gke-gcloud-auth-plugin
gcloud container clusters get-credentials $GKE_CLUSTER_NAME --project=$PROJECT --region=$GCP_ZONE

BASE_DIR=${PWD}

if [[ -n ${CHANGED_DOCKER_COMPONENTS} ]]; then
  # Loop through the changed components and build their images
  echo ${CHANGED_DOCKER_COMPONENTS}
  IFS=' ' read -r -a array <<<"$CHANGED_DOCKER_COMPONENTS"
  for component in "${array[@]}"; do
    echo "Building image for $component..."
    cd ${BASE_DIR}/components/$component/docker
    # Build cloudbuild.yaml for each component
    cat >cloudbuild.yaml <<EOL
steps:
  - id: "$component"
    name: "gcr.io/kaniko-project/executor:latest"
    args:
      [
        "--context=.",
        "--cache=true",
        "--cache-ttl=6h",
        "--destination=eu.gcr.io/${PROJECT}/$component",
      ]
EOL

    # Submit the build to Google Cloud Build
    gcloud builds submit .
    echo "Image for $component built and pushed to registry."

    if [[ $(find ${BASE_DIR}/components/$component/manifests -name "*_deployment.yaml" | wc -l) -gt 0 ]]; then
      echo "Rolling out deployment for $component..."
      kubectl rollout restart deployment $component
      echo "Deployment for $component rolled out."
    else
      echo "No Attached Kubernetes Deployment to restart. "
    fi
  done
fi

if [[ -n ${CHANGED_K8S_COMPONENTS} ]]; then
  sudo apt-get update
  sudo apt-get install -y gettext-base
  IFS=' ' read -r -a array <<<"$CHANGED_K8S_COMPONENTS"
  for component in "${array[@]}"; do
    cat $component | envsubst | kubectl apply -f -
  done
fi

