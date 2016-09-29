"""
Core logic for Comprehensive Theming.
"""
import os
from django.conf import settings

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
        locale_dir = theme.path / "conf" / "locale"
        if locale_dir.isdir():
            settings.LOCALE_PATHS = (locale_dir, ) + settings.LOCALE_PATHS

        if theme.themes_base_dir not in settings.MAKO_TEMPLATES['main']:
            settings.MAKO_TEMPLATES['main'].insert(0, theme.themes_base_dir)

        customer_themes_dir = os.path.join(theme.themes_base_dir, 'customer_themes')
        if os.path.isdir(customer_themes_dir):
            settings.STATICFILES_DIRS.insert(0, ('customer_themes', customer_themes_dir))

        theme_root = settings.ENV_ROOT / "themes" / settings.THEME_NAME
        settings.STATICFILES_DIRS.append(
            (u'', theme_root / 'lms' / 'static')
        )
