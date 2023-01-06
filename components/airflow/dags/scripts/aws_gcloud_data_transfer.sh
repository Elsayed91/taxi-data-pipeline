#!/bin/bash

# A helper script to transfer data from S3 to GCS.
# Options:
# --data-source:      The data source path. Required.
# --destination:      The destination path. Required.
# --creds-file:       The credentials file to use for the transfer. Required.
# --exclude-prefixes: A list of prefixes to exclude from the transfer. Optional.
# --include-prefixes: A list of prefixes to include in the transfer. Optional.
# --check-exists:     Check if the file already exists in the destination before
#   starting the transfer. Optional. --fail-if-exists:   Fail the script if the
#   file already exists in the destination. Only applicable if --check-exists is
#   set. Optional.
# Notes:
# 1. If --include-prefixes is not set and the file name is not '*',
#   --include-prefixes is set to the file name, to transfer the exact file.
# 2. If --check-exists is set, the script will if the file already exists in the
#   destination, or continue if it does not.
# 3.  If --fail-if-exists is set, the script will exit with a status of 1 if the
#   file already exists in the destination. if not, it will exit with status of
#   0. this can be useful if you want to fail an airflow dag for example if
#   a file exists already.

while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
    --data-source)
        data_source="$2"
        shift 2
        ;;
    --destination)
        destination="$2"
        shift 2
        ;;
    --creds-file)
        creds_file="$2"
        shift 2
        ;;
    --exclude-prefixes)
        exclude_prefixes="$2"
        shift 2
        ;;
    --include-prefixes)
        include_prefixes="$2"
        shift 2
        ;;
    --check-exists)
        check_exists=true
        shift
        ;;
    --fail-if-exists)
        fail_if_exists=true
        shift
        ;;
    --)
        shift
        break
        ;;
    *)
        echo "Unrecognized option: $1" >&2
        exit 1
        ;;
    esac
done

project=$(gcloud config get-value project)
file_name=${data_source##*/} # Extract the file name from the data source path
file_name=${file_name:-*}    # Set the file name to '*' if it is empty
# Extract the directory path from the data source path
data_source=${data_source%/*}/

if [[ "${check_exists}" == true ]]; then
    file_path="${destination}/${file_name}"
    result=$(gsutil -q stat $file_path || echo 1)
    if [[ "$result" == 1 ]]; then
        # return 1 if error i.e if file doesnt exist so if ==1 file doesnt exist
        # and proceed else exists
        echo "File ${file_path} does not exist. Continuing with script."
    else
        echo "File already exists. Exiting script."
        if [[ "${fail_if_exists}" == true ]]; then
            exit 1
        else
            exit 0
        fi
    fi
fi

if [[ -z "$include_prefixes" && "$file_name" != "*" ]]; then
    job=$(gcloud transfer jobs create \
        "${data_source}" "${destination}/" \
        --source-creds-file="${creds_file}" \
        --project "${project}" \
        --include-prefixes="${file_name}" \
        ${exclude_prefixes:+"--exclude-prefixes=${exclude_prefixes[@]}"})
else
    job=$(gcloud transfer jobs create \
        "${data_source}" "${destination}/" \
        --source-creds-file="${creds_file}" \
        --project "${project}" \
        ${include_prefixes:+"--include-prefixes=${include_prefixes[@]}"} \
        ${exclude_prefixes:+"--exclude-prefixes=${exclude_prefixes[@]}"})
fi

job=$(echo "$job" | sed -n 's/.*name://p' | sed -e 's/^[[:space:]]*//' -e \
    's/[[:space:]]*$//')

echo -n "job created with id "$job""
# Wait for job to finish
while true; do
    STATUS=$(gcloud transfer operations list --job-names="${job}" \
        --format="value(metadata.status)" | grep .)
    echo -n "current job status: "$STATUS""
    if [[ -n "${STATUS}" && "${STATUS}" = "SUCCESS" ]]; then
        break
    fi
    sleep 5
done
