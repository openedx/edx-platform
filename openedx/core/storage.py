"""
Django storage backends for Open edX.
"""
from django_pipeline_forgiving.storages import PipelineForgivingStorage
from django.contrib.staticfiles.storage import StaticFilesStorage
from django.core.files.storage import get_storage_class
from django.utils.lru_cache import lru_cache

from pipeline.storage import NonPackagingMixin
from require.storage import OptimizedFilesMixin
from openedx.core.djangoapps.theming.storage import (
    ThemeStorage,
    ThemeCachedFilesMixin,
    ThemePipelineMixin
)


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
