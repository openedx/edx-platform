"""
Core logic for Comprehensive Theming.
"""

from os.path import basename

from django.conf import settings

import edxmako


def comprehensive_theme_changes(path_theme):
    """
    Calculate the set of changes needed to enable a comprehensive theme.

    Arguments:
        path_theme (path.path): the full path to the theming directory to use.

    Returns:
        A dict indicating the changes to make:

            * 'settings': a dictionary of settings names and their new values.

            * 'mako_paths': a list of directories to prepend to the edxmako
                template lookup path.

    """

    changes = {
        'settings': {},
        'mako_paths': [],
    }
    path_project = path_theme / basename(settings.PROJECT_ROOT)
    path_templates = path_project / 'templates'
    path_static = path_project / 'static'
    path_locale = path_project / 'conf' / 'locale'
    path_favicon = path_project / 'static' / 'images' / 'favicon.ico'
    if path_templates.isdir():
        changes['settings']['TEMPLATE_DIRS'] = [path_templates] + settings.DEFAULT_TEMPLATE_ENGINE['DIRS']
        changes['mako_paths'].append(path_templates)
    if path_static.isdir():
        changes['settings']['STATICFILES_DIRS'] = [path_static] + settings.STATICFILES_DIRS
    if path_locale.isdir():
        changes['settings']['LOCALE_PATHS'] = [path_locale] + settings.LOCALE_PATHS
    if path_favicon.isfile():
        # TODO: Should this be unicode?
        changes['settings']['FAVICON_PATH'] = str(path_favicon)
    return changes


def enable_comprehensive_theme(theme_dir):
    """
    Add directories to relevant paths for comprehensive theming.
    """
    changes = comprehensive_theme_changes(theme_dir)

    # Use the changes
    for name, value in changes['settings'].iteritems():
        setattr(settings, name, value)
    for template_dir in changes['mako_paths']:
        edxmako.paths.add_lookup('main', template_dir, prepend=True)
