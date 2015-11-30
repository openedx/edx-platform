"""
Core logic for Comprehensive Theming.
"""

from os.path import basename

from django.conf import settings

from path import Path

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
    paths = get_paths(path_theme)
    if paths['templates'].isdir():
        configuration['settings']['TEMPLATE_DIRS'] = (
            [paths['templates']] + settings.DEFAULT_TEMPLATE_ENGINE['DIRS']
        )
        configuration['mako_paths'].append(paths['templates'])
    if paths['static'].isdir():
        configuration['settings']['STATICFILES_DIRS'] = (
            [paths['static']] + settings.STATICFILES_DIRS
        )
    if paths['locale'].isdir():
        configuration['settings']['LOCALE_PATHS'] = (
            [paths['locale']] + settings.LOCALE_PATHS
        )
    if paths['favicon'].isfile():
        # TODO: Should this be unicode?
        configuration['settings']['FAVICON_PATH'] = str(paths['favicon'])
    return configuration


def get_paths(path_theme, name_project=None):
    """
    Get list of relevant paths within a theme
    """
        name_project = name_project or basename(settings.PROJECT_ROOT)
        path_project: path_theme / name_project
        paths = {
            'locale': path_project / 'conf' / 'locale',
            'tempates': path_project / 'templates',
            'static': path_project / 'static',
            'sass': path_project / 'static' / 'sass',
            'css': path_project / 'static' / 'css',
            'favicon': path_project / 'static' / 'images' / 'favicon.ico',
        }
        return paths


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
