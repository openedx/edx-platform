#!/usr/bin/env bash

############################################################################
#
#   reset-test-db.sh
#
#   Resets the MySQL test database for the bok-choy acceptance tests.
#
#   If it finds a cached schema and migration history, it will start
#   from the cached version to speed up migrations.
#
#   If no cached database exists, it will create one.  This can be
#   checked into the repo to speed up future tests.
#
#   Note that we do NOT want to re-use the cache between test runs!
#   A newer commit could introduce migrations that do not exist
#   in other commits, which could cause migrations to fail in the other
#   commits.
#
#   For this reason, we always use a cache that was committed to master
#   at the time the branch was created.
#
############################################################################

# Fail fast
set -e

DB_CACHE_DIR="common/test/db_cache"

if [[ -z "$BOK_CHOY_HOSTNAME" ]]; then
    MYSQL_HOST=""
    SETTINGS="bok_choy"
else
    MYSQL_HOST="--host=edx.devstack.mysql57"
    SETTINGS="bok_choy_docker"
fi

for i in "$@"; do
    case $i in
        -r|--rebuild_cache)
            REBUILD_CACHE=true
            ;;
        -m|--migrations)
            APPLY_MIGRATIONS=true
            ;;
        -c|--calculate_migrations)
            CALCULATE_MIGRATIONS=true
            ;;
        -u|--use-existing-db)
            USE_EXISTING_DB=true
            ;;
    esac
done

declare -A databases
declare -a database_order
databases=(["default"]="edxtest" ["student_module_history"]="student_module_history_test")
database_order=("default" "student_module_history")

calculate_migrations() {
    echo "Calculating migrations for fingerprinting."
    output_file="common/test/db_cache/bok_choy_${db}_migrations.yaml"
    # Redirect stdout to /dev/null because the script will print
    # out all migrations to both stdout and the output file.
    ./manage.py lms --settings "$SETTINGS" show_unapplied_migrations --database "$db" --output_file "$output_file" 1>/dev/null
}

run_migrations() {
    echo "Running the lms migrations on the $db bok_choy DB."
    ./manage.py lms --settings "$SETTINGS" migrate --database "$db" --traceback --noinput
    echo "Running the cms migrations on the $db bok_choy DB."
    ./manage.py cms --settings "$SETTINGS" migrate --database "$db" --traceback --noinput
}

load_cache_into_db() {
    echo "Loading the schema from the filesystem into the $db MySQL DB."
    mysql "$MYSQL_HOST" -u root "${databases["$db"]}" < "$DB_CACHE_DIR/bok_choy_schema_$db.sql"
    echo "Loading the fixture data from the filesystem into the $db MySQL DB."
    ./manage.py lms --settings "$SETTINGS" loaddata --database "$db" "$DB_CACHE_DIR/bok_choy_data_$db.json"
    echo "Loading the migration data from the filesystem into the $db MySQL DB."
    mysql "$MYSQL_HOST" -u root "${databases["$db"]}" < "$DB_CACHE_DIR/bok_choy_migrations_data_$db.sql"
}

rebuild_cache_for_db() {
    # Make sure the DB has all migrations applied
    run_migrations

    # Dump the schema and data to the cache
    echo "Using the dumpdata command to save the $db fixture data to the filesystem."
    ./manage.py lms --settings "$SETTINGS" dumpdata --database "$db" > "$DB_CACHE_DIR/bok_choy_data_$db.json" --exclude=api_admin.Catalog
    echo "Saving the schema of the $db bok_choy DB to the filesystem."
    mysqldump "$MYSQL_HOST" -u root --no-data --skip-comments --skip-dump-date "${databases[$db]}" > "$DB_CACHE_DIR/bok_choy_schema_$db.sql"

    # dump_data does not dump the django_migrations table so we do it separately.
    echo "Saving the django_migrations table of the $db bok_choy DB to the filesystem."
    mysqldump $MYSQL_HOST -u root --no-create-info --skip-comments --skip-dump-date "${databases["$db"]}" django_migrations > "$DB_CACHE_DIR/bok_choy_migrations_data_$db.sql"
}

for db in "${database_order[@]}"; do
    if ! [[ $USE_EXISTING_DB ]]; then
        echo "CREATE DATABASE IF NOT EXISTS ${databases[$db]};" | mysql $MYSQL_HOST -u root

        # Clear out the test database
        #
        # We are using the reset_db command which uses "DROP DATABASE" and
        # "CREATE DATABASE" in case the tests are being run in an environment (e.g. devstack
        # or a jenkins worker environment) that already ran tests on another commit that had
        # different migrations that created, dropped, or altered tables.
        echo "Issuing a reset_db command to the $db bok_choy MySQL database."
        ./manage.py lms --settings "$SETTINGS" reset_db --traceback --router "$db"
    fi

    if ! [[ $CALCULATE_MIGRATIONS ]]; then
        # If there are cached database schemas/data, then load them.
        # If they are missing, then we will want to build new cache files even if
        # not explicitly directed to do so via arguments passed to this script.
        if [[ ! -f $DB_CACHE_DIR/bok_choy_schema_$db.sql || ! -f $DB_CACHE_DIR/bok_choy_data_$db.json || ! -f $DB_CACHE_DIR/bok_choy_migrations_data_$db.sql ]]; then
            REBUILD_CACHE=true
        else
            load_cache_into_db
        fi
    fi
done

if [[ $REBUILD_CACHE ]]; then
    echo "Cleaning the DB cache directory and building new files."
    mkdir -p $DB_CACHE_DIR && rm -f $DB_CACHE_DIR/bok_choy*

    for db in "${database_order[@]}"; do
        rebuild_cache_for_db
    done
elif [[ $APPLY_MIGRATIONS ]]; then
    for db in "${database_order[@]}"; do
        run_migrations
    done
elif [[ $CALCULATE_MIGRATIONS ]]; then
    for db in "${database_order[@]}"; do
        calculate_migrations
    done
fi
