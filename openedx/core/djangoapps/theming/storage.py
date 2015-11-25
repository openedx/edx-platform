"""
Comprehensive Theming support for Django's collectstatic functionality.
See https://docs.djangoproject.com/en/1.8/ref/contrib/staticfiles/
"""
import os.path
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, SuspiciousOperation
from django.contrib.staticfiles.storage import StaticFilesStorage, CachedFilesMixin
from django.utils._os import safe_join


class ComprehensiveThemingAwareMixin(object):
    """
    Mixin for Django storage system to make it aware of the currently-active
    comprehensive theme, so that it can generate theme-scoped URLs for themed
    static assets.
    """
    def __init__(self, *args, **kwargs):
        super(ComprehensiveThemingAwareMixin, self).__init__(*args, **kwargs)
        COMP_THEME_DIR = getattr(settings, "COMP_THEME_DIR", "")  # pylint: disable=invalid-name
        if not COMP_THEME_DIR:
            self.theme_location = None
            return

        if not isinstance(COMP_THEME_DIR, basestring):
            raise ImproperlyConfigured("Your COMP_THEME_DIR setting must be a string")

        PROJECT_ROOT = getattr(settings, "PROJECT_ROOT", "")  # pylint: disable=invalid-name
        if PROJECT_ROOT.endswith("cms"):
            component = "studio"
        else:
            component = "lms"
        self.theme_location = os.path.join(COMP_THEME_DIR, component, "static")

    @property
    def prefix(self):
        """
        This is used by the ComprehensiveThemeFinder in the collection step.
        """
        COMP_THEME_DIR = getattr(settings, "COMP_THEME_DIR", "")  # pylint: disable=invalid-name
        if not COMP_THEME_DIR:
            return None
        theme_name = os.path.basename(os.path.normpath(COMP_THEME_DIR))
        return "themes/{name}/".format(name=theme_name)

    def themed(self, name):
        """
        Given a name, return a boolean indicating whether that name exists
        as a themed asset in the comprehensive theme.
        """
        # Nothing can be themed if we don't have a theme location.
        if not self.theme_location:
            return False

        try:
            path = safe_join(self.theme_location, name)
        except ValueError:
            raise SuspiciousOperation("Attempted access to '%s' denied." % name)
        return os.path.exists(os.path.normpath(path))

    def path(self, name):
        """
        Get the path to the real asset on disk
        """
        if self.themed(name):
            base = self.theme_location
        else:
            base = self.location
        try:
            path = safe_join(base, name)
        except ValueError:
            raise SuspiciousOperation("Attempted access to '%s' denied." % name)
        return os.path.normpath(path)

    def url(self, name, *args, **kwargs):
        """
        Add the theme prefix to the asset URL
        """
        if self.themed(name):
            name = self.prefix + name
        return super(ComprehensiveThemingAwareMixin, self).url(name, *args, **kwargs)


class CachedComprehensiveThemingStorage(
        ComprehensiveThemingAwareMixin,
        CachedFilesMixin,
        StaticFilesStorage
    ):  # nopep8
    """
    Used by the ComprehensiveThemeFinder class. Mixes in support for cached
    files and comprehensive theming in static files.
    """
    pass
