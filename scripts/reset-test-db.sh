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
    #
    # We are using the django-extensions's reset_db command which uses "DROP DATABASE" and
    # "CREATE DATABASE" in case the tests are being run in an environment (e.g. devstack
    # or a jenkins worker environment) that already ran tests on another commit that had
    # different migrations that created, dropped, or altered tables.
    echo "Issuing a reset_db command to the bok_choy MySQL database."
    ./manage.py lms --settings bok_choy reset_db --traceback --noinput --router $db

    # If there are cached database schemas/data, load them
    if [[ ! -f $DB_CACHE_DIR/bok_choy_schema_$db.sql || ! -f $DB_CACHE_DIR/bok_choy_data_$db.json ]]; then
        echo "Missing $DB_CACHE_DIR/bok_choy_schema_$db.sql or $DB_CACHE_DIR/bok_choy_data_$db.json, rebuilding cache"
        REBUILD_CACHE=true
    fi

done

# migrations are only stored in the default database
if [[ ! -f $DB_CACHE_DIR/bok_choy_migrations_data.sql ]]; then
    REBUILD_CACHE=true
fi



# If there are cached database schemas/data, load them
if [[ -z $REBUILD_CACHE ]]; then

    echo "Found the bok_choy DB cache files. Loading them into the database..."

    for db in "${!databases[@]}"; do
        # Load the schema, then the data (including the migration history)
        echo "Loading the schema from the filesystem into the MySQL DB."
        mysql -u root "${databases["$db"]}" < $DB_CACHE_DIR/bok_choy_schema_$db.sql
        echo "Loading the fixture data from the filesystem into the MySQL DB."
        ./manage.py lms --settings bok_choy loaddata --database $db $DB_CACHE_DIR/bok_choy_data_$db.json
    done

    # Migrations are stored in the default database
    echo "Loading the migration data from the filesystem into the MySQL DB."
    mysql -u root "${databases['default']}" < $DB_CACHE_DIR/bok_choy_migrations_data.sql

    # Re-run migrations to ensure we are up-to-date
    echo "Running the lms migrations on the bok_choy DB."
    ./manage.py lms --settings bok_choy migrate --traceback --noinput
    echo "Running the cms migrations on the bok_choy DB."
    ./manage.py cms --settings bok_choy migrate --traceback --noinput

# Otherwise, update the test database and update the cache
else
    echo "Did not find a bok_choy DB cache. Creating a new one from scratch."
    # Clean the cache directory
    rm -rf $DB_CACHE_DIR && mkdir -p $DB_CACHE_DIR

    # Re-run migrations on the test database
    echo "Issuing a migrate command to the bok_choy MySQL database for the lms django apps."
    ./manage.py lms --settings bok_choy migrate --traceback --noinput
    echo "Issuing a migrate command to the bok_choy MySQL database for the cms django apps."
    ./manage.py cms --settings bok_choy migrate --traceback --noinput

    for db in "${!databases[@]}"; do
        # Dump the schema and data to the cache
        echo "Using the dumpdata command to save the fixture data to the filesystem."
        ./manage.py lms --settings bok_choy dumpdata --database $db > $DB_CACHE_DIR/bok_choy_data_$db.json
        echo "Saving the schema of the bok_choy DB to the filesystem."
        mysqldump -u root --no-data --skip-comments --skip-dump-date "${databases[$db]}" > $DB_CACHE_DIR/bok_choy_schema_$db.sql
    done

    # dump_data does not dump the django_migrations table so we do it separately.
    echo "Saving the django_migrations table of the bok_choy DB to the filesystem."
    mysqldump -u root --no-create-info "${databases['default']}" django_migrations > $DB_CACHE_DIR/bok_choy_migrations_data.sql
fi
