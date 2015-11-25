"""
Static file finders for Django.
https://docs.djangoproject.com/en/1.8/ref/settings/#std:setting-STATICFILES_FINDERS
Yes, this interface is private and undocumented, but we need to access it anyway.
"""
from path import Path
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.contrib.staticfiles import utils
from django.contrib.staticfiles.finders import BaseFinder
from openedx.core.djangoapps.theming.storage import CachedComprehensiveThemingStorage


class ComprehensiveThemeFinder(BaseFinder):
    """
    A static files finder that searches the active comprehensive theme
    for static files. If the ``COMP_THEME_DIR`` setting is unset, or the
    ``COMP_THEME_DIR`` does not exist on the file system, this finder will
    never find any files.
    """
    def __init__(self, *args, **kwargs):
        COMP_THEME_DIR = getattr(settings, "COMP_THEME_DIR", "")  # pylint: disable=invalid-name
        if not COMP_THEME_DIR:
            self.storage = None
            return

        if not isinstance(settings.COMP_THEME_DIR, basestring):
            raise ImproperlyConfigured("Your COMP_THEME_DIR setting must be a string")

        PROJECT_ROOT = getattr(settings, "PROJECT_ROOT", "")  # pylint: disable=invalid-name
        if PROJECT_ROOT.endswith("cms"):
            THEME_STATIC_DIR = Path(settings.COMP_THEME_DIR) / "studio" / "static"  # pylint: disable=invalid-name
        else:
            THEME_STATIC_DIR = Path(settings.COMP_THEME_DIR) / "lms" / "static"  # pylint: disable=invalid-name

        self.storage = CachedComprehensiveThemingStorage(location=THEME_STATIC_DIR)

        super(ComprehensiveThemeFinder, self).__init__(*args, **kwargs)

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
