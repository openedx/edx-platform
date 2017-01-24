"""
:class:`~django_require.staticstorage.OptimizedCachedRequireJsStorage`
"""

from require.storage import OptimizedFilesMixin
from django_pipeline_forgiving.storages import PipelineForgivingStorage


class OptimizedCachedRequireJsStorage(OptimizedFilesMixin, PipelineForgivingStorage):
    """
    Custom storage backend that is used by Django-require.
    """
    pass
