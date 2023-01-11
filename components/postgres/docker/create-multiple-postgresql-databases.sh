#!/bin/bash
# This script is used to initialize a PostgreSQL database with additional databases and users specified in environment variables.
# It reads environment variables that are set in the format <DB_NAME>_DB, <DB_NAME>_USER, and <DB_NAME>_PASSWORD,
# and uses them to create a new database, user, and password for the specified database

set -e

items="$(env | awk -F "=" '{print $1}' | grep ".*_DB$")"
echo $items
array=($(echo "$items" | tr ' ' '\n'))
delete="POSTGRES_DB"
databases=("${array[@]/$delete/}")
echo $databases
function create_db() {
    local db_name=$1
    local db_user=$2
    local db_password=$3
    local type=$4
    echo "$db_name, $db_user, $db_password, $type"
    if [[ -z ${db_user} ]]; then
        db_user=$type
    fi
    if [[ -z ${db_password} ]]; then
        db_password=$type
    fi
    echo "  Creating user and database $database"
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
        CREATE DATABASE $db_name;
        CREATE USER $db_user WITH SUPERUSER PASSWORD '$db_password';
        ALTER USER $db_user CREATEDB CREATEROLE;
        GRANT ALL PRIVILEGES ON DATABASE $db_name TO $db_user;
EOSQL
}

if [[ -n "$databases" ]]; then
    echo "creating extra databases."
    for db in ${databases[@]}; do
        suffix="_DB"
        type=${db/%$suffix/}
        user_literal="${db}_USER"
        password_literal="${db}_PASSWORD"
        create_db ${!db} ${!user_literal} ${!password_literal} $type >/dev/null 2>&1
        echo "created database and admin user for for ${type,,}"
    done
fi

# hellossasas
