"""
:class:`~django_require.staticstorage.OptimizedCachedRequireJsStorage`
"""

from pipeline.storage import PipelineCachedStorage
from require.storage import OptimizedFilesMixin


class OptimizedCachedRequireJsStorage(OptimizedFilesMixin, PipelineCachedStorage):
    """
    Custom storage backend that is used by Django-require.
    """
    def hashed_name(self, name, content=None):
        try:
            return super(OptimizedCachedRequireJsStorage, self).hashed_name(name, content)
        except ValueError:
            # Return the original name rather than aborting collectstatic
            return name
