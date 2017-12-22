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

declare -a database_order
database_order=("default" "student_module_history")

for db in "${database_order[@]}"; do
    # Use a different database than the one used for testing,
    # because we will need to empty out the database to calculate
    # the migrations fingerprint.
    # Choosing an arbitrary name "calculate_migrations" for the db.
    echo "DROP DATABASE IF EXISTS calculate_migrations;" | mysql $MYSQL_HOST -u root
    echo "CREATE DATABASE calculate_migrations;" | mysql $MYSQL_HOST -u root

    # Now output all the migrations in the platform to a file.
    echo "Calculating migrations for fingerprinting."

    output_file="common/test/db_cache/bok_choy_${db}_migrations.yaml"
    # Redirect stdout to /dev/null because the script will print
    # out all migrations to both stdout and the output file.
    ./manage.py lms --settings $SETTINGS show_unapplied_migrations --database $db --output_file $output_file 1>/dev/null
done

echo "DROP DATABASE IF EXISTS calculate_migrations;" | mysql $MYSQL_HOST -u root
