"""
Utility methods for bokchoy database manipulation.
"""


import os
import tarfile

import boto
from paver.easy import BuildFailure, sh

from pavelib.prereqs import compute_fingerprint
from pavelib.utils.envs import Env

CACHE_FOLDER = 'common/test/db_cache'
FINGERPRINT_FILEPATH = '{}/{}/bok_choy_migrations.sha1'.format(Env.REPO_ROOT, CACHE_FOLDER)


def remove_files_from_folder(files, folder):
    """
    Remove the specified files from the folder.
    Catch any errors as nonfatal.
    """
    for file_name in files:
        file_with_path = os.path.join(folder, file_name)
        try:
            os.remove(file_with_path)
            print('\tRemoved {}'.format(file_with_path))
        except OSError:
            print('\tCould not remove {}. Continuing.'.format(file_with_path))
            continue


def reset_test_db(db_cache_files, update_cache_files=True, use_existing_db=False):
    """
    Reset the bokchoy test db for a new test run

    The called script will flush your db (or create it if it doesn't yet
    exist), load in the db cache files files if they exist on disk,
    and optionally apply migrations and write up-to-date cache files.
    """
    cmd = '{}/scripts/reset-test-db.sh'.format(Env.REPO_ROOT)
    if update_cache_files:
        cmd = '{} --rebuild_cache'.format(cmd)
    if use_existing_db:
        cmd = '{} --use-existing-db'.format(cmd)
    sh(cmd)
    verify_files_exist(db_cache_files)


def compute_fingerprint_and_write_to_disk(migration_output_files, all_db_files):
    """
    Write the fingerprint for the bok choy migrations state to disk.
    """
    fingerprint = fingerprint_bokchoy_db_files(migration_output_files, all_db_files)
    write_fingerprint_to_file(fingerprint)
    return fingerprint


def fingerprint_bokchoy_db_files(migration_output_files, all_db_files):
    """
    Generate a sha1 checksum for files used to configure the bokchoy
    databases. This checksum will represent the current 'state' of
    the databases, including schema and data, as well as the yaml files
    that contain information about all the migrations.

    It can be used to determine if migrations need to be run after
    loading the schema and data.
    """
    calculate_bokchoy_migrations(migration_output_files)
    msg = "Verifying that all files needed to compute the fingerprint exist."
    print(msg)
    verify_files_exist(all_db_files)

    file_paths = [
        os.path.join(CACHE_FOLDER, db_file) for db_file in all_db_files
    ]
    msg = "Computing the fingerprint."
    print(msg)
    fingerprint = compute_fingerprint(file_paths)
    print("The fingerprint for bokchoy db files is: {}".format(fingerprint))
    return fingerprint


def write_fingerprint_to_file(fingerprint):
    """
    Write the fingerprint of the database files to disk for use
    in future comparisons. This file gets checked into the repo
    along with the files.
    """
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


def calculate_bokchoy_migrations(migration_output_files):
    """
    Run the calculate-bokchoy-migrations script, which will generate two
    yml files. These will tell us whether or not we need to run migrations.

    NOTE: the script first clears out the database, then calculates
          what migrations need to be run, which is all of them.
    """
    sh('{}/scripts/reset-test-db.sh --calculate_migrations'.format(Env.REPO_ROOT))
    verify_files_exist(migration_output_files)


def does_fingerprint_on_disk_match(fingerprint):
    """
    Determine if the fingerprint for the bokchoy database cache files
    that was written to disk matches the one specified.
    """
    cache_fingerprint = get_bokchoy_db_fingerprint_from_file()
    return fingerprint == cache_fingerprint


def is_fingerprint_in_bucket(fingerprint, bucket_name):
    """
    Test if a zip file matching the given fingerprint is present within an s3 bucket.
    If there is any issue reaching the bucket, show the exception but continue by
    returning False
    """
    zipfile_name = '{}.tar.gz'.format(fingerprint)
    try:
        conn = boto.connect_s3(anon=True)
        bucket = conn.get_bucket(bucket_name)
    except Exception as e:  # pylint: disable=broad-except
        print("Exception caught trying to reach S3 bucket {}: {}".format(bucket_name, e))
        return False
    key = boto.s3.key.Key(bucket=bucket, name=zipfile_name)
    return key.exists()


