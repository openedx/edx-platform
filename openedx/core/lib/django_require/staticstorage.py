"""
:class:`~django_require.staticstorage.OptimizedCachedRequireJsStorage`
"""

from django_pipeline_forgiving.storages import PipelineForgivingStorage
from require.storage import OptimizedFilesMixin


class OptimizedCachedRequireJsStorage(OptimizedFilesMixin, PipelineForgivingStorage):
    """
    Custom storage backend that is used by Django-require.
    """
    pass
