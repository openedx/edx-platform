"""
Storage backend for course import and export.
"""


from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage
from storages.utils import setting

from openedx.core.storage import get_storage_instance


class ImportExportS3Storage(S3Boto3Storage):  # pylint: disable=abstract-method
    """
    S3 backend for course import and export OLX files.
    """

    def __init__(self):
        bucket = setting('COURSE_IMPORT_EXPORT_BUCKET', settings.AWS_STORAGE_BUCKET_NAME)
        super().__init__(bucket_name=bucket, custom_domain=None, querystring_auth=True)


course_import_export_storage = get_storage_instance(settings.COURSE_IMPORT_EXPORT_STORAGE)
