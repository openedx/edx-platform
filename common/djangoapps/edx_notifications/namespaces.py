"""
Methods regarding how namespaces are managed
"""

import abc

_NAMESPACE_RESOLVER = None


class NotificationNamespaceResolver(object):
    """
    Abstract interface that provides and interface
    for the Notification subsystem to get more
    runtime context around namespaces.

    Namespace resolvers will return this information as a dict:

    {
        'namespace': <String> ,
        'display_name': <String representing a human readible name for the namespace>,
        'features': {
            'digests': <boolean, saying if namespace supports a digest>
        },
        'default_user_resolver': <pointer to a UserScopeResolver instance>
    }

    or None if the handler cannot resolve it
    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def resolve(self, namespace, instance_context):
        """
        Namespace resolvers will return this information as a dict:

        {
            'namespace': <String> ,
            'display_name': <String representing a human readible name for the namespace>,
            'features': {
                'digests': <boolean, saying if namespace supports a digest>
            },
            'default_user_resolver': <pointer to a UserScopeResolver instance>
        }
        or None if the handler cannot resolve it
        """
        raise NotImplementedError()


class DefaultNotificationNamespaceResolver(NotificationNamespaceResolver):
    """
    Default namespace resolver
    """

    def resolve(self, namespace, instance_context):
        """
        Default implementation
        """
        return {
            'namespace': namespace,
            'display_name': namespace,
            'features': {
                'digests': False
            },
            'default_user_resolver': None
        }


def register_namespace_resolver(instance, instance_context=None):
    """
    Right now we only support a singleton
    """

    global _NAMESPACE_RESOLVER  # pylint: disable=global-statement
    _NAMESPACE_RESOLVER = {
        'instance': instance,
        'instance_context': instance_context,
    }


def resolve_namespace(namespace):
    """
    Call into the registered Namesapce Resolver
    """

    if not _NAMESPACE_RESOLVER or not _NAMESPACE_RESOLVER['instance']:
        return None

    return _NAMESPACE_RESOLVER['instance'].resolve(namespace, _NAMESPACE_RESOLVER['instance_context'])