def get_bokchoy_db_fingerprint_from_file():
    """
    Return the value recorded in the fingerprint file.
    """
    try:
        with open(FINGERPRINT_FILEPATH) as fingerprint_file:
            cached_fingerprint = fingerprint_file.read().strip()
    except OSError:
        return None
    return cached_fingerprint


def get_file_from_s3(bucket_name, zipfile_name, path):
    """
    Get the file from s3 and save it to disk.
    """
    print("Retrieving {} from bucket {}.".format(zipfile_name, bucket_name))
    conn = boto.connect_s3(anon=True)
    bucket = conn.get_bucket(bucket_name)
    key = boto.s3.key.Key(bucket=bucket, name=zipfile_name)
    if not key.exists():
        msg = "Did not find expected file {} in the S3 bucket {}".format(
            zipfile_name, bucket_name
        )
        raise BuildFailure(msg)

    zipfile_path = os.path.join(path, zipfile_name)
    key.get_contents_to_filename(zipfile_path)


def extract_files_from_zip(files, zipfile_path, to_path):
    """
    Extract files from a zip.
    """
    with tarfile.open(name=zipfile_path, mode='r') as tar_file:
        for file_name in files:
            tar_file.extract(file_name, path=to_path)
    verify_files_exist(files)


def refresh_bokchoy_db_cache_from_s3(fingerprint, bucket_name, bokchoy_db_files):
    """
    If the cache files for the current fingerprint exist
    in s3 then replace what you have on disk with those.
    If no copy exists on s3 then continue without error.
    """
    path = CACHE_FOLDER
    if is_fingerprint_in_bucket(fingerprint, bucket_name):
        zipfile_name = '{}.tar.gz'.format(fingerprint)
        get_file_from_s3(bucket_name, zipfile_name, path)
        zipfile_path = os.path.join(path, zipfile_name)
        print("Extracting db cache files.")
        extract_files_from_zip(bokchoy_db_files, zipfile_path, path)
        os.remove(zipfile_path)


def create_tarfile_from_db_cache(fingerprint, files, path):
    """
    Create a tar.gz file with the current bokchoy DB cache files.
    """
    zipfile_name = '{}.tar.gz'.format(fingerprint)
    zipfile_path = os.path.join(path, zipfile_name)
    with tarfile.open(name=zipfile_path, mode='w:gz') as tar_file:
        for name in files:
            tar_file.add(os.path.join(path, name), arcname=name)
    return zipfile_name, zipfile_path


def upload_to_s3(file_name, file_path, bucket_name, replace=False):
    """
    Upload the specified files to an s3 bucket.
    """
    print("Uploading {} to s3 bucket {}".format(file_name, bucket_name))
    try:
        conn = boto.connect_s3()
    except boto.exception.NoAuthHandlerFound:
        print("No AWS credentials found. "
              "Continuing without uploading the new cache to S3.")
        return
    try:
        bucket = conn.get_bucket(bucket_name)
    except boto.exception.S3ResponseError:
        print("Unable to connect to cache bucket with these credentials. "
              "Continuing without uploading the new cache to S3.")
        return
    key = boto.s3.key.Key(bucket=bucket, name=file_name)
    bytes_written = key.set_contents_from_filename(file_path, replace=replace, policy='public-read')
    if bytes_written:
        msg = "Wrote {} bytes to {}.".format(bytes_written, key.name)
    else:
        msg = "File {} already existed in bucket {}.".format(key.name, bucket_name)
    print(msg)


def upload_db_cache_to_s3(fingerprint, bokchoy_db_files, bucket_name):
    """
    Update the S3 bucket with the bokchoy DB cache files.
    """
    zipfile_name, zipfile_path = create_tarfile_from_db_cache(
        fingerprint, bokchoy_db_files, CACHE_FOLDER
    )
    upload_to_s3(zipfile_name, zipfile_path, bucket_name)
