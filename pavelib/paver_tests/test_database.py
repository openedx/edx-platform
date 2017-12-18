"""
Tests for the Paver commands for updating test databases
"""
import unittest
import os

import boto
from moto import mock_s3
from mock import patch

from pavelib.database import verify_fingerprint_in_bucket

class TestPaverDatabaseTasks(unittest.TestCase):


    def setUp(self):
        self.conn = boto.connect_s3()
        conn.create_bucket('moto_test_bucket')
        self.bucket = conn.get_bucket('moto_test_bucket')


    @mock_s3
    @patch.dict(os.environ, {'DB_CACHE_S3_BUCKET': 'moto_test_bucket'})
    def test_fingerprint_in_bucket(self):
        key = boto.s3.key.Key(bucket=self.bucket, name='testfile.zip')
        key.set_contents_from_string('this is a test')
        self.assertTrue(verify_fingerprint_in_bucket('testfile'))


    @mock_s3
    @patch.dict(os.environ, {'DB_CACHE_S3_BUCKET': 'moto_test_bucket'})
    def test_fingerprint_not_in_bucket(self):
        key = boto.s3.key.Key(bucket=self.bucket, name='testfile.zip')
        key.set_contents_from_string('this is a test')
        self.assertFalse(verify_fingerprint_in_bucket('otherfile'))
