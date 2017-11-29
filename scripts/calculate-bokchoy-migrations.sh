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
databases=(["default"]="edxtest" ["student_module_history"]="student_module_history_test")
database_order=("default" "student_module_history")

for db in "${database_order[@]}"; do
    echo "CREATE DATABASE IF NOT EXISTS ${databases[$db]};" | mysql $MYSQL_HOST -u root

    # Clear out the test database using the reset_db command which uses "DROP DATABASE" and
    # "CREATE DATABASE". This will result in an empty database.
    echo "Clearing out the $db bok_choy MySQL database."
    ./manage.py lms --settings $SETTINGS reset_db --traceback --router $db
    # Now output all the migrations in the platform to a file.
    echo "Calculating migrations."

    # We could do this with either our custom code from the edx-django-release-util repo
    # which will output in yaml format.
    # output_file="bok_choy_${db}_migrations.yaml"
    # ./manage.py lms --settings $SETTINGS show_unapplied_migrations --database $db --output_file $output_file

    # OR we could do this with the built-in django command
    # which will output in a format that is not friendly to machine parsing.
    output_file="bok_choy_${db}_migrations.txt"
    ./manage.py lms --settings $SETTINGS showmigrations --database $db > $output_file

done


