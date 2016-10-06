"""
Theming aware template loaders.
"""
from django.utils._os import safe_join
from django.core.exceptions import SuspiciousFileOperation
from django.template.loaders.filesystem import Loader as FilesystemLoader

from openedx.core.djangoapps.edxmako.makoloader import MakoLoader
from openedx.core.djangoapps.theming.helpers import get_current_request, \
    get_current_theme, get_all_theme_template_dirs


class ThemeTemplateLoader(MakoLoader):
    """
    Filesystem Template loaders to pickup templates from theme directory based on the current site.
    """
    is_usable = True
    _accepts_engine_in_init = True

    def __init__(self, *args):
        MakoLoader.__init__(self, ThemeFilesystemLoader(*args))


class ThemeFilesystemLoader(FilesystemLoader):
    """
    Filesystem Template loaders to pickup templates from theme directory based on the current site.
    """
    is_usable = True
    _accepts_engine_in_init = True

    def get_template_sources(self, template_name, template_dirs=None):
        """
        Returns the absolute paths to "template_name", when appended to each
        directory in "template_dirs". Any paths that don't lie inside one of the
        template dirs are excluded from the result set, for security reasons.
        """
        if not template_dirs:
            template_dirs = self.engine.dirs
        theme_dirs = self.get_theme_template_sources()

        # append theme dirs to the beginning so templates are looked up inside theme dir first
        if isinstance(theme_dirs, list):
            template_dirs = theme_dirs + template_dirs

        for template_dir in template_dirs:
            try:
                yield safe_join(template_dir, template_name)
            except SuspiciousFileOperation:
                # The joined path was located outside of this template_dir
                # (it might be inside another one, so this isn't fatal).
                pass

    @staticmethod
    def get_theme_template_sources():
        """
        Return template sources for the given theme and if request object is None (this would be the case for
        management commands) return template sources for all themes.
        """
        if not get_current_request():
            # if request object is not present, then this method is being called inside a management
            # command and return all theme template sources for compression
            return get_all_theme_template_dirs()
        else:
            # template is being accessed by a view, so return templates sources for current theme
            theme = get_current_theme()
            return theme and theme.template_dirs
