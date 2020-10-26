"""
Django storage backends for Open edX.
"""
from django.contrib.staticfiles.storage import StaticFilesStorage
from django.core.files.storage import get_storage_class
from django.utils.lru_cache import lru_cache
from pipeline.storage import NonPackagingMixin, PipelineCachedStorage
from require.storage import OptimizedFilesMixin
from storages.backends.s3boto import S3BotoStorage

from openedx.core.djangoapps.theming.storage import ThemeCachedFilesMixin, ThemePipelineMixin, ThemeStorage


class PipelineForgivingStorage(PipelineCachedStorage):
    """
    An extension of the django-pipeline storage backend which forgives missing files.
    """
    def hashed_name(self, name, content=None, **kwargs):
        try:
            out = super(PipelineForgivingStorage, self).hashed_name(name, content, **kwargs)
        except ValueError:
            # This means that a file could not be found, and normally this would
            # cause a fatal error, which seems rather excessive given that
            # some packages have missing files in their css all the time.
            out = name
        return out

    def stored_name(self, name):
        try:
            out = super(PipelineForgivingStorage, self).stored_name(name)
        except ValueError:
            # This means that a file could not be found, and normally this would
            # cause a fatal error, which seems rather excessive given that
            # some packages have missing files in their css all the time.
            out = name
        return out


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
