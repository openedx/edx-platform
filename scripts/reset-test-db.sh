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

DB_CACHE_DIR="common/test/db_cache"

declare -A databases
databases=(["default"]="edxtest" ["student_module_history"]="student_module_history_test")


# Ensure the test database exists.
for db in "${!databases[@]}"; do
    echo "CREATE DATABASE IF NOT EXISTS ${databases[$db]};" | mysql -u root

    # Clear out the test database
    ./manage.py lms --settings bok_choy reset_db --traceback --noinput --router $db

    if [[ ! -f $DB_CACHE_DIR/bok_choy_schema_$db.sql || ! -f $DB_CACHE_DIR/bok_choy_data_$db.json ]]; then
        REBUILD_CACHE=true
    fi
done

# If there are cached database schemas/data, load them
if [[ -z $REBUILD_CACHE ]]; then

    for db in "${!databases[@]}"; do
        # Load the schema, then the data (including the migration history)
        mysql -u root "${databases["$db"]}" < $DB_CACHE_DIR/bok_choy_schema_$db.sql
        ./manage.py lms --settings bok_choy loaddata --database $db $DB_CACHE_DIR/bok_choy_data_$db.json
    done

    # Re-run migrations to ensure we are up-to-date
    ./manage.py lms --settings bok_choy migrate --traceback --noinput
    ./manage.py cms --settings bok_choy migrate --traceback --noinput

# Otherwise, update the test database and update the cache
else

    # Clean the cache directory
    rm -rf $DB_CACHE_DIR && mkdir -p $DB_CACHE_DIR

    # Re-run migrations on the test database
    ./manage.py lms --settings bok_choy syncdb --traceback --noinput
    ./manage.py cms --settings bok_choy syncdb --traceback --noinput
    ./manage.py lms --settings bok_choy migrate --traceback --noinput
    ./manage.py cms --settings bok_choy migrate --traceback --noinput

    for db in "${!databases[@]}"; do
        # Dump the schema and data to the cache
        ./manage.py lms --settings bok_choy dumpdata --database $db > $DB_CACHE_DIR/bok_choy_data_$db.json
        mysqldump -u root --no-data --skip-comments --skip-dump-date "${databases["$db"]}" > $DB_CACHE_DIR/bok_choy_schema_$db.sql
    done
fi
