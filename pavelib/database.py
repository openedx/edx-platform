"""
tasks for controlling the databases used in tests
"""
from __future__ import print_function
import os
import hashlib
import zipfile
import StringIO

from paver.easy import sh, needs
import boto

from pavelib.utils.passthrough_opts import PassthroughTask
from pavelib.utils.timer import timed
from pavelib.utils.envs import Env


BOKCHOY_DB_FILES = [
    'bok_choy_data_default.json',
    'bok_choy_data_student_module_history.json',
    'bok_choy_migrations_data_default.sql',
    'bok_choy_migrations_data_student_module_history.sql',
    'bok_choy_schema_default.sql',
    'bok_choy_schema_student_module_history.sql'
]

DB_CACHE_FILEPATH = '{}/common/test/db_cache/'.format(Env.REPO_ROOT)


@needs('pavelib.prereqs.install_prereqs')
@PassthroughTask
@timed
def generate_new_bokchoy_db_cache_files():
    """
    Update and cache the MYSQL database for bokchoy testing. This command
    will remove any previously cached database files and apply migrations
    on a fresh db. Additionally, the collective sha1 checksum for all of
    these files will be written to file, for future comparisons/checking
    for updates.

    You can commit the resulting files in common/test/db_cache into
    git to speed up test runs
    """
    print('Removing cached db files for bokchoy tests')
    return
    for db_file in BOKCHOY_DB_FILES:
        try:
            db_file_path = os.path.join(DB_CACHE_FILEPATH, db_file)
            os.remove(db_file_path)
            print('\tRemoved {}'.format(db_file_path))
        except OSError:
            continue
    sh('{}/scripts/reset-test-db.sh'.format(Env.REPO_ROOT))
    # Write the fingerprint of the database files to disk for use in future
    # comparisons
    fingerprint = fingerprint_bokchoy_db_files()
    with open(os.path.join(DB_CACHE_FILEPATH, 'bok_choy_migrations.sha1'), 'w') as fingerprint_file:
        fingerprint_file.write(fingerprint)


def compare_bokchoy_db_fingerprints(current_fingerprint):
    """
    Determine if the current state of the bokchoy databases and related files
    have changed since the last time they were updated in the repository by
    comparing their fingerprint to the fingerprint file saved in the repo
    """
    try:
        fingerprint_filepath = os.path.join(
            DB_CACHE_FILEPATH, 'bok_choy_migrations.sha1'
        )
        with open(fingerprint_filepath, 'r') as fingerprint_file:
            cached_fingerprint = fingerprint_file.read().strip()
    except IOError:
        print('Sha file is not present')
        return False
    print('Comparing {} to {}'.format(current_fingerprint, cached_fingerprint))
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
    # Append the output files
    db_files_to_fingerprint = BOKCHOY_DB_FILES + [
        'bok_choy_default_migrations.yaml',
        'bok_choy_student_module_history_migrations.yaml'
    ]
    hasher = hashlib.sha1()
    file_paths = [
        os.path.join(DB_CACHE_FILEPATH, db_file) for db_file in db_files_to_fingerprint
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


def download_cache_files(fingerprint):
    """
    Download a zipfile from an s3 bucket and extract its contents
    """
    conn = boto.connect_s3()
    bucket_name = os.environ.get(
        'DB_CACHE_S3_BUCKET', 'edx-tools-database-caches'
    )
    bucket = conn.get_bucket(bucket_name)
    print('Downloading {}.zip from {}'.format(fingerprint, bucket_name))
    key = bucket.get_key("{}.zip".format(fingerprint))
    zipped_cache = StringIO.StringIO()
    key.get_file(zipped_cache)
    with zipfile.ZipFile(zipped_cache) as zf:
        for filename in zf.namelist():
            if filename not in BOKCHOY_DB_FILES:
                print("Zipfile did not contain {}".format(filename))
                raise KeyError
            zf.extract(filename, DB_CACHE_FILEPATH)
    print('Successfully downloaded db cache files from {}'.format(bucket_name))


@PassthroughTask
def update_bokchoy_db_cache_files():
    """
    Determine if the database cache files used to prepare the MySQL database for
    bokchoy testing need to be updated before running tests. This is done by
    comparing a combined checksum of the files in question to the saved checksum
    file commited into the repository.

    If the checksums are in sync, do nothing.

    If the checksums are out of sync, first check if there are files matching
    the computed checksum in an S3 bucket, specified by the environment
    variable `DB_CACHE_S3_BUCKET`. If so, this will be downloaded and overwrite
    the db cache files on disk.

    If this fails, rerun migrations to manually update the cache files
    """
    fingerprint = fingerprint_bokchoy_db_files()
    if compare_bokchoy_db_fingerprints(fingerprint):
        msg = """Computed fingerprint for db files is the same as saved
        fingerprint. No action needed."""
        print(msg)
        return
    else:
        msg = """Computed fingerprint for db files differs from the saved
        fingerprint. Need to update the bokchoy db"""
        print(msg)
        if verify_fingerprint_in_bucket(fingerprint):
            try:
                download_cache_files(fingerprint)
            except KeyError:
                msg = """Incomplete zipfile downloaded from s3. Resetting the
                db to make sure that a valid test db is used"""
                print(msg)
                generate_new_bokchoy_db_cache_files()
        else:
            generate_new_bokchoy_db_cache_files()
