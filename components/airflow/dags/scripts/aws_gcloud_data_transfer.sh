#!/bin/bash
# This script is used to transfer files from an AWS S3 bucket to a Google Cloud Storage bucket.
# It accepts the following arguments:
# source-bucket, target-bucket, project, creds-file, include-prefixes, exclude-prefixes, and check-exists.
# It has an option to check if the files already exist before transferring them.
# usage example
# bash components/k8s_common/scripts/aws_gcloud_data_transfer.sh     \
# --source-bucket "s3://nyc-tlc/trip data/" --target-bucket gs://raw-8d74c9728b \
# --project stellarismus     --creds-file "./secrets/aws_creds.json"     \
# --include-prefixes "yellow_tripdata_20"     \
# --exclude-prefixes "yellow_tripdata_2009,yellow_tripdata_2010"     \
# --check-exists     -- "yellow"
# Parse arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
    --source-bucket)
        source_bucket="$2"
        shift 2
        ;;
    --target-bucket)
        target_bucket="$2"
        shift 2
        ;;
    --project)
        project="$2"
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

for folder in "${@}"; do
    file_path="${target_bucket}/${folder}/*.parquet"
    echo $check_exists
    if [[ "${check_exists}" == true ]]; then
        file_path="gs://${target_bucket}/${folder}/*.parquet"
        result=$(gsutil -q stat $file_path || echo 1)
        echo "result is $result"
        if [[ $result == 1 ]]; then
            echo "$file_path already exists"
            continue
        fi
    fi
    job=$(gcloud transfer jobs create \
        "${source_bucket}" "${target_bucket}/${folder}/" \
        --source-creds-file="${creds_file}" \
        --project "${project}" \
        ${include_prefixes:+"--include-prefixes=${include_prefixes[@]}"} \
        ${exclude_prefixes:+"--exclude-prefixes=${exclude_prefixes[@]}"} |
        sed -n 's/.*name://p' | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')
    echo -n "job created with id $job"
    # Wait for job to finish
    while true; do
        STATUS=$(gcloud transfer operations list --job-names=${job} --format="value(metadata.status)" | grep .)
        echo -n "current job status: $STATUS"
        if [[ -n ${STATUS} && ${STATUS} = "SUCCESS" ]]; then
            break
        fi
        sleep 5
    done

done
