"""
Django storage backends for Open edX.
"""


from django.conf import settings
from django.contrib.staticfiles.storage import StaticFilesStorage
from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible
from django.utils.module_loading import import_string
from functools import lru_cache
from pipeline.storage import NonPackagingMixin
from require.storage import OptimizedFilesMixin
from storages.backends.s3boto3 import S3Boto3Storage

from openedx.core.djangoapps.theming.storage import ThemeManifestFilesMixin, ThemePipelineMixin, ThemeMixin


class PipelineForgivingMixin:
    """
    An extension of the django-pipeline storage backend which forgives missing files.
    """
    def hashed_name(self, name, content=None, **kwargs):  # lint-amnesty, pylint: disable=missing-function-docstring
        try:
            out = super().hashed_name(name, content, **kwargs)  # lint-amnesty, pylint: disable=super-with-arguments
        except ValueError:
            # This means that a file could not be found, and normally this would
            # cause a fatal error, which seems rather excessive given that
            # some packages have missing files in their css all the time.
            out = name
        return out

    def stored_name(self, name):  # lint-amnesty, pylint: disable=missing-function-docstring
        try:
            out = super().stored_name(name)  # lint-amnesty, pylint: disable=super-with-arguments
        except ValueError:
            # This means that a file could not be found, and normally this would
            # cause a fatal error, which seems rather excessive given that
            # some packages have missing files in their css all the time.
            out = name
        return out


class ProductionMixin(
        PipelineForgivingMixin,
        OptimizedFilesMixin,
        ThemePipelineMixin,
        ThemeManifestFilesMixin,
        ThemeMixin,
):
    """
    This class combines several mixins that provide additional functionality, and
    can be applied over an existing Storage.
    We use this version on production.
    """
    def __init__(self, *args, **kwargs):
        kwargs.update(settings.STATICFILES_STORAGE_KWARGS.get(settings.STATICFILES_STORAGE, {}))
        super().__init__(*args, **kwargs)  # lint-amnesty, pylint: disable=super-with-arguments


class ProductionStorage(ProductionMixin, StaticFilesStorage):
    pass


class ProductionS3Storage(ProductionMixin, S3Boto3Storage):  # pylint: disable=abstract-method
    pass


class DevelopmentStorage(
        NonPackagingMixin,
        ThemePipelineMixin,
        ThemeMixin,
        StaticFilesStorage
):
    """
    This class combines Django's StaticFilesStorage class with several mixins
    that provide additional functionality. We use this version for development,
    so that we can skip packaging and optimization.
    """
    pass  # lint-amnesty, pylint: disable=unnecessary-pass


@deconstructible
class OverwriteStorage(FileSystemStorage):
    """
    FileSystemStorage subclass which automatically overwrites any previous
    file with the same name; used in test runs to avoid test file proliferation.
    Copied from django-storages when this class was removed in version 1.6.

    Comes from http://www.djangosnippets.org/snippets/976/
    (even if it already exists in S3Storage for ages)
    See also Django #4339, which might add this functionality to core.
    """

    def get_available_name(self, name, max_length=None):
        """
        Returns a filename that's free on the target storage system, and
        available for new content to be written to.
        """
        if self.exists(name):
            self.delete(name)
        return name


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
    storage_cls = import_string(storage_class or settings.DEFAULT_FILE_STORAGE)
    return storage_cls(**kwargs)
