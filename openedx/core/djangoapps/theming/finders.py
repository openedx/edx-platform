"""
Static file finders for Django.
https://docs.djangoproject.com/en/1.8/ref/settings/#std:setting-STATICFILES_FINDERS
Yes, this interface is private and undocumented, but we need to access it anyway.

A little explanation would go a long way here.. I'm sure the rationale
is obvious to you already, but it's not to me now. A future developer
likely won't understand why either.
For these kinds of decisions, it's important to know _why_ you arrived at
your conclusion, not just that you did. The lack of explanation now
means additional/redundant discovery work on behalf of a future
developer who audits this functionality.
"""
from os.path import basename

from path import Path

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.contrib.staticfiles import utils
from django.contrib.staticfiles.finders import BaseFinder

from openedx.core.djangoapps.theming.core import get_paths
from openedx.core.djangoapps.theming.storage import CachedComprehensiveThemingStorage


class ComprehensiveThemeFinder(BaseFinder):
    """
    A static files finder that searches the active comprehensive theme
    for static files. If the ``COMPREHENSIVE_THEMING_DIRECTORY`` setting
    is unset or does not exist on the file system, this finder will
    never find any files.
    """
    def __init__(self, *args, **kwargs):
        super(ComprehensiveThemeFinder, self).__init__(*args, **kwargs)
        path_theme = Path(settings.COMPREHENSIVE_THEMING_DIRECTORY)
        if not path_theme:
            self.storage = None
            return
        paths = get_paths(path_theme)
        self.storage = CachedComprehensiveThemingStorage(location=paths['static'])

    def find(self, path, all=False):  # pylint: disable=redefined-builtin
        """
        Looks for files in the default file storage, if it's local.
        """
        if not self.storage:
            return []

        if path.startswith(self.storage.prefix):
            # strip the prefix
            path = path[len(self.storage.prefix):]

        if self.storage.exists(path):
            match = self.storage.path(path)
            if all:
                match = [match]
            return match

        return []

    def list(self, ignore_patterns):
        """
        List all files of the storage.
        """
        if self.storage and self.storage.exists(''):
            for path in utils.get_files(self.storage, ignore_patterns):
                yield path, self.storage
