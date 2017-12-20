"""
tasks for controlling the databases used in tests
"""
from __future__ import print_function
import os
import tarfile

from paver.easy import sh, needs
import boto

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


def remove_cached_db_files():
    """Remove the cached db files if they exist."""
    print('Removing cached db files for bokchoy tests')
    for db_file in BOKCHOY_DB_FILES:
        try:
            db_file_path = os.path.join(
                '{}/{}'.format(Env.REPO_ROOT, CACHE_FOLDER), db_file
            )
            os.remove(db_file_path)
            print('\tRemoved {}'.format(db_file_path))
        except OSError:
            print('\tCould not remove {}. Continuing.'.format(db_file_path))
            continue


def verify_files_were_created(files):
    """
    Verify that the files were created.
    This will help notice/prevent breakages due to
    changes to the bash script file.
    """
    for file in files:
        file_path = os.path.join(CACHE_FOLDER, file)
        assert os.path.isfile(file_path)


def apply_migrations_and_create_cache_files():
    """
    Apply migrations to the test database and create the cache files.
    """
    sh('{}/scripts/reset-test-db.sh'.format(Env.REPO_ROOT))
    verify_files_were_created(BOKCHOY_DB_FILES)


def calculate_bokchoy_migrations():
    """
    Run the calculate-bokchoy-migrations script, which will generate two
    yml files. These tell whether or not we need to run migrations.
    """
    sh('{}/scripts/calculate-bokchoy-migrations.sh'.format(Env.REPO_ROOT))
    verify_files_were_created(MIGRATION_OUTPUT_FILES)


def fingerprint_bokchoy_db_files():
    """
    Generate a sha1 checksum for files used to configure the bokchoy databases.
    This checksum will represent the current 'state' of the databases,
    including schema, migrations to be run, and data. It can be used to
    determine if the databases need to be updated.
    WARNING: this will give different results depending on whether the
    bokchoy database has been flushed or not.
    """
    calculate_bokchoy_migrations()
    file_paths = [
        os.path.join(CACHE_FOLDER, db_file) for db_file in ALL_DB_FILES
    ]

    fingerprint = compute_fingerprint(file_paths)
    print("The fingerprint for bokchoy db files is: {}".format(fingerprint))
    return fingerprint


@needs('pavelib.prereqs.install_prereqs')
@PassthroughTask
@timed
def update_bokchoy_db_cache():
    """
    Update and cache the MYSQL database for bokchoy testing:
    * Remove any previously cached database files
    * Apply migrations on a fresh db
    * Write the collective sha1 checksum for all of these files to disk

    WARNING: this method will remove your current cached files
             and apply migrations, which could take several minutes.
    """
    remove_cached_db_files()
    apply_migrations_and_create_cache_files()

    # Write the fingerprint of the database files to disk for use
    # in future comparisons.
    fingerprint = fingerprint_bokchoy_db_files()
    with open(FINGERPRINT_FILEPATH, 'w') as fingerprint_file:
        fingerprint_file.write(fingerprint)


def extract_bokchoy_db_cache_files(files=BOKCHOY_DB_FILES, path=CACHE_FOLDER):
    """ Extract the files retrieved from S3."""
    remove_cached_db_files()
    with tarfile.open(name=path, mode='r') as tar_file:
        for name in files:
            tar_file.extract(name=name, path=path)
    verify_files_were_created(BOKCHOY_DB_FILES)


def get_bokchoy_db_cache_from_s3(fingerprint, bucket_name=CACHE_BUCKET_NAME, path=CACHE_FOLDER):
    """
    Retrieve the zip file with the fingerprint
    """
    zipfile_name = '{}.tar.gz'.format(fingerprint)
    zipfile_path = os.path.join(path, zipfile)

    conn = boto.connect_s3()
    bucket = conn.get_bucket(bucket_name)
    key = boto.s3.key.Key(bucket=bucket_name, name=zipfile_name)
    assert key.exists()

    with open(zipfile_path, 'w') as zipfile:
        key.get_contents_to_file(zipfile)

    extract_bokchoy_db_cache_files()


def create_tarfile(fingerprint, files=BOKCHOY_DB_FILES, path=CACHE_FOLDER):
    """ Create a tar.gz file with the current bokchoy DB cache files."""
    zipfile_name = '{}.tar.gz'.format(fingerprint)
    zipfile_path = os.path.join(path, zipfile_name)
    with tarfile.open(name=zipfile_path, mode='w:gz') as tar_file:
        for name in files:
            tarfile.add(name)


def is_fingerprint_in_bucket(fingerprint, bucket_name=CACHE_BUCKET_NAME):
    """
    Test if a zip file matching the given fingerprint is present within an s3 bucket
    """
    zipfile_name = '{}.tar.gz'.format(fingerprint)
    conn = boto.connect_s3()
    bucket = conn.get_bucket(bucket_name)
    key = boto.s3.key.Key(bucket=bucket, name=zipfile_name)
    zip_present = key.exists()

    msg = "a match in the {} bucket.".format(bucket_name)
    if zip_present:
        print("Found {}".format(msg))
    else:
        print("Couldn't find {}".format(msg))
    return zip_present


def get_bokchoy_db_fingerprint_from_file():
    """ Return the value recorded in the fingerprint file."""
    try:
        with open(FINGERPRINT_FILEPATH, 'r') as fingerprint_file:
            cached_fingerprint = fingerprint_file.read().strip()
    except IOError:
        return None
    return cached_fingerprint


def do_fingerprints_match():
    """
    Determine if the current state of the bokchoy databases and related files
    have changed since the last time they were updated in the repository by
    comparing their fingerprint to the fingerprint saved in the repo.
    """
    current_fingerprint = fingerprint_bokchoy_db_files()
    cached_fingerprint = get_bokchoy_db_fingerprint_from_file()
    return current_fingerprint == cached_fingerprint
