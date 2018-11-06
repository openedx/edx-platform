"""
Theming aware template loaders.
"""
from django.template.loaders.filesystem import Loader as FilesystemLoader

from edxmako.makoloader import MakoLoader
from openedx.core.djangoapps.theming.helpers import get_all_theme_template_dirs, get_current_request, get_current_theme


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

        return list(super(ThemeFilesystemLoader, self).get_template_sources(template_name, template_dirs))

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
