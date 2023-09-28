"""
Theming aware template loaders.
"""


from django.template.loaders.filesystem import Loader as FilesystemLoader

from common.djangoapps.edxmako.makoloader import MakoLoader
from openedx.core.djangoapps.theming.helpers import get_all_theme_template_dirs, get_current_request, get_current_theme


class ThemeTemplateLoader(MakoLoader):
    """
    Filesystem Template loaders to pickup templates from theme directory based on the current site.
    """
    is_usable = True
    _accepts_engine_in_init = True

    def __init__(self, *args):
        MakoLoader.__init__(self, ThemeFilesystemLoader(*args))  # lint-amnesty, pylint: disable=no-value-for-parameter


class ThemeFilesystemLoader(FilesystemLoader):
    """
    Filesystem Template loaders to pickup templates from theme directory based on the current site.
    """
    is_usable = True
    _accepts_engine_in_init = True

    def __init__(self, engine, dirs=None):
        if not dirs:
            self.dirs = engine.dirs
        theme_dirs = self.get_theme_template_sources()
        if isinstance(theme_dirs, list):
            self.dirs = theme_dirs + self.dirs
        super().__init__(engine, self.dirs)

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
