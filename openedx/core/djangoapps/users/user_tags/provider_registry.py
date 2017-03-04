"""
User Tag Provider Registry implemented using the platform's PluginManager.
"""
from openedx.core.lib.api.plugins import PluginManager
from openedx.core.lib.cache_utils import memoized


class UserTagProviderRegistry(PluginManager):
    """
    Registry for all of the user tag providers that have been
    made available.

    All user tag providers should implement `UserTagProvider`.
    """
    NAMESPACE = 'openedx.user_tag_provider'
    USE_PLUGIN_MANAGER = True

    @classmethod
    @memoized
    def get_registered_providers(cls):
        """
        Returns a set of all registered providers.

        Returns:
            {UserTagProvider} - All providers that are
                registered with the platform's PluginManager.
        """
        if cls.USE_PLUGIN_MANAGER:
            return set(cls.get_available_plugins().itervalues())
        else:
            return set()
