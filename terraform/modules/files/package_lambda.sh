# a script that prepares a code directory for terraform deployment as an AWS Lambda
# function by copying the code directory to a "lambda" folder, installing the required
# Python packages listed in the "requirements.txt" file to the "lambda" folder.

set -e
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)

mkdir -p ${SCRIPT_DIR}/lambda
rm -rf ${SCRIPT_DIR}/lambda/*
cp -r $1/* ${SCRIPT_DIR}/lambda
python -m pip install --target ${SCRIPT_DIR}/lambda -r ${SCRIPT_DIR}/lambda/requirements.txt
