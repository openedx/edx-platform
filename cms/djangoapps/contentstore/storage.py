"""
Storage backend for course import and export.
"""


from django.conf import settings
from django.core.files.storage import get_storage_class
from storages.backends.s3boto3 import S3Boto3Storage
from storages.utils import setting


class ImportExportS3Storage(S3Boto3Storage):  # pylint: disable=abstract-method
    """
    S3 backend for course import and export OLX files.
    """

    def __init__(self):
        bucket = setting('COURSE_IMPORT_EXPORT_BUCKET', settings.AWS_STORAGE_BUCKET_NAME)
        super().__init__(bucket=bucket, custom_domain=None, querystring_auth=True)

# pylint: disable=invalid-name
course_import_export_storage = get_storage_class(settings.COURSE_IMPORT_EXPORT_STORAGE)()
