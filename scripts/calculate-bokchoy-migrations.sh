#!/usr/bin/env bash

############################################################################
#
#   Output all migrations that would be applied to an
#   empty database for the bok-choy acceptance tests.
#
############################################################################

# Fail fast
set -e

if [[ -z "$BOK_CHOY_HOSTNAME" ]]; then
    MYSQL_HOST=""
    SETTINGS="bok_choy"
else
    MYSQL_HOST="--host=edx.devstack.mysql"
    SETTINGS="bok_choy_docker"
fi

declare -A databases
declare -a database_order
# databases=(["default"]="edxtest" ["student_module_history"]="student_module_history_test")
# database_order=("default" "student_module_history")


databases=(["student_module_history"]="calculate_migrations")
database_order=("student_module_history")


for db in "${database_order[@]}"; do
    echo "DROP DATABASE IF EXISTS calculate_migrations;" | mysql $MYSQL_HOST -u root
    echo "CREATE DATABASE calculate_migrations;" | mysql $MYSQL_HOST -u root

    # Now output all the migrations in the platform to a file.
    echo "Calculating migrations."

    output_file="common/test/db_cache/bok_choy_${db}_migrations.yaml"
    # Redirect stdout to /dev/null because it prints all migrations to both
    # stdout and the output file.
    ./manage.py lms --settings $SETTINGS show_unapplied_migrations --database $db --output_file $output_file 1>/dev/null

done

echo "DROP DATABASE IF EXISTS calculate_migrations;" | mysql $MYSQL_HOST -u root
