"""
Core logic for Comprehensive Theming.
"""
import os.path
from path import Path

from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site

from edxmako.middleware import REQUEST_CONTEXT
from util.url import strip_port_from_host


def comprehensive_theme_changes(themes_dir):
    """
    Calculate the set of changes needed to enable a comprehensive theme.

    Arguments:
        themes_dir (path.path): the full path to the directory where all themse are listed.

    Returns:
        A dict indicating the changes to make:

            * 'settings': a dictionary of settings names and their new values.

            * 'template_paths': a list of directories to prepend to template
                lookup path.

    """

    changes = {
        'settings': {},
        'template_paths': [],
    }

    root_name = get_project_root_name()

    if themes_dir.isdir():
        changes['template_paths'].append(themes_dir)

    for theme_dir in os.listdir(themes_dir):
        staticfiles_dir = os.path.join(themes_dir, theme_dir, root_name, "static")
        if staticfiles_dir.isdir():
            changes['settings']['STATICFILES_DIRS'] = [staticfiles_dir] + settings.STATICFILES_DIRS

            favicon = os.path.join(staticfiles_dir, "images", "favicon.ico")
            if favicon.isfile():
                changes['settings']['FAVICON_PATH'] = str(favicon)

        locale_dir = os.path.join(themes_dir, theme_dir, root_name, "conf", "locale")
        if locale_dir.isdir():
            changes['settings']['LOCALE_PATHS'] = [locale_dir] + settings.LOCALE_PATHS

    return changes


def enable_comprehensive_theme(theme_dir):
    """
    Add directories to relevant paths for comprehensive theming.
    """
    changes = comprehensive_theme_changes(theme_dir)

    # Use the changes
    for name, value in changes['settings'].iteritems():
        setattr(settings, name, value)
    for template_dir in changes['template_paths']:
        settings.DEFAULT_TEMPLATE_ENGINE['DIRS'].insert(0, template_dir)
        settings.MAKO_TEMPLATES['main'].insert(0, template_dir)


def get_template_path(relative_path):
        """
        Returns a path (string) to a Mako template, if one is found in theme directory
        otherwise return what is passed.
        """
        request = getattr(REQUEST_CONTEXT, 'request', None)
        if not request:
            return relative_path

        domain = get_current_site(request).domain
        domain = strip_port_from_host(domain)
        root_name = get_project_root_name()
        template_path = "/".join([
            settings.COMPREHENSIVE_THEME_DIR,
            domain,
            root_name,
            "templates"
        ])

        search_path = os.path.join(template_path, relative_path)
        if os.path.isfile(search_path):
            path = '/{domain}/{root_name}/templates/{relative_path}'.format(
                domain=domain,
                root_name=root_name,
                relative_path=relative_path,
            )
            return path
        else:
            return relative_path


def get_project_root_name():
    """
    :return:
    """
    root = Path(settings.PROJECT_ROOT)
    if root.name == "":
        root = root.parent
    return root.name
