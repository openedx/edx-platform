"""
Utility functions for integration with Name Affirmation plugin
(https://github.com/edx/edx-name-affirmation)
"""

from edx_django_utils.plugins import PluginError, PluginManager


def is_name_affirmation_installed():
    """
    Returns boolean describing whether Name Affirmation plugin is installed.
    """
    manager = PluginManager()
    try:
        plugin = manager.get_plugin('edx_name_affirmation', 'lms.djangoapp')
        return bool(plugin)
    except PluginError:
        return False


def get_name_affirmation_service():
    """
    Returns Name Affirmation service which exposes API .
    If Name Affirmation is not installed, return None.
    """
    if is_name_affirmation_installed():
        # pylint: disable=import-error
        from edx_name_affirmation.services import NameAffirmationService
        return NameAffirmationService()

    return None
