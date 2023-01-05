#!/bin/bash
set -e

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
cd $SCRIPT_DIR

terraform destroy

# kill localstack
process_id=$(ps aux | grep nohup | awk '{print $2}')
kill $process_id
