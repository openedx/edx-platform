"""
tasks for controlling the databases used in tests
"""
from __future__ import print_function
import os
import hashlib

from paver.easy import sh, needs
import boto

from pavelib.utils.passthrough_opts import PassthroughTask
from pavelib.utils.timer import timed
from pavelib.utils.envs import Env


@needs('pavelib.prereqs.install_prereqs')
@PassthroughTask
@timed
def update_bokchoy_db_cache():
    """
    Update and cache the MYSQL database for bokchoy testing. This command
    will remove any previously cached database files and apply migrations
    on a fresh db. Additionally, the collective sha1 checksum for all of
    these files will be written to file, for future comparisons/checking
    for updates.

    You can commit the resulting files in common/test/db_cache into
    git to speed up test runs
    """
    bokchoy_db_files = [
        'bok_choy_data_default.json',
        'bok_choy_data_student_module_history.json',
        'bok_choy_migrations_data_default.sql',
        'bok_choy_migrations_data_student_module_history.sql',
        'bok_choy_schema_default.sql',
        'bok_choy_schema_student_module_history.sql'
    ]
    print('Removing cached db files for bokchoy tests')
    for db_file in bokchoy_db_files:
        try:
            db_file_path = os.path.join(
                '{}/common/test/db_cache'.format(Env.REPO_ROOT), db_file
            )
            os.remove(db_file_path)
            print('\tRemoved {}'.format(db_file_path))
        except OSError:
            continue

    sh('{}/scripts/reset-test-db.sh'.format(Env.REPO_ROOT))

    # Write the fingerprint of the database files to disk for use in future
    # comparisons
    fingerprint = fingerprint_bokchoy_db_files()
    with open('common/test/db_cache/bokchoy_migrations.sha1', 'w') as fingerprint_file:
        fingerprint_file.write(fingerprint)


def compare_bokchoy_db_fingerprints():
    """
    Determine if the current state of the bokchoy databases and related files
    have changed since the last time they were updated in the repository by
    comparing their fingerprint to the fingerprint saved in the repo
    """
    try:
        fingerprint_filepath = '{}/common/test/db_cache/bokchoy_migrations.sha1'.format(Env.REPO_ROOT)
        with open(fingerprint_filepath, 'r') as fingerprint_file:
            cached_fingerprint = fingerprint_file.read().strip()
    except IOError:
        return False
    current_fingerprint = fingerprint_bokchoy_db_files()
    return current_fingerprint == cached_fingerprint


def fingerprint_bokchoy_db_files():
    """
    Generate a sha1 checksum for files used to configure the bokchoy databases.
    This checksum will represent the current 'state' of the databases,
    including schema, migrations to be run and data. It can be used to determine
    if the databases need to be updated.
    """
    # Run the calculate-bokchoy-migrations script, which will generate two
    # yml files. These tell whether or not we need to run migrations
    sh('{}/scripts/calculate-bokchoy-migrations.sh'.format(Env.REPO_ROOT))
    db_files = [
        # Bokchoy db schema and data fixtures
        'bok_choy_data_default.json',
        'bok_choy_data_student_module_history.json',
        'bok_choy_migrations_data_default.sql',
        'bok_choy_migrations_data_student_module_history.sql',
        'bok_choy_schema_default.sql',
        'bok_choy_schema_student_module_history.sql',
        # Output files from scripts/calculate-bokchoy-migrations.sh
        'bok_choy_default_migrations.yaml',
        'bok_choy_student_module_history_migrations.yaml'
    ]
    hasher = hashlib.sha1()
    file_paths = [
        os.path.join('common/test/db_cache', db_file) for db_file in db_files
    ]
    for file_path in file_paths:
        with open(file_path, 'rb') as file_handle:
            hasher.update(file_handle.read())
    fingerprint = hasher.hexdigest()
    print("Computed fingerprint for bokchoy db files: {}".format(fingerprint))
    return fingerprint


def verify_fingerprint_in_bucket(fingerprint):
    """
    Ensure that a zip file matching the given fingerprint is present within an
    s3 bucket
    """
    conn = boto.connect_s3()
    bucket_name = os.environ.get(
        'DB_CACHE_S3_BUCKET', 'edx-tools-database-caches'
    )
    bucket = conn.get_bucket(bucket_name)
    zip_present = "{}.zip".format(fingerprint) in [
        k.name for k in bucket.get_all_keys()
    ]
    if zip_present:
        print(
            "Found a match in the {} bucket".format(bucket_name)
        )
    else:
        print(
            "Couldn't find a match in the {} bucket".format(bucket_name)
        )
    return zip_present
