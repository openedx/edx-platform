"""
tasks for controlling the databases used in tests
"""
from __future__ import print_function
import os
import tarfile

import boto
from paver.easy import BuildFailure, needs, sh

from pavelib.prereqs import compute_fingerprint
from pavelib.utils.passthrough_opts import PassthroughTask
from pavelib.utils.timer import timed
from pavelib.utils.envs import Env

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
FINGERPRINT_FILEPATH = '{}/{}/bokchoy_migrations.sha1'.format(Env.REPO_ROOT, CACHE_FOLDER)


@needs('pavelib.prereqs.install_prereqs')
@PassthroughTask
@timed
def update_bokchoy_db_cache():
    """
    Update and cache the MYSQL database for bokchoy testing:
    * Remove any previously cached database files
    * Apply migrations on a fresh db
    * Write the collective sha1 checksum for all of these files to disk

    WARNING: the call to apply_migrations_and_create_cache_files
             will apply ALL migrations from scratch against an empty
             database, because we first remove the cached db files.
             This will take several minutes.
    """
    remove_cached_db_files()
    apply_migrations_and_create_cache_files()
    write_fingerprint_file()


def remove_cached_db_files():
    """
    Remove the cached db files if they exist.
    """
    print('Removing cached db files for bokchoy tests')
    for db_file in BOKCHOY_DB_FILES:
        db_file_path = os.path.join(CACHE_FOLDER, db_file)
        try:
            os.remove(db_file_path)
            print('\tRemoved {}'.format(db_file_path))
        except OSError:
            print('\tCould not remove {}. Continuing.'.format(db_file_path))
            continue


def apply_migrations_and_create_cache_files():
    """
    Apply migrations to the test database and create the cache files.

    The called script will flush your db (or create it if it doesn't yet
    exist), load in the BOKCHOY_DB_FILES files if they exist on disk,
    apply migrations, and then write up-to-date cache files.

    WARNING: This could take several minutes, depending on the
             existence and content of the original cache files.
    """
    sh('{}/scripts/reset-test-db.sh'.format(Env.REPO_ROOT))
    verify_files_exist(BOKCHOY_DB_FILES)


def write_fingerprint_file():
    """
    Write the fingerprint of the database files to disk for use
    in future comparisons. This file gets checked into the repo
    along with the files.
    """
    fingerprint = fingerprint_bokchoy_db_files()
    with open(FINGERPRINT_FILEPATH, 'w') as fingerprint_file:
        fingerprint_file.write(fingerprint)


def verify_files_exist(files):
    """
    Verify that the files were created.
    This will us help notice/prevent breakages due to
    changes to the bash script file.
    """
    for file_name in files:
        file_path = os.path.join(CACHE_FOLDER, file_name)
        if not os.path.isfile(file_path):
            msg = "Did not find expected file: {}".format(file_path)
            raise BuildFailure(msg)


def fingerprint_bokchoy_db_files():
    """
    Generate a sha1 checksum for files used to configure the bokchoy databases.
    This checksum will represent the current 'state' of the databases,
    including schema and data, as well as the yaml files that contain information
    about all the migrations.  It can be used to determine if migrations
    need to be run after loading the schema and data.
    """
    calculate_bokchoy_migrations()
    # We don't need to reverify that the MIGRATION_OUTPUT_FILES exist
    # because we just did that in calculate_bokchoy_migrations().
    verify_files_exist(BOKCHOY_DB_FILES)

    file_paths = [
        os.path.join(CACHE_FOLDER, db_file) for db_file in ALL_DB_FILES
    ]

    fingerprint = compute_fingerprint(file_paths)
    print("The fingerprint for bokchoy db files is: {}".format(fingerprint))
    return fingerprint


