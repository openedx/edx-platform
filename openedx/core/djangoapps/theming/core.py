"""
Core logic for Comprehensive Theming.
"""

from django.conf import settings

import edxmako


def comprehensive_theme_changes(theme_dir):
    """
    Calculate the set of changes needed to enable a comprehensive theme.

    Arguments:
        theme_dir (path.path): the full path to the theming directory to use.

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

    templates_dir = theme_dir / "lms" / "templates"
    if templates_dir.isdir():
        changes['settings']['TEMPLATE_DIRS'] = [templates_dir] + settings.DEFAULT_TEMPLATE_ENGINE['DIRS']
        changes['mako_paths'].append(templates_dir)

    staticfiles_dir = theme_dir / "lms" / "static"
    if staticfiles_dir.isdir():
        changes['settings']['STATICFILES_DIRS'] = [staticfiles_dir] + settings.STATICFILES_DIRS

    locale_dir = theme_dir / "lms" / "conf" / "locale"
    if locale_dir.isdir():
        changes['settings']['LOCALE_PATHS'] = [locale_dir] + settings.LOCALE_PATHS

    favicon = theme_dir / "lms" / "static" / "images" / "favicon.ico"
    if favicon.isfile():
        changes['settings']['FAVICON_PATH'] = str(favicon)

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
