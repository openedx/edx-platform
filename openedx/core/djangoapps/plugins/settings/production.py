"""
Production environment variables for `edx_django_utils.plugins` plugins.
"""

from ..constants import plugins_locale_root


def plugin_settings(settings):
    """
    Settings for the `edx_django_utils.plugins` plugins.
    """
    locale_root = settings.REPO_ROOT / plugins_locale_root
    if locale_root.isdir():
        for plugin_locale in locale_root.listdir():
            # Add the plugin locale directory only if it's a non-empty directory
            if plugin_locale.isdir() and plugin_locale.listdir():
                settings.LOCALE_PATHS.append(plugin_locale)
