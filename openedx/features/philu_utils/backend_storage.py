import os
from datetime import datetime
from logging import getLogger

from boto import connect_s3
from boto.s3.key import Key
from botocore.exceptions import ClientError
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.translation import ugettext_lazy as _

from .constants import AWS_S3_PATH

log = getLogger(__name__)


class CustomS3Storage(FileSystemStorage):
    """
    A custom storage class which saves file on S3 bucket instead of local file storage.

    Once file is saved on local storage it is uploaded to s3 and then deleted immediately from local storage. Note this
    class has limited functionality as compared to its base class. Base class functions like size, file creating time
    etc will provide inconsistent result. If any of these methods are required, their custom implementation has to be
    provided.

    TODO update boto to boto3 on next project upgrade, if moto is upgraded to support boto3
    """
    aws_bucket_name = getattr(settings, 'FILE_UPLOAD_STORAGE_BUCKET_NAME', None)
    aws_access_key_id = getattr(settings, 'AWS_ACCESS_KEY_ID', None)
    aws_secret_access_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)

    def _s3_client(self):
        return connect_s3(
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
        )

    def _get_available_name(self, name, max_length=None):
        """Truncate name if it is more than allowed max length and get alternate name if name already exists"""
        if self._exists(name):
            _, file_name = os.path.split(name)
            file_root, file_ext = os.path.splitext(file_name)
            name = self.get_alternative_name(file_root, file_ext)
        return name

    def _exists(self, name):
        """Check if file with same name exists on S3, on same path"""
        try:
            bucket = self._s3_client().get_bucket(self.aws_bucket_name)
            key = Key(bucket=bucket, name=name)
            return key.exists()
        except ClientError:
            return False

    def save(self, name, content, max_length=None):
        """Save file on S3 with unique name. Delete local file, at the end"""
        if name is None:
            name = content.name

        name = self._get_available_name(name, max_length)
        name = super(CustomS3Storage, self).save(name, content, max_length)

        try:
            self._upload_file_to_s3_bucket(name)
        except Exception as err:
            log.exception(err)
            raise Exception(_('Unable to save file, please try again'))
        finally:
            self._delete_file_from_local_storage(name)

        return name

    def _upload_file_to_s3_bucket(self, name):
        bucket = self._s3_client().get_bucket(self.aws_bucket_name)
        key = Key(bucket=bucket, name=name)
        key.set_contents_from_filename(self.path(name))

    def _delete_file_from_local_storage(self, name):
        super(CustomS3Storage, self).delete(name)

    def delete(self, name):
        client = self._s3_client()
        key = Key(client)
        key.key = name
        bucket = client.get_bucket(self.aws_bucket_name)
        bucket.delete_key(key)

    def url(self, name):
        return AWS_S3_PATH.format(bucket=self.aws_bucket_name, key=name)

    def get_alternative_name(self, file_root, file_ext):
        """Make file name unique, by appending time, so that S3 does not override file with same name"""
        return '{file_root}_{extra_characters}{extension}'.format(
            file_root=file_root,
            extra_characters=datetime.now().strftime('%H%M%S'),
            extension=file_ext
        )

    def exists(self, name):
        """Do not allow base class to update name in endless loop"""
        return False
