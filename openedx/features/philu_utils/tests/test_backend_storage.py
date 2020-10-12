"""
Unit tests of backend storage
"""
import os.path

from boto import connect_s3
from boto.s3.key import Key
from django.conf import settings
from django.core.files.base import ContentFile
from django.test import TestCase

from common.test.utils import MockS3Mixin
from openedx.features.philu_utils.backend_storage import CustomS3Storage, ScormXblockS3Storage


class CustomS3StorageTest(MockS3Mixin, TestCase):
    """
    Unit test class to test CustomS3Storage backend
    """
    aws_bucket_name = getattr(settings, 'FILE_UPLOAD_STORAGE_BUCKET_NAME', None)
    aws_access_key_id = getattr(settings, 'AWS_ACCESS_KEY_ID', None)
    aws_secret_access_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)

    def setUp(self):
        super(CustomS3StorageTest, self).setUp()
        self.custom_storage = CustomS3Storage()
        self.scorm_xblock_storage = ScormXblockS3Storage()
        # create virtual bucket to store images
        connect = connect_s3(aws_access_key_id=self.aws_access_key_id, aws_secret_access_key=self.aws_secret_access_key)
        connect.create_bucket(self.aws_bucket_name)
        self.bucket = connect.get_bucket(self.aws_bucket_name)

    def test_custom_s3_storage_save_to_s3_successfully(self):
        """
        Create file on local storage, upload it to S3. Assert that uploaded file does not override previous files and
        local file from storage is deleted immediately.
        """
        name = self.custom_storage.save('path/img/dummy.txt', ContentFile(b'This is dummy text'))

        # assert that original file has been deleted from local file storage
        self.assertFalse(os.path.exists(self.custom_storage.path(name)))

        # since file is stored first time in virtual S3 bucket, name will not change
        self.assertEqual(name, 'path/img/dummy.txt')

        # assert that file exists in virtual S3 bucket
        self.assertTrue(Key(bucket=self.bucket, name=name).exists())

        # upload file with same name to S3
        name = self.custom_storage.save('path/img/dummy.txt', ContentFile(b'This is dummy text'))

        # Virtual S3 bucket already have file by same name, so custom_storage will return updated name
        self.assertNotEqual(name, 'path/img/dummy.txt')

        # assert that file with updated name exists in virtual S3 bucket
        self.assertTrue(Key(bucket=self.bucket, name=name).exists())

    def test_custom_s3_storage_delete_from_s3(self):
        """
        Upload file to S3 and assert that it does not exist on S3 when it is deleted from there.
        """
        name = self.custom_storage.save('path/img/delete.txt', ContentFile(b'This is dummy text'))

        # assert that original file has been deleted from local file storage
        self.assertFalse(os.path.exists(self.custom_storage.path(name)))
        # assert that file exists in virtual S3 bucket
        self.assertTrue(Key(bucket=self.bucket, name=name).exists())

        self.custom_storage.delete(name)
        # assert that file has been deleted from virtual S3 bucket
        self.assertFalse(Key(bucket=self.bucket, name=name).exists())

    def test_scorm_s3_storage_open_file_successfully(self):
        """
        Upload file to S3 and assert that it does not exist on S3 or the file is not retrieved correctly.
        """
        name = self.scorm_xblock_storage.save('path/img/dummy.txt', ContentFile(b'This is dummy text'))
        tempfile = self.scorm_xblock_storage.open(name)
        # asset if file is not retrieved correctly
        self.assertEquals(tempfile.read(), b'This is dummy text')
        # assert that file does not exists.
        self.assertTrue(self.scorm_xblock_storage.exists(name))
