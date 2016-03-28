"""
Core logic for Comprehensive Theming.
"""
import os.path
from path import Path as path
from django.conf import settings

from .helpers import (
    get_project_root_name,
)


def enable_comprehensive_theming(themes_dir):
    """
    Add directories to relevant paths for comprehensive theming.
    :param themes_dir: path to base theme directory
    """
    if isinstance(themes_dir, basestring):
        themes_dir = path(themes_dir)

    if themes_dir.isdir():
        settings.DEFAULT_TEMPLATE_ENGINE['DIRS'].insert(0, themes_dir)
        settings.MAKO_TEMPLATES['main'].insert(0, themes_dir)

    for theme_dir in os.listdir(themes_dir):
        staticfiles_dir = os.path.join(themes_dir, theme_dir, get_project_root_name(), "static")
        if staticfiles_dir.isdir():
            settings.STATICFILES_DIRS = settings.STATICFILES_DIRS + [staticfiles_dir]

        locale_dir = os.path.join(themes_dir, theme_dir, get_project_root_name(), "conf", "locale")
        if locale_dir.isdir():
            settings.LOCALE_PATHS = (locale_dir, ) + settings.LOCALE_PATHS
