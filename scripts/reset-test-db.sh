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

# Ensure the test database exists.
echo "CREATE DATABASE IF NOT EXISTS edxtest;" | mysql -u root

# Clear out the test database
./manage.py lms --settings bok_choy reset_db --traceback --noinput

# If there are cached database schemas/data, load them
if [[ -f $DB_CACHE_DIR/bok_choy_schema.sql && -f $DB_CACHE_DIR/bok_choy_data.json ]]; then

    # Load the schema, then the data (including the migration history)
    echo "Loading cached schema and fixture data..."
    mysql -u root edxtest < $DB_CACHE_DIR/bok_choy_schema.sql
    ./manage.py lms --settings bok_choy loaddata $DB_CACHE_DIR/bok_choy_data.json

    # Re-run migrations to ensure we are up-to-date
    echo "Executing lms migrations..."
    ./manage.py lms --settings bok_choy migrate --traceback --noinput --verbosity 0
    echo "Executing studio migrations..."
    ./manage.py cms --settings bok_choy migrate --traceback --noinput --verbosity 0
    echo "Finished resetting the bok-choy test database."

# Otherwise, update the test database and update the cache
else

    # Clean the cache directory
    rm -rf $DB_CACHE_DIR && mkdir -p $DB_CACHE_DIR

    # Re-run migrations on the test database
    ./manage.py lms --settings bok_choy syncdb --traceback --noinput
    ./manage.py cms --settings bok_choy syncdb --traceback --noinput
    ./manage.py lms --settings bok_choy migrate --traceback --noinput
    ./manage.py cms --settings bok_choy migrate --traceback --noinput

    # Dump the schema and data to the cache
    ./manage.py lms --settings bok_choy dumpdata > $DB_CACHE_DIR/bok_choy_data.json
    mysqldump -u root --no-data --skip-comments --skip-dump-date edxtest > $DB_CACHE_DIR/bok_choy_schema.sql
fi

