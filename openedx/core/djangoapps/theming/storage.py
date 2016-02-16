"""
Comprehensive Theming support for Django's collectstatic functionality.
See https://docs.djangoproject.com/en/1.8/ref/contrib/staticfiles/
"""
from path import Path
import os.path
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
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
        theme_dir = getattr(settings, "COMPREHENSIVE_THEME_DIR", "")
        if not theme_dir:
            self.theme_location = None
            return

        if not isinstance(theme_dir, basestring):
            raise ImproperlyConfigured("Your COMPREHENSIVE_THEME_DIR setting must be a string")

        root = Path(settings.PROJECT_ROOT)
        if root.name == "":
            root = root.parent
        self.root_name = root.name

        if theme_dir:
            self.theme_location = theme_dir

    @property
    def prefix(self):
        """
        This is used by the ComprehensiveThemeFinder in the collection step.
        """
        theme_prefix = ""
        if self.theme_location:
            theme_prefix = "/static"
        return theme_prefix

    def themed(self, name):
        """
        Given a name, return a boolean indicating whether that name exists
        as a themed asset in the comprehensive theme.
        """
        # Nothing can be themed if we don't have a theme location.
        if not self.theme_location:
            return False

        path = safe_join(self.theme_location, name)
        return os.path.exists(path)

    def path(self, name):
        """
        Get the path to the real asset on disk
        """
        if self.themed(name):
            base = self.theme_location
        else:
            base = self.location
        path = safe_join(base, name)
        return os.path.normpath(path)

    def url(self, name, domain=None):
        """
        Add the theme prefix to the asset URL
        """
        if name.startswith(self.prefix):
            # strip the prefix
            name_without_prefix = name[len(self.prefix):]
        else:
            name_without_prefix = name

        if domain:
            themed_path = domain + "/" + self.root_name + self.prefix + name_without_prefix
            if self.themed(themed_path):
                name = self.prefix + "/" + domain + name_without_prefix
        return super(ComprehensiveThemingAwareMixin, self).url(name)


class CachedComprehensiveThemingStorage(
        ComprehensiveThemingAwareMixin,
        CachedFilesMixin,
        StaticFilesStorage
):
    """
    Used by the ComprehensiveThemeFinder class. Mixes in support for cached
    files and comprehensive theming in static files.
    """
    pass
