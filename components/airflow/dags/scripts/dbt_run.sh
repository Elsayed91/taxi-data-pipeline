#!/bin/bash
# Helper script to run DBT operations
# Script does not restrict user by predefining the dbt commands to run, it leaves it open for you to enter them
# yet provides way to to also reduce cluter from having to input too many commands, namely docs generation commands
# options:
# --commands: This option takes a string containing multiple commands separated by semicolons (;) as its argument.
# The script will split the string into an array of commands and run each command in the order they are listed.
# --generate-docs: When this option is present, the script will run the dbt docs generate command to generate DBT documentation,
# and then run the upload_results.py script to upload the static HTML documentation to Google Cloud Storage.
# It will also run the edr monitor send-report command to generate an Elementary report and upload it to the specified GCS bucket.
# --debug: When this option is present, the script will run the dbt debug command with the specified profiles directory.
# --deps: When this option is present, the script will run the dbt deps command with the specified profiles directory to install dependencies.

cd ${DBT_PROFILES_DIR}
echo ${PWD}
set -e
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
    --commands)
        commands="$2"
        shift
        shift
        ;;
    --generate-docs)
        generate_docs=true
        shift
        ;;
    --debug)
        debug=true
        shift
        ;;
    --deps)
        deps=true
        shift
        ;;
    esac
done

if [[ -n $deps ]]; then
    echo "installing dependencies."
    dbt deps
fi

if [[ -n $commands ]]; then
    IFS=';' read -r -a array <<<"$commands"
    for command in "${array[@]}"; do
        echo "running "${command}"."
        $command
    done
fi
if [[ -n $generate_docs ]]; then
    echo "generating dbt docs."
    dbt docs generate
    SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
    echo "uploading dbt docs static HTML to GCS"
    python ${SCRIPT_DIR}/upload_dbt_results.py
    echo "generating elementary report."
    edr monitor send-report --profiles-dir ${DBT_PROFILES_DIR} \
        --google-service-account-path $KEYFILE \
        --gcs-bucket-name gs://$DOCS_BUCKET/elementary
    # --update-bucket-website true \
    # --bucket-file-path elementary/
fi

if [[ -n $debug ]]; then
    echo "running dbt debug."
    dbt debug
fi

exit_code=$?
exit $exit_code
