"""
File that manages how notification distribution scopes are handled
"""

import types
import abc
from django.db.models.query import ValuesQuerySet, ValuesListQuerySet

_SCOPE_RESOLVERS = {}


class NotificationUserScopeResolver(object):
    """
    Abstract interface that has one sole purpose
    to translate a scope_name, scope_context to
    a collection of user_ids as a list, function generator, or
    ValuesQuerySet/ValuesListQuerySet (only!!!)
    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def resolve(self, scope_name, scope_context, instance_context):
        """
        Convert scope_name with scope_context and instance_context to
        a collection of user_ids as a list, function generator, or
        ValuesQuerySet/ValuesListQuerySet (only!!!)
        """
        raise NotImplementedError()


class SingleUserScopeResolver(object):
    """
    Simple implementation for scope_name='user' where there must
    be a user_id inside the scope_context
    """

    def resolve(self, scope_name, scope_context, instance_context):  # pylint: disable=unused-argument
        """
        Convert scope_name with scope_context and instance_context to
        a collection of user_ids as a list, function generator, or
        ValuesQuerySet/ValuesListQuerySet (only!!!)
        """

        user_ids = None
        if scope_name == 'user':
            if 'user_id' in scope_context:
                user_ids = []
                user_ids.append(scope_context['user_id'])

        return user_ids


def register_user_scope_resolver(scope_name, instance, instance_context=None):
    """
    Adds a ScopeResolver to our list of resolvers. There can be more than
    one registration of a ScopeResolver for a single scope_name
    """
    global _CHANNEL_PROVIDERS  # pylint: disable=global-statement,global-variable-not-assigned

    if scope_name not in _SCOPE_RESOLVERS:
        _SCOPE_RESOLVERS[scope_name] = {}

    _SCOPE_RESOLVERS[scope_name][hash(instance)] = {}
    _SCOPE_RESOLVERS[scope_name][hash(instance)]['instance'] = instance
    _SCOPE_RESOLVERS[scope_name][hash(instance)]['instance_context'] = instance_context


def clear_user_scope_resolvers():
    """
    Removes all entries in our resolvers registry
    """

    _SCOPE_RESOLVERS.clear()


def has_user_scope_resolver(scope_name):
    """
    Returns true/false if there's a resolver for that scope_name
    """

    return scope_name in _SCOPE_RESOLVERS


def resolve_user_scope(scope_name, scope_context):
    """
    Given a scope and scope context this will go through all
    registered NotificationScopeResolvers and try to resolve it
    into a user_id which can be of type list, function generator, ValuesQuerySet, or
    ValuesListQuerySet (only!!!)
    """

    if not has_user_scope_resolver(scope_name):
        err_msg = (
            'Could not find scope resolver "{scope_name}"'.format(scope_name=scope_name)
        )
        raise TypeError(err_msg)

    user_ids = None
    for _, instance_info in _SCOPE_RESOLVERS[scope_name].iteritems():
        instance = instance_info['instance']
        user_ids = instance.resolve(scope_name, scope_context, instance_info['instance_context'])

    if not user_ids:
        # Could not resolve so return None
        return None

    if (not isinstance(user_ids, list) and
            not isinstance(user_ids, types.GeneratorType) and
            not isinstance(user_ids, ValuesListQuerySet) and
            not isinstance(user_ids, ValuesQuerySet)):

        err_msg = (
            'NotificationUserScopeResolver "{scope_name}" with context "{scope_context}" should return an instance '
            'of type list, GeneratorType, ValuesQuerySet, or ValuesListQuerySet. Type {arg_type} was returned!'
            .format(scope_name=scope_name, scope_context=scope_context, arg_type=type(user_ids))
        )
        raise TypeError(err_msg)

    return user_ids
