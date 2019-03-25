"""
:class:`~django_require.staticstorage.OptimizedCachedRequireJsStorage`
"""

from openedx.core.storage import PipelineForgivingStorage
from require.storage import OptimizedFilesMixin


class OptimizedCachedRequireJsStorage(OptimizedFilesMixin, PipelineForgivingStorage):
    """
    Custom storage backend that is used by Django-require.
    """
    pass
