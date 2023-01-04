#!/bin/bash

function generate_random_env() {
    # this function takes a CSV file with a key, expression and a destination
    # the key is the item for which a random value to be generated
    # expression is what kind of random value is to be generated
    # destination is where the key-value will be appended, like .env file
    # it first looks up if a key-value pair exist, if so, it skips the record
    # it a key exist but no value (key=) then it evaluates and add the outcome of the
    # expression as value
    # if it doesnt exist at all, it adds the key value pair
    # this section [ sed -i "/^$key=/s/=.*/=\"${value//\//\\/}\"/" "$destination" ]
    # ensures that slashes in the $value variable will be escaped using variable expansion
    # https://stackoverflow.com/questions/27787536/how-to-pass-a-variable-containing-slashes-to-sed
    # the $key == "key" also ensures that header doesnt get parsed
    input=$(<"$1")
    while IFS=',' read -r key expression destination; do
        if [[ $key == "key" ]]; then
            continue
        elif grep -q "$key=\"*\"" "$destination"; then
            continue
        elif grep -q "$key=$" "$destination"; then
            value=$(bash -c "echo $expression")
            echo $value
            sed -i "/^$key=/s/=.*/=\"${value//\//\\/}\"/" $destination
        else
            value=$(bash -c "echo $expression")
            echo "$key=\"$value\"" >>"$destination"
            export "$key=$value"
        fi
    done <<<"$input"
}

mass_kubectl() {
    # mass_kubectl [FILES...]
    # uses kubectl apply on one or more kubectl manifests
    # usage:
    # single usage: mass_kubectl my_manifest.yaml
    # multiple files: mass_kubectl manifest1.yaml manifest2.yaml manifest3.yaml
    # recusively to match a pattern: mass_kubectl "dir/*/manifests/*_service.yaml"
    # uses envsubst to substitute variables in the manifest files before applying them.
    local FILES="$@"
    for FILE in $FILES; do
        [[ -e "$FILE" ]] || continue
        cat "$FILE" | envsubst | kubectl apply -f -
    done
}

resize() {
    node_pools=$(gcloud container node-pools list --cluster $GKE_CLUSTER_NAME --format='value(name)')

    for pool in $node_pools; do
        gcloud container clusters resize $GKE_CLUSTER_NAME --node-pool $pool --num-nodes $1 -q
    done
}

gitpush() {
    git add .
    git commit -m "$(openssl rand -hex 5)"
    git push -u origin main
}

kill_failed() {
    local namespace=${1:-default}
    kubectl get pods -n $namespace | grep Error | cut -d' ' -f 1 | xargs kubectl delete pod
    kubectl get pods -n $namespace | grep CrashLoopBackOff | cut -d' ' -f 1 | xargs kubectl delete pod
    kubectl get pods -n $namespace | grep ImagePullBackOff | cut -d' ' -f 1 | xargs kubectl delete pod
}

# wait_for_all_pods() {
#     pods=$(kubectl get pods -o name)
#     for pod in "${pods}"; do
#         while [[ $(kubectl get pods ${pod#*2} -o 'jsonpath={..status.conditions[?(@.type=="Ready")].status}') != "True" ]]; do
#             echo "pod ${pod#*2} still not ready, sleeping 2 seconds"
#             sleep 2
#         done
#     done
# }
