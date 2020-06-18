"""
Tasks for controlling the databases used in tests
"""


from paver.easy import cmdopts, needs, task

from pavelib.utils.db_utils import (
    compute_fingerprint_and_write_to_disk,
    does_fingerprint_on_disk_match,
    fingerprint_bokchoy_db_files,
    is_fingerprint_in_bucket,
    refresh_bokchoy_db_cache_from_s3,
    remove_files_from_folder,
    reset_test_db,
    upload_db_cache_to_s3
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

# Output files from scripts/reset-test-db.sh --calculate_migrations
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
@cmdopts([
    ("rewrite_fingerprint", None, "Optional flag that will write the new sha1 fingerprint to disk")
])
def update_local_bokchoy_db_from_s3(options):
    """
    Prepare the local MYSQL test database for running bokchoy tests. Since
    most pull requests do not introduce migrations, this task provides
    an optimization for caching the state of the db when migrations are
    added into a bucket in s3. Subsequent commits can avoid rerunning
    migrations by using the cache files from s3, until the local cache files
    are updated by running the `update_bokchoy_db_cache` Paver task, and
    committing the updated cache files to github.

    Steps:
    1. Determine which migrations, if any, need to be applied to your current
       db cache files to make them up to date
    2. Compute the sha1 fingerprint of the local db cache files and the output
       of the migration
    3a. If the fingerprint computed in step 2 is equal to the local
        fingerprint file, load the cache files into the MYSQL test database
    3b. If the fingerprints are not equal, but there is bucket matching the
        fingerprint computed in step 2, download and extract the contents of
        bucket (db cache files) and load them into the MYSQL test database
    3c. If the fingerprints are not equal AND there is no bucket matching the
        fingerprint computed in step 2, load the local db cache files into
        the MYSQL test database and apply any needed migrations. Create a
        bucket in s3 named the fingerprint computed in step 2 and push the
        newly updated db cache files to the bucket.

    NOTE: the computed fingerprints referenced in this and related functions
    represent the state of the db cache files and migration output PRIOR
    to running migrations. The corresponding s3 bucket named for a given
    fingerprint contains the db cache files AFTER applying migrations
    """
    fingerprint = fingerprint_bokchoy_db_files(MIGRATION_OUTPUT_FILES, ALL_DB_FILES)
    fingerprints_match = does_fingerprint_on_disk_match(fingerprint)

    # Calculating the fingerprint already reset the DB, so we don't need to
    # do it again (hence use_existing_db=True below)
    if fingerprints_match:
        print("DB cache files match the current migrations.")
        reset_test_db(BOKCHOY_DB_FILES, update_cache_files=False, use_existing_db=True)

    elif is_fingerprint_in_bucket(fingerprint, CACHE_BUCKET_NAME):
        print("Found updated bokchoy db files at S3.")
        refresh_bokchoy_db_cache_from_s3(fingerprint, CACHE_BUCKET_NAME, BOKCHOY_DB_FILES)
        reset_test_db(BOKCHOY_DB_FILES, update_cache_files=False, use_existing_db=True)

    else:
        msg = "{} {} {}".format(
            "Did not find updated bokchoy db files at S3.",
            "Loading the bokchoy db files from disk",
            "and running migrations."
        )
        print(msg)
        reset_test_db(BOKCHOY_DB_FILES, update_cache_files=True, use_existing_db=True)
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

    rewrite_fingerprint = getattr(options, 'rewrite_fingerprint', False)
    # If the rewrite_fingerprint flag is set, and the fingerpint has changed,
    # write it to disk.
    if not fingerprints_match and rewrite_fingerprint:
        print("Updating fingerprint and writing to disk.")
        compute_fingerprint_and_write_to_disk(MIGRATION_OUTPUT_FILES, ALL_DB_FILES)
