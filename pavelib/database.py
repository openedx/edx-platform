"""
Tasks for controlling the databases used in tests
"""
from __future__ import print_function
import os

from paver.easy import needs

from pavelib.utils.db_utils import (
    remove_files_from_folder, reset_test_db, compute_fingerprint_and_write_to_disk,
    fingerprint_bokchoy_db_files, does_fingerprint_on_disk_match, is_fingerprint_in_bucket,
    get_file_from_s3, extract_files_from_zip, create_tarfile_from_db_cache, upload_to_s3
)
from pavelib.utils.passthrough_opts import PassthroughTask
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
@PassthroughTask
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
@PassthroughTask
@timed
def update_local_bokchoy_db_from_s3():
    """
    Update the MYSQL database for bokchoy testing:
    * Determine if your current cache files are up to date
      with all the migrations
    * If not then check if there is a copy up at s3
    * If so then download then extract it
    * Otherwise apply migrations as usual
    """
    fingerprint = fingerprint_bokchoy_db_files(MIGRATION_OUTPUT_FILES, ALL_DB_FILES)

    if does_fingerprint_on_disk_match(fingerprint):
        print ("DB cache files match the current migrations.")
        # TODO: we don't really need to apply migrations, just to
        # load the db cache files into the database.
        reset_test_db(BOKCHOY_DB_FILES, update_cache_files=False)

    elif is_fingerprint_in_bucket(fingerprint, CACHE_BUCKET_NAME):
        print ("Found updated bokchoy db files at S3.")
        refresh_bokchoy_db_cache_from_s3(fingerprint=fingerprint)
        reset_test_db(BOKCHOY_DB_FILES, update_cache_files=False)
        # Write the new fingerprint to disk so that it reflects the
        # current state of the system.
        compute_fingerprint_and_write_to_disk(MIGRATION_OUTPUT_FILES, ALL_DB_FILES)

    else:
        msg = "{} {} {}".format(
            "Did not find updated bokchoy db files at S3.",
            "Loading the bokchoy db files from disk",
            "and running migrations."
        )
        print (msg)
        reset_test_db(BOKCHOY_DB_FILES, update_cache_files=True)
        # Write the new fingerprint to disk so that it reflects the
        # current state of the system.
        # E.g. you could have added a new migration in your PR.
        compute_fingerprint_and_write_to_disk(MIGRATION_OUTPUT_FILES, ALL_DB_FILES)


@needs('pavelib.prereqs.install_prereqs')
@PassthroughTask
@timed
def refresh_bokchoy_db_cache_from_s3(fingerprint=None):
    """
    If the cache files for the current fingerprint exist
    in s3 then replace what you have on disk with those.
    If no copy exists on s3 then continue without error.
    """
    if not fingerprint:
        fingerprint = fingerprint_bokchoy_db_files(MIGRATION_OUTPUT_FILES, ALL_DB_FILES)

    bucket_name = CACHE_BUCKET_NAME
    path = CACHE_FOLDER
    if is_fingerprint_in_bucket(fingerprint, bucket_name):
        zipfile_name = '{}.tar.gz'.format(fingerprint)
        get_file_from_s3(bucket_name, zipfile_name, path)

        zipfile_path = os.path.join(path, zipfile_name)
        print ("Extracting db cache files.")
        extract_files_from_zip(BOKCHOY_DB_FILES, zipfile_path, path)
        os.remove(zipfile_path)


@needs('pavelib.prereqs.install_prereqs')
@PassthroughTask
@timed
def upload_db_cache_to_s3():
    """
    Update the S3 bucket with the bokchoy DB cache files.
    """
    fingerprint = fingerprint_bokchoy_db_files(MIGRATION_OUTPUT_FILES, ALL_DB_FILES)
    zipfile_name, zipfile_path = create_tarfile_from_db_cache(
        fingerprint, BOKCHOY_DB_FILES, CACHE_FOLDER
    )
    upload_to_s3(zipfile_name, zipfile_path, CACHE_BUCKET_NAME)
