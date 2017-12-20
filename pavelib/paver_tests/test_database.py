"""
Tests for the Paver commands for updating test databases
"""
from unittest import TestCase

import boto
from mock import patch

from common.test.utils import MockS3Mixin
from pavelib.database import is_fingerprint_in_bucket


class TestPaverDatabaseTasks(MockS3Mixin, TestCase):
    """Tests for the Database cache file manipulation."""
    def setUp(self):
        super(TestPaverDatabaseTasks, self).setUp()
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
