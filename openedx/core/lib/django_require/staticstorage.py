"""
:class:`~django_require.staticstorage.OptimizedCachedRequireJsStorage`
"""

from pipeline.storage import PipelineCachedStorage
from require.storage import OptimizedFilesMixin

from openedx.core.storage import PipelineForgivingMixin


class OptimizedCachedRequireJsStorage(OptimizedFilesMixin, PipelineForgivingMixin, PipelineCachedStorage):
    """
    Custom storage backend that is used by Django-require.
    """
    pass
