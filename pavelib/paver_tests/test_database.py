"""
Tests for the Paver commands for updating test databases and its utility methods
"""


import os
import shutil
import tarfile
from tempfile import mkdtemp
from unittest import TestCase

import boto
from mock import call, patch, Mock

from pavelib import database
from pavelib.utils import db_utils
from pavelib.utils.db_utils import extract_files_from_zip
from pavelib.utils.envs import Env

from .utils import PaverTestCase


class TestPaverDbUtils(TestCase):
    """ Tests for paver bokchoy database utils """
    @patch('pavelib.utils.db_utils.verify_files_exist')
    def test_extract_files_from_zip(self, _mock_verify):
        test_dir = mkdtemp()
        output_dir = mkdtemp()
        self.addCleanup(shutil.rmtree, test_dir)
        self.addCleanup(shutil.rmtree, output_dir)

        tmp_file_name = os.path.join(test_dir, 'test.txt')
        with open(tmp_file_name, 'w') as tmp_file:
            tmp_file.write('Test file content')

        tmp_tarfile = os.path.join(test_dir, 'test.tar.gz')

        with tarfile.open(name=tmp_tarfile, mode='w:gz') as tar_file:
            tar_file.add(tmp_file_name, arcname='test.txt')

        extract_files_from_zip(['test.txt'], tmp_tarfile, output_dir)

        extracted_file = os.path.join(output_dir, 'test.txt')
        assert os.path.isfile(extracted_file)

        with open(extracted_file) as test_file:
            data = test_file.read()
        assert data == 'Test file content'


def _write_temporary_db_cache_files(path, files):
    """
    create some temporary files to act as the local db cache files so that
    we can compute a fingerprint
    """
    for index, filename in enumerate(files):
        filepath = os.path.join(path, filename)
        with open(filepath, 'w') as cache_file:
            cache_file.write(str(index))


