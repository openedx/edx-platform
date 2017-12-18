"""
Tests for the Paver commands for updating test databases and its utility methods
"""
import shutil
import tarfile
from tempfile import mkdtemp
import os
from unittest import TestCase

import boto
from mock import patch

from common.test.utils import MockS3Mixin
from pavelib.utils.db_utils import is_fingerprint_in_bucket, extract_files_from_zip


class TestPaverDbS3Utils(MockS3Mixin, TestCase):
    """ Tests for paver bokchoy database utils related to s3 """
    def setUp(self):
        super(TestPaverDbS3Utils, self).setUp()
        conn = boto.connect_s3()
        conn.create_bucket('moto_test_bucket')
        self.bucket = conn.get_bucket('moto_test_bucket')

    def test_fingerprint_in_bucket(self):
        key = boto.s3.key.Key(bucket=self.bucket, name='testfile.tar.gz')
        key.set_contents_from_string('this is a test')
        self.assertTrue(is_fingerprint_in_bucket('testfile', 'moto_test_bucket'))

    def test_fingerprint_not_in_bucket(self):
        key = boto.s3.key.Key(bucket=self.bucket, name='testfile.tar.gz')
        key.set_contents_from_string('this is a test')
        self.assertFalse(is_fingerprint_in_bucket('otherfile', 'moto_test_bucket'))


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

        with open(extracted_file, 'r') as test_file:
            data = test_file.read()
        assert data == 'Test file content'
