"""
Helper methods for working with learning contexts
"""
from edx_django_utils.plugins import PluginManager
from opaque_keys import OpaqueKey
from opaque_keys.edx.keys import LearningContextKey, UsageKeyV2

from openedx.core.djangoapps.xblock.apps import get_xblock_app_config


class LearningContextPluginManager(PluginManager):
    """
    Plugin manager that uses stevedore extension points (entry points) to allow
    learning contexts to register as plugins.

    The key of the learning context must match the CANONICAL_NAMESPACE of its
    LearningContextKey
    """
    NAMESPACE = 'openedx.learning_context'


_learning_context_cache = {}


def get_learning_context_impl(key):
    """
    Given an opaque key, get the implementation of its learning context.

    Returns a subclass of LearningContext

    Raises TypeError if the specified key isn't a type that has a learning
    context.
    Raises PluginError if there is some misconfiguration causing the context
    implementation to not be installed.
    """
    if isinstance(key, LearningContextKey):
        context_type = key.CANONICAL_NAMESPACE  # e.g. 'lib'
    elif isinstance(key, UsageKeyV2):
        context_type = key.context_key.CANONICAL_NAMESPACE
    elif isinstance(key, OpaqueKey):
        # Maybe this is an older modulestore key etc.
        raise TypeError("Opaque key {} does not have a learning context.".format(key))
    else:
        raise TypeError("key '{}' is not an opaque key. You probably forgot [KeyType].from_string(...)".format(key))

    try:
        return _learning_context_cache[context_type]
    except KeyError:
        # Load this learning context type.
        params = get_xblock_app_config().get_learning_context_params()
        _learning_context_cache[context_type] = LearningContextPluginManager.get_plugin(context_type)(**params)
        return _learning_context_cache[context_type]
