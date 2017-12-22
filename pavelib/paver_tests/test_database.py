"""
Tests for the Paver commands for updating test databases and its utility methods
"""
from unittest import TestCase

import boto

from common.test.utils import MockS3Mixin
from pavelib.utils.db_utils import is_fingerprint_in_bucket


class TestPaverDbUtils(MockS3Mixin, TestCase):
    """ Tests for paver bokchoy database utils """
    def setUp(self):
        super(TestPaverDbUtils, self).setUp()
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
