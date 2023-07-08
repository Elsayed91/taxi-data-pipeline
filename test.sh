CHANGED_K8S_COMPONENTS=$(echo ".github/workflows/components_cicd.sh components/flaskapp/docker/Dockerfile components/flaskapp/docker/app.py components/flaskapp/docker/requirements.txt components/flaskapp/docker/templates/404.html components/flaskapp/docker/templates/500.html components/flaskapp/manifests/docs_app_deployment.yaml components/flaskapp/manifests/docs_app_service.yaml components/ml_serve/docker/serve_utils.py"  | xargs -n1 | grep -E "components/.+/manifests") 
echo ${CHANGED_K8S_COMPONENTS}
IFS=' ' read -r -a array <<<"$CHANGED_K8S_COMPONENTS"
for component in "${array[@]}"; do
    echo "Building image for $component..."
done