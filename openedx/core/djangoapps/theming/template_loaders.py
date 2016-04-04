"""
Theming aware template loaders.
"""
from django.template.loaders.filesystem import Loader as FilesystemLoader

from edxmako.makoloader import MakoLoader
from openedx.core.djangoapps.theming.helpers import get_template_path_with_theme


class ThemeTemplateLoader(MakoLoader):
    """
    This is a Django loader object which will load the template based on current request and its corresponding theme.
    """
    def __call__(self, template_name, template_dirs=None):
        template_name = get_template_path_with_theme(template_name).lstrip("/")
        return self.load_template(template_name, template_dirs)


class ThemeFilesystemLoader(ThemeTemplateLoader):
    """
    Filesystem Template loaders to pickup templates from theme directory based on the current site.
    """
    is_usable = True
    _accepts_engine_in_init = True

    def __init__(self, *args):
        ThemeTemplateLoader.__init__(self, FilesystemLoader(*args))
