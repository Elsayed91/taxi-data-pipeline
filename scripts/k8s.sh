#!/bin/bash
# set -e
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
source ${SCRIPT_DIR}/functions.sh

# gcloud container clusters get-credentials $GKE_CLUSTER_NAME --project=$PROJECT --region=$GCP_ZONE
# kubectl create secret generic gcsfs-creds --from-file=key.json=terraform/modules/files/gcp_key_spark.json
# kubectl annotate serviceaccount $CLUSTER_KSA --overwrite iam.gke.io/gcp-service-account="${CLUSTER_SA}@${PROJECT}.iam.gserviceaccount.com"
# kubectl create secret docker-registry gcr-json-key --docker-server="${DOCKER_SERVER}" --docker-username="${DOCKER_USERNAME}" --docker-password="$(gcloud auth print-access-token)" --docker-email=any@valid.email
# kubectl patch serviceaccount $CLUSTER_KSA -p '{"imagePullSecrets": [{"name": "gcr-json-key"}]}'
# kubectl create clusterrolebinding admin-role --clusterrole=cluster-admin --serviceaccount=default:default
# kubectl create configmap scripts --from-file=components/k8s_common/scripts
#
# mass_kubectl "components/*/manifests/*_service.yaml"
# mass_kubectl "components/*/manifests/*_configmap.yaml"
# mass_kubectl "components/*/manifests/*_secrets.yaml"
# sleep 10
# mass_kubectl "components/*/manifests/*_deployment.yaml"
# wait_for_all_pods

# kubectl exec -t $(kubectl get pods -o name | grep airflow) -c scheduler -- airflow dags unpause full-refresh &&
#     airflow dags trigger full-refresh