def calculate_bokchoy_migrations():
    """
    Run the calculate-bokchoy-migrations script, which will generate two
    yml files. These will tell us whether or not we need to run migrations.

    NOTE: the script first clears out the database, then calculates
          what migrations need to be run, which is all of them.
    """
    sh('{}/scripts/calculate-bokchoy-migrations.sh'.format(Env.REPO_ROOT))
    verify_files_exist(MIGRATION_OUTPUT_FILES)


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
    fingerprint = fingerprint_bokchoy_db_files()

    if not is_cache_up_to_date(fingerprint):
        if is_fingerprint_in_bucket(fingerprint):
            msg = "Found updated bokchoy db files at S3."
            print (msg)
            get_bokchoy_db_cache_from_s3(fingerprint)
            # TODO we dont need to rewrite the cache files
            apply_migrations_and_create_cache_files()
            write_fingerprint_file()

        else:
            msg = "{} {} {}".format(
                "Did not find updated bokchoy db files at S3.",
                "Loading the bokchoy db files from disk",
                "and running migrations."
            )
            print (msg)
            apply_migrations_and_create_cache_files()
            write_fingerprint_file()
    else:
        msg = "DB cache files match the current migrations"
        print (msg)
        # TODO we don't need to recreate the cache files.
        apply_migrations_and_create_cache_files()


def is_cache_up_to_date(current_fingerprint):
    """
    Determine if the bokchoy database cache files at the current
    commit are up to date with the migrations at the commit.
    """
    cache_fingerprint = get_bokchoy_db_fingerprint_from_file()
    return current_fingerprint == cache_fingerprint


def is_fingerprint_in_bucket(fingerprint, bucket_name=CACHE_BUCKET_NAME):
    """
    Test if a zip file matching the given fingerprint is present within an s3 bucket
    """
    zipfile_name = '{}.tar.gz'.format(fingerprint)
    conn = boto.connect_s3()
    bucket = conn.get_bucket(bucket_name)
    key = boto.s3.key.Key(bucket=bucket, name=zipfile_name)
    return key.exists()


def get_bokchoy_db_cache_from_s3(fingerprint, bucket_name=CACHE_BUCKET_NAME, path=CACHE_FOLDER):
    """
    Retrieve the zip file with the fingerprint
    """
    zipfile_name = '{}.tar.gz'.format(fingerprint)
    conn = boto.connect_s3()
    bucket = conn.get_bucket(bucket_name)
    key = boto.s3.key.Key(bucket=bucket, name=zipfile_name)
    if not key.exists():
        msg = "Did not find expected file {} in the S3 bucket {}".format(
            zipfile_name, bucket_name
        )
        raise BuildFailure(msg)

    zipfile_path = os.path.join(path, zipfile_name)
    with open(zipfile_path, 'w') as zipfile:
        key.get_contents_to_file(zipfile)

    extract_bokchoy_db_cache_files()
    # TODO remove the tar file


def get_bokchoy_db_fingerprint_from_file():
    """
    Return the value recorded in the fingerprint file.
    """
    try:
        with open(FINGERPRINT_FILEPATH, 'r') as fingerprint_file:
            cached_fingerprint = fingerprint_file.read().strip()
    except IOError:
        return None
    return cached_fingerprint


def extract_bokchoy_db_cache_files(path=CACHE_FOLDER):
    """
    Extract the files retrieved from S3.
    """
    remove_cached_db_files()
    with tarfile.open(name=path, mode='r') as tar_file:
        for name in BOKCHOY_DB_FILES:
            tar_file.extract(name=name, path=path)
    verify_files_exist(BOKCHOY_DB_FILES)


def create_tarfile(fingerprint, path=CACHE_FOLDER):
    """
    Create a tar.gz file with the current bokchoy DB cache files.
    """
    zipfile_name = '{}.tar.gz'.format(fingerprint)
    zipfile_path = os.path.join(path, zipfile_name)
    with tarfile.open(name=zipfile_path, mode='w:gz') as tar_file:
        for name in BOKCHOY_DB_FILES:
            tar_file.add(name)