class TestPaverDatabaseTasks(PaverTestCase):
    """
    Tests for the high level database tasks
    """

    def setUp(self):
        super().setUp()
        # This value is the actual sha1 fingerprint calculated for the dummy
        # files used in these tests
        self.expected_fingerprint = 'ccaa8d8dcc7d030cd6a6768db81f90d0ef976c3d'
        self.fingerprint_filename = '{}.tar.gz'.format(self.expected_fingerprint)
        self.bucket = Mock(name='test_bucket')

    @patch.object(db_utils, 'CACHE_FOLDER', mkdtemp())
    @patch.object(db_utils, 'FINGERPRINT_FILEPATH', os.path.join(mkdtemp(), 'fingerprint'))
    @patch.object(db_utils, 'sh')
    def test_load_data_from_local_cache(self, _mock_sh):
        """
        Assuming that the computed db cache file fingerprint is the same as
        the stored fingerprint, verify that we make a call to load data into
        the database without running migrations
        """
        self.addCleanup(shutil.rmtree, db_utils.CACHE_FOLDER)
        self.addCleanup(os.remove, db_utils.FINGERPRINT_FILEPATH)
        _write_temporary_db_cache_files(db_utils.CACHE_FOLDER, database.ALL_DB_FILES)
        # write the local fingerprint file with the same value than the
        # computed fingerprint
        with open(db_utils.FINGERPRINT_FILEPATH, 'w') as fingerprint_file:
            fingerprint_file.write(self.expected_fingerprint)

        with patch.object(db_utils, 'get_file_from_s3', wraps=db_utils.get_file_from_s3) as _mock_get_file:
            database.update_local_bokchoy_db_from_s3()  # pylint: disable=no-value-for-parameter
            # Make sure that the local cache files are used - NOT downloaded from s3
            self.assertFalse(_mock_get_file.called)
        calls = [
            call('{}/scripts/reset-test-db.sh --calculate_migrations'.format(Env.REPO_ROOT)),
            call('{}/scripts/reset-test-db.sh --use-existing-db'.format(Env.REPO_ROOT))
        ]
        _mock_sh.assert_has_calls(calls)

    @patch.object(database, 'CACHE_BUCKET_NAME', 'test_bucket')
    @patch.object(db_utils, 'CACHE_FOLDER', mkdtemp())
    @patch.object(db_utils, 'FINGERPRINT_FILEPATH', os.path.join(mkdtemp(), 'fingerprint'))
    @patch.object(db_utils, 'sh')
    def test_load_data_from_s3_fingerprint(self, _mock_sh):
        """
        Assuming that the computed db cache file fingerprint is different
        than the stored fingerprint AND there is a matching fingerprint file
        in s3, verify that we make a call to load data into the database
        without running migrations
        """
        self.addCleanup(shutil.rmtree, db_utils.CACHE_FOLDER)
        self.addCleanup(os.remove, db_utils.FINGERPRINT_FILEPATH)
        _write_temporary_db_cache_files(db_utils.CACHE_FOLDER, database.ALL_DB_FILES)

        # zip the temporary files and push them to s3 bucket
        zipfile_path = os.path.join(db_utils.CACHE_FOLDER, self.fingerprint_filename)
        with tarfile.open(name=zipfile_path, mode='w:gz') as tar_file:
            for name in database.ALL_DB_FILES:
                tar_file.add(os.path.join(db_utils.CACHE_FOLDER, name), arcname=name)
        key = boto.s3.key.Key(bucket=self.bucket, name=self.fingerprint_filename)
        key.set_contents_from_filename(zipfile_path, replace=False)

        # write the local fingerprint file with a different value than
        # the computed fingerprint
        local_fingerprint = '123456789'
        with open(db_utils.FINGERPRINT_FILEPATH, 'w') as fingerprint_file:
            fingerprint_file.write(local_fingerprint)

        with patch('boto.connect_s3', Mock(return_value=Mock())):
            with patch.object(db_utils, 'get_file_from_s3') as _mock_get_file:
                database.update_local_bokchoy_db_from_s3()  # pylint: disable=no-value-for-parameter
                # Make sure that the fingerprint file is downloaded from s3
                _mock_get_file.assert_called_once_with(
                    'test_bucket', self.fingerprint_filename, db_utils.CACHE_FOLDER
                )

        calls = [
            call('{}/scripts/reset-test-db.sh --calculate_migrations'.format(Env.REPO_ROOT)),
            call('{}/scripts/reset-test-db.sh --use-existing-db'.format(Env.REPO_ROOT))
        ]
        _mock_sh.assert_has_calls(calls)

    @patch.object(database, 'CACHE_BUCKET_NAME', 'test_bucket')
    @patch.object(db_utils, 'CACHE_FOLDER', mkdtemp())
    @patch.object(db_utils, 'FINGERPRINT_FILEPATH', os.path.join(mkdtemp(), 'fingerprint'))
    @patch.object(db_utils, 'sh')
    def test_load_data_and_run_migrations(self, _mock_sh):
        """
        Assuming that the computed db cache file fingerprint is different
        than the stored fingerprint AND there is NO matching fingerprint file
        in s3, verify that we make a call to load data into the database, run
        migrations and update the local db cache files
        """
        self.addCleanup(shutil.rmtree, db_utils.CACHE_FOLDER)
        self.addCleanup(os.remove, db_utils.FINGERPRINT_FILEPATH)
        _write_temporary_db_cache_files(db_utils.CACHE_FOLDER, database.ALL_DB_FILES)

        # write the local fingerprint file with a different value than
        # the computed fingerprint
        local_fingerprint = '123456789'
        with open(db_utils.FINGERPRINT_FILEPATH, 'w') as fingerprint_file:
            fingerprint_file.write(local_fingerprint)

        database.update_local_bokchoy_db_from_s3()  # pylint: disable=no-value-for-parameter
        calls = [
            call('{}/scripts/reset-test-db.sh --calculate_migrations'.format(Env.REPO_ROOT)),
            call('{}/scripts/reset-test-db.sh --rebuild_cache --use-existing-db'.format(Env.REPO_ROOT))
        ]
        _mock_sh.assert_has_calls(calls)

    @patch.object(database, 'CACHE_BUCKET_NAME', 'test_bucket')
    @patch.object(db_utils, 'CACHE_FOLDER', mkdtemp())
    @patch.object(db_utils, 'FINGERPRINT_FILEPATH', os.path.join(mkdtemp(), 'fingerprint'))
    @patch.object(db_utils, 'sh')
    def test_updated_db_cache_pushed_to_s3(self, _mock_sh):
        """
        Assuming that the computed db cache file fingerprint is different
        than the stored fingerprint AND there is NO matching fingerprint file
        in s3, verify that an updated fingeprint file is pushed to s3
        """
        self.addCleanup(shutil.rmtree, db_utils.CACHE_FOLDER)
        self.addCleanup(os.remove, db_utils.FINGERPRINT_FILEPATH)
        _write_temporary_db_cache_files(db_utils.CACHE_FOLDER, database.ALL_DB_FILES)

        # write the local fingerprint file with a different value than
        # the computed fingerprint
        local_fingerprint = '123456789'
        with open(db_utils.FINGERPRINT_FILEPATH, 'w') as fingerprint_file:
            fingerprint_file.write(local_fingerprint)

        database.update_local_bokchoy_db_from_s3()  # pylint: disable=no-value-for-parameter
        self.assertTrue(self.bucket.get_key(self.fingerprint_filename))
