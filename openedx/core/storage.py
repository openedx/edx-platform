"""
Django storage backends for Open edX.
"""

from django_pipeline_forgiving.storages import PipelineForgivingStorage

import pytz
from datetime import datetime, timedelta

from django.contrib.staticfiles.storage import StaticFilesStorage, CachedFilesMixin
from pipeline.storage import PipelineMixin, NonPackagingMixin

from django.core.files.storage import get_storage_class
from django.utils.lru_cache import lru_cache

from require.storage import OptimizedFilesMixin

from openedx.core.djangoapps.theming.storage import (
    ThemeStorage,
    ThemeCachedFilesMixin,
    ThemePipelineMixin
)
from storages.backends.s3boto import S3BotoStorage

from storages.backends.azure_storage import AzureStorage
from azure.storage import AccessPolicy, SharedAccessPolicy


class ProductionStorage(
        PipelineForgivingStorage,
        OptimizedFilesMixin,
        ThemePipelineMixin,
        ThemeCachedFilesMixin,
        ThemeStorage,
        StaticFilesStorage
):
    """
    This class combines Django's StaticFilesStorage class with several mixins
    that provide additional functionality. We use this version on production.
    """
    pass


class DevelopmentStorage(
        NonPackagingMixin,
        ThemePipelineMixin,
        ThemeStorage,
        StaticFilesStorage
):
    """
    This class combines Django's StaticFilesStorage class with several mixins
    that provide additional functionality. We use this version for development,
    so that we can skip packaging and optimization.
    """
    pass


class S3ReportStorage(S3BotoStorage):  # pylint: disable=abstract-method
    """
    Storage for reports.
    """
    def __init__(self, acl=None, bucket=None, custom_domain=None, **settings):
        """
        init method for S3ReportStorage, Note that we have added an extra key-word
        argument named "custom_domain" and this argument should not be passed to the superclass's init.

        Args:
            acl: content policy for the uploads i.e. private, public etc.
            bucket: Name of S3 bucket to use for storing and/or retrieving content
            custom_domain: custom domain to use for generating file urls
            **settings: additional settings to be passed in to S3BotoStorage,

        Returns:

        """
        if custom_domain:
            self.custom_domain = custom_domain
        super(S3ReportStorage, self).__init__(acl=acl, bucket=bucket, **settings)


@lru_cache()
def get_storage(storage_class=None, **kwargs):
    """
    Returns a storage instance with the given class name and kwargs. If the
    class name is not given, an instance of the default storage is returned.
    Instances are cached so that if this function is called multiple times
    with the same arguments, the same instance is returned. This is useful if
    the storage implementation makes http requests when instantiated, for
    example.
    """
    return get_storage_class(storage_class)(**kwargs)


class AzureStorageExtended(AzureStorage):
    """
    A wrapper around the django-stores implementation for Azure blob storage
    so that it is fully comptaible. The version in the library's repository
    is out of date
    """

    def __init__(self, container=None, url_expiry_secs=None, *args, **kwargs):
        """
        Override base implementation so that we can accept a container
        parameter and an expiration on urls
        """
        super(AzureStorage, self).__init__(*args, **kwargs)
        self._connection = None
        self.url_expiry_secs = url_expiry_secs

        if container:
            self.azure_container = container

    def url(self, name):
        """
        Override this method so that we can add SAS authorization tokens
        """

        sas_token = None
        if self.url_expiry_secs:
            now = datetime.utcnow().replace(tzinfo=pytz.utc)
            expire_at = now + timedelta(seconds=self.url_expiry_secs)

            policy = AccessPolicy()
            # generate an ISO8601 time string and use split() to remove the sub-second
            # components as Azure will reject them. Plus add the timezone at the end.
            policy.expiry = expire_at.isoformat().split('.')[0] + 'Z'
            policy.permission = 'r'

            sas_token = self.connection.generate_shared_access_signature(
                self.azure_container,
                blob_name=name,
                shared_access_policy=SharedAccessPolicy(access_policy=policy),
            )

        return self.connection.make_blob_url(
            container_name=self.azure_container,
            blob_name=name,
            protocol=self.azure_protocol,
            sas_token=sas_token
        )

    def listdir(self, path):
        """
        The base implementation does not have a definition for this method
        which Open edX requires
        """
        if not path:
            path = None

        blobs = self.connection.list_blobs(
            container_name=self.azure_container,
            prefix=path,
        )
        results = []
        for f in blobs:
            name = f.name
            if path:
                name = name.replace(path, '')
            results.append(name)

        return ((), results)
