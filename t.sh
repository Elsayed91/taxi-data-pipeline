#!/bin/bash
# This script is used to transfer files from an AWS S3 bucket to a Google Cloud Storage bucket.
# It accepts the following arguments:
# source-bucket, target-bucket, project, creds-file, include-prefixes, exclude-prefixes, and check-exists.
# It has an option to check if the files already exist before transferring them.

while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
    --source)
        source="$2"
        shift 2
        ;;
    --destination)
        destination="$2"
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
    --fail-if-exists)
        fail_if_exists=true
        shift
        ;;
    *)
        echo "Unrecognized option: $1" >&2
        exit 1
        ;;
    esac
done

if [[ -z "$project" ]]; then
    project=$(gcloud config get-value project)
fi

file_part=${source##*/}

if [[ -z "$file_part" ]]; then
    # Filename is empty, so set source and filename to *
    source=${source%/*}/
    filename="*"
else
    # Filename is not empty, so set source and include_prefixes
    source=${source%/*}/
    filename=$file_part
    include_prefixes="$filename"

fi

if [[ "${check_exists}" == true ]]; then
    file_path="${destination}/${filename}"
    result=$(gsutil -q stat $file_path || echo 1)
    if [[ "$result" == 1 ]]; then # If the result is 1, then the file does not exist
        echo "File does not exist. Continuing with script."
    else
        echo "File already exists. Exiting script."
        if [[ "${fail_if_exists}" == true ]]; then
            exit 1
        else
            exit 0
        fi
    fi
fi

echo 'pre job echo'

job=$(gcloud transfer jobs create \
    "${source}" "${destination}/" \
    --source-creds-file="${creds_file}" \
    --project "${project}" \
    ${include_prefixes:+"--include-prefixes=${include_prefixes[@]}"} \
    ${exclude_prefixes:+"--exclude-prefixes=${exclude_prefixes[@]}"} |
    sed -n 's/.*name://p' | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')

echo -n "job created with id $job"

if [[ "$job" =~ transferJobs/[0-9]+ ]]; then #prevents loops due to sed interferring with error
    true
else
    echo "Error: $job does not match regex transferJobs/<numbers>"
    exit 1
fi

while true; do
    STATUS=$(gcloud transfer operations list --job-names=${job} --format="value(metadata.status)")
    echo -n "current job status: $STATUS"
    if [[ -n ${STATUS} && ${STATUS} = "SUCCESS" ]]; then
        break
    fi
    sleep 5
done

#!/bin/bash
# This script is used to transfer files from an AWS S3 bucket to a Google Cloud Storage bucket.
# It accepts the following arguments:
# source-bucket, target-bucket, project, creds-file, include-prefixes, exclude-prefixes, and check-exists.
# It has an option to check if the files already exist before transferring them.

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
    if [[ "${check_exists}" == true ]]; then
        file_path="gs://${target_bucket}/${folder}/*.parquet"
        result=$(gsutil -q stat $file_path || echo 1)
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
