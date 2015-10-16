"""
:class:`~django_require.staticstorage.OptimizedCachedRequireJsStorage`
"""

import logging

from pipeline.storage import PipelineCachedStorage
from require.storage import OptimizedFilesMixin

log = logging.getLogger(__name__)


class OptimizedCachedRequireJsStorage(OptimizedFilesMixin, PipelineCachedStorage):
    """
    Custom storage backend that is used by Django-require.
    """
    def hashed_name(self, name, content=None):
        """
        Returns the MD5 hashed version of a file name.

        Note: this overrides the default implementation to catch ValueErrors
        which indicate that the file doesn't exist so that the collectstatic
        process doesn't abort. Instead, a warning is logged and then the
        original file name is returned.
        """
        try:
            return super(OptimizedCachedRequireJsStorage, self).hashed_name(name, content)
        except ValueError:
            log.warn("File not found in OptimizedCachedRequireJsStorage: %r", name)
            return name
