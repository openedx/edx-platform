"""
Tests for instructor_task/models.py.
"""
import copy
from cStringIO import StringIO
import time

import boto
from django.conf import settings
from django.test import SimpleTestCase, override_settings
from mock import patch

from common.test.utils import MockS3Mixin
from instructor_task.models import ReportStore
from instructor_task.tests.test_base import TestReportMixin
from opaque_keys.edx.locator import CourseLocator


class ReportStoreTestMixin(object):
    """
    Mixin for report store tests.
    """
    def setUp(self):
        super(ReportStoreTestMixin, self).setUp()
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
        self.assertEqual(report_store.links_for(self.course_id), [])

        report_store.store(self.course_id, 'old_file', StringIO())
        time.sleep(1)  # Ensure we have a unique timestamp.
        report_store.store(self.course_id, 'middle_file', StringIO())
        time.sleep(1)  # Ensure we have a unique timestamp.
        report_store.store(self.course_id, 'new_file', StringIO())

        self.assertEqual(
            [link[0] for link in report_store.links_for(self.course_id)],
            ['new_file', 'middle_file', 'old_file']
        )


class LocalFSReportStoreTestCase(ReportStoreTestMixin, TestReportMixin, SimpleTestCase):
    """
    Test the old LocalFSReportStore configuration.
    """
    def create_report_store(self):
        """
        Create and return a DjangoStorageReportStore using the old
        LocalFSReportStore configuration.
        """
        return ReportStore.from_config(config_name='GRADES_DOWNLOAD')


@patch.dict(settings.GRADES_DOWNLOAD, {'STORAGE_TYPE': 's3'})
class S3ReportStoreTestCase(MockS3Mixin, ReportStoreTestMixin, TestReportMixin, SimpleTestCase):
    """
    Test the old S3ReportStore configuration.
    """
    def create_report_store(self):
        """
        Create and return a DjangoStorageReportStore using the old
        S3ReportStore configuration.
        """
        connection = boto.connect_s3()
        connection.create_bucket(settings.GRADES_DOWNLOAD['BUCKET'])
        return ReportStore.from_config(config_name='GRADES_DOWNLOAD')


class DjangoStorageReportStoreLocalTestCase(ReportStoreTestMixin, TestReportMixin, SimpleTestCase):
    """
    Test the DjangoStorageReportStore implementation using the local
    filesystem.
    """
    def create_report_store(self):
        """
        Create and return a DjangoStorageReportStore configured to use the
        local filesystem for storage.
        """
        test_settings = copy.deepcopy(settings.GRADES_DOWNLOAD)
        test_settings['STORAGE_KWARGS'] = {'location': settings.GRADES_DOWNLOAD['ROOT_PATH']}
        with override_settings(GRADES_DOWNLOAD=test_settings):
            return ReportStore.from_config(config_name='GRADES_DOWNLOAD')


class DjangoStorageReportStoreS3TestCase(MockS3Mixin, ReportStoreTestMixin, TestReportMixin, SimpleTestCase):
    """
    Test the DjangoStorageReportStore implementation using S3 stubs.
    """
    def create_report_store(self):
        """
        Create and return a DjangoStorageReportStore configured to use S3 for
        storage.
        """
        test_settings = copy.deepcopy(settings.GRADES_DOWNLOAD)
        test_settings['STORAGE_CLASS'] = 'storages.backends.s3boto.S3BotoStorage'
        test_settings['STORAGE_KWARGS'] = {
            'bucket': settings.GRADES_DOWNLOAD['BUCKET'],
            'location': settings.GRADES_DOWNLOAD['ROOT_PATH'],
        }
        with override_settings(GRADES_DOWNLOAD=test_settings):
            connection = boto.connect_s3()
            connection.create_bucket(settings.GRADES_DOWNLOAD['STORAGE_KWARGS']['bucket'])
            return ReportStore.from_config(config_name='GRADES_DOWNLOAD')
