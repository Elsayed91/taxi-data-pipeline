#!/bin/bash
# set -e
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
source ${SCRIPT_DIR}/functions.sh

# gcloud container clusters get-credentials $GKE_CLUSTER_NAME --project=$PROJECT --region=$GCP_ZONE
mass_kubectl "components/k8s_common/*"
mass_kubectl "components/*/manifests/*_service.yaml"
# kubectl create secret generic gcsfs-creds --from-file=key.json=terraform/modules/files/gcp_key_spark.json
# kubectl annotate serviceaccount $CLUSTER_KSA --overwrite iam.gke.io/gcp-service-account="${CLUSTER_SA}@${PROJECT}.iam.gserviceaccount.com"
# kubectl create secret docker-registry gcr-json-key --docker-server="${DOCKER_SERVER}" --docker-username="${DOCKER_USERNAME}" --docker-password="$(gcloud auth print-access-token)" --docker-email=any@valid.email
# kubectl patch serviceaccount $CLUSTER_KSA -p '{"imagePullSecrets": [{"name": "gcr-json-key"}]}'
# kubectl create clusterrolebinding admin-role --clusterrole=cluster-admin --serviceaccount=default:default

# yamls="components/kubernetes"
# mass_kubectl ${yamls}/misc/*.yaml
# mass_kubectl ${yamls}/services/*.yaml
# mass_kubectl ${yamls}/secrets/*.yaml ${yamls}/configmaps/*.yaml
# sleep 10
# mass_kubectl ${yamls}/deployments/*.yaml

# wait_for_all_pods #wait all deployments to be in ready status

# kubectl exec -t $(kubectl get pods -o name | grep airflow) -c scheduler -- airflow dags unpause full-refresh &&
#     airflow dags trigger full-refresh
