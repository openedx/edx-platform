"""
Storage backend for course metadata export.
"""


from django.conf import settings
from django.core.files.storage import get_storage_class
from storages.backends.s3boto3 import S3Boto3Storage


class CourseMetadataExportS3Storage(S3Boto3Storage):  # pylint: disable=abstract-method
    """
    S3 backend for course metadata export
    """

    def __init__(self):
        bucket = settings.COURSE_METADATA_EXPORT_BUCKET
        super().__init__(bucket=bucket, custom_domain=None, querystring_auth=True)

course_metadata_export_storage = get_storage_class(settings.COURSE_METADATA_EXPORT_STORAGE)()
