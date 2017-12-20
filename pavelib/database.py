"""
tasks for controlling the databases used in tests
"""
from __future__ import print_function
import os

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
FINGERPRINT_FILEPATH = '{}/common/test/db_cache/bokchoy_migrations.sha1'.format(Env.REPO_ROOT)


def remove_cached_db_files():
    """Remove the cached db files if they exist."""
    print('Removing cached db files for bokchoy tests')
    for db_file in BOKCHOY_DB_FILES:
        try:
            db_file_path = os.path.join(
                '{}/common/test/db_cache'.format(Env.REPO_ROOT), db_file
            )
            os.remove(db_file_path)
            print('\tRemoved {}'.format(db_file_path))
        except OSError:
            print('\tCould not remove {}. Continuing.'.format(db_file_path))
            continue


def calculate_bokchoy_migrations():
    """
    Run the calculate-bokchoy-migrations script, which will generate two
    yml files. These tell whether or not we need to run migrations.
    """
    sh('{}/scripts/calculate-bokchoy-migrations.sh'.format(Env.REPO_ROOT))


def fingerprint_bokchoy_db_files():
    """
    Generate a sha1 checksum for files used to configure the bokchoy databases.
    This checksum will represent the current 'state' of the databases,
    including schema, migrations to be run and data. It can be used to determine
    if the databases need to be updated.
    """
    calculate_bokchoy_migrations()
    file_paths = [
        os.path.join('common/test/db_cache', db_file) for db_file in ALL_DB_FILES
    ]

    fingerprint = compute_fingerprint(file_paths)
    print("Computed fingerprint for bokchoy db files: {}".format(fingerprint))
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
    """
    remove_cached_db_files()

    # Apply migrations to the test database and create the cache files
    sh('{}/scripts/reset-test-db.sh'.format(Env.REPO_ROOT))

    # Write the fingerprint of the database files to disk for use in future
    # comparisons
    fingerprint = fingerprint_bokchoy_db_files()
    with open(FINGERPRINT_FILEPATH, 'w') as fingerprint_file:
        fingerprint_file.write(fingerprint)

def is_fingerprint_in_bucket(fingerprint, bucket_name=CACHE_BUCKET_NAME):
    """
    Test if a zip file matching the given fingerprint is present within an s3 bucket
    """
    conn = boto.connect_s3()
    bucket = conn.get_bucket(bucket_name)
    zip_present = "{}.zip".format(fingerprint) in [
        k.name for k in bucket.get_all_keys()
    ]
    msg = "a match in the {} bucket.".format(bucket_name)
    if zip_present:
        print("Found {}".format(msg))
    else:
        print("Couldn't find {}".format(msg))
    return zip_present


def compare_bokchoy_db_fingerprints():
    """
    Determine if the current state of the bokchoy databases and related files
    have changed since the last time they were updated in the repository by
    comparing their fingerprint to the fingerprint saved in the repo.

    Returns:
        True if the fingerprint can be read off disk and matches, False otherwise.
    """
    try:
        with open(FINGERPRINT_FILEPATH, 'r') as fingerprint_file:
            cached_fingerprint = fingerprint_file.read().strip()
    except IOError:
        return False
    current_fingerprint = fingerprint_bokchoy_db_files()
    return current_fingerprint == cached_fingerprint
