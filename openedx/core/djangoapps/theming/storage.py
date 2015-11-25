"""
Comprehensive Theming support for Django's collectstatic functionality.
See https://docs.djangoproject.com/en/1.8/ref/contrib/staticfiles/
"""
import os.path
from path import Path
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.contrib.staticfiles.storage import StaticFilesStorage, CachedFilesMixin
from django.utils._os import safe_join

from pipeline.storage import PipelineMixin, NonPackagingMixin
from require.storage import OptimizedFilesMixin

from openedx.core.djangoapps.theming.core import get_paths


class ComprehensiveThemingAwareMixin(object):
    """
    Mixin for Django storage system to make it aware of the currently-active
    comprehensive theme, so that it can generate theme-scoped URLs for themed
    static assets.
    """
    def __init__(self, *args, **kwargs):
        super(ComprehensiveThemingAwareMixin, self).__init__(*args, **kwargs)
        path_theme = Path(settings.COMPREHENSIVE_THEMING_DIRECTORY)
        if not path_theme:
            self.theme_location = None
            return
        paths = get_paths(path_theme)
        self.theme_location = paths['static']

    @property
    def prefix(self):
        """
        This is used by the ComprehensiveThemeFinder in the collection step.
        """
        pathname_theme = settings.COMPREHENSIVE_THEMING_DIRECTORY
        if not pathname_theme:
            return None
        theme_name = os.path.basename(os.path.normpath(pathname_theme))
        return "themes/{name}/".format(name=theme_name)

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


class ProductionStorage(
        ComprehensiveThemingAwareMixin,
        OptimizedFilesMixin,
        PipelineMixin,
        CachedFilesMixin,
        StaticFilesStorage
    ):  # nopep8
    """
    This class combines Django's StaticFilesStorage class with several mixins
    that provide additional functionality. We use this version on production.
    """
    pass


class DevelopmentStorage(
        ComprehensiveThemingAwareMixin,
        NonPackagingMixin,
        PipelineMixin,
        StaticFilesStorage
    ):  # nopep8
    """
    This class combines Django's StaticFilesStorage class with several mixins
    that provide additional functionality. We use this version for development,
    so that we can skip packaging and optimization.
    """
    pass
