"""
Tasks for controlling the databases used in tests
"""
from __future__ import print_function

from paver.easy import needs, task

from pavelib.utils.db_utils import (
    remove_files_from_folder, reset_test_db, compute_fingerprint_and_write_to_disk,
    fingerprint_bokchoy_db_files, does_fingerprint_on_disk_match, is_fingerprint_in_bucket,
    refresh_bokchoy_db_cache_from_s3, upload_db_cache_to_s3
)
from pavelib.utils.timer import timed

# Bokchoy db schema and data fixtures
BOKCHOY_DB_FILES = [
    'bok_choy_data_default.json',
    'bok_choy_data_student_module_history.json',
    'bok_choy_migrations_data_default.sql',
    'bok_choy_migrations_data_student_module_history.sql',
    'bok_choy_schema_default.sql',
    'bok_choy_schema_student_module_history.sql'
]

# Output files from scripts/calculate-bokchoy-migrations.sh
MIGRATION_OUTPUT_FILES = [
    'bok_choy_default_migrations.yaml',
    'bok_choy_student_module_history_migrations.yaml'
]

ALL_DB_FILES = BOKCHOY_DB_FILES + MIGRATION_OUTPUT_FILES
CACHE_BUCKET_NAME = 'edx-tools-database-caches'
CACHE_FOLDER = 'common/test/db_cache'


@needs('pavelib.prereqs.install_prereqs')
@task
@timed
def update_bokchoy_db_cache():
    """
    Update and cache the MYSQL database for bokchoy testing:
    * Remove any previously cached database files
    * Apply migrations on a fresh db
    * Write the collective sha1 checksum for all of these files to disk

    WARNING: This will take several minutes.
    """
    print('Removing cached db files for bokchoy tests')
    remove_files_from_folder(BOKCHOY_DB_FILES, CACHE_FOLDER)
    reset_test_db(BOKCHOY_DB_FILES, update_cache_files=True)
    compute_fingerprint_and_write_to_disk(MIGRATION_OUTPUT_FILES, ALL_DB_FILES)


@needs('pavelib.prereqs.install_prereqs')
@task
@timed
def update_local_bokchoy_db_from_s3():
    """
    Update the MYSQL database for bokchoy testing:
    * Determine if your current cache files are up to date
      with all the migrations
    * If not then check if there is a copy up at s3
    * If so then download then extract it
    * Otherwise apply migrations as usual and push the new cache
      files to s3
    """
    fingerprint = fingerprint_bokchoy_db_files(MIGRATION_OUTPUT_FILES, ALL_DB_FILES)

    if does_fingerprint_on_disk_match(fingerprint):
        print ("DB cache files match the current migrations.")
        reset_test_db(BOKCHOY_DB_FILES, update_cache_files=False)

    elif is_fingerprint_in_bucket(fingerprint, CACHE_BUCKET_NAME):
        print ("Found updated bokchoy db files at S3.")
        refresh_bokchoy_db_cache_from_s3(fingerprint, CACHE_BUCKET_NAME, BOKCHOY_DB_FILES)
        reset_test_db(BOKCHOY_DB_FILES, update_cache_files=False)

    else:
        msg = "{} {} {}".format(
            "Did not find updated bokchoy db files at S3.",
            "Loading the bokchoy db files from disk",
            "and running migrations."
        )
        print (msg)
        reset_test_db(BOKCHOY_DB_FILES, update_cache_files=True)
        # Check one last time to see if the fingerprint is present in
        # the s3 bucket. This could occur because the bokchoy job is
        # sharded and running the same task in parallel
        if not is_fingerprint_in_bucket(fingerprint, CACHE_BUCKET_NAME):
            upload_db_cache_to_s3(fingerprint, BOKCHOY_DB_FILES, CACHE_BUCKET_NAME)
        else:
            msg = "{} {}. {}".format(
                "Found a matching fingerprint in bucket ",
                CACHE_BUCKET_NAME,
                "Not pushing to s3"
            )
            print(msg)
