"""
Core logic for Comprehensive Theming.
"""

from os.path import basename

from django.conf import settings

import edxmako


def get_configuration(path_theme):
    """
    Calculate the configuration needed to enable a comprehensive theme.

    Arguments:
        path_theme (path.Path): the full path to the theming directory to use.

    Returns:
        A dict indicating the configuration to apply:

            * 'settings': a dictionary of settings names and their new values.

            * 'mako_paths': a list of directories to prepend to the edxmako
                template lookup path.

    """

    configuration = {
        'settings': {},
        'mako_paths': [],
    }
    path_project = path_theme / basename(settings.PROJECT_ROOT)
    path_templates = path_project / 'templates'
    path_static = path_project / 'static'
    path_locale = path_project / 'conf' / 'locale'
    path_favicon = path_project / 'static' / 'images' / 'favicon.ico'
    if path_templates.isdir():
        configuration['settings']['TEMPLATE_DIRS'] = (
            [path_templates] + settings.DEFAULT_TEMPLATE_ENGINE['DIRS']
        )
        configuration['mako_paths'].append(path_templates)
    if path_static.isdir():
        configuration['settings']['STATICFILES_DIRS'] = (
            [path_static] + settings.STATICFILES_DIRS
        )
    if path_locale.isdir():
        configuration['settings']['LOCALE_PATHS'] = (
            [path_locale] + settings.LOCALE_PATHS
        )
    if path_favicon.isfile():
        # TODO: Should this be unicode?
        configuration['settings']['FAVICON_PATH'] = str(path_favicon)
    return configuration


def try_enable_theme():
    """
    Add directories to relevant paths for comprehensive theming.
    """
    path_themes = Path(settings.COMPREHENSIVE_THEMING_DIRECTORY)
    if not path_theme:
        return False
    configuration = get_configuration(path_theme)
    for name, value in configuration['settings'].iteritems():
        setattr(settings, name, value)
    for template_dir in configuration['mako_paths']:
        edxmako.paths.add_lookup('main', template_dir, prepend=True)
    return True
