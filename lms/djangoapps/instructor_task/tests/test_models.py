"""
Tests for instructor_task/models.py.
"""

from cStringIO import StringIO
import mock
import time
from datetime import datetime
from unittest import TestCase

from instructor_task.models import LocalFSReportStore, S3ReportStore
from instructor_task.tests.test_base import TestReportMixin
from opaque_keys.edx.locator import CourseLocator


class MockKey(object):
    """
    Mocking a boto S3 Key object.
    """
    def __init__(self, bucket):
        self.last_modified = datetime.now()
        self.bucket = bucket

    def set_contents_from_string(self, contents, headers):  # pylint: disable=unused-argument
        """ Expected method on a Key object. """
        self.bucket.store_key(self)

    def generate_url(self, expires_in):  # pylint: disable=unused-argument
        """ Expected method on a Key object. """
        return "http://fake-edx-s3.edx.org/"


class MockBucket(object):
    """ Mocking a boto S3 Bucket object. """
    def __init__(self, _name):
        self.keys = []

    def store_key(self, key):
        """ Not a Bucket method, created just to store the keys in the Bucket for testing purposes. """
        self.keys.append(key)

    def list(self, prefix):  # pylint: disable=unused-argument
        """ Expected method on a Bucket object. """
        return self.keys


class MockS3Connection(object):
    """ Mocking a boto S3 Connection """
    def __init__(self, access_key, secret_key):
        pass

    def get_bucket(self, bucket_name):
        """ Expected method on an S3Connection object. """
        return MockBucket(bucket_name)


class ReportStoreTestMixin(object):
    """
    Mixin for report store tests.
    """
    def setUp(self):
        self.course_id = CourseLocator(org="testx", course="coursex", run="runx")

    def create_report_store(self):
        """
        Subclasses should override this and return their report store.
        """
        pass

    def test_links_for_order(self):
        """
        Test that ReportStore.links_for() returns file download links
        in reverse chronological order.
        """
        report_store = self.create_report_store()
        report_store.store(self.course_id, 'old_file', StringIO())
        time.sleep(1)  # Ensure we have a unique timestamp.
        report_store.store(self.course_id, 'middle_file', StringIO())
        time.sleep(1)  # Ensure we have a unique timestamp.
        report_store.store(self.course_id, 'new_file', StringIO())

        self.assertEqual(
            [link[0] for link in report_store.links_for(self.course_id)],
            ['new_file', 'middle_file', 'old_file']
        )


class LocalFSReportStoreTestCase(ReportStoreTestMixin, TestReportMixin, TestCase):
    """
    Test the LocalFSReportStore model.
    """
    def create_report_store(self):
        """ Create and return a LocalFSReportStore. """
        return LocalFSReportStore.from_config(config_name='GRADES_DOWNLOAD')


@mock.patch('instructor_task.models.S3Connection', new=MockS3Connection)
@mock.patch('instructor_task.models.Key', new=MockKey)
@mock.patch('instructor_task.models.settings.AWS_SECRET_ACCESS_KEY', create=True, new="access_key")
@mock.patch('instructor_task.models.settings.AWS_ACCESS_KEY_ID', create=True, new="access_id")
class S3ReportStoreTestCase(ReportStoreTestMixin, TestReportMixin, TestCase):
    """
    Test the S3ReportStore model.
    """
    def create_report_store(self):
        """ Create and return a S3ReportStore. """
        return S3ReportStore.from_config(config_name='GRADES_DOWNLOAD')
