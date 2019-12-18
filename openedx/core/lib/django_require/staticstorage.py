"""
:class:`~django_require.staticstorage.OptimizedCachedRequireJsStorage`
"""

from openedx.core.storage import PipelineForgivingMixin
from pipeline.storage import PipelineCachedStorage
from require.storage import OptimizedFilesMixin


class OptimizedCachedRequireJsStorage(OptimizedFilesMixin, PipelineForgivingMixin, PipelineCachedStorage):
    """
    Custom storage backend that is used by Django-require.
    """
    pass
