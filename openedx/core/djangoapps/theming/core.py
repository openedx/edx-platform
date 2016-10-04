"""
Core logic for Comprehensive Theming.
"""
from django.conf import settings
from path import Path as path

from .helpers import get_themes

from logging import getLogger
logger = getLogger(__name__)  # pylint: disable=invalid-name


def enable_theming():
    """
    Add directories and relevant paths to settings for comprehensive theming.
    """
    # Deprecated Warnings
    if hasattr(settings, "COMPREHENSIVE_THEME_DIR"):
        logger.warning(
            "\033[93m \nDeprecated: "
            "\n\tCOMPREHENSIVE_THEME_DIR setting has been deprecated in favor of COMPREHENSIVE_THEME_DIRS.\033[00m"
        )

    for theme in get_themes():
        if theme.themes_base_dir not in settings.MAKO_TEMPLATES['main']:
            settings.MAKO_TEMPLATES['main'].insert(0, theme.themes_base_dir)

    _add_theming_locales()


def _add_theming_locales():
    """
    Add locale paths to settings for comprehensive theming.
    """
    theme_locale_paths = settings.COMPREHENSIVE_THEME_LOCALE_PATHS
    for locale_path in theme_locale_paths:
        settings.LOCALE_PATHS += (path(locale_path), )  # pylint: disable=no-member
