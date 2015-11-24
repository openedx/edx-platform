"""
Static file finders for Django.
https://docs.djangoproject.com/en/1.8/ref/settings/#std:setting-STATICFILES_FINDERS
Yes, this interface is private and undocumented, but we need to access it anyway.
"""
from os.path import basename

from path import Path

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.contrib.staticfiles import utils
from django.contrib.staticfiles.finders import BaseFinder

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
        path_project = path_theme / basename(settings.PROJECT_ROOT)
        path_static = path_project / 'static'
        self.storage = CachedComprehensiveThemingStorage(location=path_static)

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
